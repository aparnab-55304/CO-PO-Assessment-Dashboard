
import streamlit as st
import pandas as pd

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CO-PO Assessment Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("CO–PO Assessment Dashboard")
st.caption("Automated Course Outcome and Programme Outcome Assessment")

# =========================================================
# BASIC STRUCTURE
# =========================================================

CO_NAMES = ["CO1", "CO2", "CO3", "CO4"]
PO_NAMES = ["PO1", "PO2"]
ASSESSMENTS = ["PA1", "PA2", "LE1", "LE2"]

# Default coverage based on the supplied Excel workbook
default_coverage = pd.DataFrame({
    "CO": CO_NAMES,
    "PA1": [1, 1, 0, 0],
    "PA2": [0, 0, 1, 1],
    "LE1": [1, 1, 1, 1],
    "LE2": [1, 1, 1, 1]
})

# Default assessment weights
default_assessment_weights = {
    "PA1": 3.0,
    "PA2": 4.0,
    "LE1": 8.0,
    "LE2": 5.0
}

# =========================================================
# 1. CO WEIGHTS
# =========================================================

st.header("1. Course Outcome Weights")

st.write(
    "Enter the relative weight of each Course Outcome. "
    "These weights determine how assessment marks are "
    "distributed among the COs."
)

default_co_weights = [8.0, 8.0, 7.0, 7.0]

co_cols = st.columns(4)
co_weights = {}

for i, co in enumerate(CO_NAMES):
    with co_cols[i]:
        co_weights[co] = st.number_input(
            co,
            min_value=0.0,
            value=default_co_weights[i],
            step=1.0,
            key=f"co_weight_{co}"
        )

total_co_weight = sum(co_weights.values())

st.metric("Total CO Weight", f"{total_co_weight:.2f}")

if total_co_weight <= 0:
    st.error("The total CO weight must be greater than zero.")

# =========================================================
# 2. PO WEIGHTS
# =========================================================

st.header("2. Programme Outcome Weights")

st.write(
    "Enter the relative importance of PO1 and PO2. "
    "These weights are used to calculate each PO's "
    "contribution to the overall programme attainment."
)

default_po_weights = [8.0, 8.0]

po_cols = st.columns(2)
po_weights = {}

for i, po in enumerate(PO_NAMES):
    with po_cols[i]:
        po_weights[po] = st.number_input(
            po,
            min_value=0.0,
            value=default_po_weights[i],
            step=1.0,
            key=f"po_weight_{po}"
        )

total_po_weight = sum(po_weights.values())

st.metric("Total PO Weight", f"{total_po_weight:.2f}")

if total_po_weight <= 0:
    st.error("The total PO weight must be greater than zero.")

# =========================================================
# 3. ASSESSMENT WEIGHTS
# =========================================================

st.header("3. Assessment Weights")

st.write(
    "Enter the maximum internal marks allocated to "
    "each assessment."
)

assessment_cols = st.columns(4)
assessment_weights = {}

for i, assessment in enumerate(ASSESSMENTS):
    with assessment_cols[i]:
        assessment_weights[assessment] = st.number_input(
            assessment,
            min_value=0.0,
            value=default_assessment_weights[assessment],
            step=1.0,
            key=f"assessment_weight_{assessment}"
        )

total_assessment_weight = sum(assessment_weights.values())

st.metric(
    "Total Assessment Weight",
    f"{total_assessment_weight:.2f}"
)

# Explain the three different weight totals
with st.expander("How are the three types of weights used?"):
    st.write(
        "- **CO weights:** Relative weights used to distribute "
        "assessment marks among covered COs."
    )
    st.write(
        "- **Assessment weights:** Maximum marks allocated "
        "to PA1, PA2, LE1 and LE2."
    )
    st.write(
        "- **PO weights:** Relative importance of PO1 and PO2 "
        "when calculating overall weighted PO attainment."
    )
    st.write(
        "These totals do not need to be equal because they "
        "represent different quantities."
    )

st.divider()

# =========================================================
# 4. EDITABLE ASSESSMENT COVERAGE
# =========================================================

st.header("4. Assessment–CO Coverage Matrix")

st.write(
    "Edit the coverage matrix according to your course. "
    "Enter 1 if an assessment covers a CO and 0 otherwise."
)

coverage_input = st.data_editor(
    default_coverage,
    width="stretch",
    hide_index=True,
    num_rows="fixed",
    key="coverage_editor",
    column_config={
        "CO": st.column_config.TextColumn(
            "Course Outcome",
            disabled=True
        ),
        **{
            assessment: st.column_config.NumberColumn(
                assessment,
                min_value=0,
                max_value=1,
                step=1
            )
            for assessment in ASSESSMENTS
        }
    }
)

# Validate coverage
coverage_valid = True

coverage_values = coverage_input[ASSESSMENTS].apply(
    pd.to_numeric,
    errors="coerce"
)

if coverage_values.isna().any().any():
    coverage_valid = False
    st.error("Coverage cells must contain only 0 or 1.")

elif not coverage_values.isin([0, 1]).all().all():
    coverage_valid = False
    st.error("Coverage cells must contain only 0 or 1.")

coverage = coverage_values.copy()
coverage.index = coverage_input["CO"].tolist()

st.caption("1 = Covered; 0 = Not covered.")

st.divider()

# =========================================================
# 5. AUTOMATIC ASSESSMENT–CO ALLOCATION MATRIX
# =========================================================

st.header("5. Assessment–CO Allocation Matrix")

allocation = pd.DataFrame(
    0.0,
    index=ASSESSMENTS,
    columns=CO_NAMES
)

allocation_valid = True

if total_co_weight <= 0:
    allocation_valid = False

if coverage_valid and total_co_weight > 0:

    for assessment in ASSESSMENTS:

        denominator = sum(
            coverage.loc[co, assessment] * co_weights[co]
            for co in CO_NAMES
        )

        if assessment_weights[assessment] > 0 and denominator <= 0:
            allocation_valid = False
            st.error(
                f"{assessment} has a positive assessment weight "
                "but no covered CO with a positive CO weight."
            )
            continue

        if denominator > 0:

            for co in CO_NAMES:

                allocation.loc[assessment, co] = (
                    assessment_weights[assessment]
                    * coverage.loc[co, assessment]
                    * co_weights[co]
                    / denominator
                )

if allocation_valid and coverage_valid:

    st.subheader("Calculated Allocation")

    st.dataframe(
        allocation.round(3),
        width="stretch"
    )

    co_allocation = allocation.sum(axis=0)

    allocation_summary = pd.DataFrame({
        "CO": CO_NAMES,
        "Allocated Marks": [
            co_allocation[co] for co in CO_NAMES
        ]
    })

    st.subheader("Total Marks Allocated to Each CO")

    st.dataframe(
        allocation_summary.round(3),
        width="stretch",
        hide_index=True
    )

    st.info(
        f"Total allocated marks: "
        f"{allocation.to_numpy().sum():.2f} "
        f"| Total assessment weight: "
        f"{total_assessment_weight:.2f}"
    )

st.divider()

# =========================================================
# 6. CO–PO MAPPING MATRIX
# =========================================================

st.header("6. CO–PO Mapping Matrix")

st.write(
    "Enter the relationship between each CO and PO."
)

st.caption(
    "0 = No relationship | 1 = Low | 2 = Medium | 3 = High"
)

default_mapping = pd.DataFrame({
    "CO": CO_NAMES,
    "PO1": [3, 2, 1, 2],
    "PO2": [2, 3, 2, 1]
})

mapping_input = st.data_editor(
    default_mapping,
    width="stretch",
    hide_index=True,
    num_rows="fixed",
    key="mapping_editor",
    column_config={
        "CO": st.column_config.TextColumn(
            "Course Outcome",
            disabled=True
        ),
        **{
            po: st.column_config.NumberColumn(
                po,
                min_value=0,
                max_value=3,
                step=1
            )
            for po in PO_NAMES
        }
    }
)

mapping = mapping_input.set_index("CO")[PO_NAMES].astype(float)

mapping_valid = mapping.isin([0, 1, 2, 3]).all().all()

if not mapping_valid:
    st.error("CO–PO mapping values must be 0, 1, 2 or 3.")

st.divider()

# =========================================================
# 7. RAW MARKS INPUT
# =========================================================

st.header("7. Student Assessment Marks")

st.write(
    "Teachers can enter raw marks. The dashboard converts "
    "them automatically into percentages using the maximum "
    "marks entered below."
)

st.subheader("Maximum Marks for Each Assessment")

max_cols = st.columns(4)
max_marks = {}

for i, assessment in enumerate(ASSESSMENTS):

    with max_cols[i]:

        max_marks[assessment] = st.number_input(
            f"{assessment} Maximum Marks",
            min_value=0.01,
            value=100.0,
            step=1.0,
            key=f"max_marks_{assessment}"
        )

st.subheader("Enter Student Marks")

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
    **{
        assessment: [0.0] * int(number_of_students)
        for assessment in ASSESSMENTS
    }
})

student_input = st.data_editor(
    student_data,
    width="stretch",
    hide_index=True,
    num_rows="fixed",
    key="student_marks_editor",
    column_config={
        "Student": st.column_config.TextColumn(
            "Student Name"
        ),
        **{
            assessment: st.column_config.NumberColumn(
                f"{assessment} Raw Marks",
                min_value=0.0,
                max_value=float(max_marks[assessment]),
                step=0.5
            )
            for assessment in ASSESSMENTS
        }
    }
)

# =========================================================
# 8. CONVERT RAW MARKS INTO PERCENTAGES
# =========================================================

student_percentages = student_input.copy()

marks_valid = True

for assessment in ASSESSMENTS:

    raw_marks = pd.to_numeric(
        student_input[assessment],
        errors="coerce"
    )

    if raw_marks.isna().any():
        marks_valid = False
        st.error(f"Invalid marks found in {assessment}.")
        continue

    if (raw_marks < 0).any() or (
        raw_marks > max_marks[assessment]
    ).any():

        marks_valid = False

        st.error(
            f"{assessment} marks must be between "
            f"0 and {max_marks[assessment]}."
        )

    student_percentages[assessment] = (
        raw_marks / max_marks[assessment] * 100
    )

st.subheader("Student Marks Converted into Percentages")

if marks_valid:

    percentage_display = student_percentages.copy()

    for assessment in ASSESSMENTS:
        percentage_display[assessment] = (
            percentage_display[assessment].round(2)
        )

    st.dataframe(
        percentage_display,
        width="stretch",
        hide_index=True
    )

st.divider()

# =========================================================
# 9. STUDENT-WISE CO ATTAINMENT
# =========================================================

st.header("8. Student-wise CO Attainment")

student_co_results = []

if (
    allocation_valid
    and coverage_valid
    and marks_valid
    and total_co_weight > 0
):

    for _, student in student_percentages.iterrows():

        result = {
            "Student": student["Student"]
        }

        for co in CO_NAMES:

            numerator = 0.0
            denominator = 0.0

            for assessment in ASSESSMENTS:

                weight = allocation.loc[assessment, co]

                numerator += (
                    student[assessment] * weight
                )

                denominator += weight

            if denominator > 0:

                result[co] = numerator / denominator

            else:

                result[co] = None

        student_co_results.append(result)

    co_results = pd.DataFrame(student_co_results)

    st.dataframe(
        co_results.round(2),
        width="stretch",
        hide_index=True
    )

    # Average CO attainment
    average_co = co_results[CO_NAMES].mean()

    co_summary = pd.DataFrame({
        "CO": CO_NAMES,
        "CO Weight": [
            co_weights[co] for co in CO_NAMES
        ],
        "Allocated Marks": [
            allocation[ASSESSMENTS].loc[:, co].sum()
            for co in CO_NAMES
        ],
        "Average Attainment (%)": [
            average_co[co] for co in CO_NAMES
        ]
    })

    # Display N/A instead of 0 for unavailable COs
    co_summary_display = co_summary.copy()

    co_summary_display["Average Attainment (%)"] = (
        co_summary_display["Average Attainment (%)"].apply(
            lambda x: "N/A" if pd.isna(x) else round(x, 2)
        )
    )

    st.subheader("Average CO Attainment")

    st.dataframe(
        co_summary_display,
        width="stretch",
        hide_index=True
    )

else:

    st.warning(
        "CO attainment will appear after the weights, "
        "coverage and student marks have been validated."
    )

st.divider()

# =========================================================
# 10. CO–PO ASSESSMENT MATRIX
# =========================================================

st.header("9. CO–PO Assessment Matrix")

if (
    allocation_valid
    and coverage_valid
    and marks_valid
    and mapping_valid
    and total_co_weight > 0
):

    co_po_matrix = pd.DataFrame(
        index=CO_NAMES,
        columns=PO_NAMES,
        dtype=float
    )

    for co in CO_NAMES:

        for po in PO_NAMES:

            if pd.isna(average_co[co]):
                co_po_matrix.loc[co, po] = None

            else:
                co_po_matrix.loc[co, po] = (
                    average_co[co] * mapping.loc[co, po]
                )

    st.subheader("CO Attainment × CO–PO Mapping")

    st.dataframe(
        co_po_matrix.round(2),
        width="stretch"
    )

    st.caption(
        "Each cell represents the CO attainment multiplied "
        "by its mapping strength for that PO."
    )

    # =====================================================
    # 11. PO ATTAINMENT AND WEIGHTED CONTRIBUTION
    # =====================================================

    st.header("10. Programme Outcome Attainment")

    po_attainment = {}
    po_contribution = {}

    for po in PO_NAMES:

        valid_cos = [
            co for co in CO_NAMES
            if not pd.isna(average_co[co])
        ]

        denominator = sum(
            mapping.loc[co, po]
            for co in valid_cos
        )

        if denominator > 0:

            po_attainment[po] = sum(
                average_co[co] * mapping.loc[co, po]
                for co in valid_cos
            ) / denominator

        else:

            po_attainment[po] = None

    if total_po_weight > 0:

        for po in PO_NAMES:

            if po_attainment[po] is not None:

                po_contribution[po] = (
                    po_attainment[po]
                    * po_weights[po]
                    / total_po_weight
                )

            else:

                po_contribution[po] = None

    po_summary = pd.DataFrame({
        "PO": PO_NAMES,
        "PO Weight": [
            po_weights[po] for po in PO_NAMES
        ],
        "PO Attainment (%)": [
            po_attainment[po] for po in PO_NAMES
        ],
        "Weight Share (%)": [
            po_weights[po] / total_po_weight * 100
            if total_po_weight > 0 else 0
            for po in PO_NAMES
        ],
        "Weighted Contribution": [
            po_contribution[po] for po in PO_NAMES
        ]
    })

    po_summary_display = po_summary.copy()

    for column in [
        "PO Attainment (%)",
        "Weight Share (%)",
        "Weighted Contribution"
    ]:

        po_summary_display[column] = (
            po_summary_display[column].apply(
                lambda x: "N/A" if pd.isna(x) else round(x, 2)
            )
        )

    st.dataframe(
        po_summary_display,
        width="stretch",
        hide_index=True
    )

    # Overall weighted PO attainment
    available_contributions = [
        po_contribution[po]
        for po in PO_NAMES
        if po_contribution[po] is not None
    ]

    unavailable_po_weights = sum(
        po_weights[po]
        for po in PO_NAMES
        if po_contribution[po] is None
    )

    if unavailable_po_weights == 0:

        overall_po_attainment = sum(
            available_contributions
        )

        st.metric(
            "Overall Weighted PO Attainment",
            f"{overall_po_attainment:.2f}%"
        )

    else:

        st.warning(
            "Overall weighted PO attainment is not shown because "
            "one or more POs have no calculable attainment. "
            "Check the CO–PO mapping and assessment coverage."
        )

else:

    st.warning(
        "The CO–PO matrix and PO attainment require valid "
        "CO attainment, coverage and mapping values."
    )

st.divider()

# =========================================================
# 12. CHARTS
# =========================================================

st.header("11. Attainment Dashboard")

if (
    allocation_valid
    and coverage_valid
    and marks_valid
    and mapping_valid
    and total_co_weight > 0
):

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        st.subheader("CO Attainment")

        co_chart = co_summary.set_index("CO")[
            "Average Attainment (%)"
        ]

        st.bar_chart(co_chart)

    with chart_col2:

        st.subheader("PO Attainment")

        po_chart = pd.Series(
            po_attainment,
            name="PO Attainment (%)"
        )

        st.bar_chart(po_chart)

# =========================================================
# 13. DOWNLOAD RESULTS
# =========================================================

st.divider()

st.header("12. Download Results")

if (
    allocation_valid
    and coverage_valid
    and marks_valid
    and mapping_valid
    and total_co_weight > 0
):

    download_col1, download_col2 = st.columns(2)

    with download_col1:

        st.download_button(
            "Download Assessment–CO Matrix",
            allocation.to_csv().encode("utf-8"),
            "Assessment_CO_Matrix.csv",
            "text/csv"
        )

        st.download_button(
            "Download Student CO Results",
            co_results.to_csv(index=False).encode("utf-8"),
            "Student_CO_Attainment.csv",
            "text/csv"
        )

        st.download_button(
            "Download CO Summary",
            co_summary.to_csv(index=False).encode("utf-8"),
            "CO_Summary.csv",
            "text/csv"
        )

    with download_col2:

        st.download_button(
            "Download CO–PO Matrix",
            co_po_matrix.to_csv().encode("utf-8"),
            "CO_PO_Matrix.csv",
            "text/csv"
        )

        st.download_button(
            "Download PO Summary",
            po_summary.to_csv(index=False).encode("utf-8"),
            "PO_Summary.csv",
            "text/csv"
        )

        st.download_button(
            "Download Student Percentage Marks",
            student_percentages.to_csv(index=False).encode("utf-8"),
            "Student_Percentage_Marks.csv",
            "text/csv"
        )

st.success("Dashboard is ready.")
