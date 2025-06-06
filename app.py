from flask import Flask, render_template, request
import plotly.graph_objs as go
import plotly.offline as pyo

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_div = ""

    if request.method == 'POST':
        # Read truck dimensions
        def convert(val, unit):
            v = float(val)
            if unit == 'cm':
                v /= 100.0
            return v

        truck_length = convert(request.form['truck_length'], request.form['truck_length_unit'])
        truck_width = convert(request.form['truck_width'], request.form['truck_width_unit'])
        truck_height = convert(request.form['truck_height'], request.form['truck_height_unit'])

        total_crates = int(request.form['total_crates'])

        crates = []

        # Read crate info
        for i in range(1, total_crates + 1):
            label = request.form.get(f'crate{i}_label', f'Crate {i}')
            l = convert(request.form[f'crate{i}_length'], request.form[f'crate{i}_length_unit'])
            w = convert(request.form[f'crate{i}_width'], request.form[f'crate{i}_width_unit'])
            h = convert(request.form[f'crate{i}_height'], request.form[f'crate{i}_height_unit'])
            stackable = request.form.get(f'crate{i}_stackable', 'no')
            stack_target = request.form.get(f'crate{i}_stack_target') if stackable == 'yes' else None

            crates.append({
                'label': label,
                'l': l,
                'w': w,
                'h': h,
                'stackable': stackable,
                'stack_target': stack_target,
                'x': None, 'y': None, 'z': None
            })

        # Simple placement algorithm
        occupied = []  # occupied zones [(x,y,z,w,l,h)]

        for idx, crate in enumerate(crates):
            if crate['stackable'] == 'yes' and crate['stack_target']:
                target_idx = int(crate['stack_target']) - 1
                target_crate = crates[target_idx]

                crate['x'] = target_crate['x']
                crate['y'] = target_crate['y']
                crate['z'] = target_crate['z'] + target_crate['h']
            else:
                # place on floor, find next available X position
                current_x = sum(c['l'] for c in crates[:idx] if c['z'] == 0 or c['z'] is None)
                crate['x'] = current_x
                crate['y'] = 0
                crate['z'] = 0

            # Save occupied area
            occupied.append((
                crate['x'], crate['y'], crate['z'],
                crate['l'], crate['w'], crate['h']
            ))

        # Plot
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

        colors = ['blue', 'red', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow', 'lime', 'pink']

        for idx, crate in enumerate(crates):
            x = crate['x']
            y = crate['y']
            z = crate['z']
            l = crate['l']
            w = crate['w']
            h = crate['h']
            label = crate['label']
            color = colors[idx % len(colors)]

            # Draw crate
            fig.add_trace(go.Mesh3d(
                x=[x, x + l, x + l, x, x, x + l, x + l, x],
                y=[y, y, y + w, y + w, y, y, y + w, y + w],
                z=[z, z, z, z, z + h, z + h, z + h, z + h],
                i=[0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 5, 4],
                j=[1, 2, 3, 0, 5, 6, 7, 4, 4, 5, 6, 7],
                k=[5, 6, 7, 4, 0, 1, 2, 3, 1, 2, 3, 0],
                opacity=0.7,
                color=color,
                name=label
            ))

            # Add label as text point
            fig.add_trace(go.Scatter3d(
                x=[x + l/2],
                y=[y + w/2],
                z=[z + h + 0.1],
                mode='text',
                text=[label],
                textposition='top center',
                textfont=dict(size=12, color='black')
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

    return render_template('index.html', plot_div=plot_div)

if __name__ == '__main__':
    app.run(debug=True)
