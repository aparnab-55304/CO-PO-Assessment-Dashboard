
import streamlit as st
import pandas as pd
import numpy as np
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
st.caption(
    "Automated Course Outcome and Programme Outcome Assessment"
)

# =========================================================
# 2. SESSION STATE AND RESET
# =========================================================

if "reset_count" not in st.session_state:
    st.session_state.reset_count = 0

if st.button("🔄 Reset Dashboard"):
    st.session_state.reset_count += 1
    st.rerun()

reset_id = st.session_state.reset_count

# =========================================================
# 3. EXCEL UPLOAD
# =========================================================

st.header("1. Upload Course Information")

uploaded_file = st.file_uploader(
    "Upload Course Group Excel File",
    type=["xlsx", "xls"],
    key=f"course_upload_{reset_id}"
)

if uploaded_file is None:
    st.info("Please upload the Course_Group_Dummy.xlsx file.")
    st.stop()


@st.cache_data
def load_course_data(file_bytes):

    excel_file = BytesIO(file_bytes)

    # The supplied workbook has its headers in row 2.
    df = pd.read_excel(
        excel_file,
        sheet_name=0,
        header=1
    )

    df.columns = df.columns.astype(str).str.strip()

    # Fallback if the workbook uses row 1 as the header.
    if "Program Code" not in df.columns:
        df = pd.read_excel(
            BytesIO(file_bytes),
            sheet_name=0,
            header=0
        )
        df.columns = df.columns.astype(str).str.strip()

    return df


try:
    course_data = load_course_data(uploaded_file.getvalue())

except Exception as e:
    st.error(f"Unable to read the Excel file: {e}")
    st.stop()


# =========================================================
# 4. IDENTIFY EXCEL COLUMNS
# =========================================================

required_columns = [
    "Program Code",
    "Program"
]

missing_columns = [
    col for col in required_columns
    if col not in course_data.columns
]

if missing_columns:
    st.error(
        "The uploaded Excel file is missing these columns: "
        + ", ".join(missing_columns)
    )
    st.stop()


# Department column
if "Handling Department" in course_data.columns:
    department_column = "Handling Department"

elif "Teaching Department" in course_data.columns:
    department_column = "Teaching Department"

else:
    st.error("Department column not found in the uploaded file.")
    st.stop()


# Clean important fields
course_data = course_data.dropna(
    subset=["Program Code", "Program", department_column]
).copy()

for col in ["Program Code", "Program", department_column]:
    course_data[col] = course_data[col].astype(str).str.strip()


# =========================================================
# 5. COURSE SELECTION
# =========================================================

st.header("2. Course Details")

col1, col2 = st.columns(2)

with col1:

    departments = sorted(
        course_data[department_column].unique().tolist()
    )

    selected_department = st.selectbox(
        "Select Department",
        departments,
        key=f"department_{reset_id}"
    )

    department_data = course_data[
        course_data[department_column] == selected_department
    ].copy()

    course_names = sorted(
        department_data["Program"].unique().tolist()
    )

    selected_course_name = st.selectbox(
        "Select Course Name",
        course_names,
        key=f"course_name_{reset_id}"
    )


with col2:

    name_data = department_data[
        department_data["Program"] == selected_course_name
    ].copy()

    course_codes = sorted(
        name_data["Program Code"].unique().tolist()
    )

    selected_course_code = st.selectbox(
        "Select Course Code",
        course_codes,
        key=f"course_code_{reset_id}"
    )

    # Semester selection
    if "Semester" in course_data.columns:

        semester_values = (
            course_data["Semester"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        semester_values = sorted(semester_values)

        selected_semester = st.selectbox(
            "Select Semester",
            semester_values,
            key=f"semester_{reset_id}"
        )

    else:

        selected_semester = st.selectbox(
            "Select Semester",
            [f"Semester {i}" for i in range(1, 9)],
            key=f"semester_{reset_id}"
        )


selected_course_data = name_data[
    name_data["Program Code"] == selected_course_code
].copy()


# If Semester exists, filter the selected semester when possible.
if "Semester" in selected_course_data.columns:

    semester_filtered = selected_course_data[
        selected_course_data["Semester"].astype(str)
        == str(selected_semester)
    ]

    if not semester_filtered.empty:
        selected_course_data = semester_filtered


if selected_course_data.empty:
    st.error("No matching course record was found.")
    st.stop()


course_record = selected_course_data.iloc[0]


# =========================================================
# 6. DISPLAY COURSE INFORMATION
# =========================================================

st.subheader("Selected Course Information")

info1, info2, info3 = st.columns(3)

info1.metric("Department", selected_department)
info2.metric("Course Code", selected_course_code)
info3.metric("Semester", selected_semester)

st.write("**Course Name:**", selected_course_name)


# =========================================================
# 7. DETERMINE NUMBER OF COs
# =========================================================

st.header("3. Course Outcomes")

if "CO" in selected_course_data.columns:

    co_value = pd.to_numeric(
        selected_course_data["CO"],
        errors="coerce"
    ).dropna()

    if not co_value.empty:
        number_of_cos = int(co_value.iloc[0])
    else:
        number_of_cos = 0

else:
    number_of_cos = 0


if number_of_cos <= 0:

    st.warning(
        "The selected course has no CO count in the Excel file. "
        "Please enter the number of COs manually."
    )

    number_of_cos = st.number_input(
        "Enter Number of Course Outcomes",
        min_value=1,
        max_value=15,
        value=4,
        step=1,
        key=f"manual_cos_{reset_id}"
    )

else:

    st.success(
        f"Number of Course Outcomes identified from Excel: "
        f"{number_of_cos}"
    )


number_of_cos = int(number_of_cos)

CO_NAMES = [
    f"CO{i}" for i in range(1, number_of_cos + 1)
]

PO_NAMES = ["PO1", "PO2"]

ASSESSMENTS = ["PA1", "PA2", "LE1", "LE2"]


# =========================================================
# 8. CO WEIGHTS
# =========================================================

st.header("4. CO Weight Allocation")

st.write(
    "Enter the weight assigned to each Course Outcome."
)

co_weight_df = pd.DataFrame({
    "Course Outcome": CO_NAMES,
    "CO Weight": [0.0] * number_of_cos
})

co_weights_table = st.data_editor(
    co_weight_df,
    key=f"co_weights_{reset_id}_{selected_course_code}",
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

st.caption(
    f"Total CO Weight: {co_weights.sum():.2f}"
)


# =========================================================
# 9. ASSESSMENT COVERAGE AND WEIGHTS
# =========================================================

st.header("5. Assessment–CO Coverage Matrix")

st.write(
    "Enter the assessment weight and select the COs covered "
    "by each assessment. All values are editable."
)

assessment_rows = []

for assessment in ASSESSMENTS:

    row = {
        "Assessment": assessment,
        "Assessment Weight": 0.0,
        "Maximum Marks": 0.0
    }

    for co in CO_NAMES:
        row[co] = 0

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
    key=f"assessment_matrix_{reset_id}_{selected_course_code}_{number_of_cos}",
    hide_index=True,
    width="stretch",
    disabled=["Assessment"],
    column_config=assessment_column_config
)


# =========================================================
# 10. DISPLAY WEIGHT TOTALS
# =========================================================

assessment_weight_total = pd.to_numeric(
    assessment_matrix["Assessment Weight"],
    errors="coerce"
).fillna(0).sum()

st.metric(
    "Total Assessment Weight",
    f"{assessment_weight_total:.2f}"
)


# =========================================================
# 11. CO–PO MAPPING MATRIX
# =========================================================

st.header("6. CO–PO Mapping Matrix")

st.write(
    "Enter the mapping strength between each CO and PO. "
    "Use 0 for no mapping and positive values for mapped outcomes."
)

mapping_df = pd.DataFrame({
    "Course Outcome": CO_NAMES,
    "PO1": [0.0] * number_of_cos,
    "PO2": [0.0] * number_of_cos
})

mapping_table = st.data_editor(
    mapping_df,
    key=f"mapping_{reset_id}_{selected_course_code}_{number_of_cos}",
    hide_index=True,
    width="stretch",
    disabled=["Course Outcome"],
    column_config={
        "Course Outcome": st.column_config.TextColumn(
            "Course Outcome",
            disabled=True
        ),
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
# 12. PO WEIGHTS
# =========================================================

st.header("7. Programme Outcome Weights")

po_weight_df = pd.DataFrame({
    "Programme Outcome": PO_NAMES,
    "PO Weight": [0.0, 0.0]
})

po_weight_table = st.data_editor(
    po_weight_df,
    key=f"po_weights_{reset_id}_{selected_course_code}",
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

st.caption(
    f"Total PO Weight: {po_weights.sum():.2f}"
)


# =========================================================
# 13. STUDENT MARKS INPUT
# =========================================================

st.header("8. Student Assessment Marks")

student_count = st.number_input(
    "Enter Number of Students",
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
        f"Student {i}" for i in range(1, student_count + 1)
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
    key=f"student_marks_{reset_id}_{selected_course_code}_{student_count}",
    hide_index=True,
    width="stretch",
    disabled=["Student"],
    column_config=marks_column_config
)


# =========================================================
# 14. CALCULATE ASSESSMENT PERCENTAGES
# =========================================================

st.header("9. Calculate CO and PO Attainment")

calculate_button = st.button(
    "Calculate CO–PO Attainment",
    type="primary",
    width="stretch"
)


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


if calculate_button:

    errors = []

    # ---------------------------------------------
    # Validate CO weights
    # ---------------------------------------------

    if (co_weights < 0).any():
        errors.append("CO weights cannot be negative.")

    # ---------------------------------------------
    # Validate assessment weights
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

    # ---------------------------------------------
    # Validate student marks
    # ---------------------------------------------

    for assessment in ASSESSMENTS:

        max_mark = maximum_marks[
            assessment_matrix["Assessment"] == assessment
        ].iloc[0]

        if max_mark <= 0:
            if assessment_weights[
                assessment_matrix["Assessment"] == assessment
            ].iloc[0] > 0:
                errors.append(
                    f"Enter a positive maximum mark for {assessment}."
                )

        else:

            if (
                student_marks[assessment] < 0
            ).any():
                errors.append(
                    f"{assessment} marks cannot be negative."
                )

            if (
                student_marks[assessment] > max_mark
            ).any():
                errors.append(
                    f"Some {assessment} marks exceed the maximum marks."
                )

    # ---------------------------------------------
    # Validate assessment coverage
    # ---------------------------------------------

    for _, row in assessment_matrix.iterrows():

        if row["Assessment Weight"] > 0:

            covered = [
                co for co in CO_NAMES
                if bool(row[co])
            ]

            if len(covered) == 0:

                errors.append(
                    f"{row['Assessment']} has a positive weight "
                    "but no CO has been selected."
                )

            elif sum(
                co_weights[co] for co in covered
            ) <= 0:

                errors.append(
                    f"{row['Assessment']} covers COs whose "
                    "total CO weight is zero."
                )

    # ---------------------------------------------
    # Validate PO weights and mapping
    # ---------------------------------------------

    if (po_weights < 0).any():
        errors.append("PO weights cannot be negative.")

    if errors:

        for error in errors:
            st.error(error)

        st.stop()

    # =====================================================
    # 15. ASSESSMENT–CO ALLOCATION MATRIX
    # =====================================================

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

            if denominator > 0:

                for co in covered_cos:

                    allocation_matrix.loc[
                        assessment, co
                    ] = (
                        weight
                        * co_weights[co]
                        / denominator
                    )

    st.subheader("Assessment–CO Allocation Matrix")

    st.dataframe(
        allocation_matrix,
        width="stretch"
    )

    # =====================================================
    # 16. STUDENT MARKS TO PERCENTAGES
    # =====================================================

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

            student_percentages[assessment] = np.nan

    st.subheader("Student Assessment Percentage")

    st.dataframe(
        student_percentages,
        width="stretch"
    )

    # =====================================================
    # 17. STUDENT-WISE CO ATTAINMENT
    # =====================================================

    student_co_attainment = pd.DataFrame(
        index=student_marks.index
    )

    student_co_attainment["Student"] = (
        student_marks["Student"]
    )

    for co in CO_NAMES:

        allocated_weights = allocation_matrix[co]

        total_allocated_weight = allocated_weights.sum()

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
                        student_percentages[assessment]
                        .fillna(0)
                        * allocated_weight
                    )

            student_co_attainment[co] = (
                weighted_scores / total_allocated_weight
            )

        else:

            student_co_attainment[co] = np.nan

    st.subheader("Student-wise CO Attainment (%)")

    st.dataframe(
        student_co_attainment,
        width="stretch"
    )

    # =====================================================
    # 18. CO SUMMARY
    # =====================================================

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

    # =====================================================
    # 19. CO–PO CONTRIBUTION MATRIX
    # =====================================================

    co_po_matrix = pd.DataFrame(
        index=CO_NAMES,
        columns=PO_NAMES,
        dtype=float
    )

    for co in CO_NAMES:

        co_attainment = (
            co_summary.loc[
                co_summary["CO"] == co,
                "CO Attainment (%)"
            ].iloc[0]
        )

        for po in PO_NAMES:

            mapping_value = mapping_values.loc[co, po]

            if pd.notna(co_attainment):

                co_po_matrix.loc[co, po] = (
                    co_attainment * mapping_value
                )

            else:

                co_po_matrix.loc[co, po] = np.nan

    st.subheader("CO–PO Weighted Contribution Matrix")

    st.dataframe(
        co_po_matrix.round(2),
        width="stretch"
    )

    # =====================================================
    # 20. PO ATTAINMENT
    # =====================================================

    po_attainment_values = {}

    for po in PO_NAMES:

        valid_cos = []

        for co in CO_NAMES:

            attainment = co_summary.loc[
                co_summary["CO"] == co,
                "CO Attainment (%)"
            ].iloc[0]

            mapping = mapping_values.loc[co, po]

            if (
                pd.notna(attainment)
                and mapping > 0
            ):

                valid_cos.append((attainment, mapping))

        if valid_cos:

            numerator = sum(
                attainment * mapping
                for attainment, mapping in valid_cos
            )

            denominator = sum(
                mapping for _, mapping in valid_cos
            )

            po_attainment_values[po] = (
                numerator / denominator
            )

        else:

            po_attainment_values[po] = np.nan

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

    # =====================================================
    # 21. OVERALL WEIGHTED PO ATTAINMENT
    # =====================================================

    positive_weight_pos = [
        po for po in PO_NAMES
        if po_weights[po] > 0
    ]

    missing_pos = [
        po for po in positive_weight_pos
        if pd.isna(po_attainment_values[po])
    ]

    if not positive_weight_pos:

        overall_po_attainment = np.nan

        st.warning(
            "Enter positive PO weights to calculate "
            "overall weighted PO attainment."
        )

    elif missing_pos:

        overall_po_attainment = np.nan

        st.warning(
            "Overall PO attainment cannot be calculated because "
            + ", ".join(missing_pos)
            + " has a positive weight but no valid attainment."
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

    # =====================================================
    # 22. FINAL SUMMARY MATRIX
    # =====================================================

    st.header("10. Final CO–PO Summary Matrix")

    final_matrix = pd.DataFrame(
        index=CO_NAMES
    )

    final_matrix["CO Weight"] = [
        co_weights[co] for co in CO_NAMES
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

    # =====================================================
    # 23. DOWNLOAD RESULTS
    # =====================================================

    st.header("11. Download Assessment Results")

    excel_sheets = {
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

    excel_file = create_excel_download(excel_sheets)

    st.download_button(
        label="📥 Download Complete Excel Report",
        data=excel_file,
        file_name="CO_PO_Assessment_Summary.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        width="stretch"
    )

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

