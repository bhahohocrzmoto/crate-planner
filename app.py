from flask import Flask, render_template, request
import plotly.graph_objs as go
import plotly.offline as pyo

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    plot_div = ""
    if request.method == 'POST':
        # Example: fixed crate (we will later replace with user input)
        x, y, z, l, w, h = 0, 0, 0, 1, 1, 1
        fig = go.Figure(data=[go.Mesh3d(
            x=[x, x + l, x + l, x, x, x + l, x + l, x],
            y=[y, y, y + w, y + w, y, y, y + w, y + w],
            z=[z, z, z, z, z + h, z + h, z + h, z + h],
            color='blue',
            opacity=0.5
        )])
        plot_div = pyo.plot(fig, output_type='div', include_plotlyjs='cdn')

    return render_template('index.html', plot_div=plot_div)

if __name__ == '__main__':
    app.run(debug=True)
