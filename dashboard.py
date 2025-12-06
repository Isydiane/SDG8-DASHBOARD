import streamlit as st
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect("applicants.db")
cursor = conn.cursor()

# --- BASELINE DATA ---
INITIAL_DATA = {
    "Age_Group": ["18-21", "22-25", "26-30"],
    "Unemployment_Rate (%)": [14.5, 10.2, 6.7],
    "Underemployment_Rate (%)": [22.1, 18.4, 12.9],
    "NEET_Rate (%)": [19.0, 16.3, 12.5],
    "Average_Monthly_Wage (PHP)": [9500, 14500, 19800]
}
df = pd.DataFrame(INITIAL_DATA)

# --- PAGE CONFIG ---
st.set_page_config(page_title="Youth Employment Tracker (SDG 8)", page_icon="📊", layout="centered")

# --- CUSTOM CSS for beige background ---
st.markdown("""
    <style>
    body {
        background-color: #f5e6c4;
    }
    .stApp {
        background-color: #f5e6c4;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGIN SCREEN ---
def login():
    st.title("Youth Employment Tracker (SDG 8)")

    # Display logo at the top (centered)
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.image("logo.png", width=250)
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Login Portal")

    user_type = st.selectbox("Select User Type", ["Applicant", "Admin"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if user_type == "Admin" and username == "admin" and password == "1234":
            st.success("Welcome Admin!")
            show_admin_dashboard()
        elif user_type == "Applicant":
            cursor.execute("SELECT password FROM applicant_credentials WHERE username=?", (username,))
            result = cursor.fetchone()
            if result and result[0] == password:
                st.success(f"Welcome {username}!")
                show_applicant_dashboard(username)
            else:
                st.error("Invalid Applicant credentials")
        else:
            st.error("Invalid login")

# --- ADMIN DASHBOARD ---
def show_admin_dashboard():
    st.header("Admin Dashboard")

    # Load applicants from database
    applicants = pd.read_sql("SELECT * FROM applicants", conn)

    # --- Filters ---
    st.subheader("Filter Applicants")
    regions = applicants["address"].dropna().unique().tolist()
    age_groups = applicants["age_group"].dropna().unique().tolist()

    selected_region = st.selectbox("Select Region", ["All"] + regions)
    selected_age_group = st.selectbox("Select Age Group", ["All"] + age_groups)

    # Apply filters
    filtered = applicants.copy()
    if selected_region != "All":
        filtered = filtered[filtered["address"] == selected_region]
    if selected_age_group != "All":
        filtered = filtered[filtered["age_group"] == selected_age_group]

    # --- Display filtered table ---
    st.dataframe(filtered)

    # --- Export Options ---
    st.subheader("Export Data")
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="applicants_filtered.csv",
        mime="text/csv"
    )

    excel = filtered.to_excel("applicants_filtered.xlsx", index=False)
    with open("applicants_filtered.xlsx", "rb") as f:
        st.download_button(
            label="📥 Download as Excel",
            data=f,
            file_name="applicants_filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- Charts ---
    st.subheader("Youth Employment Charts")
    st.bar_chart(df.set_index("Age_Group")["Unemployment_Rate (%)"])
    st.bar_chart(df.set_index("Age_Group")["Underemployment_Rate (%)"])
    st.line_chart(df.set_index("Age_Group")["NEET_Rate (%)"])
    st.bar_chart(df.set_index("Age_Group")["Average_Monthly_Wage (PHP)"])

# --- APPLICANT DASHBOARD ---
def show_applicant_dashboard(username):
    st.header("Applicant Dashboard")
    st.write("Submit your resume and view job recommendations")

    full_name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=15, max_value=30)
    address = st.text_input("Address")
    skills = st.text_input("Skills (comma separated)")
    education = st.text_input("Education")
    experience = st.number_input("Work Experience (years)", min_value=0)

    if st.button("Submit Resume"):
        age_group = "18-21" if 18 <= age <= 21 else "22-25" if 22 <= age <= 25 else "26-30"
        cursor.execute("""
            INSERT INTO applicants (full_name, age, age_group, address, skills, education, experience)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (full_name, age, age_group, address, skills, education, experience))
        conn.commit()
        st.success("Resume submitted successfully!")

    # --- Job Portal ---
    st.subheader("Job Portal")
    JOB_LIST = [
        ("Cashier (Local Store)", 12000),
        ("Service Crew", 10000),
        ("Data Encoder", 14000),
        ("Barangay Support Staff", 11000),
        ("Warehouse Helper", 13000),
        ("Factory Worker (Santa Barbara)", 14000),
        ("Rice Mill Operator", 16000),
        ("Municipal Office Clerk", 15000),
        ("Call Center Trainee (Iloilo City)", 18000),
        ("IT Assistant Intern", 12000),
    ]

    search = st.text_input("Search Job")
    if search:
        jobs = [j for j in JOB_LIST if search.lower() in j[0].lower()]
    else:
        jobs = JOB_LIST

    jobs_df = pd.DataFrame(jobs, columns=["Job Title", "Monthly Salary"])
    st.table(jobs_df)

    # --- Interview Scheduling ---
    selected_job = st.selectbox("Select a job to schedule interview", jobs_df["Job Title"])
    if st.button("Schedule Interview"):
        st.success(f"📅 Interview scheduled for:\n\n**{selected_job}**\nTomorrow at 9:00 AM")

# --- MAIN ---
login()
