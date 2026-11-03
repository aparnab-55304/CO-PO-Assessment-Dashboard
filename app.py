
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="CO Assessment Dashboard",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# 2. CUSTOM CSS
# ==========================================

st.markdown("""
<style>
.stApp {
    background-color: #F4F7FB;
}
.main-title {
    color: #17365D;
    font-size: 32px;
    font-weight: bold;
}
.subtitle {
    color: #64748B;
    font-size: 15px;
}
div[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #DCE4EF;
    padding: 18px;
    border-radius: 12px;
}
div[data-testid="stMetricValue"] {
    color: #17365D;
}
section[data-testid="stSidebar"] {
    background-color: #EAF0F8;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. DEFAULT DATA
# ==========================================

ASSESSMENTS = ["PA1", "PA2", "LE", "LM"]
COS = ["CO1", "CO2", "CO3", "CO4"]

DEFAULT_MARKS = pd.DataFrame({
    "Assessment": ASSESSMENTS,
    "Weight": [3, 4, 8, 5]
})

DEFAULT_COVERAGE = pd.DataFrame({
    "Assessment": ASSESSMENTS,
    "CO1": [True, False, True, True],
    "CO2": [True, False, True, True],
    "CO3": [False, True, True, True],
    "CO4": [False, True, True, True]
})

# ==========================================
# 4. SESSION STATE
# ==========================================

if "marks" not in st.session_state:
    st.session_state.marks = DEFAULT_MARKS.copy()

if "coverage" not in st.session_state:
    st.session_state.coverage = DEFAULT_COVERAGE.copy()

if "co_weights" not in st.session_state:
    st.session_state.co_weights = {
        "CO1": 8.0,
        "CO2": 8.0,
        "CO3": 7.0,
        "CO4": 7.0
    }

# ==========================================
# 5. HEADER
# ==========================================

st.markdown(
    '<div class="main-title">📊 CO ASSESSMENT DASHBOARD</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Course Outcome Assessment, '
    'Weight Allocation and Performance Analysis</div>',
    unsafe_allow_html=True
)

st.divider()

# ==========================================
# 6. SIDEBAR
# ==========================================

st.sidebar.title("⚙️ Dashboard Settings")

course_name = st.sidebar.text_input(
    "Course Name",
    "Statistical Computing"
)

course_code = st.sidebar.text_input(
    "Course Code",
    "ST040303"
)

internal_max = st.sidebar.number_input(
    "Maximum Internal Marks",
    min_value=1.0,
    value=20.0,
    step=1.0
)

external_max = st.sidebar.number_input(
    "Maximum External Marks",
    min_value=1.0,
    value=30.0,
    step=1.0
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Edit assessment marks, CO weights and coverage "
    "using the tables in the dashboard."
)

# ==========================================
# 7. ASSESSMENT WEIGHTS
# ==========================================

st.header("1. Assessment Weight Allocation")

st.write(
    "Enter the maximum marks/weights assigned to each assessment."
)

marks_df = st.data_editor(
    st.session_state.marks,
    num_rows="dynamic",
    use_container_width=True,
    key="marks_editor",
    column_config={
        "Assessment": st.column_config.TextColumn(
            "Assessment",
            required=True
        ),
        "Weight": st.column_config.NumberColumn(
            "Assessment Weight",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            required=True
        )
    }
)

# ==========================================
# 8. CO WEIGHTS
# ==========================================

st.header("2. Course Outcome Weights")

st.write(
    "Enter the external/overall weight assigned to each CO."
)

cols = st.columns(4)

co_weights = {}

for i, co in enumerate(COS):
    with cols[i]:
        co_weights[co] = st.number_input(
            co,
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.co_weights[co]),
            step=1.0,
            key="input_" + co
        )

total_co_weight = sum(co_weights.values())

st.info(
    f"Total CO Weight: {total_co_weight:.2f} / "
    f"External Maximum: {external_max:.2f}"
)

# ==========================================
# 9. CO COVERAGE MATRIX
# ==========================================

st.header("3. CO Coverage Matrix")

st.write(
    "Select the COs covered by each assessment."
)

st.caption(
    "Checked = 1 (Covered) | Unchecked = 0 (Not Covered)"
)

coverage_df = st.data_editor(
    st.session_state.coverage,
    num_rows="dynamic",
    use_container_width=True,
    key="coverage_editor",
    column_config={
        "Assessment": st.column_config.TextColumn(
            "Assessment",
            disabled=True
        ),
        **{
            co: st.column_config.CheckboxColumn(
                co,
                default=False
            )
            for co in COS
        }
    }
)

# ==========================================
# 10. VALIDATION
# ==========================================

valid = True

if marks_df.empty:
    st.error("Enter at least one assessment.")
    valid = False

elif marks_df["Assessment"].isna().any():
    st.error("Assessment names cannot be empty.")
    valid = False

elif marks_df["Assessment"].astype(str).str.strip().eq("").any():
    st.error("Assessment names cannot be empty.")
    valid = False

elif marks_df["Assessment"].duplicated().any():
    st.error("Assessment names must be unique.")
    valid = False

elif marks_df["Weight"].isna().any() or (marks_df["Weight"] < 0).any():
    st.error("Assessment weights must be non-negative.")
    valid = False

elif total_co_weight <= 0:
    st.error("The total CO weight must be greater than zero.")
    valid = False

elif external_max <= 0 or internal_max <= 0:
    st.error("Maximum marks must be greater than zero.")
    valid = False

elif set(marks_df["Assessment"].astype(str)) != set(
    coverage_df["Assessment"].astype(str)
):
    st.error("Assessment names in the coverage matrix must match the assessment table.")
    valid = False

# ==========================================
# 11. CALCULATION
# ==========================================

if valid:

    marks_df = marks_df.copy()
    coverage_df = coverage_df.copy()

    result_rows = []

    for _, assessment in marks_df.iterrows():

        name = str(assessment["Assessment"])
        assessment_weight = float(assessment["Weight"])

        coverage_row = coverage_df[
            coverage_df["Assessment"].astype(str) == name
        ].iloc[0]

        covered_cos = [
            co for co in COS
            if bool(coverage_row[co])
        ]

        covered_weight = sum(
            co_weights[co] for co in covered_cos
        )

        row = {
            "Assessment": name,
            "Assessment Weight": assessment_weight
        }

        for co in COS:

            if co in covered_cos and covered_weight > 0:

                contribution = (
                    co_weights[co] / covered_weight
                ) * assessment_weight

            else:
                contribution = 0.0

            row[co] = contribution

        row["Total"] = sum(row[co] for co in COS)

        result_rows.append(row)

    result_df = pd.DataFrame(result_rows)

    # CO-wise internal totals

    co_totals = {
        co: result_df[co].sum()
        for co in COS
    }

    total_internal = sum(co_totals.values())
    total_assessment_weight = marks_df["Weight"].sum()

    # CO-wise allocation of internal CCA marks
    # Based on CO weight / total CO weight * internal maximum

    cca_weights = {
        co: (co_weights[co] / total_co_weight) * internal_max
        for co in COS
    }

    # ======================================
    # 12. DASHBOARD SUMMARY
    # ======================================

    st.divider()
    st.header("4. Dashboard Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total Assessments",
        len(marks_df)
    )

    c2.metric(
        "Internal Maximum",
        f"{internal_max:.2f}"
    )

    c3.metric(
        "External Maximum",
        f"{external_max:.2f}"
    )

    c4.metric(
        "Total CO Weight",
        f"{total_co_weight:.2f}"
    )

    st.divider()

    # ======================================
    # 13. ASSESSMENT CONTRIBUTION TABLE
    # ======================================

    st.header("5. Assessment-wise CO Contribution")

    st.write(
        "Each assessment weight is distributed among "
        "the covered COs according to their relative weights."
    )

    display_result = result_df.copy()

    st.dataframe(
        display_result.round(2),
        use_container_width=True,
        hide_index=True
    )

    # ======================================
    # 14. CO-WISE INTERNAL SUMMARY
    # ======================================

    st.header("6. CO-wise Internal Assessment")

    co_result = pd.DataFrame({
        "Course Outcome": COS,
        "CO Weight": [co_weights[co] for co in COS],
        "Internal Marks": [co_totals[co] for co in COS],
        "CCA Maximum": [cca_weights[co] for co in COS]
    })

    co_result["Percentage of Internal Maximum"] = (
        co_result["Internal Marks"] / internal_max * 100
    )

    co_result["Difference"] = (
        co_result["CCA Maximum"] -
        co_result["Internal Marks"]
    )

    st.dataframe(
        co_result.round(2),
        use_container_width=True,
        hide_index=True
    )

    # ======================================
    # 15. CO PERFORMANCE CHART
    # ======================================

    st.divider()
    st.header("7. Visual Analysis")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("CO-wise Internal Marks")

        fig1 = px.bar(
            co_result,
            x="Course Outcome",
            y="Internal Marks",
            color="Course Outcome",
            text="Internal Marks",
            title="Internal Marks Obtained by Each CO"
        )

        fig1.update_layout(
            showlegend=False,
            yaxis_title="Internal Marks",
            xaxis_title="Course Outcome"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    with col2:

        st.subheader("CO-wise CCA Allocation")

        fig2 = px.bar(
            co_result,
            x="Course Outcome",
            y="CCA Maximum",
            color="Course Outcome",
            text="CCA Maximum",
            title="Internal CCA Weight Allocation"
        )

        fig2.update_layout(
            showlegend=False,
            yaxis_title="CCA Maximum",
            xaxis_title="Course Outcome"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # ======================================
    # 16. ASSESSMENT STACKED CHART
    # ======================================

    st.subheader("Assessment-wise CO Distribution")

    assessment_long = result_df.melt(
        id_vars=["Assessment"],
        value_vars=COS,
        var_name="Course Outcome",
        value_name="Contribution"
    )

    fig3 = px.bar(
        assessment_long,
        x="Assessment",
        y="Contribution",
        color="Course Outcome",
        barmode="stack",
        title="CO Contribution in Each Assessment"
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # ======================================
    # 17. COVERAGE HEATMAP
    # ======================================

    st.subheader("CO Coverage Heatmap")

    heatmap_data = coverage_df.set_index(
        "Assessment"
    )[COS].astype(int)

    fig4 = px.imshow(
        heatmap_data,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Assessment and CO Coverage"
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )

    # ======================================
    # 18. INTERNAL AND EXTERNAL SUMMARY
    # ======================================

    st.divider()
    st.header("8. Overall CO Weight Summary")

    overall_result = pd.DataFrame({
        "Course Outcome": COS,
        "External CO Weight": [co_weights[co] for co in COS],
        "Internal CCA Maximum": [cca_weights[co] for co in COS],
        "Overall Maximum": [
            co_weights[co] + cca_weights[co]
            for co in COS
        ]
    })

    st.dataframe(
        overall_result.round(2),
        use_container_width=True,
        hide_index=True
    )

    # ======================================
    # 19. DOWNLOAD EXCEL REPORT
    # ======================================

    st.divider()
    st.header("9. Download Report")

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        marks_df.to_excel(
            writer,
            sheet_name="Assessment_Weights",
            index=False
        )

        coverage_df.to_excel(
            writer,
            sheet_name="CO_Coverage",
            index=False
        )

        result_df.to_excel(
            writer,
            sheet_name="Assessment_Contribution",
            index=False
        )

        co_result.to_excel(
            writer,
            sheet_name="CO_Internal_Summary",
            index=False
        )

        overall_result.to_excel(
            writer,
            sheet_name="Overall_CO_Summary",
            index=False
        )

    st.download_button(
        label="📥 Download Complete Excel Report",
        data=output.getvalue(),
        file_name="CO_Assessment_Dashboard_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ======================================
    # 20. FOOTER
    # ======================================

    st.divider()

    st.markdown(
        f"""
        <center>
        <b>CO Assessment Dashboard</b><br>
        {course_name} | {course_code}<br>
        Internal Assessment and CO Weight Analysis
        </center>
        """,
        unsafe_allow_html=True
    )

    # Save editable data for next rerun
    st.session_state.marks = marks_df.copy()
    st.session_state.coverage = coverage_df.copy()
    st.session_state.co_weights = co_weights.copy()

else:
    st.warning("Correct the input errors to generate the dashboard.")
