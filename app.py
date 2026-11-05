
import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CO Weightage Allocation Dashboard",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# THEME
# =========================================================

st.markdown("""
<style>
    .stApp {
        background-color: #FFFFFF;
        color: #111111;
    }

    h1, h2, h3, h4, p, label {
        color: #111111 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #FFFFFF;
    }

    div[data-testid="stNumberInput"] input {
        background-color: #FFFFFF;
        color: #111111;
    }

    .stButton > button {
        background-color: #174D36;
        color: white;
        border-radius: 7px;
        border: none;
        font-weight: bold;
    }

    .stButton > button:hover {
        background-color: #246B4B;
        color: white;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #D6D6D6;
    }

    .dashboard-title {
        color: #174D36;
        font-size: 30px;
        font-weight: bold;
    }

    .section-title {
        color: #174D36;
        font-size: 21px;
        font-weight: bold;
        margin-top: 15px;
    }

    hr {
        border-top: 1px solid #D6D6D6;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# CONSTANTS
# =========================================================

EXCEL_FILE = Path(__file__).parent / "Course Group.xlsx"

ASSESSMENTS = ["PA1", "PA2", "LE1", "LE2"]

EXPECTED_COLUMNS = [
    "Program Code",
    "Program",
    "Program Type Name",
    "Program Type",
    "Category",
    "ExamType",
    "ISA",
    "ESA",
    "ISA PRACTICAL",
    "ESA PRACTICAL",
    "Credit",
    "Handling Department",
    "Teaching Department",
    "Total Seat",
    "CO"
]


# =========================================================
# LOAD COURSE GROUP EXCEL FILE
# =========================================================

@st.cache_data
def load_course_data():

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            "Course Group.xlsx was not found. "
            "Place it in the same folder as app.py."
        )

    # Your actual column headings are in Excel row 3.
    df = pd.read_excel(
        EXCEL_FILE,
        header=2,
        engine="openpyxl"
    )

    # Clean column headings
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
    )

    # Remove empty rows and columns
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    # Remove unwanted spaces in text columns
    for column in df.columns:
        if df[column].dtype == "object":
            df[column] = df[column].astype("string").str.strip()

    # Remove rows without a Program Code
    if "Program Code" in df.columns:
        df = df.dropna(subset=["Program Code"])

    return df


# =========================================================
# LOAD DATA
# =========================================================

try:
    course_df = load_course_data()

except Exception as e:
    st.error(f"Unable to load course details: {e}")
    st.stop()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_options(data, column):

    if column not in data.columns:
        return ["All"]

    values = (
        data[column]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    values = sorted([v for v in values if v and v.lower() != "nan"])

    return ["All"] + values


def apply_filter(data, column, selected_value):

    if (
        column in data.columns
        and selected_value != "All"
    ):
        data = data[
            data[column].astype(str).str.strip()
            == selected_value
        ]

    return data


def safe_number(value):

    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def format_number(value):

    return round(float(value), 2)


# =========================================================
# DASHBOARD TITLE
# =========================================================

st.markdown(
    '<div class="dashboard-title">'
    'CO Weightage Allocation Dashboard'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("---")


# =========================================================
# COURSE DETAILS
# =========================================================

st.markdown(
    '<div class="section-title">Course Details</div>',
    unsafe_allow_html=True
)

filtered_df = course_df.copy()

# Department selection
department_columns = [
    col for col in [
        "Handling Department",
        "Teaching Department"
    ]
    if col in filtered_df.columns
]

if department_columns:

    department_options = set()

    for col in department_columns:
        department_options.update(
            filtered_df[col].dropna().astype(str).tolist()
        )

    department_options = ["All"] + sorted(department_options)

    selected_department = st.selectbox(
        "Department",
        department_options,
        key="department_select"
    )

    if selected_department != "All":

        filtered_df = filtered_df[
            filtered_df["Handling Department"].astype(str).eq(
                selected_department
            )
            | filtered_df["Teaching Department"].astype(str).eq(
                selected_department
            )
        ]


# Program Type Name
if "Program Type Name" in filtered_df.columns:

    program_type_name = st.selectbox(
        "Program Type Name",
        get_options(filtered_df, "Program Type Name"),
        key="program_type_name"
    )

    filtered_df = apply_filter(
        filtered_df,
        "Program Type Name",
        program_type_name
    )


# Program Type
if "Program Type" in filtered_df.columns:

    program_type = st.selectbox(
        "Program Type",
        get_options(filtered_df, "Program Type"),
        key="program_type"
    )

    filtered_df = apply_filter(
        filtered_df,
        "Program Type",
        program_type
    )


# Program
if "Program" in filtered_df.columns:

    program = st.selectbox(
        "Program",
        get_options(filtered_df, "Program"),
        key="program"
    )

    filtered_df = apply_filter(
        filtered_df,
        "Program",
        program
    )


# Program Code
if "Program Code" in filtered_df.columns:

    program_code = st.selectbox(
        "Program Code",
        get_options(filtered_df, "Program Code"),
        key="program_code"
    )

    filtered_df = apply_filter(
        filtered_df,
        "Program Code",
        program_code
    )


# Category
if "Category" in filtered_df.columns:

    category = st.selectbox(
        "Category",
        get_options(filtered_df, "Category"),
        key="category"
    )

    filtered_df = apply_filter(
        filtered_df,
        "Category",
        category
    )


# Exam Type
if "ExamType" in filtered_df.columns:

    exam_type = st.selectbox(
        "Exam Type",
        get_options(filtered_df, "ExamType"),
        key="exam_type"
    )

    filtered_df = apply_filter(
        filtered_df,
        "ExamType",
        exam_type
    )


# =========================================================
# SELECTED COURSE DETAILS
# =========================================================

st.markdown("---")
st.markdown(
    '<div class="section-title">Selected Course Information</div>',
    unsafe_allow_html=True
)

if filtered_df.empty:

    st.warning("No course details found for the selected options.")
    st.stop()

selected_course = filtered_df.iloc[0]

details_to_display = [
    "Program Code",
    "Program",
    "Program Type Name",
    "Program Type",
    "Category",
    "ExamType",
    "Handling Department",
    "Teaching Department",
    "Credit",
    "Total Seat",
    "CO"
]

available_details = [
    col for col in details_to_display
    if col in filtered_df.columns
]

detail_columns = st.columns(3)

for index, column in enumerate(available_details):

    with detail_columns[index % 3]:

        value = selected_course[column]

        if pd.isna(value):
            value = "-"

        st.markdown(f"**{column}**")
        st.write(str(value))


# =========================================================
# NUMBER OF COURSE OUTCOMES
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">Course Outcome Details</div>',
    unsafe_allow_html=True
)

default_co_count = 5

if "CO" in filtered_df.columns:

    co_values = pd.to_numeric(
        filtered_df["CO"],
        errors="coerce"
    ).dropna()

    if not co_values.empty:

        possible_count = int(co_values.max())

        if 1 <= possible_count <= 20:
            default_co_count = possible_count

number_of_cos = st.number_input(
    "Number of Course Outcomes",
    min_value=1,
    max_value=20,
    value=default_co_count,
    step=1,
    key="number_of_cos"
)

CO_LIST = [
    f"CO{i}" for i in range(1, int(number_of_cos) + 1)
]


# =========================================================
# ASSESSMENT WEIGHTAGE INPUT
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">Assessment Weightage Allocation</div>',
    unsafe_allow_html=True
)

st.write("Enter the total weight and the weight assigned to each CO.")

assessment_weights = {}
assessment_co_weights = {}

for assessment in ASSESSMENTS:

    st.markdown(f"**{assessment}**")

    assessment_weights[assessment] = st.number_input(
        f"Total Weight - {assessment}",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key=f"total_weight_{assessment}"
    )

    assessment_co_weights[assessment] = {}

    co_columns = st.columns(min(len(CO_LIST), 5))

    for index, co in enumerate(CO_LIST):

        with co_columns[index % len(co_columns)]:

            weight = st.number_input(
                f"{co} Weight",
                min_value=0.0,
                value=0.0,
                step=0.5,
                key=f"{assessment}_{co}"
            )

            assessment_co_weights[assessment][co] = weight

    st.markdown("---")


# =========================================================
# CO ASSESSMENT SUMMARY MATRIX
# =========================================================

st.markdown(
    '<div class="section-title">CO Assessment Summary Matrix</div>',
    unsafe_allow_html=True
)

matrix_rows = []

allocation = {}

for assessment in ASSESSMENTS:

    total_assessment_weight = assessment_weights[assessment]

    co_weights = assessment_co_weights[assessment]

    selected_total = sum(
        co_weights[co] for co in CO_LIST
    )

    allocation[assessment] = {}

    row = {
        "Assessment": assessment,
        "Assessment Weight": total_assessment_weight
    }

    for co in CO_LIST:

        assigned_weight = co_weights[co]

        if selected_total > 0:

            allocated_weight = (
                assigned_weight / selected_total
            ) * total_assessment_weight

        else:
            allocated_weight = 0.0

        allocation[assessment][co] = allocated_weight

        row[co] = assigned_weight

    row["TOTAL"] = sum(
        co_weights[co] for co in CO_LIST
    )

    matrix_rows.append(row)


matrix_df = pd.DataFrame(matrix_rows)

# Total row
total_row = {
    "Assessment": "TOTAL",
    "Assessment Weight": sum(assessment_weights.values())
}

for co in CO_LIST:

    total_row[co] = sum(
        assessment_co_weights[a][co]
        for a in ASSESSMENTS
    )

total_row["TOTAL"] = sum(
    total_row[co] for co in CO_LIST
)

matrix_df = pd.concat(
    [matrix_df, pd.DataFrame([total_row])],
    ignore_index=True
)

st.dataframe(
    matrix_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# CO-WISE TOTAL ASSESSMENT WEIGHT
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">CO-wise Total Assessment Weight</div>',
    unsafe_allow_html=True
)

co_total_rows = []

for co in CO_LIST:

    total_co_weight = sum(
        allocation[assessment][co]
        for assessment in ASSESSMENTS
    )

    co_total_rows.append({
        "Course Outcome": co,
        "Total Assessment Weight": format_number(total_co_weight)
    })


co_total_df = pd.DataFrame(co_total_rows)

st.dataframe(
    co_total_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# FINAL CO ALLOCATION MATRIX
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">Final CO Assessment Allocation Matrix</div>',
    unsafe_allow_html=True
)

final_rows = []

for assessment in ASSESSMENTS:

    row = {
        "Assessment": assessment,
        "Assessment Weight": assessment_weights[assessment]
    }

    for co in CO_LIST:

        row[co] = format_number(
            allocation[assessment][co]
        )

    row["TOTAL"] = format_number(
        sum(allocation[assessment].values())
    )

    final_rows.append(row)


final_total_row = {
    "Assessment": "TOTAL",
    "Assessment Weight": sum(assessment_weights.values())
}

for co in CO_LIST:

    final_total_row[co] = format_number(
        sum(
            allocation[assessment][co]
            for assessment in ASSESSMENTS
        )
    )

final_total_row["TOTAL"] = format_number(
    sum(assessment_weights.values())
)

final_rows.append(final_total_row)

final_df = pd.DataFrame(final_rows)

st.dataframe(
    final_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# CCA WEIGHTAGE
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">CCA Weightage</div>',
    unsafe_allow_html=True
)

cca_total_weight = st.number_input(
    "Total CCA Weight",
    min_value=0.0,
    value=0.0,
    step=1.0,
    key="cca_total_weight"
)

total_assessment_weight = sum(
    assessment_weights.values()
)

cca_rows = []

for co in CO_LIST:

    weight_per_co = sum(
        allocation[assessment][co]
        for assessment in ASSESSMENTS
    )

    if total_assessment_weight > 0:

        weight_per_co_in_cca = (
            weight_per_co / total_assessment_weight
        ) * cca_total_weight

    else:
        weight_per_co_in_cca = 0.0

    cca_rows.append({
        "Course Outcome": co,
        "Weight per CO": format_number(weight_per_co),
        "Total Weight": format_number(total_assessment_weight),
        "Weight per CO in CCA": format_number(weight_per_co_in_cca)
    })


cca_df = pd.DataFrame(cca_rows)

st.dataframe(
    cca_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# EXCEL REPORT GENERATION
# =========================================================

def create_excel_report():

    output = BytesIO()

    course_details_df = pd.DataFrame(
        [selected_course[available_details].to_dict()]
    )

    co_weight_rows = []

    for co in CO_LIST:

        co_weight_rows.append({
            "Course Outcome": co,
            "Total Assessment Weight": sum(
                allocation[a][co] for a in ASSESSMENTS
            )
        })

    co_weight_df = pd.DataFrame(co_weight_rows)

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        matrix_df.to_excel(
            writer,
            sheet_name="CO Assessment Matrix",
            index=False
        )

        final_df.to_excel(
            writer,
            sheet_name="Final CO Allocation",
            index=False
        )

        co_total_df.to_excel(
            writer,
            sheet_name="CO-wise Total",
            index=False
        )

        cca_df.to_excel(
            writer,
            sheet_name="CCA Weight Summary",
            index=False
        )

        course_details_df.to_excel(
            writer,
            sheet_name="Course Details",
            index=False
        )

        co_weight_df.to_excel(
            writer,
            sheet_name="CO Weightages",
            index=False
        )

        # Individual assessment sheets
        for assessment in ASSESSMENTS:

            individual_rows = []

            for co in CO_LIST:

                individual_rows.append({
                    "Course Outcome": co,
                    "Teacher Assigned Weight":
                        assessment_co_weights[assessment][co],
                    "Allocated Assessment Weight":
                        allocation[assessment][co]
                })

            individual_df = pd.DataFrame(individual_rows)

            individual_df.to_excel(
                writer,
                sheet_name=f"{assessment} Weightage",
                index=False
            )

        # Format all worksheets
        workbook = writer.book

        header_fill = PatternFill(
            fill_type="solid",
            fgColor="174D36"
        )

        header_font = Font(
            bold=True,
            color="FFFFFF"
        )

        total_fill = PatternFill(
            fill_type="solid",
            fgColor="E8D8B5"
        )

        thin_border = Border(
            bottom=Side(style="thin", color="D6D6D6")
        )

        for worksheet in workbook.worksheets:

            worksheet.freeze_panes = "A2"

            worksheet.auto_filter.ref = worksheet.dimensions

            for cell in worksheet[1]:

                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center"
                )

            for row in worksheet.iter_rows(min_row=2):

                for cell in row:

                    cell.border = thin_border
                    cell.alignment = Alignment(
                        horizontal="center",
                        vertical="center"
                    )

            # Highlight TOTAL rows
            for row in worksheet.iter_rows(min_row=2):

                if str(row[0].value).upper() == "TOTAL":

                    for cell in row:

                        cell.fill = total_fill
                        cell.font = Font(bold=True)

            # Set column widths
            for column_cells in worksheet.columns:

                max_length = 0
                column_letter = get_column_letter(
                    column_cells[0].column
                )

                for cell in column_cells:

                    if cell.value is not None:

                        max_length = max(
                            max_length,
                            len(str(cell.value))
                        )

                worksheet.column_dimensions[
                    column_letter
                ].width = min(max_length + 4, 35)

            worksheet.row_dimensions[1].height = 25

    output.seek(0)

    return output


# =========================================================
# DOWNLOAD BUTTON
# =========================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">Download Report</div>',
    unsafe_allow_html=True
)

excel_file = create_excel_report()

st.download_button(
    label="Download CO Assessment Excel Report",
    data=excel_file,
    file_name="CO_Weightage_Allocation_Report.xlsx",
    mime=(
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    ),
    use_container_width=True
)


# =========================================================
# RESET BUTTON
# =========================================================

st.markdown("---")

if st.button("Reset Dashboard"):

    st.cache_data.clear()

    for key in list(st.session_state.keys()):
        del st.session_state[key]

    st.rerun()
