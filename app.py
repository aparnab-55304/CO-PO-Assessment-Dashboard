
import streamlit as st
import pandas as pd
import numpy as np

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="CO-PO Assessment Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 CO–PO Assessment Dashboard")
st.write("Automated Course Outcome and Programme Outcome Assessment")

st.divider()

# --------------------------------------------------
# DEFAULT SETTINGS FROM THE EXCEL WORKBOOK
# --------------------------------------------------

CO_NAMES = ["CO1", "CO2", "CO3", "CO4"]
PO_NAMES = ["PO1", "PO2", "PO3", "PO4", "PO5"]

# Fixed assessment weights (editable by teacher)
DEFAULT_ASSESSMENT_WEIGHTS = {
    "PA1": 3,
    "PA2": 4,
    "LE": 8,
    "LM": 5
}

# Fixed assessment coverage
coverage = pd.DataFrame(
    [
        [1, 1, 0, 0],
        [0, 0, 1, 1],
        [1, 1, 1, 1],
        [1, 1, 1, 1]
    ],
    index=["PA1", "PA2", "LE", "LM"],
    columns=CO_NAMES
)

# --------------------------------------------------
# 1. TEACHER INPUT: CO WEIGHTS
# --------------------------------------------------

st.header("1. Course Outcome (CO) Weights")

st.caption("Enter the weight assigned to each Course Outcome.")

co_cols = st.columns(4)

co_weights = {}

default_co_weights = [8, 8, 7, 7]

for i, co in enumerate(CO_NAMES):
    with co_cols[i]:
        co_weights[co] = st.number_input(
            co,
            min_value=0.0,
            max_value=100.0,
            value=float(default_co_weights[i]),
            step=1.0,
            key=f"weight_{co}"
        )

total_co_weight = sum(co_weights.values())

st.info(f"Total CO Weight: {total_co_weight:.2f}")

# --------------------------------------------------
# 2. TEACHER INPUT: PO WEIGHTS
# --------------------------------------------------

st.header("2. Programme Outcome (PO) Weights")

st.caption("Enter the weight assigned to each Programme Outcome.")

po_cols = st.columns(5)

po_weights = {}

default_po_weights = [8, 8, 7, 7, 6]

for i, po in enumerate(PO_NAMES):
    with po_cols[i]:
        po_weights[po] = st.number_input(
            po,
            min_value=0.0,
            max_value=100.0,
            value=float(default_po_weights[i]),
            step=1.0,
            key=f"weight_{po}"
        )

total_po_weight = sum(po_weights.values())

st.info(f"Total PO Weight: {total_po_weight:.2f}")

st.divider()

# --------------------------------------------------
# 3. ASSESSMENT WEIGHTS
# --------------------------------------------------

st.header("3. Assessment Weights")

st.caption(
    "Default values are taken from your Excel workbook. "
    "Change them if your course uses different weights."
)

assessment_weights = {}

assess_cols = st.columns(4)

for i, assessment in enumerate(DEFAULT_ASSESSMENT_WEIGHTS):
    with assess_cols[i]:
        assessment_weights[assessment] = st.number_input(
            assessment,
            min_value=0.0,
            value=float(DEFAULT_ASSESSMENT_WEIGHTS[assessment]),
            step=1.0,
            key=f"assessment_{assessment}"
        )

total_assessment_weight = sum(assessment_weights.values())

st.info(
    f"Total Assessment Weight: {total_assessment_weight:.2f}"
)

# --------------------------------------------------
# 4. AUTOMATIC ASSESSMENT-CO MATRIX
# --------------------------------------------------

st.header("4. Assessment–CO Matrix")

st.write("Fixed assessment coverage:")

st.dataframe(
    coverage,
    use_container_width=True
)

st.caption(
    "1 = Assessment covers the CO; 0 = Assessment does not cover the CO."
)

# Calculate allocation matrix
allocation = pd.DataFrame(
    0.0,
    index=coverage.index,
    columns=coverage.columns
)

for assessment in coverage.index:

    denominator = sum(
        coverage.loc[assessment, co] * co_weights[co]
        for co in CO_NAMES
    )

    if denominator > 0:
        for co in CO_NAMES:
            allocation.loc[assessment, co] = (
                assessment_weights[assessment]
                * coverage.loc[assessment, co]
                * co_weights[co]
                / denominator
            )

st.subheader("Automatically Calculated CO Allocation")

st.dataframe(
    allocation.round(3),
    use_container_width=True
)

co_allocation_totals = allocation.sum(axis=0)

st.subheader("Total Internal Marks Allocated to Each CO")

st.dataframe(
    pd.DataFrame({
        "CO": CO_NAMES,
        "Allocated Marks": [
            co_allocation_totals[co] for co in CO_NAMES
        ]
    }).round(3),
    use_container_width=True
)

st.divider()

# --------------------------------------------------
# 5. CO-PO MAPPING MATRIX
# --------------------------------------------------

st.header("5. CO–PO Mapping Matrix")

st.write(
    "Enter the relationship between each CO and PO. "
    "This is required to calculate PO attainment."
)

st.caption(
    "0 = No relationship, 1 = Low, 2 = Medium, 3 = High"
)

mapping_default = pd.DataFrame(
    [
        [3, 2, 1, 0, 0],
        [2, 3, 2, 1, 0],
        [1, 2, 3, 2, 1],
        [0, 1, 2, 3, 2]
    ],
    index=CO_NAMES,
    columns=PO_NAMES
)

mapping_input = mapping_default.copy()
mapping_input.index.name = "CO"

mapping_input = st.data_editor(
    mapping_input,
    use_container_width=True,
    key="co_po_mapping",
    column_config={
        po: st.column_config.NumberColumn(
            po,
            min_value=0,
            max_value=3,
            step=1
        )
        for po in PO_NAMES
    }
)

mapping = mapping_input.astype(float)

st.divider()

# --------------------------------------------------
# 6. STUDENT MARKS INPUT
# --------------------------------------------------

st.header("6. Student Assessment Marks")

st.write(
    "Enter each student's LE1 and LM1 marks as percentages "
    "(0 to 100)."
)

number_of_students = st.number_input(
    "Number of Students",
    min_value=1,
    max_value=200,
    value=5,
    step=1
)

student_data = pd.DataFrame({
    "Student": [
        f"Student {i+1}" for i in range(int(number_of_students))
    ],
    "LE1": [70.0] * int(number_of_students),
    "LM1": [75.0] * int(number_of_students)
})

student_input = st.data_editor(
    student_data,
    use_container_width=True,
    num_rows="fixed",
    key="student_marks",
    column_config={
        "Student": st.column_config.TextColumn(
            "Student Name"
        ),
        "LE1": st.column_config.NumberColumn(
            "LE1 (%)",
            min_value=0.0,
            max_value=100.0,
            step=1.0
        ),
        "LM1": st.column_config.NumberColumn(
            "LM1 (%)",
            min_value=0.0,
            max_value=100.0,
            step=1.0
        )
    }
)

st.divider()

# --------------------------------------------------
# 7. CALCULATE CO ATTAINMENT
# --------------------------------------------------

st.header("7. Student-wise CO Attainment")

# LE and LM are the student-level assessments entered above.
# Their CO allocations are used as weights.

student_co_results = []

le_weights = allocation.loc["LE", CO_NAMES]
lm_weights = allocation.loc["LM", CO_NAMES]

for _, student in student_input.iterrows():

    result = {"Student": student["Student"]}

    for co in CO_NAMES:

        total_weight = le_weights[co] + lm_weights[co]

        if total_weight > 0:
            attainment = (
                student["LE1"] * le_weights[co]
                + student["LM1"] * lm_weights[co]
            ) / total_weight
        else:
            attainment = 0.0

        result[co] = attainment

    student_co_results.append(result)

co_results = pd.DataFrame(student_co_results)

st.dataframe(
    co_results.round(2),
    use_container_width=True
)

# Average CO attainment across students
average_co = co_results[CO_NAMES].mean()

st.subheader("Average CO Attainment")

co_summary = pd.DataFrame({
    "CO": CO_NAMES,
    "Average Attainment (%)": [
        average_co[co] for co in CO_NAMES
    ],
    "CO Weight": [
        co_weights[co] for co in CO_NAMES
    ]
})

st.dataframe(
    co_summary.round(2),
    use_container_width=True
)

# --------------------------------------------------
# 8. AUTOMATIC CO-PO ASSESSMENT MATRIX
# --------------------------------------------------

st.header("8. CO–PO Assessment Matrix")

# Calculate weighted CO contribution to each PO.
# Normalize by the total mapping strength for each PO.

co_po_matrix = pd.DataFrame(
    0.0,
    index=CO_NAMES,
    columns=PO_NAMES
)

for po in PO_NAMES:

    denominator = mapping[po].sum()

    if denominator > 0:
        for co in CO_NAMES:
            co_po_matrix.loc[co, po] = (
                average_co[co] * mapping.loc[co, po]
                / denominator
            )

st.subheader("CO Contribution to PO Attainment")

st.dataframe(
    co_po_matrix.round(2),
    use_container_width=True
)

# Calculate PO attainment
po_attainment = {}

for po in PO_NAMES:

    denominator = mapping[po].sum()

    if denominator > 0:
        po_attainment[po] = (
            sum(
                average_co[co] * mapping.loc[co, po]
                for co in CO_NAMES
            ) / denominator
        )
    else:
        po_attainment[po] = 0.0

po_summary = pd.DataFrame({
    "PO": PO_NAMES,
    "PO Weight": [
        po_weights[po] for po in PO_NAMES
    ],
    "PO Attainment (%)": [
        po_attainment[po] for po in PO_NAMES
    ],
    "Weighted PO Marks": [
        po_attainment[po] * po_weights[po] / 100
        for po in PO_NAMES
    ]
})

st.subheader("Programme Outcome Attainment")

st.dataframe(
    po_summary.round(2),
    use_container_width=True
)

# --------------------------------------------------
# 9. DASHBOARD CHARTS
# --------------------------------------------------

st.header("9. Attainment Dashboard")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("CO Attainment")
    st.bar_chart(
        co_summary.set_index("CO")[
            "Average Attainment (%)"
        ]
    )

with chart_col2:
    st.subheader("PO Attainment")
    st.bar_chart(
        po_summary.set_index("PO")[
            "PO Attainment (%)"
        ]
    )

# --------------------------------------------------
# 10. DOWNLOAD RESULTS
# --------------------------------------------------

st.divider()

st.header("10. Download Results")

co_csv = co_summary.to_csv(index=False).encode("utf-8")

po_csv = po_summary.to_csv(index=False).encode("utf-8")

matrix_csv = co_po_matrix.to_csv().encode("utf-8")

student_csv = co_results.to_csv(index=False).encode("utf-8")

download_col1, download_col2 = st.columns(2)

with download_col1:
    st.download_button(
        "Download CO Results",
        co_csv,
        "CO_Attainment.csv",
        "text/csv"
    )

    st.download_button(
        "Download PO Results",
        po_csv,
        "PO_Attainment.csv",
        "text/csv"
    )

with download_col2:
    st.download_button(
        "Download CO-PO Matrix",
        matrix_csv,
        "CO_PO_Matrix.csv",
        "text/csv"
    )

    st.download_button(
        "Download Student Results",
        student_csv,
        "Student_CO_Attainment.csv",
        "text/csv"
    )

st.success("Dashboard calculations completed.")
