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

        # Read Crate 1 dimensions
        crate1_length = float(request.form['crate1_length'])
        crate1_width = float(request.form['crate1_width'])
        crate1_height = float(request.form['crate1_height'])

        # Read units and convert to meters if needed
        def convert(value_str, unit):
            value = float(value_str)
            if unit == 'cm':
                return value / 100.0
            return value

        truck_length = convert(truck_length, request.form['truck_length_unit'])
        truck_width = convert(truck_width, request.form['truck_width_unit'])
        truck_height = convert(truck_height, request.form['truck_height_unit'])

        crate1_length = convert(crate1_length, request.form['crate1_length_unit'])
        crate1_width = convert(crate1_width, request.form['crate1_width_unit'])
        crate1_height = convert(crate1_height, request.form['crate1_height_unit'])

        # Simple placement: crate at (0,0,0)
        crates = [
            (crate1_length, crate1_width, crate1_height, 0, 0, 0)
        ]

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

        # Draw crates
        for idx, (l, w, h, x, y, z) in enumerate(crates):
            fig.add_trace(go.Mesh3d(
                x=[x, x + l, x + l, x, x, x + l, x + l, x],
                y=[y, y, y + w, y + w, y, y, y + w, y + w],
                z=[z, z, z, z, z + h, z + h, z + h, z + h],
                i=[0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 5, 4],
                j=[1, 2, 3, 0, 5, 6, 7, 4, 4, 5, 6, 7],
                k=[5, 6, 7, 4, 0, 1, 2, 3, 1, 2, 3, 0],
                opacity=0.7,
                color='blue'
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

    return render_template('index.html', plot_div=plot_div)

if __name__ == '__main__':
    app.run(debug=True)
