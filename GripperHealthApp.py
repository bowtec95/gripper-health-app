import streamlit as st
import streamlit.components.v1 as components
from openpyxl import load_workbook

st.set_page_config(layout="wide")

st.image("mujin logo.png", width=250)

st.title("Gripper Health App")

gripper_type = st.selectbox(
    "Select Gripper Type",
    ["(Select)", "63 Channel Gripper", "Mega Gripper"]
)

gripper_version = st.selectbox(
    "Select Gripper Version",
    ["(Select)", "V1", "V2", "V3"]
)

if gripper_type == "(Select)" or gripper_version == "(Select)":
    st.warning("Please select both Gripper Type and Version")
    st.stop()

st.write(f"Selected: {gripper_version} {gripper_type}")

uploaded_file = st.file_uploader(
    "Upload spreadsheet file",
    type=["xlsx"]
)

# --- Highlight Modules ---
highlight_text = st.text_input(
    "Highlight specific modules",
    placeholder="Example: 23,30,19,18"
)

highlight_modules = []

if highlight_text:

    for item in highlight_text.split(","):

        try:
            highlight_modules.append(int(item.strip()))
        except:
            pass

# --- Pressure Ranges ---
if gripper_type == "Mega Gripper":

    TARGET_LOW = -500
    TARGET_HIGH = -300
    GRAPH_MIN = -700

else:

    TARGET_LOW = -40000
    TARGET_HIGH = -25000
    GRAPH_MIN = -70000

def get_module_color(samples):

    core_samples = samples[1:7]

    for index, value in enumerate(core_samples):

        try:
            value = float(value)
        except:
            continue

        # Within acceptable range
        if TARGET_LOW <= value <= TARGET_HIGH:

            # Reached quickly
            if index <= 1:
                return "green"

            # Reached later
            else:
                return "yellow"

    # Never reached acceptable range
    return "red"

module_colors = {}
module_samples = {}

# --- Analyze Spreadsheet ---
if uploaded_file:

    wb = load_workbook(uploaded_file, data_only=True)
    ws = wb.active

    max_col = ws.max_column

    for col in range(2, max_col + 1):

        module_name = ws.cell(row=1, column=col).value

        try:
            module_number = int(module_name)
        except:
            continue

        module_start = 2 + ((module_number - 1) * 6)

        start_row = module_start - 1
        end_row = module_start + 7

        samples = []

        for row in range(start_row, end_row):

            value = ws.cell(row=row, column=col).value

            if value is not None:
                samples.append(float(value))

        module_samples[module_number] = samples
        module_colors[module_number] = get_module_color(samples)

    st.success("File uploaded and analyzed successfully")

# --- Gripper Layout ---
if gripper_type in ["63 Channel Gripper", "Mega Gripper"]:

    st.subheader(f"{gripper_version} {gripper_type} Layout")

    if gripper_type == "63 Channel Gripper":

        rows = 7
        cols = 9
        box_size = 40
        grid_height = 450

    else:

        rows = 5
        cols = 22
        box_size = 40
        grid_height = 360

    html = f"""
    <div style="
        display: grid;
        grid-template-columns: repeat({cols}, {box_size}px);
        gap: 6px;
        padding: 12px;
        border: 3px solid black;
        width: max-content;
        background-color: #f5f5f5;
    ">
    """

    for row in range(rows):
        for col in range(cols):

            # Bottom-right = 1
            # Top-left = highest number
            num = (rows - row) + ((cols - 1 - col) * rows)

            color = module_colors.get(num, "white")

            if num in highlight_modules:
                border_style = "4px solid hotpink"
            else:
                border_style = "1px solid black"

            html += f"""
            <div style="
                width: {box_size}px;
                height: {box_size}px;
                border: {border_style};
                background-color: {color};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 9px;
                font-weight: bold;
            ">
            {num}
            </div>
            """

    html += "</div>"

    components.html(html, height=grid_height)

    st.caption("Orientation: Front face of gripper")

# --- Graph Section ---
if uploaded_file:

    max_module = 110 if gripper_type == "Mega Gripper" else 63

    selected_module = st.selectbox(
        "Select module to graph",
        list(range(1, max_module + 1))
    )

    samples = module_samples.get(selected_module, [])

    # Start at 0 and end at 0
    graph_samples = [0] + samples[1:7] + [0]

    st.subheader(f"Module {selected_module} Pressure Readings")

    st.text("Samples: " + str(graph_samples))

    status = module_colors.get(selected_module, "white")

    if status == "green":
        status_text = "Reached acceptable pressure and maintained"

    elif status == "yellow":
        status_text = "Delayed time in reaching acceptable pressure"

    elif status == "red":
        status_text = "Failed to reach acceptable pressure"

    else:
        status_text = "No data"

    st.write(f"Status: {status_text}")

    if graph_samples:

        max_val = 0
        min_val = GRAPH_MIN

        graph_width = 700
        graph_height = 420

        left_margin = 70
        top_margin = 30
        bottom_y = 360
        chart_height = 330
        point_spacing = 75

        def get_y(value):

            return bottom_y - (
                (0 - value) /
                (0 - min_val) * chart_height
            )

        points = []

        for i, value in enumerate(graph_samples):

            x = left_margin + (i * point_spacing)
            y = get_y(value)

            points.append(f"{x},{y}")

        polyline_points = " ".join(points)

        target_top_y = get_y(TARGET_LOW)
        target_bottom_y = get_y(TARGET_HIGH)

        target_height = (
            target_bottom_y - target_top_y
        )

        graph_html = f"""
        <svg width="{graph_width}"
             height="{graph_height}"
             style="border:1px solid black;
                    background:#f9f9f9;">

            <!-- Goal Window -->
            <rect x="{left_margin}"
                  y="{target_top_y}"
                  width="560"
                  height="{target_height}"
                  fill="lightgreen"
                  opacity="0.35" />

            <!-- Axes -->
            <line x1="{left_margin}"
                  y1="{bottom_y}"
                  x2="620"
                  y2="{bottom_y}"
                  stroke="black" />

            <line x1="{left_margin}"
                  y1="{top_margin}"
                  x2="{left_margin}"
                  y2="{bottom_y}"
                  stroke="black" />

            <!-- Data Line -->
            <polyline
                points="{polyline_points}"
                fill="none"
                stroke="blue"
                stroke-width="3"
            />
        """

        for i, value in enumerate(graph_samples):

            x = left_margin + (i * point_spacing)
            y = get_y(value)

            graph_html += f"""
            <circle cx="{x}"
                    cy="{y}"
                    r="4"
                    fill="red" />

            <text x="{x - 20}"
                  y="{y - 10}"
                  font-size="10">
                  {int(value)}
            </text>
            """

        x_labels = [
            "Start",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "End"
        ]

        for i, label in enumerate(x_labels):

            x = left_margin + (i * point_spacing)

            graph_html += f"""
            <text x="{x - 10}"
                  y="390"
                  font-size="12">
                  {label}
            </text>
            """

        graph_html += f"""

            <!-- Y Labels -->
            <text x="25"
                  y="{bottom_y}"
                  font-size="12">0</text>

            <text x="5"
                  y="{top_margin + 5}"
                  font-size="12">{GRAPH_MIN}</text>

            <text x="5"
                  y="{get_y(TARGET_HIGH)}"
                  font-size="12">{TARGET_HIGH}</text>

            <text x="5"
                  y="{get_y(TARGET_LOW)}"
                  font-size="12">{TARGET_LOW}</text>

        </svg>
        """

        components.html(graph_html, height=440)
