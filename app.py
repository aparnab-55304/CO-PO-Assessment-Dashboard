
import streamlit as st
import pandas as pd
from io import BytesIO

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CO Assessment Summary Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("CO Assessment Summary Dashboard")
st.caption("CO-wise Assessment Weight Allocation")

# =====================================================
# RESET
# =====================================================

if st.button("Reset Dashboard"):
    st.session_state.clear()
    st.rerun()

# =====================================================
# COURSE DETAILS
# =====================================================

st.header("1. Course Details")

col1, col2 = st.columns(2)

with col1:
    department = st.text_input("Department")
    course_name = st.text_input("Course Name")

with col2:
    course_code = st.text_input("Course Code")
    semester = st.selectbox("Semester", range(1, 9))

st.divider()

# =====================================================
# COURSE OUTCOMES
# =====================================================

st.header("2. Course Outcomes")

co_count = st.number_input(
    "Number of Course Outcomes",
    min_value=1,
    max_value=15,
    value=4,
    step=1
)

co_names = [
    f"CO{i}" for i in range(1, int(co_count) + 1)
]

# =====================================================
# TEACHER-ASSIGNED CO WEIGHTS
# =====================================================

st.subheader("Teacher-Assigned CO Weights")

st.write(
    "Enter the overall weight assigned by the teacher "
    "to each Course Outcome."
)

co_weight_input = pd.DataFrame({
    "CO": co_names,
    "Assigned CO Weight": [0.0] * int(co_count)
})

edited_co_weights = st.data_editor(
    co_weight_input,
    key=f"co_weights_{co_count}",
    hide_index=True,
    disabled=["CO"],
    num_rows="fixed",
    column_config={
        "CO": st.column_config.TextColumn(
            "Course Outcome",
            disabled=True
        ),
        "Assigned CO Weight": st.column_config.NumberColumn(
            "Assigned CO Weight",
            min_value=0.0,
            step=0.5,
            format="%.2f"
        )
    },
    width="stretch"
)

co_weights = {
    row["CO"]: float(row["Assigned CO Weight"])
    for _, row in edited_co_weights.iterrows()
}

st.divider()

# =====================================================
# PA1 AND PA2 INPUT
# =====================================================

st.header("3. PA Assessment Input Matrix")

st.write(
    "Enter the total weight of PA1 and PA2 and tick "
    "the COs covered by each assessment."
)

pa_names = ["PA1", "PA2"]

pa_rows = []

for assessment in pa_names:
    row = {
        "Assessment": assessment,
        "Assessment Weight": 0.0
    }

    for co in co_names:
        row[co] = False

    pa_rows.append(row)

pa_input = pd.DataFrame(pa_rows)

pa_config = {
    "Assessment": st.column_config.TextColumn(
        "Assessment",
        disabled=True
    ),
    "Assessment Weight": st.column_config.NumberColumn(
        "Assessment Weight",
        min_value=0.0,
        step=0.5,
        format="%.2f"
    )
}

for co in co_names:
    pa_config[co] = st.column_config.CheckboxColumn(
        co,
        help=f"Tick if {co} is covered in this PA"
    )

edited_pa = st.data_editor(
    pa_input,
    key=f"pa_input_{co_count}",
    hide_index=True,
    disabled=["Assessment"],
    num_rows="fixed",
    column_config=pa_config,
    width="stretch"
)

st.divider()

# =====================================================
# LE1 AND LE2 INPUT
# =====================================================

st.header("4. Learning Evaluation Input")

st.write(
    "LE1 and LE2 are single-weight assessments. "
    "Enter only the total weight assigned to each."
)

le_input = pd.DataFrame({
    "Assessment": ["LE1", "LE2"],
    "Total Assigned Weight": [0.0, 0.0]
})

edited_le = st.data_editor(
    le_input,
    key="le_input",
    hide_index=True,
    disabled=["Assessment"],
    num_rows="fixed",
    column_config={
        "Assessment": st.column_config.TextColumn(
            "Assessment",
            disabled=True
        ),
        "Total Assigned Weight": st.column_config.NumberColumn(
            "Total Assigned Weight",
            min_value=0.0,
            step=0.5,
            format="%.2f"
        )
    },
    width="stretch"
)

st.divider()

# =====================================================
# CALCULATE PA CO-WISE ALLOCATION
# =====================================================

pa_summary_rows = []

for _, row in edited_pa.iterrows():

    assessment = row["Assessment"]
    assessment_weight = float(row["Assessment Weight"])

    selected_cos = [
        co for co in co_names
        if bool(row[co])
    ]

    denominator = sum(
        co_weights[co] for co in selected_cos
    )

    result = {
        "Assessment": assessment,
        "Assessment Weight": assessment_weight
    }

    for co in co_names:

        if bool(row[co]) and denominator > 0:
            allocated_weight = (
                assessment_weight * co_weights[co]
            ) / denominator
        else:
            allocated_weight = 0.0

        result[co] = allocated_weight

    pa_summary_rows.append(result)

pa_summary = pd.DataFrame(pa_summary_rows)

# =====================================================
# CO-WISE TOTAL ASSESSMENT WEIGHT
# PA1 AND PA2 ONLY
# =====================================================

st.header("5. CO-wise Total Assessment Weight")

st.caption(
    "Calculated from PA1 and PA2 allocations only. "
    "LE1 and LE2 are not distributed among COs."
)

co_total_data = []

for co in co_names:

    total = pa_summary[co].sum()

    co_total_data.append({
        "Course Outcome": co,
        "Teacher-Assigned CO Weight": co_weights[co],
        "Total PA Assessment Weight": total
    })

co_total_df = pd.DataFrame(co_total_data)

st.dataframe(
    co_total_df.round(2),
    hide_index=True,
    width="stretch"
)

st.divider()

# =====================================================
# FINAL SUMMARY MATRIX
# =====================================================

st.header("6. Calculated CO Assessment Summary Matrix")

st.write(
    "PA1 and PA2 show their calculated CO-wise allocation. "
    "LE1 and LE2 show their single assigned total weights."
)

summary_rows = []

# Add PA rows
for _, row in pa_summary.iterrows():

    result = {
        "Assessment": row["Assessment"],
        "Assessment Weight": row["Assessment Weight"]
    }

    for co in co_names:
        result[co] = row[co]

    result["TOTAL"] = row["Assessment Weight"]

    summary_rows.append(result)

# Add LE rows: no CO-wise allocation
for _, row in edited_le.iterrows():

    result = {
        "Assessment": row["Assessment"],
        "Assessment Weight": float(
            row["Total Assigned Weight"]
        )
    }

    for co in co_names:
        result[co] = "—"

    result["TOTAL"] = float(
        row["Total Assigned Weight"]
    )

    summary_rows.append(result)

# Create summary dataframe
summary_matrix = pd.DataFrame(summary_rows)

# Add total row
total_row = {
    "Assessment": "TOTAL",
    "Assessment Weight": summary_matrix[
        "Assessment Weight"
    ].sum()
}

for co in co_names:
    total_row[co] = pa_summary[co].sum()

total_row["TOTAL"] = summary_matrix["TOTAL"].sum()

summary_matrix = pd.concat(
    [summary_matrix, pd.DataFrame([total_row])],
    ignore_index=True
)

display_columns = (
    ["Assessment", "Assessment Weight"]
    + co_names
    + ["TOTAL"]
)

summary_matrix = summary_matrix[display_columns]

st.dataframe(
    summary_matrix.round(2),
    hide_index=True,
    width="stretch"
)

# =====================================================
# VALIDATION
# =====================================================

st.header("7. Validation")

for _, row in edited_pa.iterrows():

    assessment = row["Assessment"]
    assessment_weight = float(row["Assessment Weight"])

    selected_cos = [
        co for co in co_names
        if bool(row[co])
    ]

    denominator = sum(
        co_weights[co] for co in selected_cos
    )

    if assessment_weight > 0 and not selected_cos:
        st.warning(
            f"{assessment}: Select at least one CO."
        )

    elif assessment_weight > 0 and denominator == 0:
        st.warning(
            f"{assessment}: Selected COs have zero "
            "teacher-assigned weight."
        )

# =====================================================
# EXCEL DOWNLOAD
# =====================================================

st.divider()

st.header("8. Download Summary Matrix")

course_details = pd.DataFrame({
    "Field": [
        "Department",
        "Course Name",
        "Course Code",
        "Semester",
        "Number of COs"
    ],
    "Value": [
        department,
        course_name,
        course_code,
        semester,
        co_count
    ]
})

output = BytesIO()

with pd.ExcelWriter(
    output,
    engine="openpyxl"
) as writer:

    course_details.to_excel(
        writer,
        sheet_name="Course Details",
        index=False
    )

    edited_co_weights.to_excel(
        writer,
        sheet_name="CO Weights",
        index=False
    )

    edited_pa.to_excel(
        writer,
        sheet_name="PA Input",
        index=False
    )

    edited_le.to_excel(
        writer,
        sheet_name="LE Input",
        index=False
    )

    co_total_df.to_excel(
        writer,
        sheet_name="CO-wise Total",
        index=False
    )

    summary_matrix.to_excel(
        writer,
        sheet_name="CO Summary Matrix",
        index=False
    )

st.download_button(
    label="Download CO Assessment Summary",
    data=output.getvalue(),
    file_name="CO_Assessment_Summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success("CO Assessment Summary Matrix is ready.")
