
import streamlit as st
import pandas as pd
from io import BytesIO

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CO Assessment Summary Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 CO Assessment Summary Dashboard")
st.caption("Automated CO-wise Assessment Weight Distribution")

# =========================================================
# RESET
# =========================================================

if st.button("🔄 Reset Dashboard"):
    st.session_state.clear()
    st.rerun()

# =========================================================
# COURSE DETAILS
# =========================================================

st.header("1. Course Details")

col1, col2 = st.columns(2)

with col1:
    department = st.text_input(
        "Department",
        placeholder="Enter Department"
    )

    course_name = st.text_input(
        "Course Name",
        placeholder="Enter Course Name"
    )

with col2:
    course_code = st.text_input(
        "Course Code",
        placeholder="Enter Course Code"
    )

    semester = st.selectbox(
        "Semester",
        list(range(1, 9))
    )

st.divider()

# =========================================================
# COURSE OUTCOMES
# =========================================================

st.header("2. Course Outcomes")

co_count = st.number_input(
    "Number of Course Outcomes",
    min_value=1,
    max_value=15,
    value=4,
    step=1
)

co_names = [
    f"CO{i}" for i in range(1, int(co_count) + 1)
]

# =========================================================
# TEACHER-ASSIGNED CO WEIGHTS
# =========================================================

st.subheader("2.1 Teacher-Assigned CO Weights")

st.write(
    "The teacher assigns the weight for each Course Outcome. "
    "These weights are used to distribute the assessment weight "
    "among the selected COs."
)

co_weight_data = pd.DataFrame({
    "Course Outcome": co_names,
    "Weight Assigned by Teacher": [0.0] * int(co_count)
})

co_weights_df = st.data_editor(
    co_weight_data,
    key=f"co_weight_editor_{co_count}",
    hide_index=True,
    disabled=["Course Outcome"],
    column_config={
        "Course Outcome": st.column_config.TextColumn(
            "Course Outcome"
        ),
        "Weight Assigned by Teacher": st.column_config.NumberColumn(
            "Weight Assigned by Teacher",
            min_value=0.0,
            step=0.5,
            format="%.2f"
        )
    },
    width="stretch"
)

co_weights = dict(
    zip(
        co_weights_df["Course Outcome"],
        co_weights_df["Weight Assigned by Teacher"]
    )
)

# Total course weight
total_course_weight = st.number_input(
    "Total Course Weight",
    min_value=0.0,
    value=30.0,
    step=1.0,
    help="Enter the total weight used for CCA calculation."
)

st.divider()

# =========================================================
# ASSESSMENT COVERAGE MATRIX
# =========================================================

st.header("3. CO Assessment Summary Matrix")

st.write(
    "Enter the weight of each assessment and tick the COs "
    "covered by that assessment."
)

assessment_names = ["PA1", "PA2", "LE1", "LE2"]

assessment_columns = (
    ["Assessment", "Assessment Weight"] + co_names
)

assessment_data = []

for assessment in assessment_names:

    row = {
        "Assessment": assessment,
        "Assessment Weight": 0.0
    }

    for co in co_names:
        row[co] = False

    assessment_data.append(row)

assessment_df = pd.DataFrame(
    assessment_data,
    columns=assessment_columns
)

assessment_config = {
    "Assessment": st.column_config.TextColumn(
        "Assessment",
        disabled=True
    ),
    "Assessment Weight": st.column_config.NumberColumn(
        "Assessment Weight",
        min_value=0.0,
        step=0.5,
        format="%.2f"
    )
}

for co in co_names:

    assessment_config[co] = st.column_config.CheckboxColumn(
        co,
        help=f"Tick if {co} is covered by this assessment."
    )

edited_assessment_df = st.data_editor(
    assessment_df,
    key=f"assessment_editor_{co_count}",
    hide_index=True,
    disabled=["Assessment"],
    column_config=assessment_config,
    width="stretch"
)

# =========================================================
# CALCULATE CO-WISE ASSESSMENT WEIGHTS
# =========================================================

st.subheader("3.1 Calculated CO Assessment Summary")

summary_rows = []

for _, row in edited_assessment_df.iterrows():

    assessment = row["Assessment"]
    assessment_weight = float(row["Assessment Weight"])

    covered_cos = [
        co for co in co_names
        if bool(row[co])
    ]

    total_covered_co_weight = sum(
        co_weights[co] for co in covered_cos
    )

    allocated_weights = {}

    for co in co_names:

        if (
            co in covered_cos
            and total_covered_co_weight > 0
        ):

            allocated_weights[co] = (
                co_weights[co] / total_covered_co_weight
            ) * assessment_weight

        else:
            allocated_weights[co] = 0.0

    summary_row = {
        "Assessment": assessment,
        "Assessment Weight": assessment_weight
    }

    for co in co_names:
        summary_row[
            f"{co} (Assigned: {co_weights[co]:g})"
        ] = allocated_weights[co]

    summary_row["TOTAL"] = sum(
        allocated_weights.values()
    )

    summary_rows.append(summary_row)

summary_matrix = pd.DataFrame(summary_rows)

# =========================================================
# TOTAL ROW
# =========================================================

total_row = {
    "Assessment": "TOTAL",
    "Assessment Weight": edited_assessment_df[
        "Assessment Weight"
    ].sum()
}

for co in co_names:

    col_name = f"{co} (Assigned: {co_weights[co]:g})"

    total_row[col_name] = summary_matrix[col_name].sum()

total_row["TOTAL"] = summary_matrix["TOTAL"].sum()

summary_matrix = pd.concat(
    [
        summary_matrix,
        pd.DataFrame([total_row])
    ],
    ignore_index=True
)

st.dataframe(
    summary_matrix.round(2),
    hide_index=True,
    width="stretch"
)

st.caption(
    "The number in each CO column heading represents the weight "
    "assigned to that CO by the teacher. The cell values represent "
    "the assessment weight allocated to that CO."
)

st.divider()

# =========================================================
# CO-WISE WEIGHT IN CCA
# =========================================================

st.header("4. CO-wise Weight in CCA")

total_assessment_weight = float(
    edited_assessment_df["Assessment Weight"].sum()
)

cca_rows = []

for co in co_names:

    assigned_weight = co_weights[co]

    if total_course_weight > 0:

        cca_weight = (
            assigned_weight / total_course_weight
        ) * total_assessment_weight

    else:
        cca_weight = 0.0

    cca_rows.append({
        "Course Outcome": co,
        "Weight Assigned by Teacher": assigned_weight,
        "Total Course Weight": total_course_weight,
        "Total Assessment Weight": total_assessment_weight,
        "Weight per CO in CCA": cca_weight
    })

cca_matrix = pd.DataFrame(cca_rows)

st.dataframe(
    cca_matrix.round(2),
    hide_index=True,
    width="stretch"
)

# =========================================================
# VALIDATION
# =========================================================

st.header("5. Validation")

if total_course_weight == 0:
    st.warning(
        "Total Course Weight is zero. CCA weights cannot be calculated."
    )

if sum(co_weights.values()) == 0:
    st.warning(
        "Please assign positive weights to the Course Outcomes."
    )

invalid_assessments = []

for _, row in edited_assessment_df.iterrows():

    if float(row["Assessment Weight"]) > 0:

        covered_cos = [
            co for co in co_names
            if bool(row[co])
        ]

        covered_weight = sum(
            co_weights[co] for co in covered_cos
        )

        if not covered_cos or covered_weight <= 0:
            invalid_assessments.append(row["Assessment"])

if invalid_assessments:

    st.warning(
        "Please select COs with positive assigned weights for: "
        + ", ".join(invalid_assessments)
    )

if (
    total_course_weight > 0
    and sum(co_weights.values()) > 0
    and not invalid_assessments
):
    st.success("CO assessment weight distribution is calculated.")

st.divider()

# =========================================================
# DOWNLOAD EXCEL REPORT
# =========================================================

st.header("6. Download Summary")

course_details = pd.DataFrame({
    "Field": [
        "Department",
        "Course Name",
        "Course Code",
        "Semester",
        "Number of COs",
        "Total Course Weight"
    ],
    "Value": [
        department,
        course_name,
        course_code,
        semester,
        co_count,
        total_course_weight
    ]
})

output = BytesIO()

with pd.ExcelWriter(
    output,
    engine="openpyxl"
) as writer:

    course_details.to_excel(
        writer,
        sheet_name="Course Details",
        index=False
    )

    co_weights_df.to_excel(
        writer,
        sheet_name="Teacher CO Weights",
        index=False
    )

    edited_assessment_df.to_excel(
        writer,
        sheet_name="Assessment Coverage",
        index=False
    )

    summary_matrix.to_excel(
        writer,
        sheet_name="CO Summary Matrix",
        index=False
    )

    cca_matrix.to_excel(
        writer,
        sheet_name="CO Weight in CCA",
        index=False
    )

st.download_button(
    label="📥 Download CO Summary Excel",
    data=output.getvalue(),
    file_name="CO_Assessment_Summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.caption(
    "CO Assessment Summary Dashboard"
)
