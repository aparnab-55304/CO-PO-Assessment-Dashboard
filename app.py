
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
    margin-top: 12px;
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
# FILE PATHS
# =========================================================

BASE_DIR = Path(__file__).parent

COURSE_GROUP_PATH = BASE_DIR / "Course Group.xlsx"
SYLLABUS_PATH = BASE_DIR / "MGU_Syllabus_Template.xlsx"

# =========================================================
# STANDARD COLUMN NAMES
# =========================================================

ALIASES = {
    "Program": [
        "Program", "Programme", "Program Name",
        "Programme Name"
    ],
    "Semester": [
        "Semester", "Semester Name", "Sem"
    ],
    "Course Code": [
        "Course Code", "Subject Code", "Paper Code",
        "Course ID", "Subject ID"
    ],
    "Course Name": [
        "Course Name", "Subject Name", "Course",
        "Subject", "Paper Name", "Course Title"
    ],
    "Credit": [
        "Credit", "Credits"
    ],
    "Total Marks": [
        "Total Marks", "Maximum Marks", "Total"
    ],
    "Internal Marks": [
        "Internal Marks", "ISA", "Internal"
    ],
    "External Marks": [
        "External Marks", "ESA", "External"
    ],
    "CO": [
        "CO", "CO Number", "Course Outcome",
        "CO Code"
    ],
    "CO Statement": [
        "CO Statement", "Course Outcome Statement",
        "Outcome Description", "Description"
    ],
    "Learning Level": [
        "Learning Level", "Bloom Level",
        "Bloom's Taxonomy", "Level"
    ],
    "Assessment": [
        "Assessment", "Assessment Name",
        "Component", "Exam Name"
    ],
    "Assessment Type": [
        "Assessment Type", "Type", "Category"
    ],
    "Maximum Marks": [
        "Maximum Marks", "Max Marks",
        "Max Mark", "Marks"
    ]
}


def standardize_columns(df):

    df = df.copy()

    df.columns = [
        str(c).strip().replace("\n", " ")
        for c in df.columns
    ]

    rename = {}

    for standard, possible_names in ALIASES.items():

        for col in df.columns:

            if col.strip().lower() in [
                x.lower() for x in possible_names
            ]:
                rename[col] = standard
                break

    return df.rename(columns=rename)


def clean_text(df):

    df = df.copy()

    for col in df.columns:

        if df[col].dtype == "object":
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
            )

    return df


def clean_code(value):

    if pd.isna(value):
        return ""

    return str(value).strip().upper()


# =========================================================
# LOAD COURSE GROUP
# =========================================================

@st.cache_data
def load_course_group():

    if not COURSE_GROUP_PATH.exists():
        return pd.DataFrame()

    df = pd.read_excel(
        COURSE_GROUP_PATH,
        header=2,
        engine="openpyxl"
    )

    df = standardize_columns(df)
    df = clean_text(df)

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    return df


# =========================================================
# LOAD SYLLABUS WORKBOOK
# =========================================================

@st.cache_data
def load_syllabus():

    if not SYLLABUS_PATH.exists():
        raise FileNotFoundError(
            "MGU_Syllabus_Template.xlsx was not found."
        )

    workbook = pd.ExcelFile(
        SYLLABUS_PATH,
        engine="openpyxl"
    )

    required_sheets = [
        "Courses",
        "Course_Outcomes",
        "Assessments"
    ]

    missing = [
        s for s in required_sheets
        if s not in workbook.sheet_names
    ]

    if missing:
        raise ValueError(
            "Missing sheets: " + ", ".join(missing)
        )

    courses = pd.read_excel(
        workbook,
        sheet_name="Courses"
    )

    outcomes = pd.read_excel(
        workbook,
        sheet_name="Course_Outcomes"
    )

    assessments = pd.read_excel(
        workbook,
        sheet_name="Assessments"
    )

    courses = clean_text(standardize_columns(courses))
    outcomes = clean_text(standardize_columns(outcomes))
    assessments = clean_text(standardize_columns(assessments))

    required_courses = [
        "Program", "Semester",
        "Course Code", "Course Name"
    ]

    required_outcomes = [
        "Course Code", "CO", "CO Statement"
    ]

    required_assessments = [
        "Course Code", "Assessment",
        "Assessment Type", "Maximum Marks"
    ]

    for col in required_courses:

        if col not in courses.columns:
            raise ValueError(
                f"Courses sheet is missing: {col}"
            )

    for col in required_outcomes:

        if col not in outcomes.columns:
            raise ValueError(
                f"Course_Outcomes sheet is missing: {col}"
            )

    for col in required_assessments:

        if col not in assessments.columns:
            raise ValueError(
                f"Assessments sheet is missing: {col}"
            )

    for df in [courses, outcomes, assessments]:

        df["Course Code"] = (
            df["Course Code"].apply(clean_code)
        )

    courses = courses[
        courses["Course Code"] != ""
    ].copy()

    outcomes = outcomes[
        outcomes["Course Code"] != ""
    ].copy()

    assessments = assessments[
        assessments["Course Code"] != ""
    ].copy()

    if courses.empty:
        raise ValueError("No course records found.")

    if outcomes.empty:
        raise ValueError("No course outcome records found.")

    if assessments.empty:
        raise ValueError("No assessment records found.")

    assessments["Maximum Marks"] = pd.to_numeric(
        assessments["Maximum Marks"],
        errors="coerce"
    )

    if assessments["Maximum Marks"].isna().any():
        raise ValueError(
            "Every assessment must have numeric Maximum Marks."
        )

    if (assessments["Maximum Marks"] < 0).any():
        raise ValueError(
            "Assessment maximum marks cannot be negative."
        )

    assessments["Assessment Type"] = (
        assessments["Assessment Type"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    invalid_types = ~assessments["Assessment Type"].isin(
        ["Internal", "External"]
    )

    if invalid_types.any():
        raise ValueError(
            "Assessment Type must be Internal or External."
        )

    if courses["Course Code"].duplicated().any():
        raise ValueError(
            "Duplicate Course Code found in Courses sheet."
        )

    return courses, outcomes, assessments


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
    "Outcome-Based Education | Course Outcomes | "
    "Assessment-wise CO Marks Allocation"
)

st.divider()

# =========================================================
# AUTOMATICALLY LOAD EXCEL FILES
# =========================================================

try:

    course_group_df = load_course_group()

    courses_df, outcomes_df, assessments_df = (
        load_syllabus()
    )

except Exception as e:

    st.error(f"Excel loading error: {e}")
    st.stop()


# =========================================================
# COURSE GROUP FILTER
# =========================================================

if (
    not course_group_df.empty
    and "Program" in course_group_df.columns
):

    group_programs = set(
        course_group_df["Program"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    syllabus_programs = set(
        courses_df["Program"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    if group_programs.intersection(syllabus_programs):

        courses_df = courses_df[
            courses_df["Program"].astype(str).isin(
                group_programs
            )
        ]


# =========================================================
# PROGRAMME AND SEMESTER SELECTION
# =========================================================

st.markdown(
    '<div class="section-title">Course Selection</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

programs = sorted(
    courses_df["Program"]
    .dropna()
    .astype(str)
    .unique()
)

if not programs:
    st.error("No programmes are available in the syllabus.")
    st.stop()

with col1:

    selected_program = st.selectbox(
        "Select Programme",
        programs,
        key="selected_program"
    )

program_df = courses_df[
    courses_df["Program"].astype(str)
    == selected_program
]

semesters = sorted(
    program_df["Semester"]
    .dropna()
    .astype(str)
    .unique()
)

if not semesters:
    st.error("No semesters found for this programme.")
    st.stop()

with col2:

    selected_semester = st.selectbox(
        "Select Semester",
        semesters,
        key="selected_semester"
    )

semester_df = program_df[
    program_df["Semester"].astype(str)
    == selected_semester
]

# =========================================================
# COURSE SELECTION
# =========================================================

course_options = semester_df[
    ["Course Code", "Course Name"]
].drop_duplicates()

course_options["Display"] = (
    course_options["Course Code"].astype(str)
    + " - "
    + course_options["Course Name"].astype(str)
)

if course_options.empty:
    st.error("No subjects found for this semester.")
    st.stop()

selected_course_display = st.selectbox(
    "Select Subject / Course",
    course_options["Display"].tolist(),
    key="selected_course"
)

selected_course_code = course_options.loc[
    course_options["Display"] == selected_course_display,
    "Course Code"
].iloc[0]

selected_course = courses_df[
    courses_df["Course Code"] == selected_course_code
].iloc[0]

st.success(
    f"Selected: {selected_program} | "
    f"{selected_semester} | "
    f"{selected_course['Course Name']}"
)

# =========================================================
# GET SELECTED COURSE OUTCOMES AND ASSESSMENTS
# =========================================================

selected_outcomes = outcomes_df[
    outcomes_df["Course Code"] == selected_course_code
].copy()

selected_assessments = assessments_df[
    assessments_df["Course Code"] == selected_course_code
].copy()

if selected_outcomes.empty:
    st.error("No Course Outcomes found for this subject.")
    st.stop()

if selected_assessments.empty:
    st.error("No assessments found for this subject.")
    st.stop()

if selected_outcomes["CO"].duplicated().any():
    st.error("Duplicate CO codes found for this subject.")
    st.stop()

if selected_assessments["Assessment"].duplicated().any():
    st.error("Duplicate assessment names found for this subject.")
    st.stop()

CO_LIST = selected_outcomes["CO"].astype(str).tolist()

# =========================================================
# COURSE OUTCOMES
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">Course Outcomes</div>',
    unsafe_allow_html=True
)

display_columns = [
    c for c in [
        "CO",
        "CO Statement",
        "Learning Level"
    ]
    if c in selected_outcomes.columns
]

st.dataframe(
    selected_outcomes[display_columns],
    use_container_width=True,
    hide_index=True
)

# =========================================================
# ASSESSMENT-WISE CO MARKS ALLOCATION
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">'
    'Assessment-wise CO Marks Allocation'
    '</div>',
    unsafe_allow_html=True
)

st.write(
    "Enter the maximum marks allocated to each CO "
    "under every assessment component."
)

allocation_data = []
assessment_summary = []

internal_max_total = 0.0
external_max_total = 0.0

internal_co_totals = {
    co: 0.0 for co in CO_LIST
}

external_co_totals = {
    co: 0.0 for co in CO_LIST
}

valid_allocation = True

for _, assessment_row in selected_assessments.iterrows():

    assessment_name = str(
        assessment_row["Assessment"]
    )

    assessment_type = str(
        assessment_row["Assessment Type"]
    )

    max_marks = float(
        assessment_row["Maximum Marks"]
    )

    if assessment_type == "Internal":
        internal_max_total += max_marks
    else:
        external_max_total += max_marks

    st.markdown(f"### {assessment_name}")

    st.caption(
        f"Assessment Type: {assessment_type} | "
        f"Maximum Marks: {max_marks:g}"
    )

    co_columns = st.columns(
        min(len(CO_LIST), 4)
    )

    assessment_total = 0.0

    for i, co in enumerate(CO_LIST):

        key = (
            f"alloc_{selected_course_code}_"
            f"{assessment_name}_{co}"
        )

        if key not in st.session_state:
            st.session_state[key] = 0.0

        with co_columns[i % len(co_columns)]:

            allocated_marks = st.number_input(
                f"{co} Marks",
                min_value=0.0,
                value=float(st.session_state[key]),
                step=0.5,
                key=key
            )

        assessment_total += allocated_marks

        if assessment_type == "Internal":
            internal_co_totals[co] += allocated_marks
        else:
            external_co_totals[co] += allocated_marks

        allocation_data.append({
            "Assessment": assessment_name,
            "Assessment Type": assessment_type,
            "Course Outcome": co,
            "Allocated Maximum Marks": allocated_marks
        })

    difference = round(
        assessment_total - max_marks, 2
    )

    is_valid = abs(difference) < 0.001

    if is_valid:
        st.success(
            f"Allocated: {assessment_total:g} / "
            f"{max_marks:g}"
        )
    else:
        valid_allocation = False

        st.error(
            f"Allocated: {assessment_total:g} / "
            f"{max_marks:g} | "
            f"Difference: {difference:g}"
        )

    assessment_summary.append({
        "Assessment": assessment_name,
        "Assessment Type": assessment_type,
        "Maximum Marks": max_marks,
        "Allocated Marks": assessment_total,
        "Difference": difference,
        "Valid": is_valid
    })

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
    values="Allocated Maximum Marks"
).reset_index()

matrix_df.columns.name = None

# Arrange columns in the original CO order

matrix_df = matrix_df[
    ["Assessment", "Assessment Type"] + CO_LIST
]

# Add assessment maximum marks

max_marks_lookup = dict(
    zip(
        selected_assessments["Assessment"].astype(str),
        selected_assessments["Maximum Marks"]
    )
)

matrix_df["Total Maximum Marks"] = (
    matrix_df["Assessment"].map(max_marks_lookup)
)

matrix_df["Total Allocated Marks"] = (
    matrix_df[CO_LIST].sum(axis=1)
)

st.dataframe(
    matrix_df,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# FINAL VALIDATION
# =========================================================

if valid_allocation:

    st.success(
        "All assessment allocations match their maximum marks."
    )

else:

    st.warning(
        "Some allocations do not match the maximum marks. "
        "Correct the values before downloading the matrix."
    )

# =========================================================
# EXCEL MATRIX DOWNLOAD
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

        workbook = writer.book
        ws = workbook["CO Allocation Matrix"]

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
# DOWNLOAD
# =========================================================

st.divider()

if valid_allocation:

    report = create_excel_report()

    st.download_button(
        label="Download CO Allocation Matrix",
        data=report,
        file_name=(
            f"CO_Allocation_Matrix_{selected_course_code}.xlsx"
        ),
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
