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
<div style="
    display:flex;
    align-items:center;
    gap:20px;
">
    <img src="data:image/png;base64,{logo_base64}"
         width="220">

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
# FUNCTIONS
# ==========================================
def get_module_color(samples):

    core_samples = samples[1:7]

    min_target = min(TARGET_LOW, TARGET_HIGH)
    max_target = max(TARGET_LOW, TARGET_HIGH)

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
        return "Delayed time in reaching acceptable pressure"

    elif status == "red":
        return "Failed to reach acceptable pressure"

    return "No data"

def get_layout_settings():

    if gripper_type == "63 Channel Gripper":

        return 7, 9, 40, 450

    else:

        return 5, 22, 40, 360

def show_gripper_layout(module_colors, highlight_modules):

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

            color = module_colors.get(
                num,
                "white"
            )

            if num in highlight_modules:

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

# ==========================================
# PDF REPORT
# ==========================================
def create_pdf_report(
    module_colors,
    module_samples,
    highlight_modules
):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter)
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "Gripper Health Report",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            f"Gripper: {gripper_type}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"Target Range: "
            f"{TARGET_LOW} to {TARGET_HIGH}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            "Orientation: Front face of gripper",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 12))

    # ======================================
    # GRIPPER VISUAL
    # ======================================
    story.append(
        Paragraph(
            "Gripper Layout",
            styles["Heading2"]
        )
    )

    layout_rows, layout_cols, _, _ = (
        get_layout_settings()
    )

    layout_data = []

    for row in range(layout_rows):

        row_data = []

        for col in range(layout_cols):

            num = (
                (layout_rows - row) +
                (
                    (layout_cols - 1 - col)
                    * layout_rows
                )
            )

            row_data.append(str(num))

        layout_data.append(row_data)

    layout_table = Table(layout_data)

    layout_style = [
        (
            "GRID",
            (0,0),
            (-1,-1),
            0.5,
            colors.black
        ),
        (
            "ALIGN",
            (0,0),
            (-1,-1),
            "CENTER"
        ),
        (
            "VALIGN",
            (0,0),
            (-1,-1),
            "MIDDLE"
        ),
        (
            "FONTSIZE",
            (0,0),
            (-1,-1),
            7
        ),
    ]

    for row in range(layout_rows):
        for col in range(layout_cols):

            num = (
                (layout_rows - row) +
                (
                    (layout_cols - 1 - col)
                    * layout_rows
                )
            )

            status = module_colors.get(
                num,
                "white"
            )

            if status == "green":

                bg_color = colors.lightgreen

            elif status == "yellow":

                bg_color = colors.yellow

            elif status == "red":

                bg_color = colors.red

            else:

                bg_color = colors.white

            layout_style.append(
                (
                    "BACKGROUND",
                    (col,row),
                    (col,row),
                    bg_color
                )
            )

            if num in highlight_modules:

                layout_style.append(
                    (
                        "BOX",
                        (col,row),
                        (col,row),
                        2,
                        colors.magenta
                    )
                )

    layout_table.setStyle(
        TableStyle(layout_style)
    )

    story.append(layout_table)

    story.append(Spacer(1, 16))

    # ======================================
    # ISSUES TABLE
    # ======================================
    story.append(
        Paragraph(
            "Modules Requiring Attention",
            styles["Heading2"]
        )
    )

    rows = [
        [
            "Module",
            "Status",
            "Reason",
            "Samples"
        ]
    ]

    max_module = (
        110
        if gripper_type == "Mega Gripper"
        else 63
    )

    for module in range(1, max_module + 1):

        status = module_colors.get(
            module,
            "white"
        )

        if status in ["yellow", "red"]:

            rows.append([
                str(module),
                status.upper(),
                get_status_text(status),
                str(
                    module_samples.get(
                        module,
                        []
                    )[1:7]
                )
            ])

    if len(rows) == 1:

        story.append(
            Paragraph(
                "No delayed or failed "
                "modules found.",
                styles["Normal"]
            )
        )

    else:

        table = Table(
            rows,
            colWidths=[60,80,240,300]
        )

        table.setStyle(TableStyle([
            (
                "GRID",
                (0,0),
                (-1,-1),
                1,
                colors.black
            ),
            (
                "BACKGROUND",
                (0,0),
                (-1,0),
                colors.lightgrey
            ),
            (
                "FONTSIZE",
                (0,0),
                (-1,-1),
                8
            ),
            (
                "VALIGN",
                (0,0),
                (-1,-1),
                "TOP"
            ),
        ]))

        story.append(table)

    # ======================================
    # MANUAL FLAGS
    # ======================================
    story.append(Spacer(1, 16))

    story.append(
        Paragraph(
            "Manually Flagged Modules "
            "for Inspection",
            styles["Heading2"]
        )
    )

    if highlight_modules:

        story.append(
            Paragraph(
                ", ".join(
                    str(x)
                    for x in highlight_modules
                ),
                styles["Normal"]
            )
        )

    else:

        story.append(
            Paragraph(
                "None",
                styles["Normal"]
            )
        )

    doc.build(story)

    buffer.seek(0)

    return buffer

# ==========================================
# STORAGE
# ==========================================
module_colors = {}
module_samples = {}
highlight_modules = []

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

    highlight_text = st.text_input(
        "Highlight specific modules",
        placeholder=
            "Example: 23,30,19,18"
    )

    if highlight_text:

        for item in highlight_text.split(","):

            try:

                highlight_modules.append(
                    int(item.strip())
                )

            except:

                pass

    show_gripper_layout(
        module_colors,
        highlight_modules
    )

# ==========================================
# TAB 2 - ANALYZE DATA
# ==========================================
with tab2:

    uploaded_file = st.file_uploader(
        "Upload spreadsheet file",
        type=["xlsx", "csv"]
    )

    if uploaded_file:

        file_name = (
            uploaded_file.name.lower()
        )

        # ==================================
        # CSV
        # ==================================
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

                module_samples[
                    module_number
                ] = samples

                module_colors[
                    module_number
                ] = get_module_color(samples)

        # ==================================
        # XLSX
        # ==================================
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

                module_samples[
                    module_number
                ] = samples

                module_colors[
                    module_number
                ] = get_module_color(samples)

        st.success(
            "File uploaded and analyzed "
            "successfully"
        )

        show_gripper_layout(
            module_colors,
            highlight_modules
        )

# ==========================================
# TAB 3 - GRAPH MODULE
# ==========================================
with tab3:

    if module_samples:

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

        samples = module_samples.get(
            selected_module,
            []
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

            status = module_colors.get(
                selected_module,
                "white"
            )

            st.write(
                f"Status: "
                f"{get_status_text(status)}"
            )

    else:

        st.info(
            "Upload and analyze data first."
        )

# ==========================================
# TAB 4 - EXPORT REPORT
# ==========================================
with tab4:

    if module_samples:

        st.download_button(
            label="Export PDF Report",
            data=create_pdf_report(
                module_colors,
                module_samples,
                highlight_modules
            ),
            file_name=
                "gripper_health_report.pdf",
            mime="application/pdf"
        )

    else:

        st.info(
            "Upload and analyze data first."
        )
