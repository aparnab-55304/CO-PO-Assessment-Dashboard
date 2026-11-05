
import streamlit as st
import pandas as pd
import io

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CO-PO Assessment Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("CO-PO Assessment Summary Dashboard")

# =====================================================
# RESET BUTTON
# =====================================================

if st.button("Reset Dashboard"):
    for key in list(st.session_state.keys()):
        if key != "course_group_upload":
            del st.session_state[key]
    st.rerun()

# =====================================================
# COURSE GROUP EXCEL UPLOAD
# =====================================================

st.subheader("Upload Course Details")

uploaded_file = st.file_uploader(
    "Upload Course Group.xlsx",
    type=["xlsx"],
    key="course_group_upload"
)

if uploaded_file is None:
    st.info("Please upload the Course Group.xlsx file.")
    st.stop()

# =====================================================
# READ EXCEL FILE
# =====================================================

try:
    file_bytes = uploaded_file.getvalue()

    course_df = None

    required_columns = [
        "Program",
        "Program Code",
        "Handling Department"
    ]

    for header_row in [0, 1, 2, 3]:
        temp_df = pd.read_excel(
            io.BytesIO(file_bytes),
            header=header_row
        )

        temp_df.columns = (
            temp_df.columns.astype(str).str.strip()
        )

        if all(
            col in temp_df.columns
            for col in required_columns
        ):
            course_df = temp_df
            break

    if course_df is None:
        st.error(
            "Required columns not found in the uploaded Excel file."
        )
        st.stop()

    course_df = course_df.dropna(
        subset=required_columns
    ).copy()

    for col in required_columns:
        course_df[col] = course_df[col].astype(str).str.strip()

    course_df = course_df[
        (course_df["Program"] != "") &
        (course_df["Program Code"] != "") &
        (course_df["Handling Department"] != "")
    ]

except Exception as e:
    st.error(f"Unable to read Course Group.xlsx: {e}")
    st.stop()

# =====================================================
# COURSE DETAILS
# =====================================================

st.subheader("Course Details")

col1, col2, col3 = st.columns(3)

with col1:
    programs = sorted(
        course_df["Program"].unique().tolist()
    )

    selected_program = st.selectbox(
        "Program",
        programs,
        key="program_select"
    )

filtered_program = course_df[
    course_df["Program"] == selected_program
]

with col2:
    program_codes = sorted(
        filtered_program["Program Code"].unique().tolist()
    )

    selected_program_code = st.selectbox(
        "Program Code",
        program_codes,
        key="program_code_select"
    )

filtered_code = filtered_program[
    filtered_program["Program Code"] == selected_program_code
]

with col3:
    departments = sorted(
        filtered_code["Handling Department"].unique().tolist()
    )

    selected_department = st.selectbox(
        "Department",
        departments,
        key="department_select"
    )

# =====================================================
# COURSE OUTCOME DETAILS
# =====================================================

st.divider()
st.subheader("Course Outcome Details")

number_of_cos = st.number_input(
    "Number of Course Outcomes",
    min_value=1,
    max_value=20,
    value=4,
    step=1,
    key="number_of_cos"
)

co_names = [
    f"CO{i}" for i in range(1, int(number_of_cos) + 1)
]

# =====================================================
# CO WEIGHTS
# =====================================================

st.subheader("CO Weight Details")

co_weights = {}

weight_columns = st.columns(len(co_names))

for i, co in enumerate(co_names):
    with weight_columns[i]:
        co_weights[co] = st.number_input(
            f"{co} Weight",
            min_value=0.0,
            value=0.0,
            step=1.0,
            key=f"target_{co}"
        )

# =====================================================
# PA1 AND PA2 DETAILS
# =====================================================

st.divider()
st.subheader("PA Assessment Details")

pa_data = {}

for pa in ["PA1", "PA2"]:

    st.markdown(f"### {pa}")

    pa_total_weight = st.number_input(
        f"{pa} Total Weight",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key=f"{pa}_total_weight"
    )

    st.markdown(f"Select the COs included in {pa}")

    pa_co_data = {}

    co_columns = st.columns(len(co_names))

    for i, co in enumerate(co_names):

        with co_columns[i]:

            selected = st.checkbox(
                co,
                key=f"{pa}_{co}_checkbox"
            )

            if selected:
                assigned_weight = st.number_input(
                    f"{co} Assigned Weight",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key=f"{pa}_{co}_weight"
                )
            else:
                assigned_weight = 0.0

            pa_co_data[co] = {
                "Selected": selected,
                "Weight": assigned_weight
            }

    pa_data[pa] = {
        "Total Weight": pa_total_weight,
        "CO Data": pa_co_data
    }

# =====================================================
# LE1 AND LM DETAILS
# =====================================================

st.divider()
st.subheader("LE and LM Assessment Details")

le_col1, le_col2 = st.columns(2)

with le_col1:
    le1_weight = st.number_input(
        "LE1 Total Weight",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="le1_weight"
    )

with le_col2:
    lm_weight = st.number_input(
        "LM Total Weight",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="lm_weight"
    )

le_data = {
    "LE1": le1_weight,
    "LM": lm_weight
}

# =====================================================
# BUILD RAW ALLOCATION MATRIX
# =====================================================

raw_matrix = pd.DataFrame(
    0.0,
    index=["PA1", "PA2", "LE1", "LM"],
    columns=co_names
)

# PA1 and PA2:
# Use the teacher's individual CO allocations.
# Scale their proportions to the entered PA total weight.

for pa in ["PA1", "PA2"]:

    entered_co_total = sum(
        pa_data[pa]["CO Data"][co]["Weight"]
        for co in co_names
    )

    if entered_co_total > 0:

        for co in co_names:

            entered_weight = (
                pa_data[pa]["CO Data"][co]["Weight"]
            )

            raw_matrix.loc[pa, co] = (
                entered_weight
                * pa_data[pa]["Total Weight"]
                / entered_co_total
            )

# LE1 and LM:
# Distribute their total weights according to CO weights.
# If all CO weights are zero, distribute equally.

co_weight_total = sum(co_weights.values())

if co_weight_total > 0:
    co_proportions = {
        co: co_weights[co] / co_weight_total
        for co in co_names
    }
else:
    co_proportions = {
        co: 1 / len(co_names)
        for co in co_names
    }

for assessment in ["LE1", "LM"]:

    for co in co_names:

        raw_matrix.loc[assessment, co] = (
            le_data[assessment] * co_proportions[co]
        )

# =====================================================
# STANDARDISE GRAND TOTAL TO 20
# =====================================================

raw_grand_total = raw_matrix.to_numpy().sum()

if raw_grand_total > 0:

    allocation_matrix = (
        raw_matrix * (20 / raw_grand_total)
    )

else:

    allocation_matrix = raw_matrix.copy()

# =====================================================
# CO ASSESSMENT ALLOCATION MATRIX
# =====================================================

st.divider()
st.subheader("CO Assessment Allocation Matrix")

# Calculate row totals
allocation_matrix["TOTAL"] = (
    allocation_matrix[co_names].sum(axis=1)
)

# Calculate column totals
total_row = {
    co: allocation_matrix[co].sum()
    for co in co_names
}

total_row["TOTAL"] = allocation_matrix["TOTAL"].sum()

# Add bottom total row
display_matrix = allocation_matrix.copy()

display_matrix.loc["TOTAL"] = pd.Series(total_row)

display_matrix.index.name = "Assessment"

display_matrix = display_matrix.reset_index()

# Round values
for col in co_names + ["TOTAL"]:
    display_matrix[col] = display_matrix[col].round(2)

# Display as grid
st.dataframe(
    display_matrix,
    use_container_width=True,
    hide_index=True
)

# =====================================================
# EXCEL DOWNLOAD
# =====================================================

st.divider()
st.subheader("Download Assessment Summary")

output = io.BytesIO()

course_details = pd.DataFrame({
    "Field": [
        "Program",
        "Program Code",
        "Department"
    ],
    "Selected Value": [
        selected_program,
        selected_program_code,
        selected_department
    ]
})

co_weight_df = pd.DataFrame({
    "Course Outcome": co_names,
    "CO Weight": [
        co_weights[co] for co in co_names
    ]
})

pa_input_rows = []

for pa in ["PA1", "PA2"]:

    for co in co_names:

        pa_input_rows.append({
            "Assessment": pa,
            "Total Assessment Weight": pa_data[pa]["Total Weight"],
            "Course Outcome": co,
            "Selected": pa_data[pa]["CO Data"][co]["Selected"],
            "Entered CO Weight": pa_data[pa]["CO Data"][co]["Weight"]
        })

pa_input_df = pd.DataFrame(pa_input_rows)

le_input_df = pd.DataFrame({
    "Assessment": ["LE1", "LM"],
    "Total Weight": [
        le_data["LE1"],
        le_data["LM"]
    ]
})

with pd.ExcelWriter(
    output,
    engine="openpyxl"
) as writer:

    course_details.to_excel(
        writer,
        sheet_name="Course Details",
        index=False
    )

    co_weight_df.to_excel(
        writer,
        sheet_name="CO Weights",
        index=False
    )

    pa_input_df.to_excel(
        writer,
        sheet_name="PA Assessment",
        index=False
    )

    le_input_df.to_excel(
        writer,
        sheet_name="LE LM Assessment",
        index=False
    )

    display_matrix.to_excel(
        writer,
        sheet_name="Allocation Matrix",
        index=False
    )

st.download_button(
    label="Download Excel Summary",
    data=output.getvalue(),
    file_name="CO_Assessment_Allocation_Matrix.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
