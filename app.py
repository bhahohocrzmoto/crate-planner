from flask import Flask, render_template_string, request
import plotly.graph_objs as go
from py3dbp import Packer, Bin, Item

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    plot_div = ""

    if request.method == "POST":
        # Read truck size
        truck_length = float(request.form.get("truck_length", 10))
        truck_width = float(request.form.get("truck_width", 10))
        truck_height = float(request.form.get("truck_height", 10))

        # Initialize Packer
        packer = Packer()
        truck = Bin("Truck", truck_length, truck_width, truck_height, 100000)
        packer.add_bin(truck)

        # Read crates
        crates = []
        stack_targets = {}  # map: crate_label → stack_target_label

        crate_index = 1
        while True:
            label_key = f"crate{crate_index}_label"
            if label_key not in request.form:
                break  # no more crates

            label = request.form[label_key]
            length = float(request.form.get(f"crate{crate_index}_length", 1))
            width = float(request.form.get(f"crate{crate_index}_width", 1))
            height = float(request.form.get(f"crate{crate_index}_height", 1))
            stackable = request.form.get(f"crate{crate_index}_stackable", "No")
            stack_target = request.form.get(f"crate{crate_index}_stack_target", "")

            # Create item
            item = Item(label, length, width, height, 1)  # weight=1
            crates.append(item)

            # Remember stacking relation
            if stackable == "Yes" and stack_target.strip():
                stack_targets[label] = stack_target.strip()

            crate_index += 1

        # Add all items to packer
        for item in crates:
            packer.add_item(item)

        # Manual stacking pass
        label_to_item = {item.name: item for item in crates}
        positioned = set()

        for base_label, top_label in stack_targets.items():
            if base_label in label_to_item and top_label in label_to_item:
                base = label_to_item[base_label]
                top = label_to_item[top_label]

                # If base is not positioned yet → place at origin
                if not hasattr(base, "position"):
                    base.position = (0, 0, 0)
                    positioned.add(base.name)

                # Place top crate exactly on top
                base_x, base_y, base_z = base.position
                top.position = (base_x, base_y, base_z + base.height)
                positioned.add(top.name)

        # ❌ IMPORTANT: DO NOT call packer.pack() here
        # → because it will override positions!
        # packer.pack(bigger_first=False)

        # For crates that are not stacked at all → place them manually side by side
        # Example simple logic: place next to previous crate in X direction
        current_x = 0
        spacing = 0.5  # gap between crates
        for item in crates:
            if not hasattr(item, "position"):
                item.position = (current_x, 0, 0)
                current_x += item.width + spacing

        # Build Plotly Mesh3D plot
        fig = go.Figure()

        # Draw truck box
        fig.add_trace(go.Mesh3d(
            x=[0, truck_width, truck_width, 0, 0, truck_width, truck_width, 0],
            y=[0, 0, truck_length, truck_length, 0, 0, truck_length, truck_length],
            z=[0, 0, 0, 0, truck_height, truck_height, truck_height, truck_height],
            opacity=0.1,
            color="gray",
            name="Truck"
        ))

        # Draw crates (using manual positions!)
        colors = ["red", "blue", "green", "orange", "purple", "cyan", "magenta", "yellow"]
        for i, item in enumerate(crates):  # ⚠️ use "crates", not packer.bins[0].items
            x0, y0, z0 = item.position
            x1 = x0 + item.width
            y1 = y0 + item.length
            z1 = z0 + item.height

            fig.add_trace(go.Mesh3d(
                x=[x0, x1, x1, x0, x0, x1, x1, x0],
                y=[y0, y0, y1, y1, y0, y0, y1, y1],
                z=[z0, z0, z0, z0, z1, z1, z1, z1],
                opacity=0.8,
                color=colors[i % len(colors)],
                name=item.name,
                text=item.name
            ))

        fig.update_layout(
            scene=dict(
                xaxis_title="Width (m)",
                yaxis_title="Length (m)",
                zaxis_title="Height (m)"
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )

        plot_div = fig.to_html(full_html=False)

    # Render page
    with open("templates/index.html", "r") as f:
        html_template = f.read()

    return render_template_string(html_template, plot_div=plot_div)

# Run app
if __name__ == "__main__":
    app.run(debug=True)
