
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
st.caption("Assessment-wise Course Outcome Weight Allocation")

# =====================================================
# RESET
# =====================================================

if st.button("Reset Dashboard"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# =====================================================
# COURSE DETAILS
# =====================================================

st.header("1. Course Details")

col1, col2 = st.columns(2)

with col1:
    department = st.text_input(
        "Department",
        placeholder="Enter Department"
    )

    course_name = st.text_input(
        "Course Name",
        placeholder="Enter Course Name"
    )

with col2:
    course_code = st.text_input(
        "Course Code",
        placeholder="Enter Course Code"
    )

    semester = st.selectbox(
        "Semester",
        list(range(1, 9))
    )

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

st.write("Enter the description of each Course Outcome.")

co_description_data = {
    "CO": co_names,
    "CO Description": [""] * int(co_count)
}

co_description_df = st.data_editor(
    pd.DataFrame(co_description_data),
    key=f"co_description_{co_count}",
    hide_index=True,
    disabled=["CO"],
    column_config={
        "CO": st.column_config.TextColumn(
            "Course Outcome",
            disabled=True
        ),
        "CO Description": st.column_config.TextColumn(
            "Description",
            width="large"
        )
    },
    width="stretch"
)

st.divider()

# =====================================================
# ASSESSMENT WEIGHT INPUT
# =====================================================

st.header("3. CO Assessment Weight Allocation")

st.write(
    "For each assessment, select the COs covered and enter "
    "the actual weight assigned to each selected CO."
)

st.info(
    "Example: If PA1 covers CO1 and CO2, enter the weight "
    "assigned to CO1 and CO2 separately. The dashboard will "
    "use these entered weights directly."
)

assessment_names = ["PA1", "PA2", "LE1", "LE2"]

# Create editable input table
input_data = []

for assessment in assessment_names:

    row = {
        "Assessment": assessment,
        "Assessment Weight": 0.0
    }

    for co in co_names:
        row[f"{co} Tick"] = False
        row[f"{co} Assigned Weight"] = 0.0

    input_data.append(row)

input_df = pd.DataFrame(input_data)

# Configure columns
column_config = {
    "Assessment": st.column_config.TextColumn(
        "Assessment",
        disabled=True
    ),

    "Assessment Weight": st.column_config.NumberColumn(
        "Total Assessment Weight",
        min_value=0.0,
        step=0.5,
        format="%.2f"
    )
}

for co in co_names:

    column_config[f"{co} Tick"] = (
        st.column_config.CheckboxColumn(
            f"{co} ✓",
            help=f"Tick if {co} is covered"
        )
    )

    column_config[f"{co} Assigned Weight"] = (
        st.column_config.NumberColumn(
            f"{co} Assigned Weight",
            min_value=0.0,
            step=0.5,
            format="%.2f"
        )
    )

edited_input_df = st.data_editor(
    input_df,
    key=f"assessment_input_{co_count}",
    hide_index=True,
    disabled=["Assessment"],
    column_config=column_config,
    num_rows="fixed",
    width="stretch"
)

# =====================================================
# CALCULATED CO ASSESSMENT SUMMARY
# =====================================================

st.divider()

st.header("4. Calculated CO Assessment Summary")

st.write(
    "This matrix displays the actual weight assigned to "
    "each CO in each assessment."
)

summary_rows = []

for _, row in edited_input_df.iterrows():

    summary_row = {
        "Assessment": row["Assessment"]
    }

    total_assigned = 0.0

    for co in co_names:

        tick = bool(row[f"{co} Tick"])
        assigned_weight = float(
            row[f"{co} Assigned Weight"]
        )

        # Include the assigned weight only when CO is selected
        if tick:
            summary_row[co] = assigned_weight
            total_assigned += assigned_weight
        else:
            summary_row[co] = 0.0

    summary_row["Total Assigned Weight"] = total_assigned
    summary_row["Assessment Weight"] = float(
        row["Assessment Weight"]
    )

    summary_rows.append(summary_row)

summary_df = pd.DataFrame(summary_rows)

# Add total row
total_row = {
    "Assessment": "TOTAL"
}

for co in co_names:
    total_row[co] = summary_df[co].sum()

total_row["Total Assigned Weight"] = (
    summary_df["Total Assigned Weight"].sum()
)

total_row["Assessment Weight"] = (
    summary_df["Assessment Weight"].sum()
)

summary_df = pd.concat(
    [summary_df, pd.DataFrame([total_row])],
    ignore_index=True
)

# Arrange columns
summary_columns = (
    ["Assessment"]
    + co_names
    + ["Total Assigned Weight", "Assessment Weight"]
)

summary_df = summary_df[summary_columns]

st.dataframe(
    summary_df.round(2),
    hide_index=True,
    width="stretch"
)

# =====================================================
# CO-WISE TOTAL SUMMARY
# =====================================================

st.subheader("CO-wise Total Assigned Weight")

co_total_data = []

for co in co_names:

    total_weight = summary_df.loc[
        summary_df["Assessment"] != "TOTAL",
        co
    ].sum()

    co_total_data.append({
        "Course Outcome": co,
        "Total Assigned Weight": total_weight
    })

co_total_df = pd.DataFrame(co_total_data)

st.dataframe(
    co_total_df.round(2),
    hide_index=True,
    width="stretch"
)

# =====================================================
# VALIDATION
# =====================================================

st.subheader("Assessment Weight Validation")

for _, row in edited_input_df.iterrows():

    assessment = row["Assessment"]

    assessment_weight = float(
        row["Assessment Weight"]
    )

    assigned_total = sum(
        float(row[f"{co} Assigned Weight"])
        if bool(row[f"{co} Tick"])
        else 0.0
        for co in co_names
    )

    unchecked_weights = [
        co for co in co_names
        if (
            not bool(row[f"{co} Tick"])
            and float(row[f"{co} Assigned Weight"]) > 0
        )
    ]

    if unchecked_weights:
        st.warning(
            f"{assessment}: Weight entered for "
            f"{', '.join(unchecked_weights)} without ticking the CO."
        )

    if assessment_weight > 0:

        if abs(assigned_total - assessment_weight) > 0.001:
            st.warning(
                f"{assessment}: Total assigned CO weight "
                f"({assigned_total:.2f}) does not match "
                f"the assessment weight ({assessment_weight:.2f})."
            )
        else:
            st.success(
                f"{assessment}: Assessment weight matches "
                "the total CO assigned weight."
            )

# =====================================================
# EXCEL DOWNLOAD
# =====================================================

st.divider()

st.header("5. Download Summary")

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

    co_description_df.to_excel(
        writer,
        sheet_name="Course Outcomes",
        index=False
    )

    edited_input_df.to_excel(
        writer,
        sheet_name="Assessment Input",
        index=False
    )

    summary_df.to_excel(
        writer,
        sheet_name="CO Summary Matrix",
        index=False
    )

    co_total_df.to_excel(
        writer,
        sheet_name="CO-wise Total",
        index=False
    )

st.download_button(
    label="Download CO Assessment Summary",
    data=output.getvalue(),
    file_name="CO_Assessment_Summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.success("CO Assessment Summary Matrix is ready.")
