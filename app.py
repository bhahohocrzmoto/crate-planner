from flask import Flask, render_template, request
import plotly.graph_objs as go
import plotly.offline as pyo

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_div = ""

    if request.method == 'POST':
        # Read truck dimensions
        truck_length = float(request.form['truck_length'])
        truck_width = float(request.form['truck_width'])
        truck_height = float(request.form['truck_height'])

        # Convert function
        def convert(value_str, unit):
            value = float(value_str)
            if unit == 'cm':
                return value / 100.0
            return value

        truck_length = convert(truck_length, request.form['truck_length_unit'])
        truck_width = convert(truck_width, request.form['truck_width_unit'])
        truck_height = convert(truck_height, request.form['truck_height_unit'])

        # Now loop over crates:
        crates = []
        crate_idx = 1

        while True:
            length_field = f'crate{crate_idx}_length'
            width_field = f'crate{crate_idx}_width'
            height_field = f'crate{crate_idx}_height'

            length_unit_field = f'crate{crate_idx}_length_unit'
            width_unit_field = f'crate{crate_idx}_width_unit'
            height_unit_field = f'crate{crate_idx}_height_unit'

            if length_field in request.form:
                # Read crate dimensions
                l = convert(request.form[length_field], request.form[length_unit_field])
                w = convert(request.form[width_field], request.form[width_unit_field])
                h = convert(request.form[height_field], request.form[height_unit_field])

                # Simple placement: next to previous one in X direction
                x = sum(c[0] for c in crates)
                y = 0
                z = 0

                crates.append((l, w, h, x, y, z))

                crate_idx += 1
            else:
                break

        # Build figure
        fig = go.Figure()

        # Truck boundary (transparent box)
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

        # Example color list
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow', 'lime', 'pink']

        # Draw all crates
        for idx, (l, w, h, x, y, z) in enumerate(crates):
            color = colors[idx % len(colors)]

            fig.add_trace(go.Mesh3d(
                x=[x, x + l, x + l, x, x, x + l, x + l, x],
                y=[y, y, y + w, y + w, y, y, y + w, y + w],
                z=[z, z, z, z, z + h, z + h, z + h, z + h],
                i=[0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 5, 4],
                j=[1, 2, 3, 0, 5, 6, 7, 4, 4, 5, 6, 7],
                k=[5, 6, 7, 4, 0, 1, 2, 3, 1, 2, 3, 0],
                opacity=0.7,
                color=color
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
            title='3D Crate Planner',
            margin=dict(l=0, r=0, b=0, t=50)
        )

        plot_div = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')

    # Always return the page
    return render_template('index.html', plot_div=plot_div)

if __name__ == '__main__':
    app.run(debug=True)
