
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Automated CO-PO Assessment System",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# 2. DESIGN
# =====================================================

st.markdown("""
<style>
.stApp {
    background-color: #F4F6FA;
}
.main-title {
    font-size: 32px;
    font-weight: 800;
    color: #17365D;
}
.sub-title {
    color: #64748B;
    font-size: 15px;
}
div[data-testid="stMetric"] {
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #DCE3ED;
}
section[data-testid="stSidebar"] {
    background-color: #E9EFF7;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# 3. CONSTANTS
# =====================================================

COS = ["CO1", "CO2", "CO3", "CO4"]
POS = ["PO1", "PO2", "PO3", "PO4", "PO5", "PO6", "PO7", "PO8", "PO9", "PO10", "PO11", "PO12"]

ASSESSMENTS = ["LE1", "LM1"]

DEFAULT_CO_WEIGHTS = pd.DataFrame({
    "CO": COS,
    "Course Weight": [8.0, 8.0, 7.0, 7.0]
})

DEFAULT_PO_MAPPING = pd.DataFrame({
    "CO": COS,
    **{po: [0, 0, 0, 0] for po in POS}
})

DEFAULT_STUDENTS = pd.DataFrame({
    "Student ID": ["S001"],
    "Student Name": [""],
    "LE1": [0.0],
    "LM1": [0.0]
})

# =====================================================
# 4. SESSION STATE
# =====================================================

if "students" not in st.session_state:
    st.session_state.students = DEFAULT_STUDENTS.copy()

if "co_weights" not in st.session_state:
    st.session_state.co_weights = DEFAULT_CO_WEIGHTS.copy()

if "po_mapping" not in st.session_state:
    st.session_state.po_mapping = DEFAULT_PO_MAPPING.copy()

# =====================================================
# 5. HEADER
# =====================================================

st.markdown(
    '<div class="main-title">📊 AUTOMATED CO–PO ASSESSMENT SYSTEM</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">Student-wise Course Outcome and '
    'Programme Outcome Assessment Dashboard</div>',
    unsafe_allow_html=True
)

st.divider()

# =====================================================
# 6. SIDEBAR SETTINGS
# =====================================================

st.sidebar.title("⚙️ Assessment Settings")

course_name = st.sidebar.text_input(
    "Course Name",
    "Statistical Computing"
)

course_code = st.sidebar.text_input(
    "Course Code",
    "ST040303"
)

internal_max = st.sidebar.number_input(
    "Internal Maximum Marks",
    min_value=1.0,
    value=20.0,
    step=1.0
)

external_max = st.sidebar.number_input(
    "External Maximum Marks",
    min_value=1.0,
    value=30.0,
    step=1.0
)

st.sidebar.markdown("---")
st.sidebar.subheader("Assessment Weights")

le1_weight = st.sidebar.number_input(
    "LE1 Weight",
    min_value=0.0,
    value=10.0,
    step=1.0
)

lm1_weight = st.sidebar.number_input(
    "LM1 Weight",
    min_value=0.0,
    value=10.0,
    step=1.0
)

assessment_weights = {
    "LE1": le1_weight,
    "LM1": lm1_weight
}

assessment_total = le1_weight + lm1_weight

st.sidebar.write(
    f"Total assessment weight: {assessment_total:.2f}"
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "LE1 and LM1 weights should add up to the "
    "maximum internal marks."
)

# =====================================================
# 7. COURSE CO WEIGHTS
# =====================================================

st.header("1. Course Outcome Weight Configuration")

st.write(
    "Teacher enters the external maximum weight "
    "assigned to each Course Outcome."
)

co_weights_df = st.data_editor(
    st.session_state.co_weights,
    use_container_width=True,
    hide_index=True,
    disabled=["CO"],
    key="co_weight_editor",
    column_config={
        "Course Weight": st.column_config.NumberColumn(
            "CO Weight",
            min_value=0.0,
            max_value=external_max,
            step=1.0,
            required=True
        )
    }
)

co_weights = dict(
    zip(
        co_weights_df["CO"],
        co_weights_df["Course Weight"]
    )
)

total_co_weight = sum(co_weights.values())

st.info(
    f"Total Course Weight: {total_co_weight:.2f} / "
    f"{external_max:.2f}"
)

# =====================================================
# 8. AUTOMATIC INTERNAL CO WEIGHT
# =====================================================

st.header("2. Automatic Internal CO Weight Calculation")

if total_co_weight > 0:

    internal_co_weights = {
        co: (co_weights[co] / total_co_weight) * internal_max
        for co in COS
    }

    internal_weight_df = pd.DataFrame({
        "Course Outcome": COS,
        "External CO Weight": [co_weights[co] for co in COS],
        "Internal CO Weight": [
            internal_co_weights[co] for co in COS
        ]
    })

    st.dataframe(
        internal_weight_df.round(2),
        use_container_width=True,
        hide_index=True
    )

else:
    internal_co_weights = {co: 0.0 for co in COS}
    st.error("Total CO weight must be greater than zero.")

# =====================================================
# 9. AUTOMATIC ASSESSMENT MATRIX
# =====================================================

st.header("3. Automatically Generated Assessment Matrix")

st.write(
    "The matrix is calculated automatically using the "
    "course CO weights and assessment weights."
)

matrix_rows = []

for assessment in ASSESSMENTS:

    row = {
        "Assessment": assessment,
        "Assessment Weight": assessment_weights[assessment]
    }

    for co in COS:

        if total_co_weight > 0:
            value = (
                assessment_weights[assessment]
                * co_weights[co]
                / total_co_weight
            )
        else:
            value = 0

        row[co] = value

    row["Total"] = sum(row[co] for co in COS)

    matrix_rows.append(row)

assessment_matrix = pd.DataFrame(matrix_rows)

total_row = {
    "Assessment": "TOTAL",
    "Assessment Weight": assessment_total
}

for co in COS:
    total_row[co] = assessment_matrix[co].sum()

total_row["Total"] = assessment_matrix["Total"].sum()

assessment_matrix = pd.concat(
    [assessment_matrix, pd.DataFrame([total_row])],
    ignore_index=True
)

st.dataframe(
    assessment_matrix.round(2),
    use_container_width=True,
    hide_index=True
)

# =====================================================
# 10. CO-PO MAPPING MATRIX
# =====================================================

st.divider()

st.header("4. CO–PO Mapping Weights")

st.write(
    "Teacher enters the relationship strength between "
    "each CO and PO."
)

st.caption(
    "0 = No mapping | 1 = Low | 2 = Medium | 3 = High"
)

po_mapping_df = st.data_editor(
    st.session_state.po_mapping,
    use_container_width=True,
    hide_index=True,
    disabled=["CO"],
    key="po_mapping_editor",
    column_config={
        po: st.column_config.NumberColumn(
            po,
            min_value=0,
            max_value=3,
            step=1,
            required=True
        )
        for po in POS
    }
)

# =====================================================
# 11. STUDENT MARKS INPUT
# =====================================================

st.divider()

st.header("5. Student-wise Assessment Marks")

st.write(
    "Teachers only need to enter student details and "
    "their LE1 and LM1 marks."
)

st.caption(
    "Add students using the empty row at the bottom. "
    "Marks are calculated automatically."
)

uploaded_file = st.file_uploader(
    "Upload student marks Excel/CSV (optional)",
    type=["xlsx", "csv"]
)

if uploaded_file is not None:

    try:
        if uploaded_file.name.endswith(".csv"):
            uploaded_students = pd.read_csv(uploaded_file)
        else:
            uploaded_students = pd.read_excel(uploaded_file)

        required_columns = [
            "Student ID", "Student Name", "LE1", "LM1"
        ]

        if all(c in uploaded_students.columns for c in required_columns):
            st.session_state.students = uploaded_students[
                required_columns
            ].copy()
            st.success("Student data uploaded successfully.")
        else:
            st.error(
                "File must contain: Student ID, Student Name, LE1, LM1."
            )

    except Exception as e:
        st.error(f"Upload error: {e}")

students_df = st.data_editor(
    st.session_state.students,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="student_editor",
    column_config={
        "Student ID": st.column_config.TextColumn(
            "Student ID",
            required=True
        ),
        "Student Name": st.column_config.TextColumn(
            "Student Name"
        ),
        "LE1": st.column_config.NumberColumn(
            "LE1 Marks",
            min_value=0.0,
            max_value=10000.0,
            step=1.0,
            required=True
        ),
        "LM1": st.column_config.NumberColumn(
            "LM1 Marks",
            min_value=0.0,
            max_value=10000.0,
            step=1.0,
            required=True
        )
    }
)

# =====================================================
# 12. MARK MAXIMUMS
# =====================================================

st.subheader("Assessment Maximum Marks")

max_col1, max_col2 = st.columns(2)

with max_col1:
    le1_max = st.number_input(
        "LE1 Maximum Marks",
        min_value=0.01,
        value=10.0,
        step=1.0
    )

with max_col2:
    lm1_max = st.number_input(
        "LM1 Maximum Marks",
        min_value=0.01,
        value=10.0,
        step=1.0
    )

# =====================================================
# 13. VALIDATION
# =====================================================

valid = True

if not np.isclose(assessment_total, internal_max):
    st.error(
        "LE1 Weight + LM1 Weight must equal "
        "the maximum internal marks."
    )
    valid = False

if not np.isclose(total_co_weight, external_max):
    st.error(
        "The sum of CO weights must equal the "
        "external maximum marks."
    )
    valid = False

if students_df.empty:
    st.warning("Please enter student details.")
    valid = False

if not students_df.empty:

    if students_df["Student ID"].isna().any():
        st.error("Student IDs cannot be empty.")
        valid = False

    elif students_df["Student ID"].astype(str).str.strip().eq("").any():
        st.error("Student IDs cannot be empty.")
        valid = False

    elif students_df["Student ID"].duplicated().any():
        st.error("Student IDs must be unique.")
        valid = False

    elif students_df[["LE1", "LM1"]].isna().any().any():
        st.error("Student marks cannot be blank. Enter 0 if absent.")
        valid = False

    elif (students_df[["LE1", "LM1"]] < 0).any().any():
        st.error("Marks cannot be negative.")
        valid = False

    elif (students_df["LE1"] > le1_max).any():
        st.error("LE1 marks exceed the maximum marks.")
        valid = False

    elif (students_df["LM1"] > lm1_max).any():
        st.error("LM1 marks exceed the maximum marks.")
        valid = False

    elif students_df["Student ID"].astype(str).str.strip().eq("").any():
        valid = False

if not np.isin(
    po_mapping_df[POS].to_numpy(dtype=float),
    [0, 1, 2, 3]
).all():
    st.error("PO mapping values must be 0, 1, 2 or 3.")
    valid = False

# =====================================================
# 14. STUDENT-WISE CO CALCULATION
# =====================================================

if valid:

    st.divider()

    st.header("6. Automatic Student-wise CO Calculation")

    student_co_results = []
    student_po_results = []
    detailed_results = []

    for _, student in students_df.iterrows():

        sid = str(student["Student ID"])
        name = str(student["Student Name"])

        # Convert assessment marks to weighted marks

        le1_contribution = (
            float(student["LE1"]) / le1_max
        ) * le1_weight

        lm1_contribution = (
            float(student["LM1"]) / lm1_max
        ) * lm1_weight

        total_student_internal = (
            le1_contribution + lm1_contribution
        )

        co_row = {
            "Student ID": sid,
            "Student Name": name
        }

        # Allocate internal marks according to CO weights

        for co in COS:

            share = co_weights[co] / total_co_weight

            le1_co = le1_contribution * share
            lm1_co = lm1_contribution * share

            earned = le1_co + lm1_co

            maximum = internal_co_weights[co]

            percentage = (
                earned / maximum * 100
                if maximum > 0 else 0
            )

            co_row[co] = earned

            detailed_results.append({
                "Student ID": sid,
                "Student Name": name,
                "CO": co,
                "LE1 Contribution": le1_co,
                "LM1 Contribution": lm1_co,
                "Total CO Marks": earned,
                "CO Maximum": maximum,
                "CO Attainment (%)": percentage
            })

        co_row["Total Internal Marks"] = total_student_internal

        student_co_results.append(co_row)

        # ==========================================
        # 15. STUDENT-WISE PO ATTAINMENT
        # ==========================================

        po_row = {
            "Student ID": sid,
            "Student Name": name
        }

        for po in POS:

            weighted_total = 0
            mapping_total = 0

            for co in COS:

                mapping_value = float(
                    po_mapping_df.loc[
                        po_mapping_df["CO"] == co, po
                    ].iloc[0]
                )

                if mapping_value > 0:

                    co_percentage = (
                        co_row[co] /
                        internal_co_weights[co] * 100
                        if internal_co_weights[co] > 0
                        else 0
                    )

                    weighted_total += (
                        co_percentage * mapping_value
                    )

                    mapping_total += mapping_value

            po_attainment = (
                weighted_total / mapping_total
                if mapping_total > 0 else np.nan
            )

            po_row[po] = po_attainment

        student_po_results.append(po_row)

    # Convert results to dataframes

    student_co_df = pd.DataFrame(student_co_results)

    student_po_df = pd.DataFrame(student_po_results)

    detailed_df = pd.DataFrame(detailed_results)

    # =================================================
    # 16. CO RESULT TABLE
    # =================================================

    st.subheader("Student-wise CO Marks")

    st.dataframe(
        student_co_df.round(2),
        use_container_width=True,
        hide_index=True
    )

    # =================================================
    # 17. CO ATTAINMENT TABLE
    # =================================================

    st.subheader("Student-wise CO Attainment (%)")

    co_attainment = student_co_df[
        ["Student ID", "Student Name"]
    ].copy()

    for co in COS:

        co_attainment[co] = (
            student_co_df[co] /
            internal_co_weights[co] * 100
            if internal_co_weights[co] > 0
            else 0
        )

    st.dataframe(
        co_attainment.round(2),
        use_container_width=True,
        hide_index=True
    )

    # =================================================
    # 18. PO ATTAINMENT TABLE
    # =================================================

    st.divider()

    st.header("7. Student-wise PO Attainment")

    st.dataframe(
        student_po_df.round(2),
        use_container_width=True,
        hide_index=True
    )

    # =================================================
    # 19. CLASS AVERAGE CO ATTAINMENT
    # =================================================

    st.header("8. Class-wise CO Attainment")

    class_co = pd.DataFrame({
        "CO": COS,
        "Average CO Attainment (%)": [
            co_attainment[co].mean()
            for co in COS
        ]
    })

    st.dataframe(
        class_co.round(2),
        use_container_width=True,
        hide_index=True
    )

    # =================================================
    # 20. CLASS AVERAGE PO ATTAINMENT
    # =================================================

    st.header("9. Class-wise PO Attainment")

    class_po_rows = []

    for po in POS:

        valid_values = student_po_df[po].dropna()

        class_po_rows.append({
            "PO": po,
            "Average PO Attainment (%)": (
                valid_values.mean()
                if len(valid_values) > 0
                else np.nan
            )
        })

    class_po = pd.DataFrame(class_po_rows)

    st.dataframe(
        class_po.round(2),
        use_container_width=True,
        hide_index=True
    )

    # =================================================
    # 21. DASHBOARD KPIs
    # =================================================

    st.divider()

    st.header("10. Dashboard Summary")

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        "Total Students",
        len(students_df)
    )

    k2.metric(
        "Internal Maximum",
        f"{internal_max:.2f}"
    )

    k3.metric(
        "Average Internal Marks",
        f"{student_co_df['Total Internal Marks'].mean():.2f}"
    )

    k4.metric(
        "Course Outcomes",
        len(COS)
    )

    # =================================================
    # 22. CO CHART
    # =================================================

    st.divider()

    st.header("11. Performance Visualisation")

    chart1, chart2 = st.columns(2)

    with chart1:

        fig1 = px.bar(
            class_co,
            x="CO",
            y="Average CO Attainment (%)",
            text_auto=".2f",
            title="Average CO Attainment",
            color="CO"
        )

        fig1.update_layout(showlegend=False)

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    with chart2:

        plot_po = class_po.dropna()

        fig2 = px.bar(
            plot_po,
            x="PO",
            y="Average PO Attainment (%)",
            text_auto=".2f",
            title="Average PO Attainment",
            color="PO"
        )

        fig2.update_layout(showlegend=False)

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # =================================================
    # 23. STUDENT COMPARISON
    # =================================================

    st.subheader("Student-wise Internal Marks Comparison")

    fig3 = px.bar(
        student_co_df,
        x="Student ID",
        y="Total Internal Marks",
        color="Student ID",
        title="Student Internal Performance"
    )

    fig3.update_layout(showlegend=False)

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # =================================================
    # 24. DOWNLOAD EXCEL REPORT
    # =================================================

    st.divider()

    st.header("12. Download Complete Assessment Report")

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        co_weights_df.to_excel(
            writer,
            sheet_name="CO_Weights",
            index=False
        )

        internal_weight_df.to_excel(
            writer,
            sheet_name="Internal_CO_Weights",
            index=False
        )

        assessment_matrix.to_excel(
            writer,
            sheet_name="Assessment_Matrix",
            index=False
        )

        po_mapping_df.to_excel(
            writer,
            sheet_name="CO_PO_Mapping",
            index=False
        )

        students_df.to_excel(
            writer,
            sheet_name="Student_Marks",
            index=False
        )

        student_co_df.to_excel(
            writer,
            sheet_name="Student_CO_Marks",
            index=False
        )

        detailed_df.to_excel(
            writer,
            sheet_name="Detailed_CO_Results",
            index=False
        )

        co_attainment.to_excel(
            writer,
            sheet_name="CO_Attainment",
            index=False
        )

        student_po_df.to_excel(
            writer,
            sheet_name="Student_PO_Attainment",
            index=False
        )

        class_co.to_excel(
            writer,
            sheet_name="Class_CO_Summary",
            index=False
        )

        class_po.to_excel(
            writer,
            sheet_name="Class_PO_Summary",
            index=False
        )

    st.download_button(
        label="📥 Download Complete Excel Report",
        data=output.getvalue(),
        file_name="Automated_CO_PO_Assessment.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # =================================================
    # 25. SAVE SESSION DATA
    # =================================================

    st.session_state.students = students_df.copy()
    st.session_state.co_weights = co_weights_df.copy()
    st.session_state.po_mapping = po_mapping_df.copy()

    st.divider()

    st.success(
        "All assessment matrices and student-wise "
        "CO–PO calculations have been generated."
    )

    st.caption(
        f"{course_name} | {course_code} | "
        "Automated CO–PO Assessment System"
    )

else:

    st.warning(
        "Please correct the input errors to generate results."
    )
