
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
st.caption("Automated Course Outcome Assessment Weight Summary")

# =====================================================
# RESET BUTTON
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
# TEACHER-ASSIGNED CO WEIGHTS
# =====================================================

st.subheader("Teacher-Assigned CO Weights")

st.write(
    "Enter the overall weight assigned by the teacher "
    "to each Course Outcome."
)

co_weight_df = pd.DataFrame({
    "CO": co_names,
    "Assigned CO Weight": [0.0] * int(co_count)
})

edited_co_weights = st.data_editor(
    co_weight_df,
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
    "Enter the weight assigned to each CO in the respective "
    "assessment. The total assessment weight will be calculated "
    "automatically."
)

assessment_names = ["PA1", "PA2", "LE1", "LE2"]

input_rows = []

for assessment in assessment_names:

    row = {"Assessment": assessment}

    for co in co_names:
        row[co] = 0.0

    input_rows.append(row)

input_df = pd.DataFrame(input_rows)

input_config = {
    "Assessment": st.column_config.TextColumn(
        "Assessment",
        disabled=True
    )
}

for co in co_names:
    input_config[co] = st.column_config.NumberColumn(
        f"{co} Weight",
        min_value=0.0,
        step=0.5,
        format="%.2f",
        help=f"Enter the weight assigned to {co} in this assessment."
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

# =====================================================
# AUTOMATIC ASSESSMENT WEIGHT CALCULATION
# =====================================================

assessment_totals = []

for _, row in edited_input.iterrows():

    total = sum(
        float(row[co])
        for co in co_names
    )

    assessment_totals.append(total)

edited_input["Total Assessment Weight"] = assessment_totals

# =====================================================
# CALCULATED CO ASSESSMENT SUMMARY MATRIX
# =====================================================

st.divider()

st.header("4. Calculated CO Assessment Summary")

st.write(
    "The summary matrix displays the CO-wise weights "
    "assigned in each assessment and the total weight."
)

summary_matrix = edited_input.copy()

# Add total row
total_row = {
    "Assessment": "TOTAL"
}

for co in co_names:
    total_row[co] = summary_matrix[co].sum()

total_row["Total Assessment Weight"] = (
    summary_matrix["Total Assessment Weight"].sum()
)

summary_matrix = pd.concat(
    [
        summary_matrix,
        pd.DataFrame([total_row])
    ],
    ignore_index=True
)

# Arrange columns
summary_columns = (
    ["Assessment"]
    + co_names
    + ["Total Assessment Weight"]
)

summary_matrix = summary_matrix[summary_columns]

st.dataframe(
    summary_matrix.round(2),
    hide_index=True,
    width="stretch"
)

# =====================================================
# CO-WISE TOTAL SUMMARY
# =====================================================

st.subheader("CO-wise Total Assessment Weight")

co_total_data = []

for co in co_names:

    co_total_data.append({
        "Course Outcome": co,
        "Total Assigned Weight": summary_matrix.loc[
            summary_matrix["Assessment"] != "TOTAL",
            co
        ].sum()
    })

co_total_df = pd.DataFrame(co_total_data)

st.dataframe(
    co_total_df.round(2),
    hide_index=True,
    width="stretch"
)

# =====================================================
# VALIDATION
# =====================================================

st.subheader("5. Assessment Weight Summary")

for _, row in edited_input.iterrows():

    assessment = row["Assessment"]
    total = float(row["Total Assessment Weight"])

    st.write(
        f"**{assessment} Total Weight:** {total:.2f}"
    )

# =====================================================
# EXCEL DOWNLOAD
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
        sheet_name="CO Summary Matrix",
        index=False
    )

    co_total_df.to_excel(
        writer,
        sheet_name="CO-wise Total",
        index=False
    )

st.download_button(
    label="Download CO Assessment Summary",
    data=output.getvalue(),
    file_name="CO_Assessment_Summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success("CO Assessment Summary Matrix is ready.")
