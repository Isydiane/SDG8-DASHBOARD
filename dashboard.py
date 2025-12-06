import streamlit as st
import sqlite3
import pandas as pd

# --- Connect to database ---
conn = sqlite3.connect("applicants.db")
cursor = conn.cursor()

# --- Initial Data ---
INITIAL_DATA = {
    "Age_Group": ["18-21", "22-25", "26-30"],
    "Unemployment_Rate (%)": [14.5, 10.2, 6.7],
    "Underemployment_Rate (%)": [22.1, 18.4, 12.9],
    "NEET_Rate (%)": [19.0, 16.3, 12.5],
    "Average_Monthly_Wage (PHP)": [9500, 14500, 19800]
}
df = pd.DataFrame(INITIAL_DATA)

# --- Page Config ---
st.set_page_config(page_title="Youth Employment Tracker (SDG 8)", page_icon="📊", layout="centered")

# --- Session State ---
if "proceed" not in st.session_state:
    st.session_state["proceed"] = False

# --- Intro Screen ---
def intro_screen():
    st.markdown("""
        <style>
        .stApp { background-color: #f5e6c4; }
        .title-text {
            font-size: 32px;
            font-weight: bold;
            text-align: center;
            color: #4e342e;
        }
        .subtitle-text {
            font-size: 20px;
            text-align: center;
            color: #6d4c41;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.image("logo.png", width=250)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<p class='title-text'>Supporting Youth Economic Data Dashboard – PESO Santa Barbara</p>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle-text'>SDG 8: Decent Work and Economic Growth</p>", unsafe_allow_html=True)

    st.write("""
    This aims to create safe, fair, and productive jobs for everyone while helping economies grow sustainably.  
    It focuses on protecting workers’ rights, supporting businesses, reducing unemployment, and ensuring equal opportunities for all.
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Click to Proceed to Login"):
            st.session_state["proceed"] = True
    with col2:
        if st.button("❌ Exit Application"):
            st.warning("Thank you for visiting. You may now close the tab.")

# --- Admin Dashboard ---
def show_admin_dashboard():
    st.header("Admin Dashboard")
    applicants = pd.read_sql("SELECT * FROM applicants", conn)

    st.subheader("Filter Applicants")
    regions = applicants["address"].dropna().unique().tolist()
    age_groups = applicants["age_group"].dropna().unique().tolist()

    selected_region = st.selectbox("Select Region", ["All"] + regions)
    selected_age_group = st.selectbox("Select Age Group", ["All"] + age_groups)

    filtered = applicants.copy()
    if selected_region != "All":
        filtered = filtered[filtered["address"] == selected_region]
    if selected_age_group != "All":
        filtered = filtered[filtered["age_group"] == selected_age_group]

    st.dataframe(filtered)

    st.subheader("Export Data")
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download as CSV", data=csv, file_name="applicants_filtered.csv", mime="text/csv")

    st.subheader("Youth Employment Charts")
    st.bar_chart(df.set_index("Age_Group")["Unemployment_Rate (%)"])
    st.bar_chart(df.set_index("Age_Group")["Underemployment_Rate (%)"])
    st.line_chart(df.set_index("Age_Group")["NEET_Rate (%)"])
    st.bar_chart(df.set_index("Age_Group")["Average_Monthly_Wage (PHP)"])

# --- Applicant Dashboard ---
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
    jobs = [j for j in JOB_LIST if search.lower() in j[0].lower()] if search else JOB_LIST
    jobs_df = pd.DataFrame(jobs, columns=["Job Title", "Monthly Salary"])
    st.table(jobs_df)

    selected_job = st.selectbox("Select a job to schedule interview", jobs_df["Job Title"])
    if st.button("Schedule Interview"):
        st.success(f"📅 Interview scheduled for:\n\n**{selected_job}**\nTomorrow at 9:00 AM")

# --- Main Dashboard ---
def main():
    st.subheader("📊 Youth Employment Statistics")
    st.bar_chart(df.set_index("Age_Group")["Unemployment_Rate (%)"])
    st.bar_chart(df.set_index("Age_Group")["Underemployment_Rate (%)"])
    st.line_chart(df.set_index("Age_Group")["NEET_Rate (%)"])
    st.bar_chart(df.set_index("Age_Group")["Average_Monthly_Wage (PHP)"])

    st.subheader("💼 Job Opportunities")
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
    jobs_df = pd.DataFrame(JOB_LIST, columns=["Job Title", "Monthly Salary"])
    st.table(jobs_df)

    st.subheader("🔐 Login Portal")
    user_type = st.selectbox("Select User Type", ["Applicant", "Admin"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔵 Login"):
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
    with col2:
        st.button("🟢 Create Account")
    with col3:
        if st.button("🔴 Back to Intro"):
            st.session_state["proceed"] = False

# --- Run App ---
if st.session_state["proceed"]:
    main()
else:
    intro_screen()
