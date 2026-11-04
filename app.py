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

try:
    course_df = pd.read_excel(uploaded_file, header=1)

    course_df.columns = (
        course_df.columns.astype(str).str.strip()
    )

    required_columns = [
        "Program",
        "Program Code",
        "Handling Department"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in course_df.columns
    ]

    if missing_columns:
        st.error(f"Missing columns: {missing_columns}")
        st.stop()

except Exception as e:
    st.error(f"Unable to read the uploaded Excel file: {e}")
    st.stop()
