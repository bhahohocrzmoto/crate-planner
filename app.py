from flask import Flask, render_template_string, request
import plotly.graph_objs as go
from py3dbp import Packer, Bin, Item

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    plot_div = ""
    if request.method == "POST":
        # Read truck size
        truck_length = float(request.form["truck_length"]) * (0.01 if request.form["truck_length_unit"] == "cm" else 1)
        truck_width = float(request.form["truck_width"]) * (0.01 if request.form["truck_width_unit"] == "cm" else 1)
        truck_height = float(request.form["truck_height"]) * (0.01 if request.form["truck_height_unit"] == "cm" else 1)

        # Create truck bin
        packer = Packer()
        truck_bin = Bin("Truck", truck_length, truck_width, truck_height, 100000)
        packer.add_bin(truck_bin)

        # Read crates
        crate_count = len([key for key in request.form if key.startswith("crate") and key.endswith("_label")])
        crate_data = []

        for i in range(1, crate_count + 1):
            label = request.form.get(f"crate{i}_label")
            length = float(request.form.get(f"crate{i}_length")) * (0.01 if request.form.get(f"crate{i}_length_unit") == "cm" else 1)
            width = float(request.form.get(f"crate{i}_width")) * (0.01 if request.form.get(f"crate{i}_width_unit") == "cm" else 1)
            height = float(request.form.get(f"crate{i}_height")) * (0.01 if request.form.get(f"crate{i}_height_unit") == "cm" else 1)
            stackable = request.form.get(f"crate{i}_stackable")
            stack_target = request.form.get(f"crate{i}_stack_target") if stackable == "Yes" else None

            # Save crate info
            crate_data.append({
                "label": label,
                "length": length,
                "width": width,
                "height": height,
                "stackable": stackable,
                "stack_target": stack_target
            })

            # Add item to packer
            item = Item(label, length, width, height, 1)  # weight=1
            packer.add_item(item)

        # Pack
        packer.pack()

        # Map crate label to position (to help us with stacking)
        crate_positions = {}

        # First pass: record positions from packer
        for item in truck_bin.items:
            crate_positions[item.name] = {
                "x": item.position[0],
                "y": item.position[1],
                "z": item.position[2],
                "length": item.length,
                "width": item.width,
                "height": item.height
            }

        # Second pass: apply stacking manually if needed
        for crate in crate_data:
            if crate["stackable"] == "Yes" and crate["stack_target"]:
                target = crate_positions.get(crate["stack_target"])
                if target:
                    # Force position: same x/y, z stacked on top
                    crate_positions[crate["label"]] = {
                        "x": target["x"],
                        "y": target["y"],
                        "z": target["z"] + target["height"],
                        "length": crate["length"],
                        "width": crate["width"],
                        "height": crate["height"]
                    }

        # Plotly visualization
        fig = go.Figure()

        # Plot truck container
        fig.add_trace(go.Mesh3d(
            x=[0, truck_length, truck_length, 0, 0, truck_length, truck_length, 0],
            y=[0, 0, truck_width, truck_width, 0, 0, truck_width, truck_width],
            z=[0, 0, 0, 0, truck_height, truck_height, truck_height, truck_height],
            opacity=0.1,
            color='gray',
            name='Truck'
        ))

        # Colors
        colors = ["red", "blue", "green", "orange", "purple", "cyan", "magenta"]

        # Plot crates
        for idx, (label, pos) in enumerate(crate_positions.items()):
            color = colors[idx % len(colors)]
            x0, y0, z0 = pos["x"], pos["y"], pos["z"]
            l, w, h = pos["length"], pos["width"], pos["height"]

            fig.add_trace(go.Mesh3d(
                x=[x0, x0 + l, x0 + l, x0, x0, x0 + l, x0 + l, x0],
                y=[y0, y0, y0 + w, y0 + w, y0, y0, y0 + w, y0 + w],
                z=[z0, z0, z0, z0, z0 + h, z0 + h, z0 + h, z0 + h],
                opacity=0.7,
                color=color,
                name=label
            ))

            # Add label text in center
            fig.add_trace(go.Scatter3d(
                x=[x0 + l / 2],
                y=[y0 + w / 2],
                z=[z0 + h / 2],
                mode='text',
                text=[label],
                textposition='middle center',
                textfont=dict(color='black', size=12),
                showlegend=False
            ))

        # Optional: add connector lines for stacking
        for crate in crate_data:
            if crate["stackable"] == "Yes" and crate["stack_target"]:
                src = crate_positions[crate["stack_target"]]
                dst = crate_positions[crate["label"]]
                # Line from center of target to center of stacked crate
                fig.add_trace(go.Scatter3d(
                    x=[src["x"] + src["length"] / 2, dst["x"] + dst["length"] / 2],
                    y=[src["y"] + src["width"] / 2, dst["y"] + dst["width"] / 2],
                    z=[src["z"] + src["height"], dst["z"]],
                    mode="lines",
                    line=dict(color="gray", width=4),
                    showlegend=False
                ))

        # Layout
        fig.update_layout(
            scene=dict(
                xaxis_title="Length (m)",
                yaxis_title="Width (m)",
                zaxis_title="Height (m)",
                aspectmode='data'
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )

        # Render plot
        plot_div = fig.to_html(full_html=False)

    # Serve your current HTML (already correct!)
    with open("templates/index.html", "r") as f:
        html_template = f.read()

    return render_template_string(html_template, plot_div=plot_div)

# Run locally
if __name__ == "__main__":
    app.run(debug=True)
