from flask import Flask, render_template, request
import plotly.graph_objs as go
import plotly.offline as pyo
from py3dbp import Packer, Bin, Item

app = Flask(__name__)

def convert(value_str, unit):
    value = float(value_str)
    if unit == 'cm':
        return value / 100.0
    return value

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_div = ""

    if request.method == 'POST':
        # Read truck size
        truck_length = convert(request.form['truck_length'], request.form['truck_length_unit'])
        truck_width  = convert(request.form['truck_width'], request.form['truck_width_unit'])
        truck_height = convert(request.form['truck_height'], request.form['truck_height_unit'])

        # Read all crates
        crates = []
        crate_idx = 1

        while True:
            label_field = f'crate{crate_idx}_label'
            length_field = f'crate{crate_idx}_length'
            width_field  = f'crate{crate_idx}_width'
            height_field = f'crate{crate_idx}_height'
            stackable_field = f'crate{crate_idx}_stackable'
            stack_target_field = f'crate{crate_idx}_stack_target'

            if label_field in request.form:
                label = request.form[label_field]
                l = convert(request.form[length_field], request.form[f'crate{crate_idx}_length_unit'])
                w = convert(request.form[width_field], request.form[f'crate{crate_idx}_width_unit'])
                h = convert(request.form[height_field], request.form[f'crate{crate_idx}_height_unit'])
                stackable = request.form[stackable_field]
                stack_target = request.form.get(stack_target_field, '')

                crates.append({
                    'label': label,
                    'l': l,
                    'w': w,
                    'h': h,
                    'stackable': stackable,
                    'stack_target': stack_target,
                })

                crate_idx += 1
            else:
                break

        # Pack with py3dbp
        packer = Packer()
        bin1 = Bin("Truck", truck_length, truck_width, truck_height, 10000)
        packer.add_bin(bin1)

        for crate in crates:
            item = Item(
                crate['label'],
                crate['l'],
                crate['w'],
                crate['h'],
                1,  # weight
                False,  # rotation disabled for now
            )
            packer.add_item(item)

        packer.pack()

        # Create 3D Plotly plot
        fig = go.Figure()

        # Draw truck box (transparent)
        fig.add_trace(go.Mesh3d(
            x=[0, truck_length, truck_length, 0, 0, truck_length, truck_length, 0],
            y=[0, 0, truck_width, truck_width, 0, 0, truck_width, truck_width],
            z=[0, 0, 0, 0, truck_height, truck_height, truck_height, truck_height],
            i=[0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 5, 4],
            j=[1, 2, 3, 0, 5, 6, 7, 4, 4, 5, 6, 7],
            k=[5, 6, 7, 4, 0, 1, 2, 3, 1, 2, 3, 0],
            opacity=0.1,
            color='lightgray',
            name='Truck'
        ))

        colors = ['blue', 'red', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow']

        for idx, item in enumerate(bin1.items):
            x0 = item.position[0]
            y0 = item.position[1]
            z0 = item.position[2]

            l = item.width
            w = item.height
            h = item.depth

            color = colors[idx % len(colors)]

            fig.add_trace(go.Mesh3d(
                x=[x0, x0+l, x0+l, x0, x0, x0+l, x0+l, x0],
                y=[y0, y0, y0+w, y0+w, y0, y0, y0+w, y0+w],
                z=[z0, z0, z0, z0, z0+h, z0+h, z0+h, z0+h],
                i=[0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 5, 4],
                j=[1, 2, 3, 0, 5, 6, 7, 4, 4, 5, 6, 7],
                k=[5, 6, 7, 4, 0, 1, 2, 3, 1, 2, 3, 0],
                opacity=0.7,
                color=color,
                name=item.name
            ))

            # Add label text at center of crate
            fig.add_trace(go.Scatter3d(
                x=[x0 + l/2],
                y=[y0 + w/2],
                z=[z0 + h/2],
                mode='text',
                text=[item.name],
                textposition='middle center',
                textfont=dict(size=12, color='black'),
                showlegend=False
            ))

        # Final layout
        fig.update_layout(
            scene=dict(
                xaxis_title='Length (m)',
                yaxis_title='Width (m)',
                zaxis_title='Height (m)',
                xaxis=dict(range=[0, truck_length]),
                yaxis=dict(range=[0, truck_width]),
                zaxis=dict(range=[0, truck_height]),
            ),
            title='3D Crate Planner (True 3D)',
            margin=dict(l=0, r=0, b=0, t=50)
        )

        plot_div = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')

    return render_template('index.html', plot_div=plot_div)

if __name__ == '__main__':
    app.run(debug=True)
