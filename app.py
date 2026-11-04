
import streamlit as st
import pandas as pd
from io import BytesIO

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CO-PO Assessment Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("CO–PO Assessment Summary Dashboard")
st.caption("Automated Course Outcome and Programme Outcome Assessment")

# =========================================================
# 2. RESET
# =========================================================

if "reset_count" not in st.session_state:
    st.session_state.reset_count = 0

if st.button("🔄 Reset Dashboard"):
    st.session_state.reset_count += 1
    st.rerun()

reset_id = st.session_state.reset_count

# =========================================================
# 3. COURSE DETAILS
# =========================================================

st.header("1. Course Details")

col1, col2 = st.columns(2)

with col1:

    department_options = [
        "Department of English",
        "Department of Commerce",
        "Other"
    ]

    selected_department = st.selectbox(
        "Select Department",
        department_options,
        key=f"department_{reset_id}"
    )

    if selected_department == "Other":
        selected_department = st.text_input(
            "Enter Department Name",
            key=f"other_department_{reset_id}"
        )

    course_name = st.text_input(
        "Course Name",
        placeholder="Enter course name",
        key=f"course_name_{reset_id}"
    )

with col2:

    course_code = st.text_input(
        "Course Code",
        placeholder="Enter course code",
        key=f"course_code_{reset_id}"
    )

    semester = st.selectbox(
        "Select Semester",
        [f"Semester {i}" for i in range(1, 9)],
        key=f"semester_{reset_id}"
    )

# =========================================================
# 4. COURSE OUTCOMES
# =========================================================

st.header("2. Course Outcomes")

number_of_cos = st.number_input(
    "Enter Number of Course Outcomes",
    min_value=1,
    max_value=15,
    value=4,
    step=1,
    key=f"number_cos_{reset_id}"
)

number_of_cos = int(number_of_cos)

CO_NAMES = [
    f"CO{i}" for i in range(1, number_of_cos + 1)
]

PO_NAMES = ["PO1", "PO2"]

ASSESSMENTS = ["PA1", "PA2", "LE1", "LE2"]

# =========================================================
# 5. CO WEIGHTS
# =========================================================

st.header("3. CO Weight Allocation")

co_weight_df = pd.DataFrame({
    "Course Outcome": CO_NAMES,
    "CO Weight": [0.0] * number_of_cos
})

co_weights_table = st.data_editor(
    co_weight_df,
    key=f"co_weights_{reset_id}_{number_of_cos}",
    hide_index=True,
    width="stretch",
    disabled=["Course Outcome"],
    column_config={
        "CO Weight": st.column_config.NumberColumn(
            "CO Weight",
            min_value=0.0,
            step=0.5,
            format="%.2f"
        )
    }
)

co_weights = pd.Series(
    co_weights_table["CO Weight"].values,
    index=CO_NAMES,
    dtype=float
)

st.metric(
    "Total CO Weight",
    f"{co_weights.sum():.2f}"
)

# =========================================================
# 6. ASSESSMENT–CO COVERAGE MATRIX
# =========================================================

st.header("4. Assessment–CO Coverage Matrix")

st.write(
    "Enter the weight and maximum marks for each assessment. "
    "Select the COs covered by each assessment."
)

assessment_rows = []

for assessment in ASSESSMENTS:

    row = {
        "Assessment": assessment,
        "Assessment Weight": 0.0,
        "Maximum Marks": 0.0
    }

    for co in CO_NAMES:
        row[co] = False

    assessment_rows.append(row)

assessment_df = pd.DataFrame(assessment_rows)

assessment_column_config = {
    "Assessment": st.column_config.TextColumn(
        "Assessment",
        disabled=True
    ),

    "Assessment Weight": st.column_config.NumberColumn(
        "Weight",
        min_value=0.0,
        step=0.5,
        format="%.2f"
    ),

    "Maximum Marks": st.column_config.NumberColumn(
        "Maximum Marks",
        min_value=0.0,
        step=1.0,
        format="%.2f"
    )
}

for co in CO_NAMES:

    assessment_column_config[co] = (
        st.column_config.CheckboxColumn(
            co,
            help=f"Select if this assessment covers {co}"
        )
    )

assessment_matrix = st.data_editor(
    assessment_df,
    key=f"assessment_{reset_id}_{number_of_cos}",
    hide_index=True,
    width="stretch",
    disabled=["Assessment"],
    column_config=assessment_column_config
)

assessment_weight_total = pd.to_numeric(
    assessment_matrix["Assessment Weight"],
    errors="coerce"
).fillna(0).sum()

st.metric(
    "Total Assessment Weight",
    f"{assessment_weight_total:.2f}"
)

# =========================================================
# 7. CO–PO MAPPING
# =========================================================

st.header("5. CO–PO Mapping Matrix")

st.write(
    "Enter the mapping strength between each CO and PO. "
    "Use 0 for no mapping."
)

mapping_df = pd.DataFrame({
    "Course Outcome": CO_NAMES,
    "PO1": [0.0] * number_of_cos,
    "PO2": [0.0] * number_of_cos
})

mapping_table = st.data_editor(
    mapping_df,
    key=f"mapping_{reset_id}_{number_of_cos}",
    hide_index=True,
    width="stretch",
    disabled=["Course Outcome"],
    column_config={
        "PO1": st.column_config.NumberColumn(
            "PO1",
            min_value=0.0,
            step=0.5
        ),
        "PO2": st.column_config.NumberColumn(
            "PO2",
            min_value=0.0,
            step=0.5
        )
    }
)

mapping_values = mapping_table.set_index(
    "Course Outcome"
)[PO_NAMES].astype(float)

# =========================================================
# 8. PO WEIGHTS
# =========================================================

st.header("6. Programme Outcome Weights")

po_weight_df = pd.DataFrame({
    "Programme Outcome": PO_NAMES,
    "PO Weight": [0.0, 0.0]
})

po_weight_table = st.data_editor(
    po_weight_df,
    key=f"po_weights_{reset_id}",
    hide_index=True,
    width="stretch",
    disabled=["Programme Outcome"],
    column_config={
        "PO Weight": st.column_config.NumberColumn(
            "PO Weight",
            min_value=0.0,
            step=0.5,
            format="%.2f"
        )
    }
)

po_weights = pd.Series(
    po_weight_table["PO Weight"].values,
    index=PO_NAMES,
    dtype=float
)

st.metric(
    "Total PO Weight",
    f"{po_weights.sum():.2f}"
)

# =========================================================
# 9. STUDENT MARKS
# =========================================================

st.header("7. Student Assessment Marks")

student_count = st.number_input(
    "Number of Students",
    min_value=1,
    max_value=500,
    value=10,
    step=1,
    key=f"student_count_{reset_id}"
)

student_count = int(student_count)

st.write(
    "Enter the raw marks obtained by each student. "
    "Student names are not required."
)

marks_df = pd.DataFrame({
    "Student": [
        f"Student {i}"
        for i in range(1, student_count + 1)
    ],
    "PA1": [0.0] * student_count,
    "PA2": [0.0] * student_count,
    "LE1": [0.0] * student_count,
    "LE2": [0.0] * student_count
})

marks_column_config = {
    "Student": st.column_config.TextColumn(
        "Student",
        disabled=True
    )
}

for assessment in ASSESSMENTS:

    marks_column_config[assessment] = (
        st.column_config.NumberColumn(
            assessment,
            min_value=0.0,
            step=1.0,
            format="%.2f"
        )
    )

student_marks = st.data_editor(
    marks_df,
    key=f"student_marks_{reset_id}_{student_count}",
    hide_index=True,
    width="stretch",
    disabled=["Student"],
    column_config=marks_column_config
)

# =========================================================
# 10. CALCULATION BUTTON
# =========================================================

st.header("8. Calculate CO and PO Attainment")

calculate_button = st.button(
    "Calculate CO–PO Attainment",
    type="primary",
    width="stretch"
)

# =========================================================
# 11. EXCEL DOWNLOAD FUNCTION
# =========================================================

def create_excel_download(sheets):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        for sheet_name, dataframe in sheets.items():

            dataframe.to_excel(
                writer,
                sheet_name=sheet_name[:31],
                index=True
            )

    output.seek(0)

    return output

# =========================================================
# 12. CALCULATIONS
# =========================================================

if calculate_button:

    errors = []

    # ---------------------------------------------
    # Course details validation
    # ---------------------------------------------

    if not selected_department:
        errors.append("Enter or select a department.")

    if not course_name.strip():
        errors.append("Enter the course name.")

    if not course_code.strip():
        errors.append("Enter the course code.")

    # ---------------------------------------------
    # Assessment values
    # ---------------------------------------------

    assessment_weights = pd.to_numeric(
        assessment_matrix["Assessment Weight"],
        errors="coerce"
    ).fillna(0)

    maximum_marks = pd.to_numeric(
        assessment_matrix["Maximum Marks"],
        errors="coerce"
    ).fillna(0)

    if (assessment_weights < 0).any():
        errors.append("Assessment weights cannot be negative.")

    if (maximum_marks < 0).any():
        errors.append("Maximum marks cannot be negative.")

    if (co_weights < 0).any():
        errors.append("CO weights cannot be negative.")

    if (po_weights < 0).any():
        errors.append("PO weights cannot be negative.")

    # ---------------------------------------------
    # Validate coverage and maximum marks
    # ---------------------------------------------

    for _, row in assessment_matrix.iterrows():

        assessment = row["Assessment"]
        weight = float(row["Assessment Weight"])
        max_mark = float(row["Maximum Marks"])

        covered_cos = [
            co for co in CO_NAMES
            if bool(row[co])
        ]

        if weight > 0 and max_mark <= 0:
            errors.append(
                f"Enter positive maximum marks for {assessment}."
            )

        if weight > 0 and not covered_cos:
            errors.append(
                f"Select at least one CO for {assessment}."
            )

        if weight > 0 and covered_cos:

            denominator = sum(
                co_weights[co] for co in covered_cos
            )

            if denominator <= 0:
                errors.append(
                    f"The selected COs for {assessment} "
                    "must have positive total CO weight."
                )

    # ---------------------------------------------
    # Validate student marks
    # ---------------------------------------------

    for assessment in ASSESSMENTS:

        max_mark = float(
            maximum_marks[
                assessment_matrix["Assessment"] == assessment
            ].iloc[0]
        )

        if (student_marks[assessment] < 0).any():
            errors.append(
                f"{assessment} marks cannot be negative."
            )

        if max_mark > 0:

            if (student_marks[assessment] > max_mark).any():
                errors.append(
                    f"{assessment} marks exceed maximum marks."
                )

    # ---------------------------------------------
    # Validate mapping
    # ---------------------------------------------

    if (mapping_values < 0).any().any():
        errors.append("CO–PO mapping values cannot be negative.")

    if errors:

        for error in errors:
            st.error(error)

        st.stop()

    # =================================================
    # 13. ASSESSMENT–CO ALLOCATION MATRIX
    # =================================================

    allocation_matrix = pd.DataFrame(
        0.0,
        index=ASSESSMENTS,
        columns=CO_NAMES
    )

    for _, row in assessment_matrix.iterrows():

        assessment = row["Assessment"]
        weight = float(row["Assessment Weight"])

        covered_cos = [
            co for co in CO_NAMES
            if bool(row[co])
        ]

        if weight > 0 and covered_cos:

            denominator = sum(
                co_weights[co] for co in covered_cos
            )

            for co in covered_cos:

                allocation_matrix.loc[assessment, co] = (
                    weight
                    * co_weights[co]
                    / denominator
                )

    st.subheader("Assessment–CO Allocation Matrix")

    st.dataframe(
        allocation_matrix.round(2),
        width="stretch"
    )

    # =================================================
    # 14. RAW MARKS TO PERCENTAGES
    # =================================================

    student_percentages = pd.DataFrame(
        index=student_marks.index
    )

    student_percentages["Student"] = (
        student_marks["Student"]
    )

    for assessment in ASSESSMENTS:

        max_mark = float(
            maximum_marks[
                assessment_matrix["Assessment"] == assessment
            ].iloc[0]
        )

        if max_mark > 0:

            student_percentages[assessment] = (
                student_marks[assessment] / max_mark
            ) * 100

        else:

            student_percentages[assessment] = float("nan")

    st.subheader("Student Assessment Percentage")

    st.dataframe(
        student_percentages,
        width="stretch"
    )

    # =================================================
    # 15. STUDENT-WISE CO ATTAINMENT
    # =================================================

    student_co_attainment = pd.DataFrame(
        index=student_marks.index
    )

    student_co_attainment["Student"] = (
        student_marks["Student"]
    )

    for co in CO_NAMES:

        total_allocated_weight = (
            allocation_matrix[co].sum()
        )

        if total_allocated_weight > 0:

            weighted_scores = pd.Series(
                0.0,
                index=student_marks.index
            )

            for assessment in ASSESSMENTS:

                allocated_weight = (
                    allocation_matrix.loc[assessment, co]
                )

                if allocated_weight > 0:

                    weighted_scores += (
                        student_percentages[assessment].fillna(0)
                        * allocated_weight
                    )

            student_co_attainment[co] = (
                weighted_scores / total_allocated_weight
            )

        else:

            student_co_attainment[co] = float("nan")

    st.subheader("Student-wise CO Attainment (%)")

    st.dataframe(
        student_co_attainment,
        width="stretch"
    )

    # =================================================
    # 16. CO SUMMARY
    # =================================================

    co_summary = pd.DataFrame({
        "CO": CO_NAMES,
        "CO Weight": [
            co_weights[co] for co in CO_NAMES
        ],
        "Allocated Assessment Weight": [
            allocation_matrix[co].sum()
            for co in CO_NAMES
        ],
        "CO Attainment (%)": [
            student_co_attainment[co].mean()
            for co in CO_NAMES
        ]
    })

    co_summary["CO Attainment (%)"] = (
        co_summary["CO Attainment (%)"].round(2)
    )

    st.subheader("CO Attainment Summary")

    st.dataframe(
        co_summary,
        hide_index=True,
        width="stretch"
    )

    # =================================================
    # 17. CO–PO CONTRIBUTION MATRIX
    # =================================================

    co_po_matrix = pd.DataFrame(
        index=CO_NAMES,
        columns=PO_NAMES,
        dtype=float
    )

    for co in CO_NAMES:

        attainment = co_summary.loc[
            co_summary["CO"] == co,
            "CO Attainment (%)"
        ].iloc[0]

        for po in PO_NAMES:

            mapping = mapping_values.loc[co, po]

            if pd.notna(attainment):
                co_po_matrix.loc[co, po] = (
                    attainment * mapping
                )
            else:
                co_po_matrix.loc[co, po] = float("nan")

    st.subheader("CO–PO Weighted Contribution Matrix")

    st.dataframe(
        co_po_matrix.round(2),
        width="stretch"
    )

    # =================================================
    # 18. PO ATTAINMENT
    # =================================================

    po_attainment_values = {}

    for po in PO_NAMES:

        valid_cos = []

        for co in CO_NAMES:

            attainment = co_summary.loc[
                co_summary["CO"] == co,
                "CO Attainment (%)"
            ].iloc[0]

            mapping = mapping_values.loc[co, po]

            if pd.notna(attainment) and mapping > 0:

                valid_cos.append(
                    (attainment, mapping)
                )

        if valid_cos:

            numerator = sum(
                attainment * mapping
                for attainment, mapping in valid_cos
            )

            denominator = sum(
                mapping
                for _, mapping in valid_cos
            )

            po_attainment_values[po] = (
                numerator / denominator
            )

        else:

            po_attainment_values[po] = float("nan")

    po_summary = pd.DataFrame({
        "PO": PO_NAMES,
        "PO Weight": [
            po_weights[po] for po in PO_NAMES
        ],
        "PO Attainment (%)": [
            po_attainment_values[po]
            for po in PO_NAMES
        ]
    })

    po_summary["PO Attainment (%)"] = (
        po_summary["PO Attainment (%)"].round(2)
    )

    st.subheader("PO Attainment Summary")

    st.dataframe(
        po_summary,
        hide_index=True,
        width="stretch"
    )

    # =================================================
    # 19. OVERALL WEIGHTED PO ATTAINMENT
    # =================================================

    positive_weight_pos = [
        po for po in PO_NAMES
        if po_weights[po] > 0
    ]

    missing_pos = [
        po for po in positive_weight_pos
        if pd.isna(po_attainment_values[po])
    ]

    if not positive_weight_pos:

        overall_po_attainment = float("nan")

        st.warning(
            "Enter positive PO weights to calculate "
            "overall weighted PO attainment."
        )

    elif missing_pos:

        overall_po_attainment = float("nan")

        st.warning(
            "Overall attainment cannot be calculated. "
            "No valid attainment is available for: "
            + ", ".join(missing_pos)
        )

    else:

        total_po_weight = sum(
            po_weights[po]
            for po in positive_weight_pos
        )

        overall_po_attainment = sum(
            po_attainment_values[po] * po_weights[po]
            for po in positive_weight_pos
        ) / total_po_weight

        st.metric(
            "Overall Weighted PO Attainment (%)",
            f"{overall_po_attainment:.2f}%"
        )

    # =================================================
    # 20. FINAL SUMMARY MATRIX
    # =================================================

    st.header("9. Final CO–PO Summary Matrix")

    final_matrix = pd.DataFrame(
        index=CO_NAMES
    )

    final_matrix["CO Weight"] = [
        co_weights[co] for co in CO_NAMES
    ]

    final_matrix["Allocated Assessment Weight"] = [
        allocation_matrix[co].sum()
        for co in CO_NAMES
    ]

    final_matrix["CO Attainment (%)"] = [
        co_summary.loc[
            co_summary["CO"] == co,
            "CO Attainment (%)"
        ].iloc[0]
        for co in CO_NAMES
    ]

    for po in PO_NAMES:

        final_matrix[po + " Mapping"] = [
            mapping_values.loc[co, po]
            for co in CO_NAMES
        ]

        final_matrix[po + " Contribution"] = [
            co_po_matrix.loc[co, po]
            for co in CO_NAMES
        ]

    st.dataframe(
        final_matrix.round(2),
        width="stretch"
    )

    # =================================================
    # 21. COURSE SUMMARY
    # =================================================

    st.header("10. Course Summary")

    course_summary = pd.DataFrame({
        "Particulars": [
            "Department",
            "Course Name",
            "Course Code",
            "Semester",
            "Number of COs",
            "Number of Students",
            "Overall Weighted PO Attainment (%)"
        ],
        "Details": [
            selected_department,
            course_name,
            course_code,
            semester,
            number_of_cos,
            student_count,
            (
                round(overall_po_attainment, 2)
                if pd.notna(overall_po_attainment)
                else "N/A"
            )
        ]
    })

    st.dataframe(
        course_summary,
        hide_index=True,
        width="stretch"
    )

    # =================================================
    # 22. DOWNLOAD EXCEL REPORT
    # =================================================

    st.header("11. Download Results")

    excel_sheets = {
        "Course Details": course_summary.set_index(
            "Particulars"
        ),
        "CO Weights": co_weights_table.set_index(
            "Course Outcome"
        ),
        "Assessment Coverage": assessment_matrix.set_index(
            "Assessment"
        ),
        "Assessment CO Allocation": allocation_matrix,
        "Student Percentages": student_percentages.set_index(
            "Student"
        ),
        "Student CO Attainment": student_co_attainment.set_index(
            "Student"
        ),
        "CO Summary": co_summary.set_index("CO"),
        "CO PO Mapping": mapping_values,
        "CO PO Contribution": co_po_matrix,
        "PO Summary": po_summary.set_index("PO"),
        "Final Summary": final_matrix
    }

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        for sheet_name, dataframe in excel_sheets.items():

            dataframe.to_excel(
                writer,
                sheet_name=sheet_name[:31],
                index=True
            )

    output.seek(0)

    st.download_button(
        label="📥 Download Complete Excel Report",
        data=output,
        file_name="CO_PO_Assessment_Summary.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        width="stretch"
    )

    # =================================================
    # 23. DOWNLOAD CSV
    # =================================================

    csv_data = final_matrix.to_csv().encode("utf-8")

    st.download_button(
        label="📥 Download Final Summary as CSV",
        data=csv_data,
        file_name="CO_PO_Final_Summary.csv",
        mime="text/csv",
        width="stretch"
    )

    st.success(
        "CO–PO assessment calculations completed successfully."
    )
