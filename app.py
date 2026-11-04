
import streamlit as st
import pandas as pd

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CO-PO Summary Matrix",
    page_icon="📊",
    layout="wide"
)

st.title("CO–PO Assessment Summary Dashboard")
st.caption("Automated Weighted Assessment–CO Summary Matrix")

# =====================================================
# COURSE DETAILS
# =====================================================

st.header("Course Details")

col1, col2 = st.columns(2)

with col1:
    department = st.selectbox(
        "Department",
        [
            "Select Department",
            "Statistics",
            "Mathematics",
            "Computer Science",
            "Physics",
            "Chemistry",
            "Commerce",
            "Economics",
            "Other"
        ]
    )

    course_name = st.selectbox(
        "Course Name",
        [
            "Select Course",
            "Statistical Computing",
            "Statistical Modelling",
            "Time Series Analysis",
            "Multivariate Analysis",
            "Design and Analysis of Experiments",
            "Other"
        ]
    )

with col2:
    course_code = st.selectbox(
        "Course Code",
        [
            "Select Course Code",
            "ST040301",
            "ST040302",
            "ST040303",
            "ST500302",
            "ST500304",
            "Other"
        ]
    )

    semester = st.selectbox(
        "Semester",
        [
            "Select Semester",
            "Semester 1",
            "Semester 2",
            "Semester 3",
            "Semester 4",
            "Semester 5",
            "Semester 6",
            "Semester 7",
            "Semester 8"
        ]
    )

st.divider()

# =====================================================
# BASIC STRUCTURE
# =====================================================

ALL_CO_NAMES = ["CO1", "CO2", "CO3", "CO4", "CO5"]

ASSESSMENTS = ["PA1", "PA2", "LE", "LM"]

DEFAULT_CO_WEIGHTS = {
    "CO1": 8.0,
    "CO2": 8.0,
    "CO3": 5.0,
    "CO4": 5.0,
    "CO5": 4.0
}

DEFAULT_ASSESSMENT_WEIGHTS = {
    "PA1": 4.0,
    "PA2": 4.0,
    "LE": 6.0,
    "LM": 6.0
}

# =====================================================
# 1. COURSE OUTCOME SELECTION
# =====================================================

st.header("1. Course Outcome Selection")

selected_cos = st.multiselect(
    "Select applicable Course Outcomes",
    options=ALL_CO_NAMES,
    default=ALL_CO_NAMES
)

if not selected_cos:
    st.warning("Please select at least one CO.")
    st.stop()

CO_NAMES = selected_cos

# =====================================================
# 2. CO WEIGHTS
# =====================================================

st.header("2. Course Outcome Weights")

co_weights = {}

cols = st.columns(min(len(CO_NAMES), 5))

for i, co in enumerate(CO_NAMES):

    with cols[i % len(cols)]:

        co_weights[co] = st.number_input(
            co,
            min_value=0.0,
            value=DEFAULT_CO_WEIGHTS[co],
            step=1.0,
            key=f"weight_{co}"
        )

total_co_weight = sum(co_weights.values())

if total_co_weight <= 0:
    st.error("Total CO weight must be greater than zero.")
    st.stop()

# =====================================================
# 3. ASSESSMENT WEIGHTS
# =====================================================

st.header("3. Assessment Weights")

assessment_weights = {}

cols = st.columns(4)

for i, assessment in enumerate(ASSESSMENTS):

    with cols[i]:

        assessment_weights[assessment] = st.number_input(
            assessment,
            min_value=0.0,
            value=DEFAULT_ASSESSMENT_WEIGHTS[assessment],
            step=1.0,
            key=f"weight_{assessment}"
        )

# =====================================================
# 4. ASSESSMENT COVERAGE MATRIX
# =====================================================

st.header("4. Assessment–CO Coverage Matrix")

default_values = {
    "CO1": [1, 0, 1, 1],
    "CO2": [1, 0, 1, 1],
    "CO3": [0, 1, 1, 1],
    "CO4": [0, 1, 1, 1],
    "CO5": [0, 0, 1, 1]
}

default_coverage = pd.DataFrame(
    [
        [co] + default_values[co]
        for co in CO_NAMES
    ],
    columns=["CO"] + ASSESSMENTS
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
            a: st.column_config.NumberColumn(
                a,
                min_value=0,
                max_value=1,
                step=1
            )
            for a in ASSESSMENTS
        }
    }
)

coverage_values = coverage_input[ASSESSMENTS].apply(
    pd.to_numeric,
    errors="coerce"
)

if (
    coverage_values.isna().any().any()
    or not coverage_values.isin([0, 1]).all().all()
):
    st.error("Coverage values must be either 0 or 1.")
    st.stop()

coverage = coverage_values.copy()
coverage.index = coverage_input["CO"].tolist()

# =====================================================
# 5. SUMMARY MATRIX CALCULATION
# =====================================================

st.divider()

st.header("5. Assessment–CO Summary Matrix")

summary_matrix = pd.DataFrame(
    0.0,
    index=ASSESSMENTS,
    columns=CO_NAMES
)

for assessment in ASSESSMENTS:

    denominator = sum(
        coverage.loc[co, assessment] * co_weights[co]
        for co in CO_NAMES
    )

    assessment_weight = assessment_weights[assessment]

    if assessment_weight > 0 and denominator <= 0:

        st.error(
            f"{assessment} has positive weight "
            "but no valid CO allocation."
        )

        st.stop()

    if denominator > 0:

        for co in CO_NAMES:

            summary_matrix.loc[assessment, co] = (
                assessment_weight
                * coverage.loc[co, assessment]
                * co_weights[co]
                / denominator
            )

# =====================================================
# 6. DISPLAY SUMMARY MATRIX
# =====================================================

st.header("6. Final Summary Matrix")

display_matrix = summary_matrix.copy()

display_matrix["Total"] = display_matrix.sum(axis=1)

display_matrix.loc["Total"] = display_matrix.sum(axis=0)

st.dataframe(
    display_matrix.round(2),
    width="stretch"
)

# =====================================================
# 7. VALIDATION
# =====================================================

st.header("7. Allocation Validation")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total CO Weight",
        f"{total_co_weight:.2f}"
    )

with col2:
    st.metric(
        "Total Assessment Weight",
        f"{sum(assessment_weights.values()):.2f}"
    )

with col3:
    st.metric(
        "Total Allocated Marks",
        f"{summary_matrix.to_numpy().sum():.2f}"
    )

# =====================================================
# 8. COURSE DETAILS AND DOWNLOAD
# =====================================================

st.divider()

st.header("8. Download Summary Matrix")

course_details = pd.DataFrame({
    "Parameter": [
        "Department",
        "Course Name",
        "Course Code",
        "Semester",
        "Selected COs"
    ],
    "Details": [
        department,
        course_name,
        course_code,
        semester,
        ", ".join(CO_NAMES)
    ]
})

st.subheader("Course Information")

st.dataframe(
    course_details,
    hide_index=True,
    width="stretch"
)

# Include course information in the CSV output

output_matrix = display_matrix.round(2).reset_index()
output_matrix = output_matrix.rename(
    columns={"index": "Assessment"}
)

csv = output_matrix.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Summary Matrix (CSV)",
    data=csv,
    file_name="CO_PO_Summary_Matrix.csv",
    mime="text/csv"
)

# Download course information separately

course_csv = course_details.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Course Details (CSV)",
    data=course_csv,
    file_name="Course_Details.csv",
    mime="text/csv"
)

st.success("Summary matrix calculated successfully.")
