from flask import Flask, render_template, request
import plotly.graph_objs as go
import plotly.offline as pyo

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_div = ""
    if request.method == 'POST':
        # Read truck dimensions from form
        truck_length = float(request.form['truck_length'])
        truck_width = float(request.form['truck_width'])
        truck_height = float(request.form['truck_height'])

        # Read Crate 1 dimensions from form
        crate1_length = float(request.form['crate1_length'])
        crate1_width = float(request.form['crate1_width'])
        crate1_height = float(request.form['crate1_height'])

        # Simple placement: place crate at origin (0,0,0)
        x, y, z = 0, 0, 0
        l, w, h = crate1_length, crate1_width, crate1_height

        # Create figure
        fig = go.Figure()

        # Draw truck as transparent box (outline)
        fig.add_trace(go.Mesh3d(
            x=[0, truck_length, truck_length, 0, 0, truck_length, truck_length, 0],
            y=[0, 0, truck_width, truck_width, 0, 0, truck_width, truck_width],
            z=[0, 0, 0, 0, truck_height, truck_height, truck_height, truck_height],
            opacity=0.1,
            color='gray'
        ))

        # Draw Crate 1
        fig.add_trace(go.Mesh3d(
            x=[x, x + l, x + l, x, x, x + l, x + l, x],
            y=[y, y, y + w, y + w, y, y, y + w, y + w],
            z=[z, z, z, z, z + h, z + h, z + h, z + h],
            color='blue',
            opacity=0.5
        ))

        fig.update_layout(
            scene=dict(
                xaxis_title='Length',
                yaxis_title='Width',
                zaxis_title='Height'
            )
        )

        plot_div = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')

    return render_template('index.html', plot_div=plot_div)

if __name__ == '__main__':
    app.run(debug=True)
