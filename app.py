
import streamlit as st
import pandas as pd
from io import BytesIO

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CO Assessment Summary Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("CO Assessment Summary Dashboard")
st.caption("Automated CO Assessment Weight Allocation")

# =====================================================
# RESET
# =====================================================

if st.button("Reset Dashboard"):
    st.session_state.clear()
    st.rerun()

# =====================================================
# COURSE DETAILS
# =====================================================

st.header("1. Course Details")

col1, col2 = st.columns(2)

with col1:
    department = st.text_input("Department")
    course_name = st.text_input("Course Name")

with col2:
    course_code = st.text_input("Course Code")
    semester = st.selectbox("Semester", range(1, 9))

st.divider()

# =====================================================
# COURSE OUTCOMES
# =====================================================

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

# =====================================================
# TEACHER ASSIGNED CO WEIGHTS
# =====================================================

st.subheader("Teacher-Assigned CO Weights")

st.write(
    "Enter the weight assigned by the teacher to each CO. "
    "These values are used in the assessment allocation formula."
)

co_weight_input = pd.DataFrame({
    "CO": co_names,
    "Assigned CO Weight": [0.0] * int(co_count)
})

edited_co_weights = st.data_editor(
    co_weight_input,
    key=f"co_weights_{co_count}",
    hide_index=True,
    disabled=["CO"],
    num_rows="fixed",
    column_config={
        "CO": st.column_config.TextColumn(
            "Course Outcome",
            disabled=True
        ),
        "Assigned CO Weight": st.column_config.NumberColumn(
            "Assigned CO Weight",
            min_value=0.0,
            step=0.5,
            format="%.2f"
        )
    },
    width="stretch"
)

co_weights = {
    row["CO"]: float(row["Assigned CO Weight"])
    for _, row in edited_co_weights.iterrows()
}

st.divider()

# =====================================================
# ASSESSMENT INPUT MATRIX
# =====================================================

st.header("3. Assessment Input Matrix")

st.write(
    "Enter the total weight of each assessment and tick "
    "the COs covered by that assessment."
)

assessment_names = ["PA1", "PA2", "LE1", "LE2"]

input_rows = []

for assessment in assessment_names:

    row = {
        "Assessment": assessment,
        "Weight": 0.0
    }

    for co in co_names:
        row[co] = False

    input_rows.append(row)

input_df = pd.DataFrame(input_rows)

input_config = {
    "Assessment": st.column_config.TextColumn(
        "Assessment",
        disabled=True
    ),
    "Weight": st.column_config.NumberColumn(
        "Weight (Wi)",
        min_value=0.0,
        step=0.5,
        format="%.2f"
    )
}

for co in co_names:
    input_config[co] = st.column_config.CheckboxColumn(
        co,
        help=f"Tick if {co} is covered in this assessment"
    )

edited_input = st.data_editor(
    input_df,
    key=f"assessment_input_{co_count}",
    hide_index=True,
    disabled=["Assessment"],
    num_rows="fixed",
    column_config=input_config,
    width="stretch"
)

st.divider()

# =====================================================
# CALCULATED CO ASSESSMENT SUMMARY MATRIX
# =====================================================

st.header("4. Calculated CO Assessment Summary")

st.write(
    "The matrix is calculated automatically using the "
    "teacher-assigned CO weights and assessment coverage."
)

st.latex(
    r"A_{ij} = "
    r"\frac{W_i \times C_{ij}\times CO_j}"
    r"{\sum_j C_{ij}\times CO_j}"
)

st.caption(
    "Wi = Assessment weight | Cij = CO coverage (1 or 0) | "
    "COj = Teacher-assigned CO weight"
)

# =====================================================
# CALCULATE MATRIX
# =====================================================

summary_rows = []

for _, row in edited_input.iterrows():

    assessment = row["Assessment"]
    assessment_weight = float(row["Weight"])

    # Denominator: sum of CO weights for selected COs
    denominator = sum(
        co_weights[co]
        for co in co_names
        if bool(row[co])
    )

    summary_row = {
        "Assessment": assessment,
        "Weight": assessment_weight
    }

    allocated_total = 0.0

    for co in co_names:

        cij = 1 if bool(row[co]) else 0
        coj = co_weights[co]

        if denominator > 0:
            aij = (
                assessment_weight * cij * coj
            ) / denominator
        else:
            aij = 0.0

        summary_row[co] = aij
        allocated_total += aij

    summary_row["TOTAL"] = allocated_total

    summary_rows.append(summary_row)

summary_matrix = pd.DataFrame(summary_rows)

# =====================================================
# ADD TOTAL ROW
# =====================================================

total_row = {
    "Assessment": "TOTAL",
    "Weight": summary_matrix["Weight"].sum()
}

for co in co_names:
    total_row[co] = summary_matrix[co].sum()

total_row["TOTAL"] = summary_matrix["TOTAL"].sum()

summary_matrix = pd.concat(
    [
        summary_matrix,
        pd.DataFrame([total_row])
    ],
    ignore_index=True
)

# =====================================================
# DISPLAY GRID
# =====================================================

display_columns = (
    ["Assessment", "Weight"]
    + co_names
    + ["TOTAL"]
)

summary_matrix = summary_matrix[display_columns]

st.dataframe(
    summary_matrix.round(2),
    hide_index=True,
    width="stretch"
)

# =====================================================
# VALIDATION
# =====================================================

st.subheader("5. Validation")

for _, row in edited_input.iterrows():

    assessment = row["Assessment"]
    assessment_weight = float(row["Weight"])

    selected_cos = [
        co for co in co_names
        if bool(row[co])
    ]

    denominator = sum(
        co_weights[co] for co in selected_cos
    )

    if assessment_weight > 0 and not selected_cos:

        st.warning(
            f"{assessment}: Select at least one CO."
        )

    elif assessment_weight > 0 and denominator == 0:

        st.warning(
            f"{assessment}: Selected COs have zero assigned weight."
        )

    elif assessment_weight > 0:

        st.success(
            f"{assessment}: CO allocation calculated successfully."
        )

# =====================================================
# DOWNLOAD EXCEL REPORT
# =====================================================

st.divider()

st.header("6. Download Summary Matrix")

course_details = pd.DataFrame({
    "Field": [
        "Department",
        "Course Name",
        "Course Code",
        "Semester",
        "Number of COs"
    ],
    "Value": [
        department,
        course_name,
        course_code,
        semester,
        co_count
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

    edited_co_weights.to_excel(
        writer,
        sheet_name="CO Weights",
        index=False
    )

    edited_input.to_excel(
        writer,
        sheet_name="Assessment Input",
        index=False
    )

    summary_matrix.to_excel(
        writer,
        sheet_name="Calculated CO Summary",
        index=False
    )

st.download_button(
    label="Download CO Assessment Summary",
    data=output.getvalue(),
    file_name="CO_Assessment_Summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success("CO Assessment Summary Matrix is ready.")
