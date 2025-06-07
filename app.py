from flask import Flask, render_template, request
import plotly.graph_objs as go
from py3dbp import Packer, Bin, Item

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    plot_div = ""

    if request.method == "POST":
        # 1️⃣ Read truck size
        truck_length = float(request.form["truck_length"]) * (1 if request.form["truck_length_unit"] == "m" else 0.01)
        truck_width = float(request.form["truck_width"]) * (1 if request.form["truck_width_unit"] == "m" else 0.01)
        truck_height = float(request.form["truck_height"]) * (1 if request.form["truck_height_unit"] == "m" else 0.01)

        # 2️⃣ Read crates
        crates = []
        stack_targets = {}
        crate_idx = 1

        while True:
            label_field = f"crate{crate_idx}_label"
            length_field = f"crate{crate_idx}_length"
            width_field = f"crate{crate_idx}_width"
            height_field = f"crate{crate_idx}_height"
            stackable_field = f"crate{crate_idx}_stackable"
            target_field = f"crate{crate_idx}_stack_target"

            if label_field not in request.form:
                break

            label = request.form[label_field]
            length = float(request.form[length_field]) * (1 if request.form[f"crate{crate_idx}_length_unit"] == "m" else 0.01)
            width = float(request.form[width_field]) * (1 if request.form[f"crate{crate_idx}_width_unit"] == "m" else 0.01)
            height = float(request.form[height_field]) * (1 if request.form[f"crate{crate_idx}_height_unit"] == "m" else 0.01)
            stackable = request.form[stackable_field]

            # Store the crate
            crates.append({
                "label": label,
                "length": length,
                "width": width,
                "height": height,
            })

            # Store stacking target if defined
            if stackable == "Yes" and target_field in request.form and request.form[target_field]:
                stack_targets[label] = request.form[target_field]
                print(f"DEBUG: Crate '{label}' should be stacked on '{request.form[target_field]}'")
            else:
                print(f"DEBUG: Crate '{label}' → not stackable")

            crate_idx += 1

        # 3️⃣ Setup Packer
        packer = Packer()

        truck_bin = Bin("Truck", truck_length, truck_width, truck_height, 10000)
        packer.add_bin(truck_bin)

        for crate in crates:
            item = Item(
                crate["label"],
                crate["length"],
                crate["width"],
                crate["height"],
                1,  # weight
                0   # updatable
            )
            packer.add_item(item)

        # 4️⃣ Pack items
        packer.pack()

        # 5️⃣ Collect positions
        crate_positions = {}
        for item in truck_bin.items:
            dim = item.get_dimension()  # Correct → returns (length, width, height)
            crate_positions[item.name] = {
                "x": item.position[0],
                "y": item.position[1],
                "z": item.position[2],
                "length": dim[0],
                "width": dim[1],
                "height": dim[2]
            }
            print(f"DEBUG: Packed {item.name} at x={item.position[0]}, y={item.position[1]}, z={item.position[2]} size=({dim[0]}, {dim[1]}, {dim[2]})")

        # 6️⃣ Build 3D plot
        fig = go.Figure()

        # Draw truck
        fig.add_trace(go.Mesh3d(
            x=[0, truck_length, truck_length, 0, 0, truck_length, truck_length, 0],
            y=[0, 0, truck_width, truck_width, 0, 0, truck_width, truck_width],
            z=[0, 0, 0, 0, truck_height, truck_height, truck_height, truck_height],
            color='lightgray',
            opacity=0.1,
            name='Truck',
            alphahull=0
        ))

        # Draw crates
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow', 'brown']
        color_idx = 0

        for crate in crates:
            pos = crate_positions.get(crate["label"])
            if not pos:
                print(f"WARNING: Crate {crate['label']} was not packed!")
                continue

            x0, y0, z0 = pos["x"], pos["y"], pos["z"]
            l, w, h = pos["length"], pos["width"], pos["height"]

            fig.add_trace(go.Mesh3d(
                x=[x0, x0 + l, x0 + l, x0, x0, x0 + l, x0 + l, x0],
                y=[y0, y0, y0 + w, y0 + w, y0, y0, y0 + w, y0 + w],
                z=[z0, z0, z0, z0, z0 + h, z0 + h, z0 + h, z0 + h],
                color=colors[color_idx % len(colors)],
                opacity=0.7,
                name=crate["label"],
                alphahull=0
            ))

            # Add label text
            fig.add_trace(go.Scatter3d(
                x=[x0 + l/2],
                y=[y0 + w/2],
                z=[z0 + h/2],
                mode='text',
                text=[crate["label"]],
                textposition='middle center',
                textfont=dict(size=12, color='black'),
                showlegend=False
            ))

            color_idx += 1

        fig.update_layout(
            scene=dict(
                xaxis_title='Length (m)',
                yaxis_title='Width (m)',
                zaxis_title='Height (m)',
            ),
            margin=dict(l=0, r=0, b=0, t=0)
        )

        plot_div = fig.to_html(full_html=False)

    return render_template("index.html", plot_div=plot_div)

if __name__ == "__main__":
    app.run(debug=True)
