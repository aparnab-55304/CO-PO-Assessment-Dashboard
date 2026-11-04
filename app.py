
import streamlit as st
import pandas as pd
import io
from pathlib import Path

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CO Assessment Summary Matrix",
    page_icon="📊",
    layout="wide"
)

st.title("CO Assessment Summary Matrix")

# =====================================================
# RESET
# =====================================================

if st.button("Reset"):
    st.session_state.clear()
    st.rerun()

# =====================================================
# LOAD COURSE GROUP EXCEL
# =====================================================

file_path = Path(__file__).parent / "Course Group.xlsx"

try:
    course_df = pd.read_excel(file_path, header=1)
    course_df.columns = course_df.columns.astype(str).str.strip()

    required_columns = [
        "Program",
        "Program Code",
        "Handling Department"
    ]

    course_df = course_df.dropna(subset=required_columns)

    for col in required_columns:
        course_df[col] = course_df[col].astype(str).str.strip()

    course_df = course_df[
        (course_df["Program"] != "") &
        (course_df["Program Code"] != "") &
        (course_df["Handling Department"] != "")
    ]

except Exception:
    st.error("Unable to load Course Group.xlsx.")
    st.stop()

# =====================================================
# COURSE DETAILS
# =====================================================

st.header("Course Details")

program_options = sorted(course_df["Program"].unique())

selected_program = st.selectbox(
    "Program",
    program_options,
    key="program"
)

program_data = course_df[
    course_df["Program"] == selected_program
]

code_options = sorted(program_data["Program Code"].unique())

selected_code = st.selectbox(
    "Program Code",
    code_options,
    key="program_code"
)

code_data = program_data[
    program_data["Program Code"] == selected_code
]

department_options = sorted(
    code_data["Handling Department"].unique()
)

selected_department = st.selectbox(
    "Department",
    department_options,
    key="department"
)

# =====================================================
# COURSE OUTCOMES
# =====================================================

st.header("Course Outcomes")

num_cos = st.number_input(
    "Number of Course Outcomes",
    min_value=1,
    max_value=15,
    value=4,
    step=1
)

co_names = [
    f"CO{i+1}" for i in range(int(num_cos))
]

# =====================================================
# CO WEIGHTS
# =====================================================

st.subheader("CO Weights")

co_weights = {}

co_cols = st.columns(len(co_names))

for i, co in enumerate(co_names):
    with co_cols[i]:
        co_weights[co] = st.number_input(
            co,
            min_value=0.0,
            value=0.0,
            step=1.0,
            key=f"co_weight_{co}"
        )

# =====================================================
# PA ASSESSMENT INPUT
# =====================================================

st.header("PA Assessment Input")

pa_data = {}

for pa in ["PA1", "PA2"]:

    st.subheader(pa)

    pa_total_weight = st.number_input(
        f"{pa} Weight",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key=f"{pa}_total_weight"
    )

    st.markdown("**CO Selection and Weight Distribution**")

    pa_co_data = {}

    header_cols = st.columns([1, 1, 2])

    header_cols[0].markdown("**CO**")
    header_cols[1].markdown("**Select**")
    header_cols[2].markdown("**Assigned Weight**")

    for co in co_names:

        cols = st.columns([1, 1, 2])

        with cols[0]:
            st.write(co)

        with cols[1]:
            selected = st.checkbox(
                " ",
                key=f"{pa}_{co}_selected"
            )

        with cols[2]:
            if selected:
                assigned_weight = st.number_input(
                    f"{co} Weight",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key=f"{pa}_{co}_assigned",
                    label_visibility="collapsed"
                )
            else:
                assigned_weight = 0.0
                st.write("—")

        pa_co_data[co] = {
            "Selected": selected,
            "Weight": assigned_weight
        }

    pa_data[pa] = {
        "Total Weight": pa_total_weight,
        "CO Data": pa_co_data
    }

# =====================================================
# LEARNING EVALUATION INPUT
# =====================================================

st.header("Learning Evaluation")

le_data = {}

col1, col2 = st.columns(2)

with col1:
    le_data["LE1"] = st.number_input(
        "LE1 Weight",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="le1_weight"
    )

with col2:
    le_data["LM"] = st.number_input(
        "LM Weight",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="lm_weight"
    )

# =====================================================
# BUILD SUMMARY MATRIX
# =====================================================

st.header("CO Assessment Summary Matrix")

matrix_rows = []

# PA1 AND PA2

for pa in ["PA1", "PA2"]:

    row = {
        "Assessment": pa,
        "Weight": pa_data[pa]["Total Weight"]
    }

    co_total = 0.0

    for co in co_names:

        value = pa_data[pa]["CO Data"][co]["Weight"]

        row[co] = value
        co_total += value

    row["CO Total Assessment"] = co_total
    row["TOTAL"] = pa_data[pa]["Total Weight"]

    matrix_rows.append(row)

# LE1 AND LM

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
# COLUMN TOTALS
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

total_row["TOTAL"] = (
    pa_data["PA1"]["Total Weight"] +
    pa_data["PA2"]["Total Weight"] +
    le_data["LE1"] +
    le_data["LM"]
)

matrix_rows.append(total_row)

summary_matrix = pd.DataFrame(matrix_rows)

# =====================================================
# DISPLAY AS GRID
# =====================================================

display_matrix = summary_matrix.copy()

numeric_columns = (
    ["Weight"] +
    co_names +
    ["CO Total Assessment", "TOTAL"]
)

for col in numeric_columns:
    display_matrix[col] = pd.to_numeric(
        display_matrix[col],
        errors="coerce"
    ).round(2)

st.dataframe(
    display_matrix,
    use_container_width=True,
    hide_index=True,
    height=250
)

# =====================================================
# EXCEL DOWNLOAD
# =====================================================

st.header("Download")

output = io.BytesIO()

course_details = pd.DataFrame({
    "Field": [
        "Program",
        "Program Code",
        "Department"
    ],
    "Selected Value": [
        selected_program,
        selected_code,
        selected_department
    ]
})

co_weights_df = pd.DataFrame({
    "CO": co_names,
    "Assigned CO Weight": [
        co_weights[co] for co in co_names
    ]
})

pa_input_rows = []

for pa in ["PA1", "PA2"]:

    row = {
        "Assessment": pa,
        "Total Weight": pa_data[pa]["Total Weight"]
    }

    for co in co_names:
        row[f"{co} Selected"] = pa_data[pa]["CO Data"][co]["Selected"]
        row[f"{co} Assigned Weight"] = pa_data[pa]["CO Data"][co]["Weight"]

    pa_input_rows.append(row)

pa_input_df = pd.DataFrame(pa_input_rows)

le_input_df = pd.DataFrame({
    "Assessment": ["LE1", "LM"],
    "Weight": [
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

    co_weights_df.to_excel(
        writer,
        sheet_name="CO Weights",
        index=False
    )

    pa_input_df.to_excel(
        writer,
        sheet_name="PA Input",
        index=False
    )

    le_input_df.to_excel(
        writer,
        sheet_name="LE Input",
        index=False
    )

    summary_matrix.to_excel(
        writer,
        sheet_name="CO Summary Matrix",
        index=False
    )

st.download_button(
    label="Download Excel File",
    data=output.getvalue(),
    file_name="CO_Assessment_Summary_Matrix.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
