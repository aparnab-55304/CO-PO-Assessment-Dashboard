
import requests
import streamlit as st
import pandas as pd

from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side
)
from openpyxl.utils import get_column_letter
from io import BytesIO
from pathlib import Path


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="CO Weightage Allocation Dashboard",
    page_icon="📊",
    layout="wide"
)

EXCEL_FILE = Path(__file__).parent / "Course Group.xlsx"


# ==================================================
# GOOGLE SHEETS FUNCTIONS
# ==================================================

def get_semester_from_course_code(course_code):

    code = str(course_code).strip()

    if not code or not code[-1].isdigit():
        raise ValueError("Unable to identify semester from course code.")

    semester_number = int(code[-1])

    if semester_number == 0:
        raise ValueError("Invalid semester number in course code.")

    return f"Semester {semester_number}"


def upload_to_google_sheets(
    department,
    program,
    course_code,
    result_df
):

    try:

        url = st.secrets["apps_script_url"]
        secret = st.secrets["app_secret"]

        semester = get_semester_from_course_code(course_code)

        allocation_rows = []

        for _, row in result_df.iterrows():

            assessment = str(row["Assessment"])

            allocation_row = [
                str(course_code),
                str(department),
                str(program),
                semester,
                assessment
            ]

            for i in range(1, 6):

                co = f"CO{i}"

                allocation_row.append(
                    round(float(row[co]), 2)
                    if co in result_df.columns else 0.0
                )

            allocation_row.append(
                round(float(row["TOTAL"]), 2)
                if "TOTAL" in result_df.columns else 0.0
            )

            allocation_rows.append(allocation_row)

        response = requests.post(
            url,
            json={
                "token": secret,
                "department": str(department).strip(),
                "course_code": str(course_code).strip(),
                "course_name": str(program).strip(),
                "semester": semester,
                "allocation_rows": allocation_rows
            },
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        if result.get("status") == "success":

            st.success("Course saved successfully!")
            return True

        st.error(
            f"Google Sheets error: {result.get('message')}"
        )

        return False

    except Exception as e:

        st.error(f"Google Sheets upload failed: {e}")
        return False


def get_department_courses_from_google_sheets(department):

    try:

        url = st.secrets["apps_script_url"]
        secret = st.secrets["app_secret"]

        response = requests.get(
            url,
            params={
                "department": str(department).strip(),
                "token": secret
            },
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        if result.get("status") == "success":

            return result.get("courses", [])

        st.error(
            f"Could not retrieve courses: {result.get('message')}"
        )

        return []

    except Exception as e:

        st.error(f"Could not retrieve saved courses: {e}")
        return []


# ==================================================
# CUSTOM CSS
# ==================================================

st.markdown("""
<style>

.stApp {
    background-color: #F5F2EC;
}

.stApp p,
.stApp li,
.stApp label,
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stCaptionContainer"] {
    color: #29323A !important;
}

.dashboard-header {
    background: linear-gradient(120deg, #26364A, #52677D);
    padding: 30px 32px;
    border-radius: 12px;
    margin-bottom: 25px;
    border-bottom: 5px solid #C6A77D;
}

.dashboard-header h1,
.dashboard-header .dashboard-subtitle {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

.dashboard-header h1 {
    font-size: 30px;
    font-weight: 750;
    margin: 0;
}

.dashboard-header .dashboard-subtitle {
    font-size: 15px !important;
    font-weight: 700 !important;
    margin-top: 8px;
    margin-bottom: 0;
    opacity: 1 !important;
}

.section-heading {
    color: #26364A !important;
    font-size: 21px;
    font-weight: 750;
    margin-top: 22px;
    margin-bottom: 14px;
    border-left: 5px solid #C6A77D;
    padding-left: 12px;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF;
    border: 1px solid #E3DDD2;
    border-top: 4px solid #52677D;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 15px;
}

.assessment-title {
    color: #26364A !important;
    font-size: 20px;
    font-weight: 750;
    margin-bottom: 10px;
}

.stTextInput input,
.stNumberInput input {
    color: #29323A !important;
    -webkit-text-fill-color: #29323A !important;
    background-color: #FFFFFF !important;
}

.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stCheckbox label {
    color: #29323A !important;
    font-weight: 600 !important;
}

.stSelectbox div[data-baseweb="select"],
.stSelectbox div[data-baseweb="select"] span {
    color: #29323A !important;
}

.stButton > button,
.stDownloadButton > button {
    background-color: #26364A !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 2px solid #C6A77D !important;
    border-radius: 8px;
    font-weight: 700 !important;
    padding: 9px 22px;
    transition: 0.3s ease;
}

.stButton > button *,
.stDownloadButton > button * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 700 !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background-color: #52677D !important;
    color: #FFFFFF !important;
    border-color: #C6A77D !important;
}

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #E3DDD2;
    border-left: 4px solid #C6A77D;
    border-radius: 10px;
    padding: 15px;
}

[data-testid="stMetricLabel"] {
    color: #26364A !important;
    font-weight: 700 !important;
}

[data-testid="stMetricValue"] {
    color: #26364A !important;
    font-weight: 750 !important;
}

[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    border: 1px solid #E3DDD2;
    border-radius: 8px;
}

[data-testid="stExpander"] summary {
    color: #26364A !important;
    font-weight: 700 !important;
}

.dashboard-department {
    color: #E8DCC9 !important;
    font-size: 14px;
    font-weight: 600;
    margin-top: 12px;
    margin-bottom: 0;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# DASHBOARD HEADER
# ==================================================

st.markdown("""
<div class="dashboard-header">
    <h1>CO Weightage Allocation Dashboard</h1>
    <div class="dashboard-subtitle">
        Course Outcome Assessment Weightage Management System
    </div>
    <div class="dashboard-department">
        Developed by MIMAMSA | Department of Statistics
    </div>
</div>
""", unsafe_allow_html=True)


# ==================================================
# LOAD COURSE DETAILS FROM EXCEL
# ==================================================

@st.cache_data
def load_course_data():

    df = pd.read_excel(EXCEL_FILE, header=1)

    df.columns = [
        " ".join(
            str(col).replace("\u00a0", " ").replace("\n", " ").split()
        ).strip()
        for col in df.columns
    ]

    department_aliases = {
        "Handling Department": "Department",
        "Departmen": "Department"
    }

    df.rename(columns=department_aliases, inplace=True)

    required_columns = [
        "Department",
        "Program Type",
        "Program",
        "Program Code"
    ]

    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing Excel columns: " + ", ".join(missing_columns)
        )

    df = df[required_columns].copy()

    for col in required_columns:
        df[col] = df[col].astype("string").str.strip()

    df = df.dropna(subset=required_columns)

    for col in required_columns:
        df = df[df[col] != ""]

    return df.drop_duplicates().reset_index(drop=True)


try:

    course_data = load_course_data()

except FileNotFoundError:

    st.error(
        "Course Group.xlsx was not found. "
        "Keep it in the same folder as app.py."
    )

    st.stop()

except PermissionError:

    st.error(
        "Unable to access Course Group.xlsx. "
        "Close the Excel file if it is open."
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
        departments,
        key="department"
    )

with col2:

    program_types = sorted(
        course_data.loc[
            course_data["Department"] == department,
            "Program Type"
        ].unique().tolist()
    )

    program_type = st.selectbox(
        "Program Type",
        program_types,
        key="program_type"
    )

filtered_programs = course_data[
    (course_data["Department"] == department) &
    (course_data["Program Type"] == program_type)
]

col3, col4 = st.columns(2)

with col3:

    programs = sorted(
        filtered_programs["Program"].unique().tolist()
    )

    program = st.selectbox(
        "Course Name",
        programs,
        key="program"
    )

with col4:

    matching_courses = filtered_programs[
        filtered_programs["Program"] == program
    ]

    course_codes = matching_courses["Program Code"].unique()

    course_code = (
        course_codes[0] if len(course_codes) > 0 else ""
    )

    st.text_input(
        "Course Code",
        value=str(course_code),
        disabled=True
    )


# ==================================================
# COURSE OUTCOMES
# ==================================================

st.markdown(
    '<div class="section-heading">Course Outcome Details</div>',
    unsafe_allow_html=True
)

number_of_cos = st.number_input(
    "Number of Course Outcomes",
    min_value=1,
    max_value=5,
    value=4,
    step=1
)

co_list = [
    f"CO{i}" for i in range(1, int(number_of_cos) + 1)
]


# ==================================================
# FIXED CO WEIGHTS
# ==================================================

st.markdown(
    '<div class="section-heading">CO Weight Details</div>',
    unsafe_allow_html=True
)

co_weight_columns = st.columns(min(len(co_list), 4))

co_weightages = {}

for i, co in enumerate(co_list):

    with co_weight_columns[i % len(co_weight_columns)]:

        co_weightages[co] = st.number_input(
            f"{co} Weight",
            min_value=0.0,
            value=1.0,
            step=0.5,
            key=f"fixed_{co}_weightage"
        )

fixed_co_weightage_total = sum(co_weightages.values())


# ==================================================
# PA ASSESSMENT INPUT FUNCTION
# ==================================================

def pa_assessment_input(assessment_name, key_prefix):

    with st.container(border=True):

        st.markdown(
            f'<div class="assessment-title">{assessment_name}</div>',
            unsafe_allow_html=True
        )

        total_weight = st.number_input(
            f"{assessment_name} Total Weight",
            min_value=0.0,
            value=0.0,
            step=0.5,
            key=f"{key_prefix}_total_weight"
        )

        st.markdown(
            f"*Enter the CO allocation weights for {assessment_name}*"
        )

        checkbox_columns = st.columns(min(len(co_list), 5))

        selected_cos = []
        assessment_co_weights = {}

        for i, co in enumerate(co_list):

            with checkbox_columns[i % len(checkbox_columns)]:

                selected = st.checkbox(
                    co,
                    key=f"{key_prefix}_{co}_checkbox"
                )

                if selected:
                    selected_cos.append(co)

        if selected_cos:

            weight_columns = st.columns(min(len(selected_cos), 4))

            for i, co in enumerate(selected_cos):

                with weight_columns[i % len(weight_columns)]:

                    assessment_co_weights[co] = st.number_input(
                        f"{co} Assigned Weight",
                        min_value=0.0,
                        value=0.0,
                        step=0.5,
                        key=f"{key_prefix}_{co}_assessment_weight"
                    )

        else:

            st.caption("No Course Outcomes selected.")

    return total_weight, selected_cos, assessment_co_weights


# ==================================================
# ASSESSMENT COMPONENTS
# ==================================================

st.markdown(
    '<div class="section-heading">Assessment Configuration</div>',
    unsafe_allow_html=True
)

assessment_col1, assessment_col2, assessment_col3, assessment_col4 = (
    st.columns(4, gap="small")
)

with assessment_col1:

    pa1_weight, pa1_selected_cos, pa1_assessment_weights = (
        pa_assessment_input("PA1", "pa1")
    )

with assessment_col2:

    pa2_weight, pa2_selected_cos, pa2_assessment_weights = (
        pa_assessment_input("PA2", "pa2")
    )

with assessment_col3:

    le1_weight, le1_selected_cos, le1_assessment_weights = (
        pa_assessment_input("LE1", "le1")
    )

with assessment_col4:

    lm_weight, lm_selected_cos, lm_assessment_weights = (
        pa_assessment_input("LM", "lm")
    )

all_assessments = [
    ("PA1", pa1_weight, pa1_selected_cos, pa1_assessment_weights),
    ("PA2", pa2_weight, pa2_selected_cos, pa2_assessment_weights),
    ("LE1", le1_weight, le1_selected_cos, le1_assessment_weights),
    ("LM", lm_weight, lm_selected_cos, lm_assessment_weights)
]


# ==================================================
# BUILD ALLOCATION MATRIX
# ==================================================

assessment_names = ["PA1", "PA2", "LE1", "LM"]

raw_matrix = pd.DataFrame(
    0.0,
    index=assessment_names,
    columns=co_list
)

for assessment, total_weight, selected_cos, assessment_co_weights in all_assessments:

    for co in selected_cos:

        raw_matrix.loc[assessment, co] = max(
            0.0,
            float(assessment_co_weights.get(co, 0.0))
        )

assessment_total_sum = sum(
    float(total_weight)
    for _, total_weight, _, _ in all_assessments
)

fixed_co_weightage_total = sum(
    float(co_weightages[co]) for co in co_list
)

allocation_matrix = pd.DataFrame(
    0.0,
    index=assessment_names,
    columns=co_list
)

balance_error = None

if assessment_total_sum > 0:

    if fixed_co_weightage_total <= 0:

        balance_error = (
            "The total fixed CO weightage must be greater than zero "
            "when the assessment total is greater than zero."
        )

    else:

        row_targets = pd.Series({
            assessment: float(total_weight)
            for assessment, total_weight, _, _ in all_assessments
        })

        column_targets = pd.Series({
            co: (
                float(co_weightages[co]) / fixed_co_weightage_total
            ) * assessment_total_sum
            for co in co_list
        })

        for assessment in assessment_names:

            if (
                row_targets[assessment] > 0
                and raw_matrix.loc[assessment].sum() <= 0
            ):

                balance_error = (
                    f"{assessment}: Enter a positive assigned weight "
                    "for at least one selected CO."
                )

                break

        if balance_error is None:

            for co in co_list:

                if (
                    column_targets[co] > 0
                    and raw_matrix[co].sum() <= 0
                ):

                    balance_error = (
                        f"{co} has a positive fixed CO weightage, but "
                        "no assessment has a positive assigned weight "
                        "for this CO. Select that CO and enter a positive "
                        "assigned weight in at least one assessment."
                    )

                    break

        if balance_error is None:

            balanced = raw_matrix.astype(float).copy()

            for assessment in assessment_names:

                if row_targets[assessment] == 0:
                    balanced.loc[assessment, :] = 0.0

            for co in co_list:

                if column_targets[co] == 0:
                    balanced.loc[:, co] = 0.0

            converged = False
            tolerance = 1e-9
            max_iterations = 20000

            for _ in range(max_iterations):

                current_rows = balanced.sum(axis=1)

                for assessment in assessment_names:

                    current = current_rows[assessment]
                    target = row_targets[assessment]

                    if target == 0:
                        balanced.loc[assessment, :] = 0.0

                    elif current > 0:
                        balanced.loc[assessment, :] *= target / current

                current_columns = balanced.sum(axis=0)

                for co in co_list:

                    current = current_columns[co]
                    target = column_targets[co]

                    if target == 0:
                        balanced.loc[:, co] = 0.0

                    elif current > 0:
                        balanced.loc[:, co] *= target / current

                row_difference = (
                    balanced.sum(axis=1) - row_targets
                ).abs().max()

                column_difference = (
                    balanced.sum(axis=0) - column_targets
                ).abs().max()

                if max(row_difference, column_difference) < tolerance:

                    converged = True
                    break

            if converged:

                allocation_matrix = balanced

            else:

                balance_error = (
                    "The selected CO combinations and assigned weights "
                    "cannot satisfy all row and column totals together. "
                    "Please review the CO selections and assigned weights "
                    "for PA1, PA2, LE1 and LM."
                )

allocations = {
    assessment: {
        co: float(allocation_matrix.loc[assessment, co])
        for co in co_list
    }
    for assessment in assessment_names
}


# ==================================================
# CO-WISE TOTAL ASSESSMENT WEIGHT
# ==================================================

st.markdown(
    '<div class="section-heading">'
    'CO-wise Total Assessment Weight'
    '</div>',
    unsafe_allow_html=True
)

st.caption(
    "You can edit the CO values directly in this table. "
    "The corresponding Assigned Weight above will update automatically. "
    "These are the entered CO weights. The final matrix will match each "
    "assessment total and each proportionally converted fixed CO total."
)

assessment_prefixes = {
    "PA1": "pa1",
    "PA2": "pa2",
    "LE1": "le1",
    "LM": "lm"
}


def sync_table_edits_to_assessment_inputs(
    editor_key,
    current_co_list
):

    editor_state = st.session_state.get(editor_key, {})
    edited_rows = editor_state.get("edited_rows", {})

    for row_index, changed_values in edited_rows.items():

        try:
            row_index = int(row_index)
        except (TypeError, ValueError):
            continue

        if row_index < 0 or row_index >= len(assessment_prefixes):
            continue

        assessment_name = list(assessment_prefixes.keys())[row_index]
        key_prefix = assessment_prefixes[assessment_name]

        for column_name, new_value in changed_values.items():

            if column_name not in current_co_list:
                continue

            try:
                new_weight = max(0.0, float(new_value))
            except (TypeError, ValueError):
                new_weight = 0.0

            st.session_state[
                f"{key_prefix}_{column_name}_assessment_weight"
            ] = new_weight

            if new_weight > 0:

                st.session_state[
                    f"{key_prefix}_{column_name}_checkbox"
                ] = True


editor_key = f"co_weight_editor_{len(co_list)}"

st.session_state.pop(editor_key, None)

editable_rows = []

for assessment, entered_total, selected_cos, assessment_co_weights in all_assessments:

    row = {
        "Assessment": assessment,
        "Entered Assessment Weight": entered_total
    }

    for co in co_list:
        row[co] = float(assessment_co_weights.get(co, 0.0))

    editable_rows.append(row)

editable_live_df = pd.DataFrame(editable_rows)

column_config = {
    "Assessment": st.column_config.TextColumn(
        "Assessment",
        disabled=True
    ),
    "Entered Assessment Weight": st.column_config.NumberColumn(
        "Entered Assessment Weight",
        disabled=True,
        format="%.2f"
    )
}

for co in co_list:

    column_config[co] = st.column_config.NumberColumn(
        co,
        min_value=0.0,
        step=0.5,
        format="%.2f"
    )

st.data_editor(
    editable_live_df,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    disabled=["Assessment", "Entered Assessment Weight"],
    column_config=column_config,
    key=editor_key,
    on_change=sync_table_edits_to_assessment_inputs,
    args=(editor_key, co_list)
)


# ==================================================
# CALCULATE ALLOCATION BUTTON
# ==================================================

st.markdown("---")

calculate_button = st.button(
    "Calculate Allocation",
    use_container_width=True
)


# ==================================================
# FINAL MATRIX AND EXCEL EXPORT
# ==================================================

if calculate_button:

    errors = []

    for name, total_weight, selected_cos, assessment_co_weights in all_assessments:

        assigned_total = sum(
            assessment_co_weights.get(co, 0.0)
            for co in selected_cos
        )

        if total_weight > 0 and not selected_cos:

            errors.append(f"{name}: Select at least one CO.")

        elif total_weight > 0 and assigned_total <= 0:

            errors.append(
                f"{name}: The assigned CO weights must have "
                "a total greater than zero."
            )

    if balance_error is not None:
        errors.append(balance_error)

    if errors:

        for error in errors:
            st.error(error)

    else:

        # BUILD FINAL MATRIX

        matrix_rows = []

        for name in assessment_names:

            row = {"Assessment": name}

            for co in co_list:
                row[co] = allocation_matrix.loc[name, co]

            row["TOTAL"] = sum(
                allocation_matrix.loc[name, co]
                for co in co_list
            )

            matrix_rows.append(row)

        # TOTAL ROW

        total_row = {"Assessment": "TOTAL"}

        for co in co_list:
            total_row[co] = allocation_matrix[co].sum()

        total_row["TOTAL"] = sum(
            total_row[co] for co in co_list
        )

        matrix_rows.append(total_row)

        result_df = pd.DataFrame(matrix_rows)

        # DISPLAY MATRIX

        st.markdown("---")

        st.markdown(
            '<div class="section-heading">'
            'CO Assessment Allocation Matrix'
            '</div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            result_df.round(2),
            use_container_width=True,
            hide_index=True
        )

        # SUMMARY METRICS

        metric1, metric2, metric3 = st.columns(3)

        with metric1:

            st.metric(
                "Total CCA",
                f"{total_row['TOTAL']:.2f}"
            )

        with metric2:

            st.metric(
                "Total Marks for ESE",
                f"{fixed_co_weightage_total:.2f}"
            )

        with metric3:

            st.metric(
                "Number of Course Outcomes",
                len(co_list)
            )

        # GOOGLE SHEETS UPLOAD

        upload_success = upload_to_google_sheets(
            department,
            program,
            course_code,
            result_df
        )

        # RETRIEVE SAVED COURSES

        if upload_success:

            saved_courses = get_department_courses_from_google_sheets(
                department
            )

            if not saved_courses:

                st.error(
                    "No saved course data found. "
                    "Please check the Google Sheets connection."
                )

            else:

                output = BytesIO()

                with pd.ExcelWriter(
                    output,
                    engine="openpyxl"
                ) as writer:

                    used_sheet_names = set()

                    for course in saved_courses:

                        values = course.get("values", [])

                        if len(values) < 5:
                            continue

                        course_department = str(
                            values[0][0]
                        ).replace("DEPARTMENT:", "").strip()

                        course_program = str(
                            course.get("name", "")
                        )

                        headers = values[3][1:7]

                        if len(headers) != 6:
                            continue

                        data_rows = []

                        for row in values[4:]:

                            if len(row) < 7:
                                continue

                            if not str(row[1]).strip():
                                continue

                            data_rows.append(row[1:7])

                        if not data_rows:
                            continue

                        course_df = pd.DataFrame(
                            data_rows,
                            columns=headers
                        ).round(2)

                        # WORKSHEET NAME

                        safe_name = "".join(
                            ch for ch in course_program
                            if ch not in '[]:*?/\\'
                        ).strip("'")

                        original_name = safe_name[:31] or "Course"
                        sheet_name = original_name
                        counter = 1

                        while sheet_name in used_sheet_names:

                            suffix = f"_{counter}"

                            sheet_name = (
                                original_name[:31 - len(suffix)]
                                + suffix
                            )

                            counter += 1

                        used_sheet_names.add(sheet_name)

                        # WRITE MATRIX

                        course_df.to_excel(
                            writer,
                            sheet_name=sheet_name,
                            index=False,
                            startrow=3
                        )

                        worksheet = writer.sheets[sheet_name]
                        last_column = course_df.shape[1]

                        # DEPARTMENT HEADING

                        worksheet.merge_cells(
                            start_row=1,
                            start_column=1,
                            end_row=1,
                            end_column=last_column
                        )

                        worksheet["A1"] = (
                            "DEPARTMENT: " + course_department
                        )

                        worksheet["A1"].font = Font(
                            bold=True,
                            size=16,
                            color="FFFFFF"
                        )

                        worksheet["A1"].fill = PatternFill(
                            fill_type="solid",
                            fgColor="34495E"
                        )

                        worksheet["A1"].alignment = Alignment(
                            horizontal="center",
                            vertical="center"
                        )

                        # COURSE HEADING

                        worksheet.merge_cells(
                            start_row=2,
                            start_column=1,
                            end_row=2,
                            end_column=last_column
                        )

                        worksheet["A2"] = (
                            "COURSE NAME: " + course_program
                        )

                        worksheet["A2"].font = Font(
                            bold=True,
                            size=13,
                            color="34495E"
                        )

                        worksheet["A2"].fill = PatternFill(
                            fill_type="solid",
                            fgColor="F3EBDD"
                        )

                        worksheet["A2"].alignment = Alignment(
                            horizontal="center",
                            vertical="center"
                        )

                        # COURSE CODE

                        worksheet.merge_cells(
                            start_row=3,
                            start_column=1,
                            end_row=3,
                            end_column=last_column
                        )

                        worksheet["A3"] = (
                            str(values[4][0])
                            if len(values) > 4 else ""
                        )

                        worksheet["A3"].font = Font(
                            bold=True,
                            size=11,
                            color="34495E"
                        )

                        worksheet["A3"].alignment = Alignment(
                            horizontal="center",
                            vertical="center"
                        )

                        # TABLE HEADER

                        for cell in worksheet[4]:

                            cell.font = Font(
                                bold=True,
                                color="FFFFFF"
                            )

                            cell.fill = PatternFill(
                                fill_type="solid",
                                fgColor="52677D"
                            )

                            cell.alignment = Alignment(
                                horizontal="center",
                                vertical="center"
                            )

                        # BORDERS AND ALIGNMENT

                        thin_side = Side(
                            style="thin",
                            color="C9D0D8"
                        )

                        thin_border = Border(
                            left=thin_side,
                            right=thin_side,
                            top=thin_side,
                            bottom=thin_side
                        )

                        for row in worksheet.iter_rows(
                            min_row=4,
                            max_row=worksheet.max_row,
                            min_col=1,
                            max_col=last_column
                        ):

                            for cell in row:

                                cell.alignment = Alignment(
                                    horizontal="center",
                                    vertical="center"
                                )

                                cell.border = thin_border

                        # COLUMN WIDTHS

                        for col_num in range(
                            1,
                            worksheet.max_column + 1
                        ):

                            max_length = 0

                            for row_num in range(
                                4,
                                worksheet.max_row + 1
                            ):

                                cell_value = worksheet.cell(
                                    row=row_num,
                                    column=col_num
                                ).value

                                if cell_value is not None:

                                    max_length = max(
                                        max_length,
                                        len(str(cell_value))
                                    )

                            column_letter = get_column_letter(col_num)

                            worksheet.column_dimensions[
                                column_letter
                            ].width = min(max_length + 4, 25)

                        worksheet.row_dimensions[1].height = 28
                        worksheet.row_dimensions[2].height = 24
                        worksheet.row_dimensions[3].height = 20

                        worksheet.freeze_panes = "A5"

                # DOWNLOAD EXCEL

                if used_sheet_names:

                    output.seek(0)

                    st.download_button(
                        label="Download Excel",
                        data=output.getvalue(),
                        file_name=(
                            str(department).replace("/", "-")
                            + "_CO_Assessment_Matrix.xlsx"
                        ),
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        ),
                        use_container_width=True
                    )

                else:

                    st.error(
                        "No valid course matrices were returned "
                        "from Google Sheets for Excel export."
                    )
