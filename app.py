
import streamlit as st
import pandas as pd
from io import BytesIO

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CO Assessment Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 CO Assessment Dashboard")
st.caption("CO Assessment Summary Matrix and Student Assessment Data")

# =========================================================
# RESET BUTTON
# =========================================================

if st.button("🔄 Reset Dashboard"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
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
        options=list(range(1, 9))
    )

st.divider()

# =========================================================
# COURSE OUTCOMES
# =========================================================

st.header("2. Course Outcomes (COs)")

co_count = st.number_input(
    "Number of Course Outcomes",
    min_value=1,
    max_value=15,
    value=4,
    step=1
)

co_names = [f"CO{i}" for i in range(1, int(co_count) + 1)]

st.subheader("CO-wise Weight Allocation")

st.write(
    "Enter the weight assigned to each CO. "
    "These weights determine how assessment weight is distributed "
    "among the COs covered by an assessment."
)

co_weight_default = pd.DataFrame({
    "CO": co_names,
    "Weight per CO": [0.0] * int(co_count)
})

co_weights_df = st.data_editor(
    co_weight_default,
    key=f"co_weights_{co_count}",
    hide_index=True,
    disabled=["CO"],
    column_config={
        "CO": st.column_config.TextColumn("Course Outcome"),
        "Weight per CO": st.column_config.NumberColumn(
            "Weight per CO",
            min_value=0.0,
            step=0.5,
            format="%.2f"
        )
    },
    width="stretch"
)

co_weights = dict(
    zip(
        co_weights_df["CO"],
        co_weights_df["Weight per CO"]
    )
)

total_co_weight = sum(co_weights.values())

total_course_weight = st.number_input(
    "Total Course Weight",
    min_value=0.0,
    value=0.0,
    step=1.0
)

st.divider()

# =========================================================
# CO ASSESSMENT SUMMARY MATRIX
# =========================================================

st.header("3. CO Assessment Summary Matrix")

st.write(
    "Enter the weight of each assessment and select the COs "
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

column_config = {
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
    column_config[co] = st.column_config.CheckboxColumn(
        co,
        help=f"Select if this assessment covers {co}"
    )

edited_assessment_df = st.data_editor(
    assessment_df,
    key=f"assessment_grid_{co_count}",
    hide_index=True,
    column_config=column_config,
    disabled=["Assessment"],
    width="stretch"
)

# =========================================================
# CALCULATE ASSESSMENT-CO DISTRIBUTION
# =========================================================

st.subheader("Calculated CO Assessment Summary")

summary_rows = []

for _, row in edited_assessment_df.iterrows():

    assessment = row["Assessment"]
    assessment_weight = float(row["Assessment Weight"])

    covered_cos = [
        co for co in co_names
        if bool(row[co])
    ]

    covered_weight = sum(
        co_weights[co] for co in covered_cos
    )

    allocation = {
        co: 0.0 for co in co_names
    }

    if covered_cos and covered_weight > 0:

        for co in covered_cos:

            allocation[co] = (
                co_weights[co] / covered_weight
            ) * assessment_weight

    summary_row = {
        "Assessment": assessment,
        "Assessment Weight": assessment_weight
    }

    for co in co_names:
        summary_row[co] = allocation[co]

    summary_row["TOTAL"] = sum(
        allocation.values()
    )

    summary_rows.append(summary_row)

summary_matrix = pd.DataFrame(summary_rows)

# Total row
total_row = {
    "Assessment": "TOTAL",
    "Assessment Weight": edited_assessment_df[
        "Assessment Weight"
    ].sum()
}

for co in co_names:
    total_row[co] = summary_matrix[co].sum()

total_row["TOTAL"] = summary_matrix["TOTAL"].sum()

summary_matrix = pd.concat(
    [summary_matrix, pd.DataFrame([total_row])],
    ignore_index=True
)

# CO-wise total row
co_total_row = {
    "Assessment": "CO-wise TOTAL",
    "Assessment Weight": None
}

for co in co_names:
    co_total_row[co] = summary_matrix.loc[
        summary_matrix["Assessment"] != "CO-wise TOTAL",
        co
    ].sum()

co_total_row["TOTAL"] = sum(
    co_total_row[co] for co in co_names
)

summary_matrix = pd.concat(
    [summary_matrix, pd.DataFrame([co_total_row])],
    ignore_index=True
)

st.dataframe(
    summary_matrix.round(2),
    hide_index=True,
    width="stretch"
)

# =========================================================
# CO WEIGHT IN CCA
# =========================================================

st.subheader("CO-wise Weight in CCA")

total_assessment_weight = float(
    edited_assessment_df["Assessment Weight"].sum()
)

cca_rows = []

for co in co_names:

    co_weight = co_weights[co]

    if total_course_weight > 0:
        cca_weight = (
            co_weight / total_course_weight
        ) * total_assessment_weight
    else:
        cca_weight = 0.0

    cca_rows.append({
        "CO": co,
        "Weight per CO": co_weight,
        "Total Course Weight": total_course_weight,
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

if total_co_weight == 0:
    st.warning(
        "Enter positive CO weights to calculate the assessment distribution."
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
        "Please select at least one CO with a positive CO weight for: "
        + ", ".join(invalid_assessments)
    )

st.divider()

# =========================================================
# STUDENT ASSESSMENT DATA
# =========================================================

st.header("4. Student Assessment Data")

st.write(
    "Enter student-wise marks for PA1, PA2, LE1 and LE2. "
    "Student names are not required."
)

student_count = st.number_input(
    "Number of Students",
    min_value=1,
    max_value=200,
    value=5,
    step=1
)

st.subheader("Maximum Marks")

max_marks = {}

max_cols = st.columns(4)

for i, assessment in enumerate(assessment_names):

    with max_cols[i]:
        max_marks[assessment] = st.number_input(
            f"{assessment} Maximum Marks",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key=f"max_marks_{assessment}"
        )

# Student marks grid
student_data = {
    "Student ID": [
        f"Student {i + 1}"
        for i in range(int(student_count))
    ]
}

for assessment in assessment_names:
    student_data[assessment] = [
        0.0 for _ in range(int(student_count))
    ]

student_df = pd.DataFrame(student_data)

student_column_config = {
    "Student ID": st.column_config.TextColumn(
        "Student ID",
        disabled=True
    )
}

for assessment in assessment_names:

    student_column_config[assessment] = (
        st.column_config.NumberColumn(
            assessment,
            min_value=0.0,
            step=0.5,
            format="%.2f"
        )
    )

edited_student_df = st.data_editor(
    student_df,
    key=f"student_marks_{student_count}",
    hide_index=True,
    column_config=student_column_config,
    disabled=["Student ID"],
    num_rows="fixed",
    width="stretch"
)

# Validate marks against maximum marks
for assessment in assessment_names:

    if max_marks[assessment] > 0:

        if (
            edited_student_df[assessment]
            > max_marks[assessment]
        ).any():

            st.error(
                f"Some student marks in {assessment} "
                "exceed the maximum marks."
            )

st.divider()

# =========================================================
# DOWNLOAD EXCEL REPORT
# =========================================================

st.header("5. Download Dashboard Report")

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

max_marks_df = pd.DataFrame({
    "Assessment": assessment_names,
    "Maximum Marks": [
        max_marks[a] for a in assessment_names
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
        sheet_name="CO Weights",
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
        sheet_name="CCA Weight",
        index=False
    )

    max_marks_df.to_excel(
        writer,
        sheet_name="Maximum Marks",
        index=False
    )

    edited_student_df.to_excel(
        writer,
        sheet_name="Student Marks",
        index=False
    )

st.download_button(
    label="📥 Download Excel Report",
    data=output.getvalue(),
    file_name="CO_Assessment_Dashboard.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success(
    "CO Assessment Summary Matrix and Student Assessment Data are ready."
)
