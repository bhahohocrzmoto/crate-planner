from flask import Flask, render_template, request
import plotly.graph_objs as go
import plotly.offline as pyo

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_div = ""
    topdown_plot_div = ""

    if request.method == 'POST':
        # Read truck dimensions
        truck_length = float(request.form['truck_length'])
        truck_width = float(request.form['truck_width'])
        truck_height = float(request.form['truck_height'])

        def convert(value_str, unit):
            value = float(value_str)
            if unit == 'cm':
                return value / 100.0
            return value

        truck_length = convert(truck_length, request.form['truck_length_unit'])
        truck_width = convert(truck_width, request.form['truck_width_unit'])
        truck_height = convert(truck_height, request.form['truck_height_unit'])

        # Read crates
        crates = []
        crate_idx = 1
        while True:
            length_field = f'crate{crate_idx}_length'
            width_field = f'crate{crate_idx}_width'
            height_field = f'crate{crate_idx}_height'
            label_field = f'crate{crate_idx}_label'
            stackable_field = f'crate{crate_idx}_stackable'
            stack_target_field = f'crate{crate_idx}_stack_target'

            if length_field in request.form:
                l = convert(request.form[length_field], request.form[f'crate{crate_idx}_length_unit'])
                w = convert(request.form[width_field], request.form[f'crate{crate_idx}_width_unit'])
                h = convert(request.form[height_field], request.form[f'crate{crate_idx}_height_unit'])
                label = request.form[label_field] or f'Crate {crate_idx}'
                stackable = request.form[stackable_field]
                stack_target = request.form[stack_target_field].strip()

                crate = {
                    'label': label,
                    'l': l,
                    'w': w,
                    'h': h,
                    'stackable': stackable,
                    'stack_target': stack_target,
                    'x': None,
                    'y': None,
                    'z': None
                }
                crates.append(crate)
                crate_idx += 1
            else:
                break

        # Place crates
        placed_crates = []
        for crate in crates:
            if crate['stackable'] == 'Yes' and crate['stack_target']:
                target_label = crate['stack_target']
                target_crate = next((c for c in placed_crates if c['label'] == target_label), None)
                if target_crate:
                    crate['x'] = target_crate['x']
                    crate['y'] = target_crate['y']
                    crate['z'] = target_crate['z'] + target_crate['h']
                else:
                    crate['x'] = 0
                    crate['y'] = 0
                    crate['z'] = 0
            else:
                # Place next to previous crates in X direction
                total_length = sum(c['l'] for c in placed_crates if c['z'] == 0)
                crate['x'] = total_length
                crate['y'] = 0
                crate['z'] = 0

            placed_crates.append(crate)

        # Build 3D plot
        fig = go.Figure()

        # Truck boundary
        fig.add_trace(go.Mesh3d(
            x=[0, truck_length, truck_length, 0, 0, truck_length, truck_length, 0],
            y=[0, 0, truck_width, truck_width, 0, 0, truck_width, truck_width],
            z=[0, 0, 0, 0, truck_height, truck_height, truck_height, truck_height],
            i=[0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 5, 4],
            j=[1, 2, 3, 0, 5, 6, 7, 4, 4, 5, 6, 7],
            k=[5, 6, 7, 4, 0, 1, 2, 3, 1, 2, 3, 0],
            opacity=0.1,
            color='lightgray'
        ))

        # Colors
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow', 'lime', 'pink']

        # Plot crates
        for idx, crate in enumerate(placed_crates):
            color = colors[idx % len(colors)]
            x0 = crate['x']
            y0 = crate['y']
            z0 = crate['z']
            l = crate['l']
            w = crate['w']
            h = crate['h']

            fig.add_trace(go.Mesh3d(
                x=[x0, x0 + l, x0 + l, x0, x0, x0 + l, x0 + l, x0],
                y=[y0, y0, y0 + w, y0 + w, y0, y0, y0 + w, y0 + w],
                z=[z0, z0, z0, z0, z0 + h, z0 + h, z0 + h, z0 + h],
                i=[0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 5, 4],
                j=[1, 2, 3, 0, 5, 6, 7, 4, 4, 5, 6, 7],
                k=[5, 6, 7, 4, 0, 1, 2, 3, 1, 2, 3, 0],
                opacity=0.7,
                color=color,
                name=crate['label']
            ))

            # Add label as text annotation
            fig.add_trace(go.Scatter3d(
                x=[x0 + l/2],
                y=[y0 + w/2],
                z=[z0 + h/2],
                mode='text',
                text=[crate['label']],
                textposition='middle center'
            ))

        fig.update_layout(
            scene=dict(
                xaxis_title='Length (m)',
                yaxis_title='Width (m)',
                zaxis_title='Height (m)',
                xaxis=dict(range=[0, truck_length]),
                yaxis=dict(range=[0, truck_width]),
                zaxis=dict(range=[0, truck_height])
            ),
            title='3D Crate Planner',
            margin=dict(l=0, r=0, b=0, t=50)
        )

        plot_div = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')

        # Build 2D top-down floorplan (X-Y only)
        topdown_fig = go.Figure()
        for idx, crate in enumerate(placed_crates):
            color = colors[idx % len(colors)]
            x = crate['x']
            y = crate['y']
            l = crate['l']
            w = crate['w']
            label = crate['label']

            topdown_fig.add_shape(
                type='rect',
                x0=x,
                x1=x + l,
                y0=y,
                y1=y + w,
                line=dict(color='black'),
                fillcolor=color
            )

            topdown_fig.add_trace(go.Scatter(
                x=[x + l / 2],
                y=[y + w / 2],
                text=[label],
                mode='text'
            ))

        topdown_fig.update_layout(
            xaxis=dict(range=[0, truck_length], title='Length (m)', scaleanchor='y', scaleratio=1),
            yaxis=dict(range=[0, truck_width], title='Width (m)'),
            title='Top-down Floorplan (Truck view)',
            margin=dict(l=0, r=0, b=0, t=50)
        )

        topdown_plot_div = pyo.plot(topdown_fig, output_type='div', include_plotlyjs='cdn')

    return render_template('index.html', plot_div=plot_div, topdown_plot_div=topdown_plot_div)

if __name__ == '__main__':
    app.run(debug=True)
