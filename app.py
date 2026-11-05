
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
    page_title="MGU CO Weightage Allocation Dashboard",
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
    color: #17211C;
}
h1, h2, h3, h4, p, label {
    color: #17211C !important;
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
}
.stButton > button {
    background-color: #174D36;
    color: white;
    border-radius: 7px;
    font-weight: bold;
}
.stButton > button:hover {
    background-color: #246B4B;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# FILE PATH
# =========================================================

BASE_DIR = Path(__file__).parent
COURSE_GROUP_PATH = BASE_DIR / "Course Group.xlsx"

# =========================================================
# LOAD COURSE GROUP EXCEL
# =========================================================

@st.cache_data
def load_course_data():

    if not COURSE_GROUP_PATH.exists():
        raise FileNotFoundError(
            "Course Group.xlsx was not found in the app folder."
        )

    # The actual workbook has its column headings in row 2
    df = pd.read_excel(
        COURSE_GROUP_PATH,
        sheet_name="Sheet1",
        header=1,
        engine="openpyxl"
    )

    df.columns = [
        str(col).strip().replace("\n", " ")
        for col in df.columns
    ]

    # Remove completely empty rows and columns
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    required_columns = [
        "Program Code",
        "Program",
        "ISA",
        "ESA",
        "CO"
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(
                f"Required column '{col}' is missing from Course Group.xlsx."
            )

    # Clean course identifiers and names
    df["Program Code"] = (
        df["Program Code"]
        .astype("string")
        .str.strip()
    )

    df["Program"] = (
        df["Program"]
        .astype("string")
        .str.strip()
    )

    # Convert marks to numeric values
    numeric_columns = [
        "ISA",
        "ESA",
        "ISA PRACTICAL",
        "ESA PRACTICAL",
        "CO",
        "Credit"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    # Remove rows without course codes
    df = df[
        df["Program Code"].notna()
        & (df["Program Code"].astype(str).str.strip() != "")
    ].copy()

    return df


# =========================================================
# LOAD DATA
# =========================================================

try:
    course_df = load_course_data()

except Exception as e:
    st.error(f"Excel loading error: {e}")
    st.stop()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="dashboard-title">'
    'MGU CO Weightage Allocation Dashboard'
    '</div>',
    unsafe_allow_html=True
)

st.caption(
    "Outcome-Based Education | Course Outcome "
    "Assessment Marks Allocation"
)

st.divider()


# =========================================================
# COURSE SELECTION
# =========================================================

st.markdown(
    '<div class="section-title">Course Selection</div>',
    unsafe_allow_html=True
)

course_df["Course Display"] = (
    course_df["Program Code"].astype(str)
    + " - "
    + course_df["Program"].astype(str)
)

course_options = (
    course_df["Course Display"]
    .drop_duplicates()
    .sort_values()
    .tolist()
)

if not course_options:
    st.error("No courses were found in Course Group.xlsx.")
    st.stop()

selected_course_display = st.selectbox(
    "Select Course",
    course_options
)

selected_course = course_df[
    course_df["Course Display"] == selected_course_display
].iloc[0]

course_code = str(selected_course["Program Code"])
course_name = str(selected_course["Program"])


# =========================================================
# COURSE INFORMATION
# =========================================================

st.markdown("### Selected Course")

info1, info2, info3 = st.columns(3)

info1.metric(
    "Course Code",
    course_code
)

info2.metric(
    "Course Name",
    course_name
)

co_count = int(selected_course["CO"])

info3.metric(
    "Number of COs",
    co_count
)

if co_count <= 0:
    st.warning(
        "The selected course does not have a valid CO count."
    )
    st.stop()

# =========================================================
# CREATE CO LIST
# =========================================================

CO_LIST = [
    f"CO{i}"
    for i in range(1, co_count + 1)
]


# =========================================================
# GET ASSESSMENT COMPONENTS
# =========================================================

assessment_columns = [
    ("ISA", "Internal"),
    ("ESA", "External"),
    ("ISA PRACTICAL", "Internal"),
    ("ESA PRACTICAL", "External")
]

assessments = []

for column_name, assessment_type in assessment_columns:

    if column_name in course_df.columns:

        maximum_marks = float(
            selected_course[column_name]
        )

        if maximum_marks > 0:

            assessments.append({
                "Assessment": column_name,
                "Assessment Type": assessment_type,
                "Maximum Marks": maximum_marks
            })

if not assessments:
    st.error(
        "No assessment marks are available for this course."
    )
    st.stop()

assessments_df = pd.DataFrame(assessments)


# =========================================================
# ASSESSMENT-WISE CO ALLOCATION
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">'
    'CO Marks Allocation'
    '</div>',
    unsafe_allow_html=True
)

st.write(
    "Allocate the maximum marks of each assessment "
    "among the Course Outcomes."
)

allocation_data = []

valid_allocation = True

for assessment in assessments:

    assessment_name = assessment["Assessment"]
    assessment_type = assessment["Assessment Type"]
    maximum_marks = assessment["Maximum Marks"]

    st.markdown(f"### {assessment_name}")

    st.caption(
        f"Type: {assessment_type} | "
        f"Maximum Marks: {maximum_marks:g}"
    )

    columns = st.columns(min(len(CO_LIST), 4))

    assessment_total = 0.0

    for i, co in enumerate(CO_LIST):

        key = (
            f"allocation_{course_code}_"
            f"{assessment_name}_{co}"
        )

        if key not in st.session_state:
            st.session_state[key] = 0.0

        with columns[i % len(columns)]:

            marks = st.number_input(
                f"{co} Marks",
                min_value=0.0,
                step=0.5,
                key=key
            )

        assessment_total += marks

        allocation_data.append({
            "Assessment": assessment_name,
            "Assessment Type": assessment_type,
            "Course Outcome": co,
            "Allocated Marks": marks
        })

    difference = round(
        assessment_total - maximum_marks,
        2
    )

    if abs(difference) < 0.001:

        st.success(
            f"Allocated: {assessment_total:g} / "
            f"{maximum_marks:g}"
        )

    else:

        valid_allocation = False

        st.error(
            f"Allocated: {assessment_total:g} / "
            f"{maximum_marks:g} | "
            f"Difference: {difference:g}"
        )

    st.divider()


# =========================================================
# FINAL CO ASSESSMENT ALLOCATION MATRIX
# =========================================================

st.markdown(
    '<div class="section-title">'
    'Final CO Assessment Allocation Matrix'
    '</div>',
    unsafe_allow_html=True
)

allocation_df = pd.DataFrame(allocation_data)

matrix_df = allocation_df.pivot(
    index=["Assessment", "Assessment Type"],
    columns="Course Outcome",
    values="Allocated Marks"
).reset_index()

matrix_df.columns.name = None

matrix_df = matrix_df[
    ["Assessment", "Assessment Type"] + CO_LIST
]

# Add total maximum marks
maximum_lookup = {
    item["Assessment"]: item["Maximum Marks"]
    for item in assessments
}

matrix_df["Total Maximum Marks"] = (
    matrix_df["Assessment"].map(maximum_lookup)
)

matrix_df["Total Allocated Marks"] = (
    matrix_df[CO_LIST].sum(axis=1)
)

# Display only the final matrix
st.dataframe(
    matrix_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# VALIDATION
# =========================================================

if valid_allocation:

    st.success(
        "All assessment allocations match their maximum marks."
    )

else:

    st.warning(
        "Please correct the allocation values before downloading."
    )


# =========================================================
# EXCEL REPORT
# =========================================================

def create_excel_report():

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        matrix_df.to_excel(
            writer,
            sheet_name="CO Allocation Matrix",
            index=False
        )

        ws = writer.book["CO Allocation Matrix"]

        header_fill = PatternFill(
            "solid",
            fgColor="174D36"
        )

        header_font = Font(
            bold=True,
            color="FFFFFF"
        )

        thin_border = Border(
            bottom=Side(
                style="thin",
                color="D6D6D6"
            )
        )

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        for cell in ws[1]:

            cell.fill = header_fill
            cell.font = header_font

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True
            )

        for row in ws.iter_rows(min_row=2):

            for cell in row:

                cell.border = thin_border

                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center",
                    wrap_text=True
                )

        for column_cells in ws.columns:

            max_length = max(
                (
                    len(str(cell.value))
                    for cell in column_cells
                    if cell.value is not None
                ),
                default=10
            )

            letter = get_column_letter(
                column_cells[0].column
            )

            ws.column_dimensions[letter].width = min(
                max_length + 4,
                40
            )

        ws.row_dimensions[1].height = 30

    output.seek(0)

    return output


# =========================================================
# DOWNLOAD MATRIX
# =========================================================

st.divider()

if valid_allocation:

    report = create_excel_report()

    st.download_button(
        label="Download CO Allocation Matrix",
        data=report,
        file_name=f"CO_Allocation_{course_code}.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True
    )

else:

    st.button(
        "Download CO Allocation Matrix",
        disabled=True,
        use_container_width=True
    )


# =========================================================
# RESET
# =========================================================

if st.button("Reset Dashboard"):

    st.cache_data.clear()
    st.session_state.clear()
    st.rerun()
