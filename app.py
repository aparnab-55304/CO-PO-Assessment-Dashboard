
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
div[data-testid="stMetric"] {
    background: #F3F7F4;
    padding: 12px;
    border-radius: 8px;
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
# SYLLABUS TEMPLATE
# =========================================================

def create_syllabus_template():

    output = BytesIO()

    courses = pd.DataFrame([
        {
            "Program": "",
            "Semester": "",
            "Course Code": "",
            "Course Name": "",
            "Credit": "",
            "Total Marks": "",
            "Internal Marks": "",
            "External Marks": ""
        }
    ])

    outcomes = pd.DataFrame([
        {
            "Course Code": "",
            "CO": "CO1",
            "CO Statement": "",
            "Learning Level": ""
        },
        {
            "Course Code": "",
            "CO": "CO2",
            "CO Statement": "",
            "Learning Level": ""
        }
    ])

    assessments = pd.DataFrame([
        {
            "Course Code": "",
            "Assessment": "PA1",
            "Assessment Type": "Internal",
            "Maximum Marks": 0
        },
        {
            "Course Code": "",
            "Assessment": "PA2",
            "Assessment Type": "Internal",
            "Maximum Marks": 0
        },
        {
            "Course Code": "",
            "Assessment": "External Examination",
            "Assessment Type": "External",
            "Maximum Marks": 0
        }
    ])

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        courses.to_excel(
            writer,
            sheet_name="Courses",
            index=False
        )

        outcomes.to_excel(
            writer,
            sheet_name="Course_Outcomes",
            index=False
        )

        assessments.to_excel(
            writer,
            sheet_name="Assessments",
            index=False
        )

    output.seek(0)

    return output


# =========================================================
# LOAD COURSE GROUP
# =========================================================

@st.cache_data
def load_course_group(file_bytes=None):

    if file_bytes is not None:

        df = pd.read_excel(
            BytesIO(file_bytes),
            header=2,
            engine="openpyxl"
        )

    elif COURSE_GROUP_PATH.exists():

        df = pd.read_excel(
            COURSE_GROUP_PATH,
            header=2,
            engine="openpyxl"
        )

    else:
        return pd.DataFrame()

    df = standardize_columns(df)
    df = clean_text(df)

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    return df


# =========================================================
# LOAD SYLLABUS WORKBOOK
# =========================================================

def load_syllabus(file):

    workbook = pd.ExcelFile(file)

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

    # Required columns

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

    # Clean identifiers

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

    # Numeric maximum marks

    assessments["Maximum Marks"] = pd.to_numeric(
        assessments["Maximum Marks"],
        errors="coerce"
    )

    if assessments["Maximum Marks"].isna().any():
        raise ValueError(
            "Every assessment must have a numeric Maximum Marks value."
        )

    if (assessments["Maximum Marks"] < 0).any():
        raise ValueError(
            "Assessment maximum marks cannot be negative."
        )

    # Validate assessment types

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

    # Validate duplicate course codes

    if courses["Course Code"].duplicated().any():
        raise ValueError(
            "Duplicate Course Code found in Courses sheet. "
            "Each course must have a unique code."
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
    "Internal and External Assessment Allocation"
)

st.divider()


# =========================================================
# FILE UPLOAD
# =========================================================

st.markdown(
    '<div class="section-title">Upload Course and Syllabus Data</div>',
    unsafe_allow_html=True
)

upload_col1, upload_col2 = st.columns(2)

with upload_col1:

    course_group_file = st.file_uploader(
        "Upload Course Group.xlsx (optional)",
        type=["xlsx"],
        key="course_group_upload"
    )

with upload_col2:

    syllabus_file = st.file_uploader(
        "Upload Syllabus Excel Workbook",
        type=["xlsx"],
        key="syllabus_upload"
    )

st.download_button(
    "Download Syllabus Excel Template",
    data=create_syllabus_template(),
    file_name="MGU_Syllabus_Template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


# =========================================================
# LOAD COURSE GROUP DATA
# =========================================================

try:

    group_bytes = (
        course_group_file.getvalue()
        if course_group_file else None
    )

    course_group_df = load_course_group(group_bytes)

except Exception as e:

    st.error(f"Course Group error: {e}")
    st.stop()


# =========================================================
# LOAD SYLLABUS DATA
# =========================================================

if syllabus_file is None:

    st.info(
        "Upload the syllabus workbook to load the actual "
        "programmes, semesters, subjects, COs and assessments."
    )

    st.stop()

try:

    courses_df, outcomes_df, assessments_df = (
        load_syllabus(syllabus_file)
    )

except Exception as e:

    st.error(f"Syllabus loading error: {e}")
    st.stop()


# =========================================================
# COURSE GROUP FILTER
# =========================================================

# Course Group is used as an additional source of
# programme/course information where matching columns exist.

if not course_group_df.empty:

    if "Program" in course_group_df.columns:

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
# MAIN COURSE SELECTION
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">Course Selection</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3, tab4 = st.tabs([
    "Programme & Semester",
    "Course Details",
    "Course Outcomes",
    "Assessment Allocation"
])


with tab1:

    col1, col2 = st.columns(2)

    with col1:

        programs = sorted(
            courses_df["Program"]
            .dropna()
            .astype(str)
            .unique()
        )

        selected_program = st.selectbox(
            "Select Programme",
            programs,
            key="selected_program"
        )

    program_df = courses_df[
        courses_df["Program"].astype(str)
        == selected_program
    ]

    with col2:

        semesters = sorted(
            program_df["Semester"]
            .dropna()
            .astype(str)
            .unique()
        )

        selected_semester = st.selectbox(
            "Select Semester",
            semesters,
            key="selected_semester"
        )

    semester_df = program_df[
        program_df["Semester"].astype(str)
        == selected_semester
    ]

    st.success(
        f"Selected Programme: {selected_program} | "
        f"Semester: {selected_semester}"
    )


# =========================================================
# COURSE SELECTION
# =========================================================

with tab2:

    course_options = semester_df[
        ["Course Code", "Course Name"]
    ].drop_duplicates()

    course_options["Display"] = (
        course_options["Course Code"].astype(str)
        + " - "
        + course_options["Course Name"].astype(str)
    )

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

    st.markdown("### Selected Subject Information")

    info1, info2, info3 = st.columns(3)

    info1.metric(
        "Course Code",
        selected_course["Course Code"]
    )

    info2.metric(
        "Course Name",
        selected_course["Course Name"]
    )

    info3.metric(
        "Semester",
        selected_course["Semester"]
    )

    details = {}

    for col in [
        "Credit",
        "Total Marks",
        "Internal Marks",
        "External Marks"
    ]:

        if col in courses_df.columns:
            details[col] = selected_course[col]

    detail_cols = st.columns(4)

    for i, (key, value) in enumerate(details.items()):

        with detail_cols[i]:

            if pd.isna(value):
                value = "-"

            st.write(f"**{key}**")
            st.write(value)


# =========================================================
# SELECTED COURSE CO DETAILS
# =========================================================

selected_outcomes = outcomes_df[
    outcomes_df["Course Code"] == selected_course_code
].copy()

selected_assessments = assessments_df[
    assessments_df["Course Code"] == selected_course_code
].copy()

if selected_outcomes.empty:

    st.error(
        "No Course Outcomes are available for this subject "
        "in the syllabus workbook."
    )

    st.stop()

if selected_assessments.empty:

    st.error(
        "No assessment components are available for this subject."
    )

    st.stop()


# Remove duplicate CO entries

if selected_outcomes["CO"].duplicated().any():

    st.error(
        "Duplicate CO codes found for this course in the syllabus."
    )

    st.stop()


CO_LIST = selected_outcomes["CO"].astype(str).tolist()


# =========================================================
# CO SYLLABUS DISPLAY
# =========================================================

with tab3:

    st.markdown("### Course Outcomes Mentioned in Syllabus")

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

    st.metric(
        "Total Course Outcomes",
        len(CO_LIST)
    )


# =========================================================
# ASSESSMENT ALLOCATION
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">Assessment-wise CO Marks Allocation</div>',
    unsafe_allow_html=True
)

st.write(
    "Allocate the maximum marks of each assessment among "
    "the Course Outcomes. The total CO allocation must equal "
    "the maximum marks specified in the syllabus."
)

# Initialize persistent session values

for _, assessment_row in selected_assessments.iterrows():

    assessment_name = str(
        assessment_row["Assessment"]
    )

    for co in CO_LIST:

        key = (
            f"alloc_{selected_course_code}_"
            f"{assessment_name}_{co}"
        )

        if key not in st.session_state:
            st.session_state[key] = 0.0


allocation_data = []
assessment_summary = []

valid_allocation = True

internal_max_total = 0.0
external_max_total = 0.0

internal_co_totals = {
    co: 0.0 for co in CO_LIST
}

external_co_totals = {
    co: 0.0 for co in CO_LIST
}

for index, assessment_row in selected_assessments.iterrows():

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

    with st.expander(
        f"{assessment_name} | {assessment_type} | "
        f"Maximum Marks: {max_marks:g}",
        expanded=True
    ):

        st.write(
            f"**Maximum marks for this assessment: "
            f"{max_marks:g}**"
        )

        co_columns = st.columns(
            min(len(CO_LIST), 4)
        )

        assessment_total = 0.0

        current_allocations = {}

        for i, co in enumerate(CO_LIST):

            key = (
                f"alloc_{selected_course_code}_"
                f"{assessment_name}_{co}"
            )

            with co_columns[i % len(co_columns)]:

                allocated_marks = st.number_input(
                    f"{co} Marks",
                    min_value=0.0,
                    value=float(st.session_state[key]),
                    step=0.5,
                    key=key
                )

            current_allocations[co] = allocated_marks

            assessment_total += allocated_marks

            if assessment_type == "Internal":

                internal_co_totals[co] += allocated_marks

            else:

                external_co_totals[co] += allocated_marks

            allocation_data.append({
                "Course Code": selected_course_code,
                "Assessment": assessment_name,
                "Assessment Type": assessment_type,
                "Course Outcome": co,
                "Allocated Maximum Marks": allocated_marks
            })

        difference = round(
            assessment_total - max_marks, 2
        )

        if abs(difference) < 0.001:

            st.success(
                f"Allocated: {assessment_total:g} / "
                f"{max_marks:g} marks"
            )

        else:

            valid_allocation = False

            st.error(
                f"Allocated: {assessment_total:g} / "
                f"{max_marks:g} marks. "
                f"Difference: {difference:g}"
            )

        assessment_summary.append({
            "Assessment": assessment_name,
            "Assessment Type": assessment_type,
            "Maximum Marks": max_marks,
            "Allocated Marks": assessment_total,
            "Difference": difference,
            "Valid": abs(difference) < 0.001
        })


# =========================================================
# TOTAL MARK VALIDATION
# =========================================================

st.divider()

st.markdown("### Overall Assessment Marks")

total_max_marks = (
    internal_max_total + external_max_total
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Internal Maximum Marks",
    f"{internal_max_total:g}"
)

col2.metric(
    "External Maximum Marks",
    f"{external_max_total:g}"
)

col3.metric(
    "Total Course Marks",
    f"{total_max_marks:g}"
)


# Compare syllabus course totals if available

syllabus_total = selected_course.get(
    "Total Marks", None
)

if syllabus_total is not None and pd.notna(syllabus_total):

    try:

        expected_total = float(syllabus_total)

        if abs(expected_total - total_max_marks) > 0.001:

            valid_allocation = False

            st.warning(
                f"The sum of assessment maximum marks "
                f"({total_max_marks:g}) does not match "
                f"the course total in the syllabus "
                f"({expected_total:g})."
            )

    except (ValueError, TypeError):
        pass


# =========================================================
# INTERNAL AND EXTERNAL CO SUMMARY
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">CO-wise Internal and External Weightage</div>',
    unsafe_allow_html=True
)

co_summary_rows = []

for co in CO_LIST:

    internal = internal_co_totals[co]
    external = external_co_totals[co]

    co_summary_rows.append({
        "Course Outcome": co,
        "Internal Weightage": round(internal, 2),
        "External Weightage": round(external, 2),
        "Total CO Weightage": round(
            internal + external, 2
        )
    })

co_summary_df = pd.DataFrame(co_summary_rows)

st.dataframe(
    co_summary_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# ASSESSMENT SUMMARY
# =========================================================

st.markdown("### Assessment Validation Summary")

assessment_summary_df = pd.DataFrame(
    assessment_summary
)

st.dataframe(
    assessment_summary_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# FINAL ALLOCATION MATRIX
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">Final CO Assessment Allocation Matrix</div>',
    unsafe_allow_html=True
)

allocation_df = pd.DataFrame(allocation_data)

matrix_df = allocation_df.pivot(
    index=["Assessment", "Assessment Type"],
    columns="Course Outcome",
    values="Allocated Maximum Marks"
).reset_index()

matrix_df.columns.name = None

st.dataframe(
    matrix_df,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# FINAL STATUS
# =========================================================

st.divider()

if valid_allocation:

    st.success(
        "All assessment allocations match their respective "
        "maximum marks. The allocation report is ready."
    )

else:

    st.warning(
        "Some assessment allocations are incomplete or do not "
        "match the syllabus maximum marks. Correct them before "
        "generating the final report."
    )


# =========================================================
# EXCEL REPORT
# =========================================================

def create_excel_report():

    output = BytesIO()

    course_details = pd.DataFrame([
        selected_course.to_dict()
    ])

    co_report = selected_outcomes.copy()

    assessment_report = pd.DataFrame(
        assessment_summary
    )

    internal_report = pd.DataFrame([
        {
            "Course Outcome": co,
            "Internal Weightage": internal_co_totals[co],
            "External Weightage": external_co_totals[co],
            "Total Weightage":
                internal_co_totals[co]
                + external_co_totals[co]
        }
        for co in CO_LIST
    ])

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        course_details.to_excel(
            writer,
            sheet_name="Course Details",
            index=False
        )

        co_report.to_excel(
            writer,
            sheet_name="Course Outcomes",
            index=False
        )

        allocation_df.to_excel(
            writer,
            sheet_name="Detailed Allocation",
            index=False
        )

        matrix_df.to_excel(
            writer,
            sheet_name="CO Allocation Matrix",
            index=False
        )

        assessment_report.to_excel(
            writer,
            sheet_name="Assessment Summary",
            index=False
        )

        internal_report.to_excel(
            writer,
            sheet_name="CO Weightage Summary",
            index=False
        )

        # Workbook formatting

        workbook = writer.book

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

        for ws in workbook.worksheets:

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
                    max_length + 4, 45
                )

            ws.row_dimensions[1].height = 30

    output.seek(0)

    return output


# =========================================================
# DOWNLOAD REPORT
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">Download CO Allocation Report</div>',
    unsafe_allow_html=True
)

if valid_allocation:

    report = create_excel_report()

    st.download_button(
        label="Download CO Weightage Excel Report",
        data=report,
        file_name=(
            f"CO_Weightage_{selected_course_code}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True
    )

else:

    st.button(
        "Download CO Weightage Excel Report",
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
