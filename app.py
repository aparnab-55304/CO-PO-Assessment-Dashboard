
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
    keys_to_reset = [
        key for key in st.session_state.keys()
        if key != "course_group_upload"
    ]

    for key in keys_to_reset:
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
    st.info("Please upload the Course Group.xlsx file to continue.")
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

    # Try different header rows
    for header_row in [0, 1, 2, 3]:
        temp_df = pd.read_excel(
            io.BytesIO(file_bytes),
            header=header_row
        )

        temp_df.columns = (
            temp_df.columns.astype(str).str.strip()
        )

        if all(col in temp_df.columns for col in required_columns):
            course_df = temp_df
            break

    if course_df is None:
        st.error(
            "Required columns were not found. "
            "Please check the Excel headings: "
            "Program, Program Code and Handling Department."
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
    st.error(f"Unable to load Course Group.xlsx: {e}")
    st.stop()

# =====================================================
# COURSE DETAILS DROPDOWNS
# =====================================================

st.subheader("Course Details")

col1, col2, col3 = st.columns(3)

with col1:
    programs = sorted(
        course_df["Program"].dropna().unique().tolist()
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
        filtered_program["Program Code"].dropna().unique().tolist()
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
        filtered_code["Handling Department"].dropna().unique().tolist()
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
# PA1 AND PA2 ASSESSMENT DETAILS
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

    st.markdown(f"**Select the COs included in {pa}**")

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
# LE1 AND LM ASSESSMENT DETAILS
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
# CO ASSESSMENT SUMMARY MATRIX
# =====================================================

st.divider()

st.subheader("CO Assessment Summary Matrix")

matrix_rows = []

# PA1 and PA2 rows

for pa in ["PA1", "PA2"]:

    row = {
        "Assessment": pa,
        "Weight": pa_data[pa]["Total Weight"]
    }

    co_total = 0.0

    for co in co_names:
        weight = pa_data[pa]["CO Data"][co]["Weight"]
        row[co] = weight
        co_total += weight

    row["CO Total Assessment"] = co_total
    row["TOTAL"] = pa_data[pa]["Total Weight"]

    matrix_rows.append(row)

# LE1 and LM rows

for assessment in ["LE1", "LM"]:

    row = {
        "Assessment": assessment,
        "Weight": le_data[assessment]
    }

    for co in co_names:
        row[co] = "—"

    row["CO Total Assessment"] = "—"
    row["TOTAL"] = le_data[assessment]

    matrix_rows.append(row)

# =====================================================
# TOTAL ROW
# =====================================================

total_row = {
    "Assessment": "TOTAL",
    "Weight": (
        pa_data["PA1"]["Total Weight"] +
        pa_data["PA2"]["Total Weight"] +
        le_data["LE1"] +
        le_data["LM"]
    )
}

for co in co_names:

    total_row[co] = (
        pa_data["PA1"]["CO Data"][co]["Weight"] +
        pa_data["PA2"]["CO Data"][co]["Weight"]
    )

total_row["CO Total Assessment"] = sum(
    total_row[co] for co in co_names
)

total_row["TOTAL"] = total_row["Weight"]

matrix_rows.append(total_row)

# =====================================================
# DISPLAY MATRIX
# =====================================================

matrix_df = pd.DataFrame(matrix_rows)

st.dataframe(
    matrix_df,
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
    "CO Weight": [co_weights[co] for co in co_names]
})

pa_input_rows = []

for pa in ["PA1", "PA2"]:

    for co in co_names:

        pa_input_rows.append({
            "Assessment": pa,
            "Total Assessment Weight": pa_data[pa]["Total Weight"],
            "Course Outcome": co,
            "Selected": pa_data[pa]["CO Data"][co]["Selected"],
            "Assigned CO Weight": pa_data[pa]["CO Data"][co]["Weight"]
        })

pa_input_df = pd.DataFrame(pa_input_rows)

le_input_df = pd.DataFrame({
    "Assessment": ["LE1", "LM"],
    "Total Weight": [
        le_data["LE1"],
        le_data["LM"]
    ]
})

with pd.ExcelWriter(output, engine="openpyxl") as writer:

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

    matrix_df.to_excel(
        writer,
        sheet_name="CO Summary Matrix",
        index=False
    )

st.download_button(
    label="Download Excel Summary",
    data=output.getvalue(),
    file_name="CO_Assessment_Summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
