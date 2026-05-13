import streamlit as st
import streamlit.components.v1 as components
from openpyxl import load_workbook
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import csv
import io
import base64

st.set_page_config(layout="wide")

# ==========================================
# HEADER
# ==========================================
logo_base64 = base64.b64encode(
    open("mujin logo.png", "rb").read()
).decode()

header_html = f"""
<div style="display:flex; align-items:center; gap:20px;">
    <img src="data:image/png;base64,{logo_base64}" width="220">

    <div style="
        color:orange;
        font-size:48px;
        font-weight:bold;
        font-family:Arial,sans-serif;
    ">
        Gripper Health App
    </div>
</div>
"""

components.html(header_html, height=120)

# ==========================================
# GRIPPER SELECTION
# ==========================================
gripper_type = st.selectbox(
    "Select Gripper Type",
    [
        "(Select)",
        "63 Channel Gripper",
        "Mega Gripper"
    ]
)

if gripper_type == "(Select)":
    st.warning("Please select a Gripper Type")
    st.stop()

# ==========================================
# TARGET RANGES
# ==========================================
if gripper_type == "Mega Gripper":

    TARGET_LOW = -500
    TARGET_HIGH = -300
    GRAPH_MIN = -700

else:

    TARGET_LOW = -40000
    TARGET_HIGH = -25000
    GRAPH_MIN = -70000

# ==========================================
# SESSION STATE
# ==========================================
if "module_colors" not in st.session_state:
    st.session_state.module_colors = {}

if "module_samples" not in st.session_state:
    st.session_state.module_samples = {}

if "highlight_modules" not in st.session_state:
    st.session_state.highlight_modules = []

# ==========================================
# FUNCTIONS
# ==========================================
def parse_highlight_modules(text):

    modules = []

    if text:

        for item in text.split(","):

            try:
                modules.append(int(item.strip()))
            except:
                pass

    st.session_state.highlight_modules = modules


# ==========================================
# MODULE COLOR LOGIC
# ==========================================
def get_module_color(samples):

    core_samples = samples[1:7]

    # ======================================
    # MEGA GRIPPER LOGIC
    # ======================================
    if gripper_type == "Mega Gripper":

        for index, value in enumerate(core_samples):

            try:
                value = float(value)

            except:
                continue

            # ==================================
            # GREEN RANGE
            # ==================================
            if -500 <= value <= -300:

                # Fast response
                if index <= 1:

                    return "green"

                # Slow response
                else:

                    return "yellow"

            # ==================================
            # YELLOW WARNING RANGE
            # ==================================
            elif (
                -550 <= value < -500
                or
                -300 < value <= -250
            ):

                return "yellow"

        return "red"

    # ======================================
    # 63 CHANNEL LOGIC
    # ======================================
    else:

        min_target = min(
            TARGET_LOW,
            TARGET_HIGH
        )

        max_target = max(
            TARGET_LOW,
            TARGET_HIGH
        )

        for index, value in enumerate(core_samples):

            try:
                value = float(value)

            except:
                continue

            if min_target <= value <= max_target:

                if index <= 1:

                    return "green"

                else:

                    return "yellow"

        return "red"


def get_status_text(status):

    if status == "green":
        return "Reached acceptable pressure and maintained"

    elif status == "yellow":
        return "Delayed or warning pressure range"

    elif status == "red":
        return "Failed to reach acceptable pressure"

    return "No data"


def get_layout_settings():

    if gripper_type == "63 Channel Gripper":

        return 7, 9, 40, 450

    else:

        return 5, 22, 40, 360


def show_gripper_layout():

    st.subheader(f"{gripper_type} Layout")

    rows, cols, box_size, grid_height = (
        get_layout_settings()
    )

    html = f"""
    <div style="
        display:grid;
        grid-template-columns:
            repeat({cols}, {box_size}px);
        gap:6px;
        padding:12px;
        border:3px solid black;
        width:max-content;
        background-color:#f5f5f5;
    ">
    """

    for row in range(rows):
        for col in range(cols):

            num = (
                (rows - row) +
                ((cols - 1 - col) * rows)
            )

            color = (
                st.session_state.module_colors.get(
                    num,
                    "white"
                )
            )

            if (
                num in
                st.session_state.highlight_modules
            ):

                inner_shadow = (
                    "inset 0 0 0 4px hotpink"
                )

            else:

                inner_shadow = "none"

            html += f"""
            <div style="
                width:{box_size}px;
                height:{box_size}px;
                border:1px solid black;
                box-shadow:{inner_shadow};
                background-color:{color};
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:9px;
                font-weight:bold;
            ">
            {num}
            </div>
            """

    html += "</div>"

    components.html(html, height=grid_height)

    st.caption(
        "Orientation: Front face of gripper"
    )


def analyze_uploaded_file(uploaded_file):

    st.session_state.module_colors = {}
    st.session_state.module_samples = {}

    file_name = uploaded_file.name.lower()

    # ======================================
    # CSV
    # ======================================
    if file_name.endswith(".csv"):

        text = (
            uploaded_file.getvalue()
            .decode("utf-8")
        )

        reader = csv.reader(
            io.StringIO(text)
        )

        rows_data = list(reader)

        max_col = len(rows_data[0])

        for col in range(1, max_col + 1):

            try:

                module_name = (
                    rows_data[0][col - 1]
                )

                module_number = int(
                    float(module_name)
                )

            except:

                continue

            module_start = (
                2 +
                ((module_number - 1) * 6)
            )

            start_row = module_start - 1
            end_row = module_start + 7

            samples = []

            for row in range(
                start_row,
                end_row
            ):

                try:

                    value = (
                        rows_data
                        [row - 1]
                        [col - 1]
                    )

                except:

                    value = None

                if value not in [None, ""]:

                    samples.append(
                        float(value)
                    )

            st.session_state.module_samples[
                module_number
            ] = samples

            st.session_state.module_colors[
                module_number
            ] = get_module_color(samples)

    # ======================================
    # XLSX
    # ======================================
    else:

        wb = load_workbook(
            uploaded_file,
            data_only=True
        )

        ws = wb.active

        max_col = ws.max_column

        for col in range(1, max_col + 1):

            module_name = ws.cell(
                row=1,
                column=col
            ).value

            try:

                module_number = int(
                    float(module_name)
                )

            except:

                continue

            module_start = (
                2 +
                ((module_number - 1) * 6)
            )

            start_row = module_start - 1
            end_row = module_start + 7

            samples = []

            for row in range(
                start_row,
                end_row
            ):

                value = ws.cell(
                    row=row,
                    column=col
                ).value

                if value is not None:

                    samples.append(
                        float(value)
                    )

            st.session_state.module_samples[
                module_number
            ] = samples

            st.session_state.module_colors[
                module_number
            ] = get_module_color(samples)

# ==========================================
# TABS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "Layout",
    "Analyze Data",
    "Graph Module",
    "Export Report"
])

# ==========================================
# TAB 1 - LAYOUT
# ==========================================
with tab1:

    highlight_text_layout = st.text_input(
        "Highlight specific modules",
        placeholder=
            "Example: 23,30,19,18",
        key="highlight_layout"
    )

    parse_highlight_modules(
        highlight_text_layout
    )

    show_gripper_layout()

# ==========================================
# TAB 2 - ANALYZE DATA
# ==========================================
with tab2:

    uploaded_file = st.file_uploader(
        "Upload spreadsheet file",
        type=["xlsx", "csv"]
    )

    highlight_text_analyze = st.text_input(
        "Highlight specific modules",
        placeholder=
            "Example: 23,30,19,18",
        key="highlight_analyze"
    )

    if highlight_text_analyze:

        parse_highlight_modules(
            highlight_text_analyze
        )

    if uploaded_file:

        analyze_uploaded_file(
            uploaded_file
        )

        st.success(
            "File uploaded and analyzed "
            "successfully"
        )

    show_gripper_layout()

# ==========================================
# TAB 3 - GRAPH MODULE
# ==========================================
with tab3:

    if st.session_state.module_samples:

        max_module = (
            110
            if gripper_type == "Mega Gripper"
            else 63
        )

        selected_module = st.selectbox(
            "Select module to graph",
            list(
                range(1, max_module + 1)
            )
        )

        samples = (
            st.session_state.module_samples.get(
                selected_module,
                []
            )
        )

        if len(samples) >= 7:

            graph_samples = (
                [0] +
                samples[1:7] +
                [0]
            )

            st.subheader(
                f"Module {selected_module}"
            )

            status = (
                st.session_state.module_colors.get(
                    selected_module,
                    "white"
                )
            )

            st.write(
                f"Status: "
                f"{get_status_text(status)}"
            )

            graph_width = 700
            graph_height = 420

            left_margin = 70
            top_margin = 30
            bottom_y = 360
            chart_height = 330
            point_spacing = 75

            def get_y(value):

                return (
                    bottom_y -
                    (
                        (0 - value) /
                        (0 - GRAPH_MIN)
                    ) * chart_height
                )

            points = []

            for i, value in enumerate(
                graph_samples
            ):

                x = (
                    left_margin +
                    (i * point_spacing)
                )

                y = get_y(value)

                points.append(f"{x},{y}")

            polyline_points = (
                " ".join(points)
            )

            target_top_y = get_y(
                TARGET_LOW
            )

            target_bottom_y = get_y(
                TARGET_HIGH
            )

            target_height = (
                target_bottom_y -
                target_top_y
            )

            graph_html = f"""
            <svg width="{graph_width}"
                 height="{graph_height}"
                 style="
                    border:1px solid black;
                    background:#f9f9f9;
                 ">

                <rect
                    x="{left_margin}"
                    y="{target_top_y}"
                    width="560"
                    height="{target_height}"
                    fill="lightgreen"
                    opacity="0.35"
                />

                <line
                    x1="{left_margin}"
                    y1="{bottom_y}"
                    x2="620"
                    y2="{bottom_y}"
                    stroke="black"
                />

                <line
                    x1="{left_margin}"
                    y1="{top_margin}"
                    x2="{left_margin}"
                    y2="{bottom_y}"
                    stroke="black"
                />

                <polyline
                    points="{polyline_points}"
                    fill="none"
                    stroke="blue"
                    stroke-width="3"
                />
            """

            for i, value in enumerate(
                graph_samples
            ):

                x = (
                    left_margin +
                    (i * point_spacing)
                )

                y = get_y(value)

                graph_html += f"""
                <circle
                    cx="{x}"
                    cy="{y}"
                    r="4"
                    fill="red"
                />

                <text
                    x="{x - 20}"
                    y="{y - 10}"
                    font-size="10"
                >
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

            for i, label in enumerate(
                x_labels
            ):

                x = (
                    left_margin +
                    (i * point_spacing)
                )

                graph_html += f"""
                <text
                    x="{x - 10}"
                    y="390"
                    font-size="12"
                >
                    {label}
                </text>
                """

            graph_html += f"""
                <text
                    x="25"
                    y="{bottom_y}"
                    font-size="12"
                >
                    0
                </text>

                <text
                    x="5"
                    y="{top_margin + 5}"
                    font-size="12"
                >
                    {GRAPH_MIN}
                </text>

                <text
                    x="5"
                    y="{get_y(TARGET_HIGH)}"
                    font-size="12"
                >
                    {TARGET_HIGH}
                </text>

                <text
                    x="5"
                    y="{get_y(TARGET_LOW)}"
                    font-size="12"
                >
                    {TARGET_LOW}
                </text>

            </svg>
            """

            components.html(
                graph_html,
                height=440
            )

    else:

        st.info(
            "Upload and analyze data first."
        )

# ==========================================
# TAB 4 - EXPORT REPORT
# ==========================================
with tab4:

    st.info(
        "Export section unchanged. "
        "Keep your existing export logic."
    )
