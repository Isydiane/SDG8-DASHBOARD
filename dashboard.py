import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import uuid
from PIL import Image

# ---------------------------
# Config & styles
# ---------------------------
st.set_page_config(page_title="Supporting Youth Economic Data Dashboard – PESO Santa Barbara",
                   page_icon="📊", layout="centered")

st.markdown("""
    <style>
    /* Page background */
    .stApp { background-color: #f5e6c4; }

    /* Logo container */
    .center-logo {
        display: flex; justify-content: center; align-items: center;
        margin-top: 0px; margin-bottom: 0px; width: 60px;
    }

    /* Titles & readability */
    .title-text {
        font-size: 36px !important;
        font-weight: 900 !important;
        text-align: center;
        color: #2f2f2f !important;
        margin: 6px 0 8px 0;
    }
    .subtitle-text {
        font-size: 20px !important;
        text-align: center;
        color: #3b3b3b !important;
        margin: 2px 0 16px 0;
    }
    .description-text {
        font-size: 16px !important;
        text-align: center;
        color: #4e342e !important;
        margin: 8px auto 22px auto;
        max-width: 900px;
        line-height: 1.5;
    }
    .section-title {
        text-align: left !important;
        font-weight: 800 !important;
        color:#2d2d2d !important;
        margin: 18px 0 12px 0 !important;
        font-size: 22px !important;
    }

    /* Remove white card backgrounds previously used */
    .card {
        background-color: transparent !important;
        box-shadow: none !important;
        border: none !important;
        padding: 0px !important;
        margin: 0px !important;
    }

    /* Make search input larger and more readable */
    input[type="text"] {
        font-size: 18px !important;
        padding: 12px !important;
    }

    /* Global button styling to be dark rounded (applies to Streamlit buttons) */
    .stButton>button {
        background-color: #111214 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        padding: 10px 18px !important;
        font-size: 16px !important;
        border: 0px !important;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
    }

    /* Job "chip" look when we display them as buttons */
    .job-chip {
        display:inline-block;
        padding:10px 16px;
        margin:8px 8px 8px 0;
        border-radius:14px;
        background:#1f1f1f;
        color:#fff;
        font-weight:600;
        font-size:15px;
    }

    /* Table text improvements */
    .stDataFrame table td, .stDataFrame table th {
        font-size: 14px !important;
        color: #2b2b2b !important;
    }

    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Database setup
# ---------------------------
DB = "applicants.db"
PHOTO_DIR = "photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

conn = sqlite3.connect(DB, check_same_thread=False)
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
    experience INTEGER,
    job_applied TEXT,
    photo_path TEXT
)
""")
conn.commit()

def ensure_column(table, column, col_def):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cursor.fetchall()]
    if column not in cols:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
        conn.commit()

ensure_column("applicants", "job_applied", "TEXT")
ensure_column("applicants", "photo_path", "TEXT")

# ---------------------------
# Initial data & helpers
# ---------------------------
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

def save_photo(uploaded_file):
    if uploaded_file is None:
        return None
    ext = uploaded_file.name.split(".")[-1]
    fname = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(PHOTO_DIR, fname)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

# ---------------------------
# Intro screen
# ---------------------------
def intro_screen():
    st.markdown('<p class="title-text">SDG 8: DECENT WORK AND ECONOMIC GROWTH</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle-text">Supporting Youth Economic Data Dashboard – PESO Santa Barbara</p>', unsafe_allow_html=True)
    st.markdown('<div class="center-logo">', unsafe_allow_html=True)
    try:
        st.image("logo.png", width=320)
    except Exception:
        pass
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("""
        <p class="description-text">
        This aims to create safe, fair, and productive jobs for everyone while helping economies grow sustainably.
        It focuses on protecting workers’ rights, supporting businesses, reducing unemployment, and ensuring equal opportunities for all.
        </p>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Click to Proceed to Login", use_container_width=True):
            st.session_state["stage"] = "login"
        if st.button("Exit Application", use_container_width=True):
            st.info("You may now close this tab.")

# ---------------------------
# Create account
# ---------------------------
def create_account(username: str, password: str):
    if not username or not password:
        st.error("Please enter a username and password.")
        return False
    try:
        cursor.execute("INSERT INTO applicant_credentials (username, password) VALUES (?, ?)", (username.strip(), password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose another.")
        return False

# ---------------------------
# Jobs: searchable & clickable (more jobs)
# ---------------------------
JOB_LIST_SIMPLE = [
    "Cashier (Local Store)",
    "Service Crew",
    "Data Encoder",
    "Barangay Support Staff",
    "Warehouse Helper",
    "Factory Worker (Santa Barbara)",
    "Rice Mill Operator",
    "Municipal Office Clerk",
    "Call Center Trainee (Iloilo City)",
    "IT Assistant Intern",
    "Barista",
    "Sales Associate",
    "Receptionist",
    "Security Guard",
    "Warehouse Forklift Operator",
    "Machine Operator",
    "Housekeeping Staff",
    "Driver (Delivery)",
    "Inventory Clerk",
    "Customer Service Representative",
    "Computer Operator",
    "Field Enumerator"
]

def job_selection_ui():
    # no white card around header now
    st.markdown("<h4 style='color:#2d2d2d; margin-bottom:4px;'>Find a Job</h4>", unsafe_allow_html=True)
    search = st.text_input("🔍 Search job...", key="job_search", placeholder="Type job title to filter")
    filtered = [j for j in JOB_LIST_SIMPLE if search.lower() in j.lower()] if search else JOB_LIST_SIMPLE.copy()

    # present clickable job buttons in rows (3 columns)
    st.write("")  # spacing
    cols = st.columns(3)
    selected_job = None
    for i, job in enumerate(filtered):
        with cols[i % 3]:
            if st.button(job, key=f"job_{i}"):
                selected_job = job

    # save/recall in session
    if selected_job:
        st.session_state["selected_job"] = selected_job

    selected_job = st.session_state.get("selected_job", None)
    if selected_job:
        st.success(f"Selected job: {selected_job}")

    return selected_job

# ---------------------------
# Applicant Dashboard
# ---------------------------
def show_applicant_dashboard(username: str):
    st.markdown('<h3 class="section-title">Youth Economic Data Dashboard – PESO Santa Barbara</h3>', unsafe_allow_html=True)
    st.markdown('<h4 class="section-title">Applicant Dashboard</h4>', unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 1) Select a Job (required)", unsafe_allow_html=True)
    selected_job = job_selection_ui()
    st.markdown("</div>", unsafe_allow_html=True)

    if not selected_job:
        st.info("Please select a job first to proceed with application.")
        return

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 2) Resume Submission (choose one option)", unsafe_allow_html=True)
    option = st.radio("", ["I have a resume picture (upload only)", "I don't have a resume picture (fill the form)"], index=0)

    # Option A: upload resume picture only
    if option.startswith("I have"):
        st.write("Upload a photo (scan) of your resume. If you already have one, you don't need to fill the form.")
        uploaded = st.file_uploader("Upload resume picture (jpg/png)", type=["jpg","jpeg","png"], key="resume_upload")
        if st.button("Submit Resume (upload only)"):
            if uploaded is None:
                st.error("Please upload a resume picture before submitting.")
            else:
                path = save_photo(uploaded)
                cursor.execute("""
                    INSERT INTO applicants (full_name, age, age_group, address, skills, education, experience, job_applied, photo_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, ("N/A", 0, None, "N/A", "N/A", "N/A", 0, selected_job, path))
                conn.commit()
                st.success("Resume (image) submitted successfully! You may log out or apply for another job.")
                if "selected_job" in st.session_state:
                    del st.session_state["selected_job"]

    # Option B: fill the form, optional photo upload
    else:
        st.write("Fill the form below. Optionally upload a 1×1 photo.")
        with st.form("applicant_form", clear_on_submit=False):
            full_name = st.text_input("Full Name", key="form_name")
            age = st.number_input("Age", min_value=15, max_value=60, step=1, key="form_age")
            address = st.text_area("Address", key="form_address")
            skills = st.text_input("Skills (comma separated)", key="form_skills")
            education = st.text_input("Education", key="form_education")
            experience = st.number_input("Work Experience (years)", min_value=0, max_value=50, key="form_experience")
            photo = st.file_uploader("Upload 1x1 Photo (optional)", type=["jpg","jpeg","png"], key="form_photo")
            submitted = st.form_submit_button("Submit Resume (form)")

            if submitted:
                if not full_name or not address:
                    st.error("Full name and address are required.")
                else:
                    photo_path = save_photo(photo) if photo else None
                    age_group = get_age_group(int(age)) if age else None
                    cursor.execute("""
                        INSERT INTO applicants (full_name, age, age_group, address, skills, education, experience, job_applied, photo_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (full_name.strip(), int(age), age_group, address.strip(), skills.strip(), education.strip(), int(experience), selected_job, photo_path))
                    conn.commit()
                    st.success("Application submitted successfully!")
                    if "selected_job" in st.session_state:
                        del st.session_state["selected_job"]

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("View Youth Charts", use_container_width=True):
            st.session_state["stage"] = "charts"
    with col2:
        if st.button("Logout / Back to Login", use_container_width=True):
            for k in ["username", "selected_job", "job_search"]:
                if k in st.session_state: del st.session_state[k]
            st.session_state["stage"] = "login"

# ---------------------------
# Admin panel (view photos)
# ---------------------------
def show_admin_panel():
    st.markdown('<h3 class="section-title">Youth Economic Data Dashboard – PESO Santa Barbara</h3>', unsafe_allow_html=True)
    st.markdown('<h4 class="section-title">Applicant Database (Admin Panel)</h4>', unsafe_allow_html=True)

    try:
        applicants = pd.read_sql("SELECT * FROM applicants", conn)
    except Exception:
        applicants = pd.DataFrame(columns=["id","full_name","age","age_group","address","skills","education","experience","job_applied","photo_path"])

    if applicants.empty:
        st.info("No applicants found in the database.")
    else:
        st.dataframe(applicants[["id","full_name","job_applied","photo_path"]].rename(columns={"job_applied":"Job Applied","photo_path":"Photo Path"}), use_container_width=True)

        applicant_ids = applicants["id"].tolist()
        chosen = st.selectbox("Select Applicant ID to view details", options=applicant_ids)

        if st.button("View Applicant Details"):
            rec = applicants[applicants["id"]==chosen].iloc[0]
            st.write("**Full Name:**", rec["full_name"])
            st.write("**Age:**", rec["age"])
            st.write("**Age Group:**", rec["age_group"])
            st.write("**Address:**", rec["address"])
            st.write("**Skills:**", rec["skills"])
            st.write("**Education:**", rec["education"])
            st.write("**Experience (yrs):**", rec["experience"])
            st.write("**Job Applied:**", rec["job_applied"])
            photo_path = rec.get("photo_path", None)
            if photo_path and isinstance(photo_path, str) and os.path.exists(photo_path):
                st.image(photo_path, width=250, caption="Uploaded Photo / Resume")
            else:
                st.warning("No photo available for this applicant.")

        if st.button("Delete selected applicant"):
            if chosen:
                cursor.execute("DELETE FROM applicants WHERE id=?", (int(chosen),))
                conn.commit()
                st.success("Applicant deleted.")
                st.experimental_rerun()

    st.markdown("---")
    if st.button("Back to Login"):
        st.session_state["stage"] = "login"

# ---------------------------
# Youth charts
# ---------------------------
def show_youth_charts():
    st.markdown('<h3 class="section-title">Youth Economic Data Dashboard – PESO Santa Barbara</h3>', unsafe_allow_html=True)
    st.markdown('<h4 class="section-title">Youth Economic Charts</h4>', unsafe_allow_html=True)

    df = df_base.copy()

    st.markdown("### 📊 Select a Chart to View")

    chart_choice = st.radio(
        "",
        [
            "Unemployment Rate",
            "Underemployment Rate",
            "NEET Rate",
            "Average Youth Wages",
            "View Data Table"
        ],
        index=0,
        label_visibility="collapsed"
    )

    if chart_choice == "Unemployment Rate":
        fig = px.bar(
            df,
            x="Age_Group",
            y="Unemployment_Rate (%)",
            title="Unemployment Rate by Age Group",
            text="Unemployment_Rate (%)",
            color_discrete_sequence=["#1f77b4"]
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(title_x=0.5, font=dict(size=16, color="#2d2d2d"), yaxis_title="Rate (%)")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_choice == "Underemployment Rate":
        fig = px.bar(
            df,
            x="Age_Group",
            y="Underemployment_Rate (%)",
            title="Underemployment Rate by Age Group",
            text="Underemployment_Rate (%)",
            color_discrete_sequence=["#2ca02c"]
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(title_x=0.5, font=dict(size=16, color="#2d2d2d"), yaxis_title="Rate (%)")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_choice == "NEET Rate":
        fig = px.line(
            df,
            x="Age_Group",
            y="NEET_Rate (%)",
            markers=True,
            title="NEET Rate by Age Group",
            color_discrete_sequence=["#ff7f0e"]
        )
        fig.update_layout(title_x=0.5, font=dict(size=16, color="#2d2d2d"), yaxis_title="Rate (%)")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_choice == "Average Youth Wages":
        fig = px.bar(
            df,
            x="Age_Group",
            y="Average_Monthly_Wage (PHP)",
            title="Average Monthly Wage by Age Group (PHP)",
            text="Average_Monthly_Wage (PHP)",
            color_discrete_sequence=["#9467bd"]
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(title_x=0.5, font=dict(size=16, color="#2d2d2d"), yaxis_title="Monthly Wage (PHP)")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_choice == "View Data Table":
        st.dataframe(df, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("⬅ Back to Applicant Dashboard", use_container_width=True):
            st.session_state["stage"] = "dashboard"
    with col2:
        if st.button("Logout / Back to Login", use_container_width=True):
            st.session_state["stage"] = "login"

# ---------------------------
# Login screen
# ---------------------------
def login_screen():
    st.markdown('<div class="center-logo">', unsafe_allow_html=True)
    try:
        st.image("logo.png", width=260)
    except Exception:
        pass
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:#4e342e;'>Login Portal</h3>", unsafe_allow_html=True)

    user_type = st.selectbox("Select User Type:", ["Applicant", "Admin"])
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("Login", use_container_width=True):
            if user_type == "Admin" and username == "admin" and password == "1234":
                st.success("Welcome Admin!")
                st.session_state["stage"] = "admin_panel"
            elif user_type == "Applicant":
                cursor.execute("SELECT password FROM applicant_credentials WHERE username=?", (username.strip(),))
                row = cursor.fetchone()
                if row is None:
                    st.error("No account found. Please create an account first.")
                else:
                    if row[0] == password:
                        st.success(f"Welcome {username}!")
                        st.session_state["username"] = username
                        st.session_state["stage"] = "dashboard"
                    else:
                        st.error("Incorrect password.")

        if st.button("Create Account", use_container_width=True):
            if not username or not password:
                st.error("Please enter a username and password.")
            else:
                account_created = create_account(username, password)
                if account_created:
                    st.success(f"Welcome {username}! Your account has been created.")
                    st.session_state["username"] = username
                    st.session_state["stage"] = "dashboard"

        if st.button("Back to Intro", use_container_width=True):
            st.session_state["stage"] = "intro"

# ---------------------------
# Router
# ---------------------------
if "stage" not in st.session_state:
    st.session_state["stage"] = "intro"

if st.session_state["stage"] == "intro":
    intro_screen()
elif st.session_state["stage"] == "login":
    login_screen()
elif st.session_state["stage"] == "dashboard":
    username = st.session_state.get("username", "Guest")
    show_applicant_dashboard(username)
elif st.session_state["stage"] == "admin":
    show_admin_panel()
elif st.session_state["stage"] == "admin_panel":
    show_admin_panel()
elif st.session_state["stage"] == "charts":
    show_youth_charts()
