import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="CO Weightage Allocation Dashboard",
    page_icon="📊",
    layout="wide"
)

EXCEL_FILE = Path(__file__).parent / "Course Group.xlsx"

ASSESSMENTS = ["PA1", "PA2", "LE1", "LE2"]

# Only written exams are conducted for some marks and then converted.
# LE (attendance, etc.) is not an exam, so it has a single marks field.
EXAM_ASSESSMENTS = ["PA1", "PA2"]


# ==================================================
# CUSTOM CSS - FOREST GREEN + CHAMPAGNE
# ==================================================

st.markdown("""
<style>
.stApp {
    background-color: #F3F6F1;
}

/* Dashboard header */
.dashboard-header {
    background: linear-gradient(120deg, #183D32, #285C49);
    padding: 30px 32px;
    border-radius: 12px;
    margin-bottom: 25px;
    border-bottom: 5px solid #C8B98A;
}

.dashboard-header h1 {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-size: 30px;
    font-weight: 750;
    margin: 0;
}

.dashboard-header .dashboard-subtitle {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-size: 16px;
    font-weight: 700;
    margin-top: 8px;
    opacity: 1 !important;
}

/* Normal text */
.stApp p,
.stApp label,
.stApp li {
    color: #171717 !important;
}

/* Section headings */
.section-heading {
    color: #183D32 !important;
    font-size: 21px;
    font-weight: 750;
    margin-top: 22px;
    margin-bottom: 14px;
    border-left: 5px solid #C8B98A;
    padding-left: 12px;
}

/* Assessment cards */
.assessment-title {
    color: #183D32 !important;
    font-size: 20px;
    font-weight: 750;
}

/* Input fields */
.stTextInput input,
.stNumberInput input {
    color: #171717 !important;
    -webkit-text-fill-color: #171717 !important;
    background-color: #FFFFFF !important;
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    background-color: #183D32 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 2px solid #C8B98A !important;
    border-radius: 8px;
    font-weight: 700 !important;
    padding: 10px 22px;
}

.stButton > button *,
.stDownloadButton > button * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 700 !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background-color: #285C49 !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #DCE5DA;
    border-left: 4px solid #C8B98A;
    border-radius: 10px;
    padding: 15px;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
    color: #183D32 !important;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# HEADER
# ==================================================

st.markdown("""
<div class="dashboard-header">
    <h1>CO Weightage Allocation Dashboard</h1>
    <div class="dashboard-subtitle">
        Course Outcome Assessment Weightage Management System
    </div>
</div>
""", unsafe_allow_html=True)


# ==================================================
# LOAD COURSE DETAILS
# ==================================================

def _clean(value):
    """Normalise a cell: remove NBSP/newlines, collapse spaces, lowercase."""
    return " ".join(
        str(value).replace("\u00a0", " ").replace("\n", " ").split()
    ).strip().lower()


def _classify(cell_text):
    """Map a header cell to one of the four required column names."""
    c = cell_text
    if not c or c == "nan":
        return None
    if "depart" in c:
        return "Department"
    if "type" in c:
        return "Program Type"
    if "code" in c:
        return "Program Code"
    if c.startswith("program") or "course" in c:
        return "Program"
    return None


@st.cache_data
def load_course_data():

    required_columns = [
        "Department",
        "Program Type",
        "Program",
        "Program Code"
    ]

    workbook = pd.ExcelFile(EXCEL_FILE)

    preview = []

    for sheet in workbook.sheet_names:

        raw = pd.read_excel(workbook, sheet_name=sheet, header=None)

        # Search the first 60 rows so title/blank rows above the
        # table are skipped automatically.
        for i in range(min(60, len(raw))):

            column_positions = {}

            for position, value in enumerate(raw.iloc[i]):

                name = _classify(_clean(value))

                if name and name not in column_positions:
                    column_positions[name] = position

            if all(col in column_positions for col in required_columns):

                data = raw.iloc[i + 1:].copy()

                df = pd.DataFrame({
                    col: data.iloc[:, column_positions[col]].values
                    for col in required_columns
                })

                # Merged cells leave blanks below the first value.
                df["Department"] = df["Department"].ffill()
                df["Program Type"] = df["Program Type"].ffill()

                for col in required_columns:
                    df[col] = (
                        df[col].astype("string")
                        .str.replace("\u00a0", " ", regex=False)
                        .str.strip()
                    )

                df = df.dropna(subset=required_columns)

                for col in required_columns:
                    df = df[(df[col] != "") & (df[col].str.lower() != "nan")]

                if len(df) > 0:
                    return df.drop_duplicates().reset_index(drop=True)

        # Keep a short preview of this sheet for the error message.
        for i in range(min(8, len(raw))):
            cells = [
                str(v) for v in raw.iloc[i].tolist()
                if str(v) != "nan"
            ]
            if cells:
                preview.append(f"[{sheet}] row {i + 1}: " + " | ".join(cells))

    raise ValueError(
        "Could not find a header row containing Department, Program Type, "
        "Program and Program Code. First rows found: "
        + " || ".join(preview[:10])
    )


try:
    course_data = load_course_data()

except FileNotFoundError:
    st.error(
        "Course Group.xlsx was not found. "
        "Place it in the same folder as app.py."
    )
    st.stop()

except PermissionError:
    st.error(
        "Unable to access Course Group.xlsx. "
        "Close the Excel file if it is open and check file permissions."
    )
    st.stop()

except Exception as e:
    st.error(f"Unable to load course details: {e}")
    st.stop()


# ==================================================
# COURSE DETAILS
# ==================================================

st.markdown(
    '<div class="section-heading">Course Details</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    departments = sorted(
        course_data["Department"].unique().tolist()
    )

    department = st.selectbox(
        "Department",
        departments
    )

    program_types = sorted(
        course_data.loc[
            course_data["Department"] == department,
            "Program Type"
        ].unique().tolist()
    )

    program_type = st.selectbox(
        "Program Type",
        program_types
    )

with col2:

    filtered = course_data[
        (course_data["Department"] == department) &
        (course_data["Program Type"] == program_type)
    ]

    programs = sorted(filtered["Program"].unique().tolist())

    program = st.selectbox(
        "Course Name",
        programs
    )

    selected_course = filtered[
        filtered["Program"] == program
    ]

    course_codes = selected_course["Program Code"].unique()

    course_code = course_codes[0] if len(course_codes) else ""

    st.text_input(
        "Course Code",
        value=str(course_code),
        disabled=True
    )


# ==================================================
# COURSE OUTCOMES - FIXED WEIGHTAGES
# ==================================================

st.markdown(
    '<div class="section-heading">Course Outcomes</div>',
    unsafe_allow_html=True
)

number_of_cos = st.number_input(
    "Number of Course Outcomes",
    min_value=1,
    max_value=20,
    value=4,
    step=1
)

co_list = [
    f"CO{i}" for i in range(1, int(number_of_cos) + 1)
]

st.write("*Enter the fixed weightage for each Course Outcome:*")

fixed_columns = st.columns(min(len(co_list), 4))

fixed_co_weights = {}

for i, co in enumerate(co_list):

    with fixed_columns[i % len(fixed_columns)]:

        fixed_co_weights[co] = st.number_input(
            f"{co} Fixed Weightage",
            min_value=0.0,
            value=1.0,
            step=0.5,
            key=f"fixed_{co}"
        )

# Denominator always uses ALL fixed CO weightages.
fixed_weightage_sum = sum(fixed_co_weights.values())


# ==================================================
# SESSION STATE INITIALIZATION
# ==================================================

# Each assessment has its own independent CO weightages.

if "assessment_co_values" not in st.session_state:
    st.session_state.assessment_co_values = {}

for assessment in ASSESSMENTS:

    if assessment not in st.session_state.assessment_co_values:
        st.session_state.assessment_co_values[assessment] = {}

    for co in co_list:

        key = f"{assessment}_{co}_assessment_weight"

        if co not in st.session_state.assessment_co_values[assessment]:
            st.session_state.assessment_co_values[assessment][co] = (
                st.session_state.get(key, 0.0)
            )


# ==================================================
# SYNCHRONIZATION CALLBACKS
# ==================================================

def update_from_assessment(assessment, co):

    key = f"{assessment}_{co}_assessment_weight"

    value = st.session_state[key]

    st.session_state.assessment_co_values[
        assessment
    ][co] = value

    # Rebuild the editor from the updated assessment values.
    st.session_state.pop("co_weight_editor", None)


def update_from_table():

    editor_state = st.session_state.get(
        "co_weight_editor", {}
    )

    edited_rows = editor_state.get("edited_rows", {})

    for row_index, changes in edited_rows.items():

        # The TOTAL row (last row) is not an assessment.
        if int(row_index) >= len(ASSESSMENTS):
            continue

        assessment = ASSESSMENTS[int(row_index)]

        for co, value in changes.items():

            if co in co_list:

                value = float(value)

                st.session_state.assessment_co_values[
                    assessment
                ][co] = value

                widget_key = (
                    f"{assessment}_{co}_assessment_weight"
                )

                # Update the corresponding assessment input.
                st.session_state[widget_key] = value

    # Reset editor state so it displays the synchronized values.
    st.session_state.pop("co_weight_editor", None)


# ==================================================
# ASSESSMENT INPUT FUNCTION
# ==================================================

def assessment_input(assessment):

    with st.container(border=True):

        st.markdown(
            f'<div class="assessment-title">{assessment}</div>',
            unsafe_allow_html=True
        )

        if assessment in EXAM_ASSESSMENTS:

            in_col1, in_col2 = st.columns(2)

            with in_col1:
                conducted_marks = st.number_input(
                    f"{assessment} Exam Conducted For (Marks)",
                    min_value=0.0,
                    value=0.0,
                    step=0.5,
                    key=f"{assessment}_conducted_marks"
                )

            with in_col2:
                total_weight = st.number_input(
                    f"{assessment} Convert To (Marks)",
                    min_value=0.0,
                    value=0.0,
                    step=0.5,
                    key=f"{assessment}_total_weight"
                )

            if conducted_marks > 0 and total_weight > 0:
                st.caption(
                    f"{conducted_marks:g} marks converted to "
                    f"{total_weight:g} marks "
                    f"(factor = {total_weight:g} / {conducted_marks:g} "
                    f"= {total_weight / conducted_marks:.3f})"
                )

        else:

            # No exam and no conversion (e.g. attendance): one marks field.
            total_weight = st.number_input(
                f"{assessment} Total Marks",
                min_value=0.0,
                value=0.0,
                step=0.5,
                key=f"{assessment}_total_weight"
            )

            conducted_marks = total_weight   # factor = 1

        st.write("*Select Course Outcomes:*")

        checkbox_columns = st.columns(min(len(co_list), 5))

        selected_cos = []

        for i, co in enumerate(co_list):

            with checkbox_columns[i % len(checkbox_columns)]:

                selected = st.checkbox(
                    co,
                    key=f"{assessment}_{co}_selected"
                )

                if selected:
                    selected_cos.append(co)

        assessment_weights = {}

        if selected_cos:

            st.write("*Assessment CO Weightage:*")

            weight_columns = st.columns(min(len(selected_cos), 4))

            for i, co in enumerate(selected_cos):

                key = f"{assessment}_{co}_assessment_weight"

                # Initialize each selected assessment CO with 1.0
                # if it has not previously been assigned a value.
                if key not in st.session_state:
                    st.session_state[key] = 1.0
                    st.session_state.assessment_co_values[
                        assessment
                    ][co] = 1.0

                with weight_columns[i % len(weight_columns)]:

                    value = st.number_input(
                        f"{co} Assessment Weightage",
                        min_value=0.0,
                        step=0.5,
                        key=key,
                        on_change=update_from_assessment,
                        args=(assessment, co)
                    )

                    assessment_weights[co] = value

                    st.session_state.assessment_co_values[
                        assessment
                    ][co] = value

        return conducted_marks, total_weight, selected_cos, assessment_weights


# ==================================================
# ASSESSMENT COMPONENTS
# ==================================================

st.markdown(
    '<div class="section-heading">Assessment Components</div>',
    unsafe_allow_html=True
)

assessment_results = {}

for assessment in ASSESSMENTS:

    assessment_results[assessment] = assessment_input(
        assessment
    )


# ==================================================
# CO-WISE TOTAL ASSESSMENT WEIGHT TABLE
# ==================================================

st.markdown(
    '<div class="section-heading">'
    'CO-wise Total Assessment Weight'
    '</div>',
    unsafe_allow_html=True
)

st.caption(
    "Edit the assessment CO weightages directly in this table. "
    "Changes will also update the corresponding assessment inputs."
)

# Build the raw assessment-specific weightage table.

table_rows = []

for assessment in ASSESSMENTS:

    row = {"Assessment": assessment}

    for co in co_list:

        row[co] = st.session_state.assessment_co_values[
            assessment
        ].get(co, 0.0)

    table_rows.append(row)

table_df = pd.DataFrame(table_rows)

# Add the raw-weightage TOTAL row.
total_table_row = {"Assessment": "TOTAL"}

for co in co_list:

    total_table_row[co] = sum(
        st.session_state.assessment_co_values[
            assessment
        ].get(co, 0.0)
        for assessment in ASSESSMENTS
    )

table_df = pd.concat(
    [table_df, pd.DataFrame([total_table_row])],
    ignore_index=True
)

# Editable assessment rows. TOTAL row is ignored on edit.
disabled_columns = ["Assessment"]

edited_table = st.data_editor(
    table_df,
    key="co_weight_editor",
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    disabled=disabled_columns,
    column_config={
        "Assessment": st.column_config.TextColumn(
            "Assessment",
            disabled=True
        )
    },
    on_change=update_from_table
)


# ==================================================
# RE-CALCULATE RAW VALUES FROM SYNCHRONIZED STATE
# ==================================================

current_assessment_data = {}

for assessment in ASSESSMENTS:

    conducted_marks, total_weight, selected_cos, _ = (
        assessment_results[assessment]
    )

    current_weights = {
        co: st.session_state.assessment_co_values[assessment].get(co, 0.0)
        for co in co_list
    }

    current_assessment_data[assessment] = {
        "conducted_marks": conducted_marks,
        "total_weight": total_weight,
        "selected_cos": selected_cos,
        "weights": current_weights
    }


# ==================================================
# ALLOCATION FUNCTION
# ==================================================

def calculate_allocation(
    conducted_marks,
    total_weight,
    selected_cos,
    assessment_weights
):
    """
    Returns two dicts:
      raw       -> CO marks on the conducted-marks scale (e.g. out of 20)
      converted -> CO marks on the weightage scale (e.g. out of 30)
    """

    raw = {co: 0.0 for co in co_list}
    converted = {co: 0.0 for co in co_list}

    if fixed_weightage_sum <= 0:
        return raw, converted

    # e.g. weightage 30 / conducted 20 = 1.5
    factor = (
        total_weight / conducted_marks
        if conducted_marks > 0 else 0.0
    )

    for co in selected_cos:

        raw[co] = (
            assessment_weights.get(co, 0.0)
            / fixed_weightage_sum
        ) * conducted_marks

        converted[co] = raw[co] * factor

    return raw, converted


# ==================================================
# CALCULATE ALL ASSESSMENT ALLOCATIONS
# ==================================================

raw_allocations = {}
allocations = {}   # converted values, used in the matrix

for assessment in ASSESSMENTS:

    d = current_assessment_data[assessment]

    raw_allocations[assessment], allocations[assessment] = (
        calculate_allocation(
            d["conducted_marks"],
            d["total_weight"],
            d["selected_cos"],
            d["weights"]
        )
    )


# ==================================================
# HELPER: BUILD SUMMARY MATRIX
# ==================================================

def build_matrix():

    rows = []

    for assessment in ASSESSMENTS:

        details = current_assessment_data[assessment]

        row = {
            "Assessment": assessment,
            "Assessment Marks": details["total_weight"]
        }

        for co in co_list:
            row[co] = allocations[assessment][co]

        row["TOTAL"] = sum(allocations[assessment].values())

        rows.append(row)

    total_row = {
        "Assessment": "TOTAL",
        "Assessment Marks": sum(
            current_assessment_data[a]["total_weight"]
            for a in ASSESSMENTS
        )
    }

    for co in co_list:
        total_row[co] = sum(allocations[a][co] for a in ASSESSMENTS)

    total_row["TOTAL"] = sum(total_row[co] for co in co_list)

    rows.append(total_row)

    df = pd.DataFrame(rows)

    numeric_cols = (
        ["Assessment Marks"] + co_list + ["TOTAL"]
    )

    df[numeric_cols] = df[numeric_cols].round(2)

    return df, total_row


# ==================================================
# LIVE CO-WISE ALLOCATION SUMMARY
# ==================================================

live_allocation_df, _ = build_matrix()


# ==================================================
# CALCULATE ALLOCATION BUTTON
# ==================================================

st.markdown("---")

calculate_button = st.button(
    "Calculate Allocation",
    use_container_width=True
)


# ==================================================
# FINAL SUMMARY MATRIX AND EXCEL REPORT
# ==================================================

if calculate_button:

    errors = []

    if fixed_weightage_sum <= 0:
        errors.append(
            "The sum of fixed CO weightages must be greater than zero."
        )

    for a in EXAM_ASSESSMENTS:

        d = current_assessment_data[a]

        if d["total_weight"] > 0 and d["conducted_marks"] <= 0:
            errors.append(
                f"{a}: enter the marks the exam was conducted for."
            )

        if d["conducted_marks"] > 0 and d["total_weight"] <= 0:
            errors.append(
                f"{a}: enter the marks it should be converted to."
            )

    if errors:

        for error in errors:
            st.error(error)

    else:

        # ------------------------------------------
        # FINAL MATRIX
        # ------------------------------------------

        st.markdown(
            '<div class="section-heading">'
            'Final CO Assessment Summary Matrix'
            '</div>',
            unsafe_allow_html=True
        )

        matrix_df, final_total_row = build_matrix()

        st.dataframe(
            matrix_df,
            use_container_width=True,
            hide_index=True
        )

        # ------------------------------------------
        # SUMMARY METRICS
        # ------------------------------------------

        metric1, metric2, metric3 = st.columns(3)

        with metric1:
            st.metric(
                "Total Assessment Marks",
                f"{final_total_row['Assessment Marks']:.2f}"
            )

        with metric2:
            st.metric(
                "Total CO Allocation",
                f"{final_total_row['TOTAL']:.2f}"
            )

        with metric3:
            st.metric(
                "Number of Course Outcomes",
                len(co_list)
            )

        # ------------------------------------------
        # EXCEL EXPORT
        # ------------------------------------------

        output = BytesIO()

        course_details_df = pd.DataFrame({
            "Department": [department],
            "Program Type": [program_type],
            "Program": [program],
            "Program Code": [course_code],
            "Number of COs": [number_of_cos]
        })

        fixed_weights_df = pd.DataFrame({
            "Course Outcome": co_list,
            "Fixed CO Weightage": [
                fixed_co_weights[co] for co in co_list
            ]
        })

        co_total_df = pd.DataFrame({
            "Course Outcome": co_list,
            "Fixed CO Weightage": [
                fixed_co_weights[co] for co in co_list
            ],
            "Total Assessment Allocation": [
                round(final_total_row[co], 2) for co in co_list
            ]
        })

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            # Main summary matrix
            matrix_df.to_excel(
                writer,
                sheet_name="CO Assessment Matrix",
                index=False
            )

            # Fixed CO weightages
            fixed_weights_df.to_excel(
                writer,
                sheet_name="CO Weightages",
                index=False
            )

            # Individual assessment weightage sheets
            for assessment in ASSESSMENTS:

                details = current_assessment_data[assessment]

                selected = details["selected_cos"]

                weightage_df = pd.DataFrame({
                    "Course Outcome": selected,
                    "Fixed CO Weightage": [
                        fixed_co_weights[co] for co in selected
                    ],
                    "Assessment CO Weightage": [
                        details["weights"][co] for co in selected
                    ],
                    "Marks (Conducted Scale)": [
                        round(raw_allocations[assessment][co], 2)
                        for co in selected
                    ],
                    "Converted Marks": [
                        round(allocations[assessment][co], 2)
                        for co in selected
                    ]
                })

                weightage_df.to_excel(
                    writer,
                    sheet_name=f"{assessment} CO Weightage",
                    index=False
                )

            # Course details
            course_details_df.to_excel(
                writer,
                sheet_name="Course Details",
                index=False
            )

            # CO-wise totals
            co_total_df.to_excel(
                writer,
                sheet_name="CO-wise Total",
                index=False
            )

            # Excel formatting
            for worksheet in writer.book.worksheets:

                worksheet.freeze_panes = "A2"

                for cell in worksheet[1]:

                    cell.font = Font(
                        bold=True,
                        color="FFFFFF"
                    )

                    cell.fill = PatternFill(
                        fill_type="solid",
                        fgColor="183D32"
                    )

                    cell.alignment = Alignment(
                        horizontal="center",
                        vertical="center"
                    )

                worksheet.row_dimensions[1].height = 25

                for column_cells in worksheet.columns:

                    max_length = max(
                        (
                            len(str(cell.value))
                            for cell in column_cells
                            if cell.value is not None
                        ),
                        default=0
                    )

                    worksheet.column_dimensions[
                        column_cells[0].column_letter
                    ].width = min(max_length + 4, 40)

        output.seek(0)

        # ------------------------------------------
        # DOWNLOAD BUTTON
        # ------------------------------------------

        st.markdown(
            '<div class="section-heading">Download Results</div>',
            unsafe_allow_html=True
        )

        st.download_button(
            label="Download Excel Report",
            data=output,
            file_name="CO_Weightage_Allocation.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )
