from flask import Flask, render_template, request
import plotly.graph_objs as go
import plotly.offline as pyo
from py3dbp import Packer, Bin, Item

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_div = ""
    top_view_div = ""

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

        # Build Packer
        packer = Packer()
        bin = Bin("Truck", truck_length, truck_width, truck_height, 99999)  # very high weight limit
        packer.add_bin(bin)

        # Read crates
        crate_idx = 1
        crate_data = []

        while True:
            label_field = f'crate{crate_idx}_label'
            length_field = f'crate{crate_idx}_length'
            width_field = f'crate{crate_idx}_width'
            height_field = f'crate{crate_idx}_height'
            stackable_field = f'crate{crate_idx}_stackable'
            stack_target_field = f'crate{crate_idx}_stack_target'

            if length_field in request.form:
                label = request.form.get(label_field, f"Crate {crate_idx}")
                l = convert(request.form[length_field], request.form[f'crate{crate_idx}_length_unit'])
                w = convert(request.form[width_field], request.form[f'crate{crate_idx}_width_unit'])
                h = convert(request.form[height_field], request.form[f'crate{crate_idx}_height_unit'])
                stackable = request.form.get(stackable_field, 'No')
                stack_target = request.form.get(stack_target_field, '').strip()

                crate_data.append({
                    'label': label,
                    'l': l,
                    'w': w,
                    'h': h,
                    'stackable': stackable,
                    'stack_target': stack_target
                })

                crate_idx += 1
            else:
                break

        # ADD items to packer
        for crate in crate_data:
            item = Item(
                crate['label'],
                crate['l'],
                crate['w'],
                crate['h'],
                1  # weight can be 1 for now
            )
            packer.add_item(item)

        # Pack!
        packer.pack()

        # Visualize
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

        for idx, item in enumerate(bin.items):
            x = item.position[0]
            y = item.position[1]
            z = item.position[2]
            l = item.get_dimension()[0]
            w = item.get_dimension()[1]
            h = item.get_dimension()[2]
            label = item.name

            color = colors[idx % len(colors)]

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

            # Add label as text
            fig.add_trace(go.Scatter3d(
                x=[x + l / 2],
                y=[y + w / 2],
                z=[z + h / 2],
                mode='text',
                text=[label],
                textposition='middle center',
                showlegend=False
            ))

        # Set scene
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
