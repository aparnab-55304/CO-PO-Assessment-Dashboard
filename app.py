
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
# BASIC STRUCTURE
# =====================================================

CO_NAMES = ["CO1", "CO2", "CO3", "CO4"]
ASSESSMENTS = ["PA1", "PA2", "LE", "LM"]

# CO weights
DEFAULT_CO_WEIGHTS = [8.0, 8.0, 7.0, 7.0]

# Assessment weights
DEFAULT_ASSESSMENT_WEIGHTS = {
    "PA1": 4.0,
    "PA2": 4.0,
    "LE": 6.0,
    "LM": 6.0
}

# Default assessment coverage
default_coverage = pd.DataFrame({
    "CO": CO_NAMES,
    "PA1": [1, 1, 0, 0],
    "PA2": [0, 0, 1, 1],
    "LE": [1, 1, 1, 1],
    "LM": [1, 1, 1, 1]
})

# =====================================================
# 1. CO WEIGHTS
# =====================================================

st.header("1. Course Outcome Weights")

cols = st.columns(4)
co_weights = {}

for i, co in enumerate(CO_NAMES):
    with cols[i]:
        co_weights[co] = st.number_input(
            co,
            min_value=0.0,
            value=DEFAULT_CO_WEIGHTS[i],
            step=1.0,
            key=f"weight_{co}"
        )

total_co_weight = sum(co_weights.values())

if total_co_weight <= 0:
    st.error("Total CO weight must be greater than zero.")
    st.stop()

# =====================================================
# 2. ASSESSMENT WEIGHTS
# =====================================================

st.header("2. Assessment Weights")

cols = st.columns(4)
assessment_weights = {}

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
# 3. ASSESSMENT COVERAGE MATRIX
# =====================================================

st.header("3. Assessment–CO Coverage Matrix")

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
# 4. AUTOMATIC SUMMARY MATRIX CALCULATION
# =====================================================

st.divider()
st.header("4. Assessment–CO Summary Matrix")

# Rows = PA1, PA2, LE, LM
# Columns = CO1, CO2, CO3, CO4

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
            f"{assessment} has positive weight but no valid CO allocation."
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
# 5. DISPLAY SUMMARY MATRIX
# =====================================================

display_matrix = summary_matrix.copy()

display_matrix["Total"] = display_matrix.sum(axis=1)

display_matrix.loc["Total"] = display_matrix.sum(axis=0)

st.dataframe(
    display_matrix.round(2),
    width="stretch"
)

# =====================================================
# 6. VALIDATION
# =====================================================

st.subheader("Allocation Validation")

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
# 7. DOWNLOAD SUMMARY MATRIX
# =====================================================

st.divider()

csv = display_matrix.to_csv().encode("utf-8")

st.download_button(
    label="Download Summary Matrix (CSV)",
    data=csv,
    file_name="CO_PO_Summary_Matrix.csv",
    mime="text/csv"
)

st.success("Summary matrix calculated successfully.")
