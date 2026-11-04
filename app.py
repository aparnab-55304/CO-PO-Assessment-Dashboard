
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
st.caption("Automated Course Outcome and Programme Outcome Summary")

# =========================================================
# SESSION STATE
# =========================================================

if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

if "student_count" not in st.session_state:
    st.session_state.student_count = 5

if st.button("Reset Dashboard", type="secondary"):
    st.session_state.reset_counter += 1
    st.rerun()

reset_id = st.session_state.reset_counter

st.divider()

# =========================================================
# 1. UPLOAD COURSE EXCEL FILE
# =========================================================

st.header("1. Upload Course Excel File")

uploaded_file = st.file_uploader(
    "Upload Course_Group_Dummy.xlsx",
    type=["xlsx"],
    key=f"course_file_{reset_id}"
)

if uploaded_file is None:
    st.info("Upload the course Excel file to continue.")
    st.stop()

try:
    course_df = pd.read_excel(
        uploaded_file,
        sheet_name=0,
        header=1
    )

except Exception as e:
    st.error(f"Unable to read the Excel file: {e}")
    st.stop()

required_columns = [
    "Program Code",
    "Program",
    "Handling Department",
    "Credit",
    "CO"
]

missing_columns = [
    col for col in required_columns
    if col not in course_df.columns
]

if missing_columns:
    st.error(
        "The uploaded Excel file is missing these columns: "
        + ", ".join(missing_columns)
    )
    st.stop()

course_df = course_df.dropna(
    subset=["Program Code", "Program"]
).copy()

course_df["CO"] = pd.to_numeric(
    course_df["CO"],
    errors="coerce"
).fillna(0)

course_df["CO"] = course_df["CO"].astype(int)

course_df = course_df.reset_index(drop=True)

# Unique labels even when program codes are repeated
course_options = {}

for index, row in course_df.iterrows():

    label = (
        f"{row['Program Code']} | "
        f"{row['Program']} | "
        f"{row['Handling Department']} | "
        f"Row {index + 1}"
    )

    course_options[label] = index

selected_course_label = st.selectbox(
    "Select Course",
    list(course_options.keys()),
    key=f"selected_course_{reset_id}"
)

selected_course = course_df.loc[
    course_options[selected_course_label]
]

course_code = selected_course["Program Code"]
course_name = selected_course["Program"]
department = selected_course["Handling Department"]

excel_co_count = int(selected_course["CO"])

st.subheader("Selected Course Details")

detail_col1, detail_col2, detail_col3 = st.columns(3)

detail_col1.metric("Program Code", str(course_code))
detail_col2.metric("Course Credits", str(selected_course["Credit"]))
detail_col3.metric("COs in Excel", excel_co_count)

st.write("**Course:**", course_name)
st.write("**Handling Department:**", department)

# Allow manual CO count if Excel has zero or invalid CO count
if excel_co_count > 0:
    number_of_cos = excel_co_count

else:
    st.warning(
        "The selected course has zero COs in the uploaded file. "
        "Enter the number of COs manually."
    )

    number_of_cos = st.number_input(
        "Number of Course Outcomes",
        min_value=1,
        max_value=15,
        value=4,
        step=1,
        key=f"manual_co_count_{reset_id}"
    )

number_of_cos = int(number_of_cos)

CO_NAMES = [
    f"CO{i+1}" for i in range(number_of_cos)
]

PO_NAMES = ["PO1", "PO2"]

ASSESSMENTS = ["PA1", "PA2", "LE1", "LE2"]

st.divider()

# =========================================================
# 2. CO AND PO WEIGHTS
# =========================================================

st.header("2. CO and PO Weights")

st.caption(
    "Enter all weights here. They remain displayed together "
    "with the assessment matrix below."
)

weight_col1, weight_col2 = st.columns(2)

# ---------------- CO WEIGHTS ----------------

with weight_col1:

    st.subheader("Course Outcome Weights")

    co_weight_data = pd.DataFrame({
        "CO": CO_NAMES,
        "Weight": [0.0] * number_of_cos
    })

    co_weight_input = st.data_editor(
        co_weight_data,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        key=f"co_weights_{reset_id}",
        column_config={
            "CO": st.column_config.TextColumn(
                "Course Outcome",
                disabled=True
            ),
            "Weight": st.column_config.NumberColumn(
                "CO Weight",
                min_value=0.0,
                step=1.0
            )
        }
    )

co_weights = dict(
    zip(
        co_weight_input["CO"],
        co_weight_input["Weight"].astype(float)
    )
)

total_co_weight = sum(co_weights.values())

with weight_col1:
    st.metric(
        "Total CO Weight",
        f"{total_co_weight:.2f}"
    )

# ---------------- PO WEIGHTS ----------------

with weight_col2:

    st.subheader("Programme Outcome Weights")

    po_weight_data = pd.DataFrame({
        "PO": PO_NAMES,
        "Weight": [0.0, 0.0]
    })

    po_weight_input = st.data_editor(
        po_weight_data,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        key=f"po_weights_{reset_id}",
        column_config={
            "PO": st.column_config.TextColumn(
                "Programme Outcome",
                disabled=True
            ),
            "Weight": st.column_config.NumberColumn(
                "PO Weight",
                min_value=0.0,
                step=1.0
            )
        }
    )

po_weights = dict(
    zip(
        po_weight_input["PO"],
        po_weight_input["Weight"].astype(float)
    )
)

total_po_weight = sum(po_weights.values())

with weight_col2:
    st.metric(
        "Total PO Weight",
        f"{total_po_weight:.2f}"
    )

st.caption(
    "CO weights distribute assessment marks among COs. "
    "PO weights determine the relative contribution of PO1 and PO2 "
    "to the overall weighted PO attainment."
)

st.divider()

# =========================================================
# 3. ASSESSMENT COVERAGE AND WEIGHTS IN ONE GRID
# =========================================================

st.header("3. Assessment–CO Matrix")

st.write(
    "Select the COs covered by each assessment and enter "
    "the assessment weight in the same grid."
)

st.caption(
    "Enter 1 if the assessment covers the CO and 0 if it does not."
)

default_assessment_matrix = pd.DataFrame(
    {
        "Assessment": ASSESSMENTS,
        "Weight": [0.0, 0.0, 0.0, 0.0],
        **{
            co: [0, 0, 1, 1]
            if i >= 2 else
            ([1, 1, 0, 0] if i == 0 else [0, 0, 1, 1])
            for i, co in enumerate(CO_NAMES)
        }
    }
)

# Clear default pattern for PA1 and PA2:
# PA1 -> CO1 and CO2
# PA2 -> CO3 and CO4 (where available)
# LE1 and LE2 -> all COs

for co_index, co in enumerate(CO_NAMES):

    default_assessment_matrix.loc[
        default_assessment_matrix["Assessment"] == "PA1",
        co
    ] = 1 if co_index < 2 else 0

    default_assessment_matrix.loc[
        default_assessment_matrix["Assessment"] == "PA2",
        co
    ] = 1 if co_index >= 2 else 0

    default_assessment_matrix.loc[
        default_assessment_matrix["Assessment"].isin(["LE1", "LE2"]),
        co
    ] = 1

assessment_matrix = st.data_editor(
    default_assessment_matrix,
    width="stretch",
    hide_index=True,
    num_rows="fixed",
    key=f"assessment_matrix_{reset_id}",
    column_config={
        "Assessment": st.column_config.TextColumn(
            "Assessment",
            disabled=True
        ),
        "Weight": st.column_config.NumberColumn(
            "Assessment Weight",
            min_value=0.0,
            step=1.0
        ),
        **{
            co: st.column_config.NumberColumn(
                co,
                min_value=0,
                max_value=1,
                step=1
            )
            for co in CO_NAMES
        }
    }
)

assessment_weights = dict(
    zip(
        assessment_matrix["Assessment"],
        assessment_matrix["Weight"].astype(float)
    )
)

total_assessment_weight = sum(
    assessment_weights.values()
)

st.metric(
    "Total Assessment Weight",
    f"{total_assessment_weight:.2f}"
)

# Validate assessment coverage
coverage_values = assessment_matrix[CO_NAMES].apply(
    pd.to_numeric,
    errors="coerce"
)

coverage_valid = (
    not coverage_values.isna().any().any()
    and coverage_values.isin([0, 1]).all().all()
)

if not coverage_valid:
    st.error(
        "Coverage values must contain only 0 or 1."
    )

# =========================================================
# 4. AUTOMATIC ASSESSMENT-CO ALLOCATION
# =========================================================

st.header("4. Automatic Assessment–CO Allocation")

allocation = pd.DataFrame(
    0.0,
    index=ASSESSMENTS,
    columns=CO_NAMES
)

allocation_valid = (
    coverage_valid
    and total_co_weight > 0
)

if total_co_weight <= 0:
    st.warning(
        "Enter positive CO weights to calculate the allocation matrix."
    )

if allocation_valid:

    for _, row in assessment_matrix.iterrows():

        assessment = row["Assessment"]

        denominator = sum(
            float(row[co]) * co_weights[co]
            for co in CO_NAMES
        )

        if assessment_weights[assessment] > 0 and denominator == 0:
            allocation_valid = False

            st.error(
                f"{assessment} has a positive weight but no covered "
                "CO with a positive CO weight."
            )

            continue

        if denominator > 0:

            for co in CO_NAMES:

                allocation.loc[assessment, co] = (
                    assessment_weights[assessment]
                    * float(row[co])
                    * co_weights[co]
                    / denominator
                )

if allocation_valid:

    st.subheader("Calculated Assessment–CO Allocation Matrix")

    st.dataframe(
        allocation.round(3),
        width="stretch"
    )

    co_allocated = allocation.sum(axis=0)

    allocation_summary = pd.DataFrame({
        "CO": CO_NAMES,
        "CO Weight": [
            co_weights[co] for co in CO_NAMES
        ],
        "Allocated Marks": [
            co_allocated[co] for co in CO_NAMES
        ]
    })

    st.subheader("CO Allocation Summary")

    st.dataframe(
        allocation_summary.round(3),
        width="stretch",
        hide_index=True
    )

st.divider()

# =========================================================
# 5. CO-PO MAPPING MATRIX
# =========================================================

st.header("5. CO–PO Mapping Matrix")

st.caption(
    "0 = No relationship | 1 = Low | 2 = Medium | 3 = High"
)

mapping_data = pd.DataFrame({
    "CO": CO_NAMES,
    **{
        po: [0] * number_of_cos
        for po in PO_NAMES
    }
})

mapping_input = st.data_editor(
    mapping_data,
    width="stretch",
    hide_index=True,
    num_rows="fixed",
    key=f"mapping_{reset_id}",
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

st.divider()

# =========================================================
# 6. STUDENT MARKS
# =========================================================

st.header("6. Student Assessment Marks")

st.write(
    "Enter raw marks obtained by students. "
    "The dashboard converts them into percentages."
)

max_col, count_col = st.columns(2)

with max_col:

    st.subheader("Maximum Marks")

    max_marks = {}

    max_marks_data = pd.DataFrame({
        "Assessment": ASSESSMENTS,
        "Maximum Marks": [100.0] * 4
    })

    max_marks_input = st.data_editor(
        max_marks_data,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        key=f"max_marks_{reset_id}",
        column_config={
            "Assessment": st.column_config.TextColumn(
                disabled=True
            ),
            "Maximum Marks": st.column_config.NumberColumn(
                min_value=0.01,
                step=1.0
            )
        }
    )

    max_marks = dict(
        zip(
            max_marks_input["Assessment"],
            max_marks_input["Maximum Marks"].astype(float)
        )
    )

with count_col:

    st.subheader("Student Count")

    number_of_students = st.number_input(
        "Number of Students",
        min_value=1,
        max_value=200,
        value=5,
        step=1,
        key=f"student_count_{reset_id}"
    )

number_of_students = int(number_of_students)

student_data = pd.DataFrame({
    "Student": [
        f"Student {i+1}"
        for i in range(number_of_students)
    ],
    **{
        assessment: [0.0] * number_of_students
        for assessment in ASSESSMENTS
    }
})

student_input = st.data_editor(
    student_data,
    width="stretch",
    hide_index=True,
    num_rows="fixed",
    key=f"student_marks_{reset_id}",
    column_config={
        "Student": st.column_config.TextColumn(
            "Student",
            required=True
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
# 7. RAW MARKS TO PERCENTAGES
# =========================================================

student_percentages = student_input.copy()

marks_valid = True

for assessment in ASSESSMENTS:

    raw = pd.to_numeric(
        student_input[assessment],
        errors="coerce"
    )

    if raw.isna().any():
        marks_valid = False
        st.error(f"Invalid marks in {assessment}.")
        continue

    if (
        (raw < 0).any()
        or (raw > max_marks[assessment]).any()
    ):
        marks_valid = False
        st.error(
            f"{assessment} marks must be between 0 and "
            f"{max_marks[assessment]}."
        )
        continue

    student_percentages[assessment] = (
        raw / max_marks[assessment] * 100
    )

if marks_valid:

    st.subheader("Converted Student Marks (%)")

    st.dataframe(
        student_percentages.round(2),
        width="stretch",
        hide_index=True
    )

st.divider()

# =========================================================
# 8. STUDENT-WISE CO ATTAINMENT
# =========================================================

st.header("7. Student-wise CO Attainment")

calculations_valid = (
    allocation_valid
    and coverage_valid
    and marks_valid
    and mapping_valid
)

if calculations_valid:

    student_co_results = []

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

    average_co = co_results[CO_NAMES].mean()

    co_summary = pd.DataFrame({
        "CO": CO_NAMES,
        "CO Weight": [
            co_weights[co] for co in CO_NAMES
        ],
        "Allocated Marks": [
            allocation[ASSESSMENTS][co].sum()
            for co in CO_NAMES
        ],
        "Average CO Attainment (%)": [
            average_co[co] for co in CO_NAMES
        ]
    })

    co_display = co_summary.copy()

    co_display["Average CO Attainment (%)"] = (
        co_display["Average CO Attainment (%)"].apply(
            lambda value:
            "N/A" if pd.isna(value)
            else round(value, 2)
        )
    )

    st.subheader("CO Summary Table")

    st.dataframe(
        co_display,
        width="stretch",
        hide_index=True
    )

else:

    st.warning(
        "Complete the weights, coverage, mapping and marks "
        "correctly to calculate attainment."
    )

st.divider()

# =========================================================
# 9. CO-PO MATRIX
# =========================================================

st.header("8. CO–PO Assessment Summary Matrix")

if calculations_valid:

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

    st.subheader("CO–PO Matrix")

    st.dataframe(
        co_po_matrix.round(2),
        width="stretch"
    )

    st.caption(
        "Each cell is calculated as CO attainment multiplied "
        "by the CO–PO mapping strength."
    )

# =========================================================
# 10. PO ATTAINMENT AND WEIGHTED SUMMARY
# =========================================================

    st.header("9. PO Attainment Summary")

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

    available_po_weight = sum(
        po_weights[po]
        for po in PO_NAMES
        if po_attainment[po] is not None
    )

    for po in PO_NAMES:

        if (
            po_attainment[po] is not None
            and available_po_weight > 0
        ):

            po_contribution[po] = (
                po_attainment[po]
                * po_weights[po]
                / available_po_weight
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
        "PO Weight Share (%)": [
            po_weights[po] / available_po_weight * 100
            if (
                available_po_weight > 0
                and po_attainment[po] is not None
            )
            else None
            for po in PO_NAMES
        ],
        "Weighted PO Contribution": [
            po_contribution[po] for po in PO_NAMES
        ]
    })

    po_display = po_summary.copy()

    for column in [
        "PO Attainment (%)",
        "PO Weight Share (%)",
        "Weighted PO Contribution"
    ]:

        po_display[column] = po_display[column].apply(
            lambda value:
            "N/A" if pd.isna(value)
            else round(value, 2)
        )

    st.dataframe(
        po_display,
        width="stretch",
        hide_index=True
    )

    # Overall weighted PO attainment
    missing_weighted_po = [
        po for po in PO_NAMES
        if po_weights[po] > 0
        and po_attainment[po] is None
    ]

    if (
        available_po_weight > 0
        and not missing_weighted_po
    ):

        overall_po = sum(
            value for value in po_contribution.values()
            if value is not None
        )

        st.metric(
            "Overall Weighted PO Attainment",
            f"{overall_po:.2f}%"
        )

    elif missing_weighted_po:

        st.warning(
            "Cannot calculate overall weighted PO attainment. "
            "Check the mapping for: "
            + ", ".join(missing_weighted_po)
        )

    else:

        st.warning(
            "Enter positive PO weights and valid CO–PO mappings."
        )

# =========================================================
# 11. CHARTS
# =========================================================

st.divider()
st.header("10. Attainment Charts")

if calculations_valid:

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        st.subheader("CO Attainment")

        st.bar_chart(
            average_co.dropna()
        )

    with chart_col2:

        st.subheader("PO Attainment")

        po_chart = pd.Series({
            po: value
            for po, value in po_attainment.items()
            if value is not None
        })

        if not po_chart.empty:
            st.bar_chart(po_chart)

# =========================================================
# 12. DOWNLOAD SUMMARY TABLES
# =========================================================

st.divider()
st.header("11. Download Summary Tables")

if calculations_valid:

    download_col1, download_col2 = st.columns(2)

    with download_col1:

        st.download_button(
            "Download Assessment–CO Matrix",
            allocation.to_csv().encode("utf-8"),
            "Assessment_CO_Matrix.csv",
            "text/csv"
        )

        st.download_button(
            "Download CO Summary",
            co_summary.to_csv(index=False).encode("utf-8"),
            "CO_Summary.csv",
            "text/csv"
        )

        st.download_button(
            "Download Student CO Results",
            co_results.to_csv(index=False).encode("utf-8"),
            "Student_CO_Results.csv",
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
            "Download Student Percentages",
            student_percentages.to_csv(index=False).encode("utf-8"),
            "Student_Percentage_Marks.csv",
            "text/csv"
        )

st.divider()

st.success("CO–PO Assessment Dashboard is ready.")
