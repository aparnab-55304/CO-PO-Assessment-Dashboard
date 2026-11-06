import streamlit as st
import pandas as pd
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

from pathlib import Path

EXCEL_FILE = Path(__file__).parent / "Course Group.xlsx"
# The final matrix grand total is based on the sum of entered assessment weights.


# ==================================================
# CUSTOM CSS - FOREST GREEN + CHAMPAGNE
# ==================================================

st.markdown("""
<style>
.stApp {
    background-color: #F3F6F1;
}

.stApp p,
.stApp li,
.stApp label,
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stCaptionContainer"] {
    color: #171717 !important;
}

.dashboard-header {
    background: linear-gradient(120deg, #183D32, #285C49);
    padding: 30px 32px;
    border-radius: 12px;
    margin-bottom: 25px;
    border-bottom: 5px solid #C8B98A;
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
    color: #183D32 !important;
    font-size: 21px;
    font-weight: 750;
    margin-top: 22px;
    margin-bottom: 14px;
    border-left: 5px solid #C8B98A;
    padding-left: 12px;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF;
    border: 1px solid #DCE5DA;
    border-top: 4px solid #285C49;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 15px;
}

.assessment-title {
    color: #183D32 !important;
    font-size: 20px;
    font-weight: 750;
    margin-bottom: 10px;
}

.stTextInput input,
.stNumberInput input {
    color: #171717 !important;
    -webkit-text-fill-color: #171717 !important;
    background-color: #FFFFFF !important;
}

.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stCheckbox label {
    color: #171717 !important;
    font-weight: 600 !important;
}

.stSelectbox div[data-baseweb="select"],
.stSelectbox div[data-baseweb="select"] span {
    color: #171717 !important;
}

.stButton > button,
.stDownloadButton > button {
    background-color: #183D32 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 2px solid #C8B98A !important;
    border-radius: 8px;
    font-weight: 700 !important;
    padding: 9px 22px;
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
    color: #FFFFFF !important;
    border-color: #D8CBA5 !important;
}

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #DCE5DA;
    border-left: 4px solid #C8B98A;
    border-radius: 10px;
    padding: 15px;
}

[data-testid="stMetricLabel"] {
    color: #183D32 !important;
    font-weight: 700 !important;
}

[data-testid="stMetricValue"] {
    color: #183D32 !important;
    font-weight: 750 !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid #DCE5DA;
    border-radius: 8px;
}

[data-testid="stExpander"] summary {
    color: #183D32 !important;
    font-weight: 700 !important;
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
# COURSE OUTCOMES - FIXED CO WEIGHTAGES
# ==================================================

st.markdown(
    '<div class="section-heading">Course Outcome Details</div>',
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
    '<div class="section-heading">Assessment Components</div>',
    unsafe_allow_html=True
)

# PA1 and PA2 use individually entered CO allocations.
pa1_weight, pa1_selected_cos, pa1_assessment_weights = (
    pa_assessment_input("PA1", "pa1")
)

pa2_weight, pa2_selected_cos, pa2_assessment_weights = (
    pa_assessment_input("PA2", "pa2")
)

# LE1 and LM use the same CO-selection and assigned-weight inputs as PA1 and PA2.
le1_weight, le1_selected_cos, le1_assessment_weights = (
    pa_assessment_input("LE1", "le1")
)

lm_weight, lm_selected_cos, lm_assessment_weights = (
    pa_assessment_input("LM", "lm")
)


# Keep a common structure for the summary and Excel sheets.
all_assessments = [
    ("PA1", pa1_weight, pa1_selected_cos, pa1_assessment_weights),
    ("PA2", pa2_weight, pa2_selected_cos, pa2_assessment_weights),
    ("LE1", le1_weight, le1_selected_cos, le1_assessment_weights),
    ("LM", lm_weight, lm_selected_cos, lm_assessment_weights)
]


# ==================================================
# BUILD ALLOCATION MATRIX WITH FIXED ROW AND COLUMN TOTALS
# ==================================================

assessment_names = ["PA1", "PA2", "LE1", "LM"]

# The entered CO weights form the starting pattern for distributing
# the allocation. Unselected COs and COs with zero assigned weight
# remain unavailable for that assessment.
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

# Row targets equal the entered assessment totals exactly.
# Column targets are the fixed CO weightages converted proportionally
# to the sum of all assessment totals. Therefore, row totals, column
# totals and the grand total are all consistent.
assessment_total_sum = sum(
    float(total_weight) for _, total_weight, _, _ in all_assessments
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
        row_targets = pd.Series(
            {
                assessment: float(total_weight)
                for assessment, total_weight, _, _ in all_assessments
            }
        )

        column_targets = pd.Series(
            {
                co: (
                    float(co_weightages[co]) / fixed_co_weightage_total
                ) * assessment_total_sum
                for co in co_list
            }
        )

        # Check whether every positive row and column target has at
        # least one positive entered CO weight available for allocation.
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
            # Iterative proportional fitting (RAS method): repeatedly
            # adjust rows and columns until row totals equal the entered
            # assessment weights and column totals equal the converted
            # fixed CO weightages, while retaining the entered pattern.
            balanced = raw_matrix.astype(float).copy()

            # A zero target must have an entirely zero row/column.
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

                # Match row totals to assessment targets.
                current_rows = balanced.sum(axis=1)
                for assessment in assessment_names:
                    current = current_rows[assessment]
                    target = row_targets[assessment]
                    if target == 0:
                        balanced.loc[assessment, :] = 0.0
                    elif current > 0:
                        balanced.loc[assessment, :] *= target / current

                # Match column totals to fixed-CO targets.
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

# Store allocated values in a common dictionary.
allocations = {
    assessment: {
        co: float(allocation_matrix.loc[assessment, co])
        for co in co_list
    }
    for assessment in assessment_names
}


# ==================================================
# CO-WISE TOTAL ASSESSMENT WEIGHT - EDITABLE AND LINKED
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

# The editor callback runs before the app reruns, so it can safely update
# the number-input and checkbox values used in the assessment sections.
def sync_table_edits_to_assessment_inputs(editor_key, current_co_list):

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

            # Selecting a positive value in the table also selects that CO
            # in the corresponding assessment section above.
            if new_weight > 0:
                st.session_state[
                    f"{key_prefix}_{column_name}_checkbox"
                ] = True


editor_key = f"co_weight_editor_{len(co_list)}"

# Rebuild the editor from the current assessment inputs on every rerun.
# This keeps edits made in the table and edits made above synchronised.
st.session_state.pop(editor_key, None)

editable_rows = []

for assessment, entered_total, selected_cos, assessment_co_weights in all_assessments:

    row = {
        "Assessment": assessment,
        "Entered Assessment Weight": entered_total
    }

    for co in co_list:
        row[co] = float(assessment_co_weights.get(co, 0.0))

    row["TOTAL"] = sum(row[co] for co in co_list)
    editable_rows.append(row)

editable_total_row = {
    "Assessment": "TOTAL",
    "Entered Assessment Weight": sum(
        item[1] for item in all_assessments
    )
}

for co in co_list:
    editable_total_row[co] = sum(
        row[co] for row in editable_rows
    )

editable_total_row["TOTAL"] = sum(
    editable_total_row[co] for co in co_list
)

editable_live_df = pd.DataFrame(editable_rows + [editable_total_row])

column_config = {
    "Assessment": st.column_config.TextColumn(
        "Assessment",
        disabled=True
    ),
    "Entered Assessment Weight": st.column_config.NumberColumn(
        "Entered Assessment Weight",
        disabled=True,
        format="%.2f"
    ),
    "TOTAL": st.column_config.NumberColumn(
        "TOTAL",
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
    disabled=["Assessment", "Entered Assessment Weight", "TOTAL"],
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

    # Validate all four assessments because each requires
    # individually selected COs and assigned CO weights.
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

        # ------------------------------------------
        # BUILD FINAL MATRIX
        # ------------------------------------------

        matrix_rows = []

        for name in ["PA1", "PA2", "LE1", "LM"]:

            row = {"Assessment": name}

            for co in co_list:
                row[co] = allocation_matrix.loc[name, co]

            row["TOTAL"] = sum(
                allocation_matrix.loc[name, co]
                for co in co_list
            )

            matrix_rows.append(row)

        # ------------------------------------------
        # TOTAL ROW
        # ------------------------------------------

        total_row = {"Assessment": "TOTAL"}

        for co in co_list:
            total_row[co] = allocation_matrix[co].sum()

        total_row["TOTAL"] = sum(
            total_row[co] for co in co_list
        )

        matrix_rows.append(total_row)

        result_df = pd.DataFrame(matrix_rows)

        # ------------------------------------------
        # DISPLAY FINAL MATRIX
        # ------------------------------------------

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

        # ------------------------------------------
        # SUMMARY METRICS
        # ------------------------------------------

        metric1, metric2, metric3 = st.columns(3)

        with metric1:

            st.metric(
                "Total Assessment Allocation",
                f"{total_row['TOTAL']:.2f}"
            )

        with metric2:

            st.metric(
                "Total Fixed CO Weightage",
                f"{fixed_co_weightage_total:.2f}"
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

        course_details = pd.DataFrame({
            "Department": [department],
            "Program Type": [program_type],
            "Program": [program],
            "Program Code": [course_code],
            "Number of COs": [number_of_cos]
        })

        co_total_df = pd.DataFrame({
            "Course Outcome": co_list,

            "Fixed CO Weightage": [
                co_weightages[co] for co in co_list
            ],

            "Total Assessment Allocation": [
                total_row[co] for co in co_list
            ]
        })

        fixed_co_weightage_df = pd.DataFrame({
            "Course Outcome": co_list,

            "Fixed CO Weightage": [
                co_weightages[co] for co in co_list
            ]
        })

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            # Final allocation matrix
            result_df.round(2).to_excel(
                writer,
                sheet_name="CO Assessment Matrix",
                index=False
            )

            # Individual assessment sheets
            for name, total_weight, selected_cos, assessment_co_weights in all_assessments:

                weightage_df = pd.DataFrame({
                    "Course Outcome": selected_cos,

                    "Fixed CO Weightage": [
                        co_weightages[co] for co in selected_cos
                    ],

                    "Assessment CO Weightage": [
                        assessment_co_weights[co]
                        for co in selected_cos
                    ],

                    "Allocated Weight": [
                        allocations[name][co]
                        for co in selected_cos
                    ]
                })

                weightage_df.to_excel(
                    writer,
                    sheet_name=f"{name} CO Weightage",
                    index=False
                )

            fixed_co_weightage_df.to_excel(
                writer,
                sheet_name="CO Weightages",
                index=False
            )

            course_details.to_excel(
                writer,
                sheet_name="Course Details",
                index=False
            )

            co_total_df.to_excel(
                writer,
                sheet_name="CO-wise Total",
                index=False
            )

            # --------------------------------------
            # EXCEL FORMATTING
            # --------------------------------------

            from openpyxl.styles import (
                Font,
                PatternFill,
                Alignment
            )

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
