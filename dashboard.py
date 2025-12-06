import streamlit as st
import sqlite3
import pandas as pd

# --- Page config and global styles ---
st.set_page_config(page_title="Supporting Youth Economic Data Dashboard – PESO Santa Barbara", page_icon="📊", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f5e6c4; }
    .center-logo {
        display: flex; justify-content: center; align-items: center;
        margin-top: -50px; margin-bottom: 10px;
    }
    .title-text {
        font-size: 32px; font-weight: 1000; text-align: center; color: #4e342e; margin: 6px 0;
    }
    .subtitle-text {
        font-size: 20px; text-align: center; color: #4e342e; margin: 2px 0 10px 0;
    }
    .description-text {
        font-size: 16px; text-align: center; color: #4e342e; margin: 8px auto 22px auto; max-width: 800px; line-height: 1.5;
    }
    .section-title { text-align: center; font-weight: 600; color:#4e342e; margin: 10px 0 18px 0; }
    </style>
""", unsafe_allow_html=True)

# --- Database setup ---
conn = sqlite3.connect("applicants.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS applicant_credentials (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS applicants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT,
    age INTEGER,
    age_group TEXT,
    address TEXT,
    skills TEXT,
    education TEXT,
    experience INTEGER
)
""")
conn.commit()

# --- Initial data and helpers ---
INITIAL_DATA = {
    "Age_Group": ["18-21", "22-25", "26-30"],
    "Unemployment_Rate (%)": [14.5, 10.2, 6.7],
    "Underemployment_Rate (%)": [22.1, 18.4, 12.9],
    "NEET_Rate (%)": [19.0, 16.3, 12.5],
    "Average_Monthly_Wage (PHP)": [9500, 14500, 19800]
}
df_base = pd.DataFrame(INITIAL_DATA)

def get_age_group(age: int):
    if 18 <= age <= 21: return "18-21"
    if 22 <= age <= 25: return "22-25"
    if 26 <= age <= 30: return "26-30"
    return None

# --- Intro screen (matches your design) ---
def intro_screen():
    st.markdown('<div class="center-logo">', unsafe_allow_html=True)
    st.image("logo.png", width=300)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<p class="title-text">SDG 8: DECENT WORK AND ECONOMIC GROWTH</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-text">Supporting Youth Economic Data Dashboard – PESO Santa Barbara</p>', unsafe_allow_html=True)

    st.markdown("""
        <p class="description-text">
        This aims to create safe, fair, and productive jobs for everyone while helping economies grow sustainably.<br>
        It focuses on protecting workers’ rights, supporting businesses, reducing unemployment, and ensuring equal opportunities for all.
        </p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Click to Proceed to Login"):
            st.session_state["stage"] = "login"
    with col2:
        if st.button("Exit Application"):
            st.info("You may now close this tab.")

# --- Account creation (enforced before applicant login) ---
def create_account(username: str, password: str):
    if not username or not password:
        st.error("Please enter a username and password.")
        return False
    try:
        cursor.execute("INSERT INTO applicant_credentials (username, password) VALUES (?, ?)", (username.strip(), password))
        conn.commit()
        st.success("Account created successfully! You can now log in.")
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose another.")
        return False

# --- Applicant dashboard ---
def show_applicant_dashboard(username: str):
    st.markdown('<h3 class="section-title">Applicant Dashboard</h3>', unsafe_allow_html=True)
    st.write("Submit your resume and view job opportunities and recommendations.")

    full_name = st.text_input("Full Name")
    age = st.number_input("Age", min_value=18, max_value=30, value=18)
    address = st.text_input("Address")
    skills = st.text_input("Skills (comma separated)")
    education = st.text_input("Education")
    experience = st.number_input("Work Experience (years)", min_value=0, value=0)

    if st.button("Submit Resume"):
        age_group = get_age_group(int(age))
        cursor.execute("""
            INSERT INTO applicants (full_name, age, age_group, address, skills, education, experience)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (full_name.strip(), int(age), age_group, address.strip(), skills.strip(), education.strip(), int(experience)))
        conn.commit()
        st.success("Resume submitted successfully!")

    st.markdown('<h4 class="section-title">Job Opportunities</h4>', unsafe_allow_html=True)
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

# --- Admin dashboard ---
def show_admin_dashboard():
    st.markdown('<h3 class="section-title">Admin Dashboard</h3>', unsafe_allow_html=True)
    try:
        applicants = pd.read_sql("SELECT * FROM applicants", conn)
    except Exception:
        applicants = pd.DataFrame(columns=["id","full_name","age","age_group","address","skills","education","experience"])
    st.dataframe(applicants, use_container_width=True)

    st.markdown('<h4 class="section-title">Youth Employment Charts</h4>', unsafe_allow_html=True)
    st.bar_chart(df_base.set_index("Age_Group")["Unemployment_Rate (%)"])
    st.bar_chart(df_base.set_index("Age_Group")["Underemployment_Rate (%)"])
    st.line_chart(df_base.set_index("Age_Group")["NEET_Rate (%)"])
    st.bar_chart(df_base.set_index("Age_Group")["Average_Monthly_Wage (PHP)"])

# --- Login screen (logo centered, correct flow) ---
def login_screen():
    st.markdown('<div class="center-logo">', unsafe_allow_html=True)
    st.image("logo.png", width=230)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<h3 style='text-align:center; color:#4e342e;'>Login Portal</h3>", unsafe_allow_html=True)

    user_type = st.selectbox("Select User Type:", ["Applicant", "Admin"])
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔵 Login"):
            if user_type == "Admin" and username == "admin" and password == "1234":
                st.success("Welcome Admin!")
                show_admin_dashboard()
            elif user_type == "Applicant":
                cursor.execute("SELECT password FROM applicant_credentials WHERE username=?", (username.strip(),))
                row = cursor.fetchone()
                if row:
                    if row[0] == password:
                        st.success(f"Welcome {username}!")
                        show_applicant_dashboard(username)
                    else:
                        st.error("Incorrect password.")
                else:
                    st.error("No account found. Please create an account first.")
    with col2:
        if st.button("Create Account"):
            create_account(username, password)
    with col3:
        if st.button("Back to Intro"):
            st.session_state["stage"] = "intro"

# --- Router ---
if "stage" not in st.session_state:
    st.session_state["stage"] = "intro"

if st.session_state["stage"] == "intro":
    intro_screen()
elif st.session_state["stage"] == "login":
    login_screen()
