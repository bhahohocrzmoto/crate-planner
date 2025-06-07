from flask import Flask, render_template_string, request
import plotly.graph_objs as go
from py3dbp import Packer, Bin, Item

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    plot_div = ""

    if request.method == "POST":
        # Read truck size with unit conversion
        truck_length = float(request.form.get("truck_length", 10))
        truck_length_unit = request.form.get("truck_length_unit", "m")
        if truck_length_unit == "cm":
            truck_length /= 100.0
            
        truck_width = float(request.form.get("truck_width", 10))
        truck_width_unit = request.form.get("truck_width_unit", "m")
        if truck_width_unit == "cm":
            truck_width /= 100.0
            
        truck_height = float(request.form.get("truck_height", 10))
        truck_height_unit = request.form.get("truck_height_unit", "m")
        if truck_height_unit == "cm":
            truck_height /= 100.0

        # Initialize Packer
        packer = Packer()
        truck = Bin("Truck", truck_width, truck_height, truck_length, 100000)
        packer.add_bin(truck)

        # Read crates
        crates = []
        stack_targets = {}
        stackable_bases = set()  # Track crates that are bases for stacking

        crate_index = 1
        while True:
            label_key = f"crate{crate_index}_label"
            if label_key not in request.form:
                break

            label = request.form[label_key]
            length = float(request.form.get(f"crate{crate_index}_length", 1))
            length_unit = request.form.get(f"crate{crate_index}_length_unit", "m")
            if length_unit == "cm":
                length /= 100.0
                
            width = float(request.form.get(f"crate{crate_index}_width", 1))
            width_unit = request.form.get(f"crate{crate_index}_width_unit", "m")
            if width_unit == "cm":
                width /= 100.0
                
            height = float(request.form.get(f"crate{crate_index}_height", 1))
            height_unit = request.form.get(f"crate{crate_index}_height_unit", "m")
            if height_unit == "cm":
                height /= 100.0
                
            stackable = request.form.get(f"crate{crate_index}_stackable", "No")
            stack_target = request.form.get(f"crate{crate_index}_stack_target", "")

            item = Item(label, width, height, length, 1)
            crates.append(item)

            if stackable == "Yes" and stack_target.strip():
                stack_targets[label] = stack_target.strip()
                stackable_bases.add(stack_target.strip())  # Mark base crate

            crate_index += 1

        # First: Pack non-stackable items and stack BASE items
        packer.items = []  # Reset items
        for item in crates:
            # Only pack items that aren't top crates in a stack
            if item.name not in stack_targets.values():
                packer.add_item(item)

        # Run initial packing (for base crates and non-stackable items)
        packer.pack(bigger_first=False)

        # Second: Place stacked items on their bases
        for top_label, base_label in stack_targets.items():
            # Find base crate in packed items
            base_item = next((item for item in packer.bins[0].items if item.name == base_label), None)
            top_item = next((item for item in crates if item.name == top_label), None)
            
            if base_item and top_item:
                base_x, base_y, base_z = base_item.position
                # Place top crate directly on base
                top_item.position = (
                    base_x, 
                    base_y, 
                    base_z + base_item.height
                )
                # Add to packed items
                packer.bins[0].items.append(top_item)

        # Build Plotly Mesh3D plot
        fig = go.Figure()

        # Draw truck
        truck_shape = dict(
            x=[0, truck.width, truck.width, 0, 0, truck.width, truck.width, 0],
            y=[0, 0, truck.depth, truck.depth, 0, 0, truck.depth, truck.depth],
            z=[0, 0, 0, 0, truck.height, truck.height, truck.height, truck.height],
            opacity=0.1,
            color="gray",
            name="Truck"
        )
        fig.add_trace(go.Mesh3d(**truck_shape))

        # Draw crates
        colors = ["red", "blue", "green", "orange", "purple", "cyan", "magenta", "yellow"]
        for i, item in enumerate(packer.bins[0].items):
            x0, y0, z0 = item.position
            x1 = x0 + item.width
            y1 = y0 + item.depth
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

if __name__ == "__main__":
    app.run(debug=True)
