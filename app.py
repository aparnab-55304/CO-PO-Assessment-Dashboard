
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="CO-PO Assessment Dashboard",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM DESIGN
# --------------------------------------------------

st.markdown("""
<style>
.main {
    background-color: #f5f7fb;
}
h1 {
    color: #17365D;
}
h2, h3 {
    color: #24476B;
}
[data-testid="stMetric"] {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #e0e5ed;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("📊 CO-PO Assessment Dashboard")

st.markdown("""
**Interactive CO-PO Assessment Weight Distribution and Analysis**

This dashboard calculates assessment-wise weighted scores,
CO weight distribution and overall performance.
""")

st.divider()

# --------------------------------------------------
# ASSESSMENT WEIGHTS
# --------------------------------------------------

st.header("1. Assessment Weight Configuration")

assessment_names = [
    "Assessment 1",
    "Assessment 2",
    "Assessment 3",
    "Assessment 4",
    "Assessment 5"
]

default_weights = [4, 4, 3, 3, 6]

weight_df = pd.DataFrame({
    "Assessment": assessment_names,
    "Weight": default_weights
})

edited_weights = st.data_editor(
    weight_df,
    hide_index=True,
    use_container_width=True,
    disabled=["Assessment"],
    column_config={
        "Weight": st.column_config.NumberColumn(
            "Weight",
            min_value=0,
            max_value=20,
            step=1
        )
    },
    key="assessment_weights"
)

weights = edited_weights["Weight"].tolist()
total_weight = sum(weights)

col1, col2 = st.columns(2)

col1.metric("Total Assessment Weight", total_weight)
col2.metric("Maximum Internal Weight", 20)

if total_weight != 20:
    st.error("Assessment weights must add up to 20.")
    st.stop()

st.success("Assessment weights are valid. Total = 20.")

st.divider()

# --------------------------------------------------
# CO-PO MATRIX
# --------------------------------------------------

st.header("2. CO-PO Assessment Matrix")

st.write("""
Enter the assessment contribution or attainment percentage
for each row and assessment.

- Enter values between 0 and 100.
- Missing cells must be completed manually by the teacher.
- The dashboard will not automatically replace missing values.
""")

rows = ["PO1", "PO2", "LE", "LM"]

if "matrix_data" not in st.session_state:
    st.session_state.matrix_data = pd.DataFrame(
        np.nan,
        index=rows,
        columns=assessment_names
    )

edited_matrix = st.data_editor(
    st.session_state.matrix_data,
    use_container_width=True,
    key="matrix_editor",
    column_config={
        col: st.column_config.NumberColumn(
            col,
            min_value=0,
            max_value=100,
            step=1,
            format="%.2f"
        )
        for col in assessment_names
    }
)

st.session_state.matrix_data = edited_matrix

st.divider()

# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

st.header("3. Data Validation")

matrix = edited_matrix[assessment_names].apply(
    pd.to_numeric, errors="coerce"
)

missing_count = int(matrix.isna().sum().sum())

invalid_count = int(
    ((matrix < 0) | (matrix > 100)).sum().sum()
)

v1, v2, v3 = st.columns(3)

v1.metric("Total Cells", matrix.size)
v2.metric("Missing Cells", missing_count)
v3.metric("Invalid Cells", invalid_count)

if missing_count > 0:
    st.warning(
        "Some cells are missing. Please enter the values manually. "
        "Calculations will be completed only after all cells are filled."
    )

if invalid_count > 0:
    st.error("Values must be between 0 and 100.")

# --------------------------------------------------
# CALCULATIONS
# --------------------------------------------------

if missing_count == 0 and invalid_count == 0:

    weight_series = pd.Series(
        weights,
        index=assessment_names
    )

    # Weighted contribution of each assessment
    weighted_matrix = matrix.mul(
        weight_series / 20,
        axis=1
    )

    # Total weighted score for each row
    row_totals = weighted_matrix.sum(axis=1)

    # Assessment-wise totals
    column_totals = weighted_matrix.sum(axis=0)

    # Overall total
    grand_total = row_totals.sum()

    st.header("4. Calculated Results")

    result_df = weighted_matrix.copy()
    result_df["Total Weighted Score"] = row_totals

    st.subheader("Weighted Assessment Matrix")

    st.dataframe(
        result_df.round(2),
        use_container_width=True
    )

    r1, r2, r3 = st.columns(3)

    r1.metric("Overall Weighted Total", f"{grand_total:.2f}")
    r2.metric("Number of Dimensions", len(rows))
    r3.metric("Completed Cells", matrix.size)

    st.subheader("Assessment-wise Weighted Contribution")

    column_result = pd.DataFrame({
        "Assessment": assessment_names,
        "Assessment Weight": weights,
        "Weighted Contribution": column_totals.values
    })

    st.dataframe(
        column_result.round(2),
        hide_index=True,
        use_container_width=True
    )

    st.subheader("Row-wise Total")

    row_result = pd.DataFrame({
        "Dimension": rows,
        "Total Weighted Score": row_totals.values
    })

    st.dataframe(
        row_result.round(2),
        hide_index=True,
        use_container_width=True
    )

    # --------------------------------------------------
    # CHARTS
    # --------------------------------------------------

    st.header("5. Visual Dashboard")

    chart1, chart2 = st.columns(2)

    with chart1:
        fig1 = px.bar(
            row_result,
            x="Dimension",
            y="Total Weighted Score",
            title="Dimension-wise Weighted Scores",
            text_auto=".2f"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    with chart2:
        fig2 = px.pie(
            column_result,
            names="Assessment",
            values="Weighted Contribution",
            title="Assessment Contribution Distribution"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # --------------------------------------------------
    # EXTERNAL AND INTERNAL CO WEIGHTS
    # --------------------------------------------------

    st.divider()

    st.header("6. External and Internal CO Weight Distribution")

    external_weights = [8, 8, 7, 7]
    co_names = ["CO1", "CO2", "CO3", "CO4"]

    co_df = pd.DataFrame({
        "Course Outcome": co_names,
        "External Weight": external_weights
    })

    external_total = sum(external_weights)

    co_df["Internal Weight"] = (
        co_df["External Weight"] / external_total
    ) * 20

    co_df["External Percentage"] = (
        co_df["External Weight"] / external_total
    ) * 100

    co_df["Internal Percentage"] = (
        co_df["Internal Weight"] / 20
    ) * 100

    st.write("""
    Internal CO weights are calculated proportionally from
    external CO weights using:
    
    **Internal CO Weight = (External CO Weight / 30) × 20**
    """)

    st.dataframe(
        co_df.round(2),
        hide_index=True,
        use_container_width=True
    )

    c1, c2 = st.columns(2)

    c1.metric("External Maximum", f"{external_total}/30")
    c2.metric("Internal Maximum", "20")

    fig3 = px.bar(
        co_df,
        x="Course Outcome",
        y=["External Percentage", "Internal Percentage"],
        barmode="group",
        title="External vs Internal CO Weight Distribution",
        labels={"value": "Percentage", "variable": "Assessment"}
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # --------------------------------------------------
    # EXCEL DOWNLOAD
    # --------------------------------------------------

    st.divider()

    st.header("7. Download Assessment Report")

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        matrix.to_excel(
            writer,
            sheet_name="Input Matrix"
        )

        weighted_matrix.to_excel(
            writer,
            sheet_name="Weighted Results"
        )

        row_result.to_excel(
            writer,
            sheet_name="Row Totals",
            index=False
        )

        column_result.to_excel(
            writer,
            sheet_name="Assessment Totals",
            index=False
        )

        co_df.to_excel(
            writer,
            sheet_name="CO Weight Distribution",
            index=False
        )

    st.download_button(
        label="📥 Download Complete Excel Report",
        data=output.getvalue(),
        file_name="CO_PO_Assessment_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info(
        "Complete all missing cells and correct invalid values "
        "to generate the dashboard results."
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "CO-PO Assessment Dashboard | Developed using Python and Streamlit"
)

