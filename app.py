
import streamlit as st
import pandas as pd
import io

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CO Assessment Summary Matrix",
    page_icon="📊",
    layout="wide"
)

st.title("CO Assessment Summary Matrix")

# =====================================================
# RESET
# =====================================================

if st.button("Reset"):
    st.rerun()

# =====================================================
# COURSE DETAILS
# =====================================================

st.header("Course Details")

col1, col2 = st.columns(2)

with col1:
    department = st.text_input("Department")
    course_name = st.text_input("Course Name")

with col2:
    course_code = st.text_input("Course Code")
    semester = st.text_input("Semester")

# =====================================================
# NUMBER OF COURSE OUTCOMES
# =====================================================

st.header("Course Outcomes")

num_cos = st.number_input(
    "Number of Course Outcomes",
    min_value=1,
    max_value=15,
    value=4,
    step=1
)

co_names = [f"CO{i+1}" for i in range(int(num_cos))]

# =====================================================
# CO WEIGHTS
# =====================================================

st.subheader("CO Weights")

co_weights = {}

cols = st.columns(int(num_cos))

for i, co in enumerate(co_names):
    with cols[i]:
        co_weights[co] = st.number_input(
            co,
            min_value=0.0,
            value=0.0,
            step=1.0,
            key=f"weight_{co}"
        )

# =====================================================
# PA ASSESSMENT INPUT
# =====================================================

st.header("PA Assessment Input")

pa_data = {}

for pa in ["PA1", "PA2"]:

    st.subheader(pa)

    assessment_weight = st.number_input(
        f"{pa} Total Weight",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key=f"{pa}_weight"
    )

    selected_cos = {}

    cols = st.columns(int(num_cos))

    for i, co in enumerate(co_names):
        with cols[i]:
            selected_cos[co] = st.checkbox(
                co,
                key=f"{pa}_{co}"
            )

    pa_data[pa] = {
        "Assessment Weight": assessment_weight,
        "Selected COs": selected_cos
    }

# =====================================================
# LEARNING EVALUATION INPUT
# =====================================================

st.header("Learning Evaluation")

le_data = {}

col1, col2 = st.columns(2)

with col1:
    le_data["LE1"] = st.number_input(
        "LE1 Total Weight",
        min_value=0.0,
        value=0.0,
        step=1.0
    )

with col2:
    le_data["LE2"] = st.number_input(
        "LE2 Total Weight",
        min_value=0.0,
        value=0.0,
        step=1.0
    )

# =====================================================
# CALCULATE PA CO ALLOCATIONS
# =====================================================

pa_summary = {}

for pa in ["PA1", "PA2"]:

    assessment_weight = pa_data[pa]["Assessment Weight"]
    selected_cos = pa_data[pa]["Selected COs"]

    denominator = sum(
        co_weights[co]
        for co in co_names
        if selected_cos[co]
    )

    allocations = {}

    for co in co_names:

        if selected_cos[co] and denominator > 0:
            allocations[co] = (
                assessment_weight * co_weights[co] / denominator
            )
        else:
            allocations[co] = 0.0

    pa_summary[pa] = allocations

# =====================================================
# CO-WISE TOTAL ASSESSMENT WEIGHT
# =====================================================

st.header("CO-wise Total Assessment Weight")

co_total_data = {}

for co in co_names:
    co_total_data[co] = (
        pa_summary["PA1"][co] +
        pa_summary["PA2"][co]
    )

co_total_df = pd.DataFrame(
    [co_total_data],
    index=["Total Assessment Weight"]
)

st.dataframe(
    co_total_df.round(2),
    use_container_width=True
)

# =====================================================
# CO ASSESSMENT SUMMARY MATRIX
# =====================================================

st.header("CO Assessment Summary Matrix")

matrix_rows = []

# PA1 and PA2

for pa in ["PA1", "PA2"]:

    row = {
        "Assessment": pa,
        "Assessment Weight": pa_data[pa]["Assessment Weight"]
    }

    for co in co_names:
        row[co] = pa_summary[pa][co]

    row["TOTAL"] = sum(pa_summary[pa].values())

    matrix_rows.append(row)

# LE1 and LE2

for le in ["LE1", "LE2"]:

    row = {
        "Assessment": le,
        "Assessment Weight": le_data[le]
    }

    for co in co_names:
        row[co] = "—"

    row["TOTAL"] = le_data[le]

    matrix_rows.append(row)

# =====================================================
# TOTAL ROW
# =====================================================

total_row = {
    "Assessment": "TOTAL",
    "Assessment Weight": (
        pa_data["PA1"]["Assessment Weight"] +
        pa_data["PA2"]["Assessment Weight"] +
        le_data["LE1"] +
        le_data["LE2"]
    )
}

for co in co_names:
    total_row[co] = co_total_data[co]

total_row["TOTAL"] = (
    pa_data["PA1"]["Assessment Weight"] +
    pa_data["PA2"]["Assessment Weight"] +
    le_data["LE1"] +
    le_data["LE2"]
)

matrix_rows.append(total_row)

summary_matrix = pd.DataFrame(matrix_rows)

st.dataframe(
    summary_matrix.round(2),
    use_container_width=True,
    hide_index=True
)

# =====================================================
# EXCEL DOWNLOAD
# =====================================================

st.header("Download")

output = io.BytesIO()

course_details = pd.DataFrame({
    "Field": [
        "Department",
        "Course Name",
        "Course Code",
        "Semester"
    ],
    "Value": [
        department,
        course_name,
        course_code,
        semester
    ]
})

co_weights_df = pd.DataFrame({
    "Course Outcome": co_names,
    "Assigned Weight": [co_weights[co] for co in co_names]
})

pa_input_rows = []

for pa in ["PA1", "PA2"]:

    row = {
        "Assessment": pa,
        "Assessment Weight": pa_data[pa]["Assessment Weight"]
    }

    for co in co_names:
        row[co] = int(pa_data[pa]["Selected COs"][co])

    pa_input_rows.append(row)

pa_input_df = pd.DataFrame(pa_input_rows)

le_input_df = pd.DataFrame({
    "Assessment": ["LE1", "LE2"],
    "Total Weight": [
        le_data["LE1"],
        le_data["LE2"]
    ]
})

with pd.ExcelWriter(output, engine="openpyxl") as writer:

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

    pa_input_df.to_excel(
        writer,
        sheet_name="PA Input",
        index=False
    )

    le_input_df.to_excel(
        writer,
        sheet_name="LE Input",
        index=False
    )

    co_total_df.to_excel(
        writer,
        sheet_name="CO-wise Total"
    )

    summary_matrix.to_excel(
        writer,
        sheet_name="CO Summary Matrix",
        index=False
    )

st.download_button(
    label="Download Excel File",
    data=output.getvalue(),
    file_name="CO_Assessment_Summary_Matrix.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
