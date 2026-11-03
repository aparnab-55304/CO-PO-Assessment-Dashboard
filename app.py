
import streamlit as st
import pandas as pd
import numpy as np

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="CO-PO Assessment Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("CO–PO Assessment Dashboard")
st.write("Automated Course Outcome and Programme Outcome Assessment")

st.divider()

# ==================================================
# BASIC STRUCTURE
# ==================================================

CO_NAMES = ["CO1", "CO2", "CO3", "CO4"]
PO_NAMES = ["PO1", "PO2"]

ASSESSMENTS = ["PA1", "PA2", "LE1", "LE2"]

# Fixed assessment coverage based on the supplied workbook
coverage = pd.DataFrame(
    [
        [1, 1, 0, 0],  # PA1
        [0, 0, 1, 1],  # PA2
        [1, 1, 1, 1],  # LE1
        [1, 1, 1, 1]   # LE2
    ],
    index=ASSESSMENTS,
    columns=CO_NAMES
)

# ==================================================
# 1. CO WEIGHTS
# ==================================================

st.header("1. Course Outcome Weights")

st.caption("Enter the weight assigned to each CO.")

default_co_weights = [8, 8, 7, 7]

co_cols = st.columns(4)
co_weights = {}

for i, co in enumerate(CO_NAMES):
    with co_cols[i]:
        co_weights[co] = st.number_input(
            co,
            min_value=0.0,
            value=float(default_co_weights[i]),
            step=1.0,
            key=f"co_{co}"
        )

total_co_weight = sum(co_weights.values())

st.info(f"Total CO Weight: {total_co_weight:.2f}")

# ==================================================
# 2. PO WEIGHTS
# ==================================================

st.header("2. Programme Outcome Weights")

st.caption("Enter the weight assigned to PO1 and PO2.")

default_po_weights = [8, 8]

po_cols = st.columns(2)
po_weights = {}

for i, po in enumerate(PO_NAMES):
    with po_cols[i]:
        po_weights[po] = st.number_input(
            po,
            min_value=0.0,
            value=float(default_po_weights[i]),
            step=1.0,
            key=f"po_{po}"
        )

st.info(
    f"Total PO Weight: {sum(po_weights.values()):.2f}"
)

st.divider()

# ==================================================
# 3. ASSESSMENT WEIGHTS
# ==================================================

st.header("3. Assessment Weights")

st.caption(
    "Enter the weight allocated to PA1, PA2, LE1 and LE2."
)

default_assessment_weights = {
    "PA1": 3,
    "PA2": 4,
    "LE1": 8,
    "LE2": 5
}

assessment_cols = st.columns(4)
assessment_weights = {}

for i, assessment in enumerate(ASSESSMENTS):
    with assessment_cols[i]:
        assessment_weights[assessment] = st.number_input(
            assessment,
            min_value=0.0,
            value=float(default_assessment_weights[assessment]),
            step=1.0,
            key=f"assessment_{assessment}"
        )

total_assessment_weight = sum(assessment_weights.values())

st.info(
    f"Total Assessment Weight: {total_assessment_weight:.2f}"
)

st.divider()

# ==================================================
# 4. ASSESSMENT COVERAGE
# ==================================================

st.header("4. Assessment–CO Coverage Matrix")

st.write(
    "The following coverage is fixed according to the "
    "assessment structure in your Excel workbook."
)

st.dataframe(
    coverage,
    use_container_width=True
)

st.caption(
    "1 = Assessment covers the CO; 0 = Assessment does not cover the CO."
)

# ==================================================
# 5. AUTOMATIC ASSESSMENT-CO ALLOCATION
# ==================================================

st.header("5. Automatic Assessment–CO Allocation Matrix")

allocation = pd.DataFrame(
    0.0,
    index=ASSESSMENTS,
    columns=CO_NAMES
)

for assessment in ASSESSMENTS:

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

st.subheader("Calculated Allocation Matrix")

st.dataframe(
    allocation.round(3),
    use_container_width=True
)

co_allocation = allocation.sum(axis=0)

st.subheader("Total Marks Allocated to Each CO")

st.dataframe(
    pd.DataFrame({
        "CO": CO_NAMES,
        "Allocated Marks": [
            co_allocation[co] for co in CO_NAMES
        ]
    }).round(3),
    use_container_width=True
)

st.divider()

# ==================================================
# 6. CO-PO MAPPING
# ==================================================

st.header("6. CO–PO Mapping Matrix")

st.write(
    "Enter the relationship between each CO and PO."
)

st.caption(
    "0 = No relationship | 1 = Low | 2 = Medium | 3 = High"
)

mapping_default = pd.DataFrame(
    [
        [3, 2],
        [2, 3],
        [1, 2],
        [2, 1]
    ],
    index=CO_NAMES,
    columns=PO_NAMES
)

mapping_default.index.name = "CO"

mapping_input = st.data_editor(
    mapping_default,
    use_container_width=True,
    key="mapping_editor",
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

# ==================================================
# 7. STUDENT MARKS INPUT
# ==================================================

st.header("7. Student Assessment Marks")

st.write(
    "Enter the marks obtained by each student in PA1, PA2, LE1 and LE2."
)

st.caption(
    "Enter marks as percentages from 0 to 100."
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
        f"Student {i+1}"
        for i in range(int(number_of_students))
    ],
    "PA1": [70.0] * int(number_of_students),
    "PA2": [75.0] * int(number_of_students),
    "LE1": [80.0] * int(number_of_students),
    "LE2": [85.0] * int(number_of_students)
})

student_input = st.data_editor(
    student_data,
    use_container_width=True,
    num_rows="fixed",
    key="student_editor",
    column_config={
        "Student": st.column_config.TextColumn(
            "Student Name"
        ),
        "PA1": st.column_config.NumberColumn(
            "PA1 (%)", min_value=0.0, max_value=100.0
        ),
        "PA2": st.column_config.NumberColumn(
            "PA2 (%)", min_value=0.0, max_value=100.0
        ),
        "LE1": st.column_config.NumberColumn(
            "LE1 (%)", min_value=0.0, max_value=100.0
        ),
        "LE2": st.column_config.NumberColumn(
            "LE2 (%)", min_value=0.0, max_value=100.0
        )
    }
)

st.divider()

# ==================================================
# 8. STUDENT-WISE CO ATTAINMENT
# ==================================================

st.header("8. Student-wise CO Attainment")

student_co_results = []

for _, student in student_input.iterrows():

    result = {
        "Student": student["Student"]
    }

    for co in CO_NAMES:

        numerator = 0.0
        denominator = 0.0

        for assessment in ASSESSMENTS:

            weight = allocation.loc[assessment, co]

            numerator += (
                float(student[assessment]) * weight
            )

            denominator += weight

        if denominator > 0:
            attainment = numerator / denominator
        else:
            attainment = 0.0

        result[co] = attainment

    student_co_results.append(result)

co_results = pd.DataFrame(student_co_results)

st.dataframe(
    co_results.round(2),
    use_container_width=True
)

# Average attainment of each CO
average_co = co_results[CO_NAMES].mean()

st.subheader("Average CO Attainment")

co_summary = pd.DataFrame({
    "CO": CO_NAMES,
    "CO Weight": [
        co_weights[co] for co in CO_NAMES
    ],
    "Average Attainment (%)": [
        average_co[co] for co in CO_NAMES
    ]
})

st.dataframe(
    co_summary.round(2),
    use_container_width=True
)

st.divider()

# ==================================================
# 9. CO-PO ASSESSMENT MATRIX
# ==================================================

st.header("9. CO–PO Assessment Matrix")

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
                average_co[co]
                * mapping.loc[co, po]
                / denominator
            )

st.subheader("CO Contribution to Each PO")

st.dataframe(
    co_po_matrix.round(2),
    use_container_width=True
)

# ==================================================
# 10. PO ATTAINMENT
# ==================================================

st.header("10. Programme Outcome Attainment")

po_attainment = {}

for po in PO_NAMES:

    denominator = mapping[po].sum()

    if denominator > 0:

        po_attainment[po] = sum(
            average_co[co] * mapping.loc[co, po]
            for co in CO_NAMES
        ) / denominator

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
    "Weighted PO Contribution": [
        po_attainment[po] * po_weights[po] / 100
        for po in PO_NAMES
    ]
})

st.dataframe(
    po_summary.round(2),
    use_container_width=True
)

st.divider()

# ==================================================
# 11. DASHBOARD CHARTS
# ==================================================

st.header("11. Attainment Dashboard")

col1, col2 = st.columns(2)

with col1:

    st.subheader("CO Attainment")

    st.bar_chart(
        co_summary.set_index("CO")[
            "Average Attainment (%)"
        ]
    )

with col2:

    st.subheader("PO Attainment")

    st.bar_chart(
        po_summary.set_index("PO")[
            "PO Attainment (%)"
        ]
    )

# ==================================================
# 12. DOWNLOAD RESULTS
# ==================================================

st.divider()

st.header("12. Download Results")

col1, col2 = st.columns(2)

with col1:

    st.download_button(
        "Download CO Results",
        co_summary.to_csv(index=False).encode("utf-8"),
        "CO_Attainment.csv",
        "text/csv"
    )

    st.download_button(
        "Download PO Results",
        po_summary.to_csv(index=False).encode("utf-8"),
        "PO_Attainment.csv",
        "text/csv"
    )

with col2:

    st.download_button(
        "Download CO–PO Matrix",
        co_po_matrix.to_csv().encode("utf-8"),
        "CO_PO_Matrix.csv",
        "text/csv"
    )

    st.download_button(
        "Download Student Results",
        co_results.to_csv(index=False).encode("utf-8"),
        "Student_CO_Attainment.csv",
        "text/csv"
    )

st.success("CO–PO Assessment Dashboard calculated successfully.")
