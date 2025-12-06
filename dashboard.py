import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import sqlite3
from PIL import Image, ImageTk 
import os 

# Global variables for state management
logo_ref = None 
current_role = "Guest" 
# REMOVED: TEMP_APPLICANT_CREDENTIALS is no longer needed

# ---------------------------
# DYNAMIC DATA CONFIGURATION
# ---------------------------
# Initial baseline data
INITIAL_DATA = {
    "Age_Group": ["18-21", "22-25", "26-30"],
    "Unemployment_Rate (%)": [14.5, 10.2, 6.7],
    "Underemployment_Rate (%)": [22.1, 18.4, 12.9],
    "NEET_Rate (%)": [19.0, 16.3, 12.5],
    "Average_Monthly_Wage (PHP)": [9500, 14500, 19800]
}
df = pd.DataFrame(INITIAL_DATA)
BASE_RATES = df.set_index("Age_Group").to_dict('index')

# Define age-dependent reduction factors 
AGE_REDUCTION_FACTORS = {
    "18-21": 0.35,  
    "22-25": 0.25,  
    "26-30": 0.15  
}
RATE_REDUCTION_PER_APPLICANT = 0.25 

# ---------------------------
# UTILITIES
# ---------------------------
def get_age_group(age):
    """Determines the age group from an age value."""
    try:
        age = int(age)
    except (ValueError, TypeError):
        return None
        
    if 18 <= age <= 21:
        return "18-21"
    elif 22 <= age <= 25:
        return "22-25"
    elif 26 <= age <= 30:
        return "26-30"
    return None

# ---------------------------
# DATABASE SETUP
# ---------------------------
conn = sqlite3.connect("applicants.db")
cursor = conn.cursor()

# Table for Applicant Personal/Resume Data
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

# Table for Applicant Credentials
cursor.execute("""
CREATE TABLE IF NOT EXISTS applicant_credentials (
    username TEXT PRIMARY KEY,
    password TEXT,
    applicant_id INTEGER UNIQUE,
    FOREIGN KEY (applicant_id) REFERENCES applicants(id)
)
""")

conn.commit()

try:
    cursor.execute("SELECT age_group FROM applicants LIMIT 1")
except sqlite3.OperationalError:
    cursor.execute("ALTER TABLE applicants ADD COLUMN age_group TEXT")
    conn.commit()

# ---------------------------
# DYNAMIC DATA UPDATE FUNCTIONS
# ---------------------------

def recalculate_economic_data():
    """Recalculates Unemployment and NEET rates based on applicant data."""
    global df
    
    current_counts = {"18-21": 0, "22-25": 0, "26-30": 0}
    
    # Update age_group for old records if necessary
    cursor.execute("SELECT id, age FROM applicants WHERE age_group IS NULL OR age_group NOT IN ('18-21', '22-25', '26-30')")
    updates = [(get_age_group(age), app_id) for app_id, age in cursor.fetchall() if get_age_group(age)]
    if updates:
        cursor.executemany("UPDATE applicants SET age_group = ? WHERE id = ?", updates)
        conn.commit()

    # Get current applicant counts by age group
    cursor.execute("SELECT age_group, COUNT(*) FROM applicants WHERE age_group IS NOT NULL GROUP BY age_group")
    for group, count in cursor.fetchall():
        if group in current_counts:
            current_counts[group] = count
            
    new_data = []
    
    for group in INITIAL_DATA["Age_Group"]:
        base = BASE_RATES[group]
        applicants = current_counts.get(group, 0)
        
        # Determine reduction based on applicant count and age factor
        reduction_factor = AGE_REDUCTION_FACTORS.get(group, 0.25)
        reduction = applicants * reduction_factor
        
        # Calculate new rates, ensuring they don't go below 0.0
        new_unemployment = max(0.0, base["Unemployment_Rate (%)"] - reduction)
        new_neet = max(0.0, base["NEET_Rate (%)"] - reduction * 0.8) 
        
        new_data.append({
            "Age_Group": group,
            "Unemployment_Rate (%)": new_unemployment,
            "Underemployment_Rate (%)": base["Underemployment_Rate (%)"],
            "NEET_Rate (%)": new_neet,
            "Average_Monthly_Wage (PHP)": base["Average_Monthly_Wage (PHP)"]
        })

    df = pd.DataFrame(new_data)


def back_to_dashboard():
    """Returns to the main dashboard menu and recalculates data."""
    open_dashboard_view()

# ---------------------------
# ROLE-BASED ACCESS CONTROL IMPLEMENTATION
# ---------------------------

def setup_dashboard_buttons(role):
    """
    Dynamically grids buttons based on the user's role.
    Layout: (CENTERED)
    Row 0: [    ] [Unemployment] [Underemployment] [NEET Rate] [Job Hiring] [Logout] [    ]
    Row 1: [    ] [  Youth Wages  ] [View Data Table] [Admin] [    ]
    """
    # 1. Clear the button frame by un-gridding all possible buttons
    all_buttons = [btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn_logout]
    for btn in all_buttons:
        btn.grid_forget()

    # 2. Define the list of buttons to display (for check)
    if role == "Admin":
        buttons_in_order = [btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn_logout]
    else: # Applicant/Guest
        buttons_in_order = [btn1, btn2, btn3, btn4, btn5, btn6, btn_logout]

    # --- Row 0 (Top Row: CENTERING 5/6 buttons) ---
    # We will use 9 columns total (0-8). Start at column 1 to push the block right for centering.
    col = 1
    btn1.grid(row=0, column=col, padx=5, pady=5); col += 1 # Unemployment
    btn2.grid(row=0, column=col, padx=5, pady=5); col += 1 # Underemployment
    btn3.grid(row=0, column=col, padx=5, pady=5); col += 1 # NEET Rate
    
    if btn6 in buttons_in_order:
        btn6.grid(row=0, column=col, padx=5, pady=5); col += 1 # Job Hiring
        
    # Logout (btn_logout) is placed at column 6
    if btn_logout in buttons_in_order:
        btn_logout.grid(row=0, column=6, padx=5, pady=5) 
    
    # --- Row 1 (Bottom Row: CENTERING 2/3 buttons) ---
    # We use column 2, 3, and 4 for the three central buttons.
    col = 2 
    
    # Youth Wages (btn4)
    if btn4 in buttons_in_order:
        btn4.grid(row=1, column=col, padx=5, pady=10); col += 1
    
    # View Data Table (btn5)
    if btn5 in buttons_in_order:
        btn5.grid(row=1, column=col, padx=5, pady=10); col += 1
    
    # Admin View (btn7 - Admin Only) - Position beside View Data Table
    if btn7 in buttons_in_order and current_role == "Admin":
        btn7.grid(row=1, column=col, padx=5, pady=10); col += 1

def open_dashboard_view():
    """
    Displays the main dashboard with the TITLE and BUTTONS at the TOP,
    and the DATA TABLE at the BOTTOM.
    """
    recalculate_economic_data() 
    
    # 1. Unpack everything first
    title.pack_forget()
    button_frame.pack_forget()
    plot_frame.pack_forget() 
    
    clear_frame() # Clear any data currently in the plot frame
    
    # 2. Pack the Title frame at the VERY TOP
    title.pack(side="top", fill="x", pady=(20, 10))
    
    # 3. Setup and pack the button frame next, below the title
    setup_dashboard_buttons(current_role)
    button_frame.pack(side="top", fill="x", pady=(0, 10)) 
    
    # 4. Pack the main Data Area (plot_frame) BELOW the buttons
    # The plot_frame expands to fill the remaining space for larger graphs
    plot_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)
    
    # 5. Display the default data view (Table) inside plot_frame 
    show_table_only() 


# ---------------------------
# SINGLE-STEP ACCOUNT CREATION FORM (NO STEP 2)
# ---------------------------
def open_account_creation_form():
    """Collects Username and Password only, then saves and returns to login."""
    clear_frame()
    title.pack_forget()
    button_frame.pack_forget()
    plot_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10) 
    
    tk.Button(plot_frame, text="Back to Login", font=("Arial", 12), command=open_login_screen).pack(side="bottom", pady=20)
    
    form_container = tk.Frame(plot_frame, bg="#f5e6c4")
    form_container.pack(expand=True)
    
    # Title changed to reflect simple account creation
    tk.Label(form_container, text="Create Applicant Account", font=("Arial", 18, "bold"), bg="#f5e6c4", fg="black").pack(pady=15)
    
    fields = [
        "Username", 
        "Password", 
        "Confirm Password"
    ]
    entries = {}

    for field in fields:
        frame = tk.Frame(form_container, bg="#f5e6c4")
        frame.pack(fill="x", padx=10, pady=5)
        tk.Label(frame, text=field + ": ", width=25, anchor="w", font=("Arial", 14), bg="#f5e6c4", fg="black").pack(side="left")
        
        show = "*" if "Password" in field else ""
        ent = tk.Entry(frame, width=30, font=("Arial", 14), show=show)
        ent.pack(side="left")
        entries[field] = ent

    def submit_account_creation():
        username = entries["Username"].get().strip()
        password = entries["Password"].get()
        confirm_password = entries["Confirm Password"].get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and Password cannot be empty.")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Password and Confirm Password must match.")
            return

        cursor.execute("SELECT username FROM applicant_credentials WHERE username=?", (username,))
        if cursor.fetchone():
            messagebox.showerror("Error", "This username is already taken.")
            return
            
        # 1. Insert a placeholder/blank record into the applicants table
        # We cannot insert into applicant_credentials without a foreign key, so we insert the basic applicant record first.
        cursor.execute("""
            INSERT INTO applicants (full_name, age)
            VALUES (?, ?)
        """, (
            username, # Using username as placeholder name
            0 # Using 0 as placeholder age (will be ignored by age_group logic)
        ))
        
        applicant_id = cursor.lastrowid # Get the ID of the new applicant
        
        # 2. Insert credentials and link to the new applicant ID
        cursor.execute("""
            INSERT INTO applicant_credentials (username, password, applicant_id)
            VALUES (?, ?, ?)
        """, (username, password, applicant_id))
        
        conn.commit()
        
        messagebox.showinfo("Success", "Account created successfully! You can now log in. Remember to submit your resume details after logging in.") 
        open_login_screen()

    tk.Button(form_container, text="Create Account", 
              font=("Arial", 14, "bold"), bg="lightblue", 
              command=submit_account_creation).pack(pady=20)


# ---------------------------
# LOGIN SCREEN 
# ---------------------------
def open_login_screen():
    global logo_ref, current_role
    
    # 1. Ensure any other top-level screens (like intro) are closed
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel):
            widget.destroy()

    root.withdraw() 
    current_role = "Guest" # Reset role on logout
    
    login = tk.Toplevel(root)
    login.title("Login")
    login.attributes("-fullscreen", True)
    bg_color = "#f5e6c4" 
    login.configure(bg=bg_color)
    login.bind("<Escape>", lambda e: login.attributes("-fullscreen", False))

    center_frame = tk.Frame(login, bg=bg_color)
    center_frame.pack(expand=True)

    try:
        # NOTE: Make sure this path is correct on your computer
        img = Image.open(r"C:\Users\saveo\Desktop\SDG8\logo.png")
        img = img.resize((350, 350))
        logo = ImageTk.PhotoImage(img)

        logo_label = tk.Label(center_frame, image=logo, bg=bg_color)
        logo_label.image = logo
        logo_label.pack(pady=(10, 20))
    except Exception as e:
        tk.Label(center_frame, text="(Logo not found or path incorrect)", fg="gray", bg=bg_color, font=("Arial", 16)).pack(pady=10)


    tk.Label(center_frame, text="Login Portal", font=("Arial", 19, "bold"), bg=bg_color, fg="black").pack(pady=0)

    tk.Label(center_frame, text="Select User Type:", font=("Arial", 14), bg=bg_color, fg="black").pack()
    user_type = ttk.Combobox(center_frame, values=["Applicant", "Admin"], state="readonly", font=("Arial", 16), width=20) 
    user_type.pack(pady=5) 

    tk.Label(center_frame, text="Username:", font=("Arial", 16), bg=bg_color, fg="black").pack()
    username_entry = tk.Entry(center_frame, font=("Arial", 16), width=22)
    username_entry.pack(pady=5)

    tk.Label(center_frame, text="Password:", font=("Arial", 16), bg=bg_color, fg="black").pack()
    password_entry = tk.Entry(center_frame, show="*", font=("Arial", 16), width=22)
    password_entry.pack(pady=5)

    # UPDATED: Button now calls the single-step account creation form
    def create_account():
        login.destroy()
        root.deiconify() 
        open_account_creation_form()

    def proceed_login():
        global current_role
        utype = user_type.get()
        username = username_entry.get()
        password = password_entry.get()

        if utype == "":
            messagebox.showerror("Error", "Please choose user type.")
            return

        if utype == "Applicant":
            # Login check against applicant_credentials table
            cursor.execute("SELECT password FROM applicant_credentials WHERE username=?", (username,))
            result = cursor.fetchone()
            if result and result[0] == password:
                current_role = "Applicant"
                login.destroy()
                root.deiconify() 
                open_dashboard_view() 
            else:
                messagebox.showerror("Error", "Invalid Applicant credentials")
            return

        if utype == "Admin":
            if username == "admin" and password == "1234":
                current_role = "Admin"
                login.destroy()
                root.deiconify() 
                open_dashboard_view() 
            else:
                messagebox.showerror("Error", "Invalid admin credentials")

    tk.Button(center_frame, text="Login", width=10, height=0, font=("Arial", 16, "bold"),
              command=proceed_login, bg="lightblue").pack(pady=10) 

    # Calls the single-step account creation flow
    tk.Button(center_frame, 
              text="Create Account", # As requested, just "Create Account"
              width=20, height=0, 
              font=("Arial", 16),
              bg="lightgreen", 
              command=create_account).pack(pady=10)
        
    def back_to_intro():
        login.destroy()
        open_intro_screen()

    tk.Button(center_frame, text="Exit Application / Back to Intro", font=("Arial", 12), 
              command=back_to_intro, bg="#ffcccb").pack(pady=10)

# ---------------------------
# CHART UTILITIES / FUNCTIONS 
# ---------------------------
def clear_frame():
    for widget in plot_frame.winfo_children():
        widget.destroy()

def draw_bar_chart(values, labels, title_text, color):
    """Draws a compact, readable bar chart."""
    clear_frame()
    tk.Button(plot_frame, text="Back to Dashboard", font=("Arial", 14), command=open_dashboard_view).pack(side="bottom", pady=20) 

    canvas = tk.Canvas(plot_frame, bg="white")
    canvas.pack(fill="both", expand=True)
    max_val = max(values) if values else 1 
    bar_width = 70 
    spacing = 100 
    
    TOTAL_BAR_WIDTH = (len(values) * bar_width) + ((len(values) - 1) * spacing)
    START_X = 650 - (TOTAL_BAR_WIDTH / 2) 
    
    PLOT_HEIGHT = 350 
    Y_BOTTOM = 500 

    canvas.create_text(650, 40, text=title_text, font=("Arial", 20, "bold"), fill="black")

    for i, val in enumerate(values):
        bar_height = (val / max_val) * PLOT_HEIGHT if max_val > 0 else 0
        
        x1 = START_X + i * (bar_width + spacing) 
        y1 = Y_BOTTOM - bar_height
        x2 = x1 + bar_width
        y2 = Y_BOTTOM

        canvas.create_rectangle(x1, y1, x2, y2, fill=color)
        
        canvas.create_text((x1 + x2) / 2, y2 + 20, text=labels[i], font=("Arial", 12, "bold"))
        canvas.create_text((x1 + x2) / 2, y1 - 10, text=f"{val:.1f}", font=("Arial", 12, "bold"))

def draw_line_chart(values, labels, title_text, color):
    """Draws a compact, readable line chart."""
    clear_frame()
    tk.Button(plot_frame, text="Back to Dashboard", font=("Arial", 14), command=open_dashboard_view).pack(side="bottom", pady=20)

    canvas = tk.Canvas(plot_frame, bg="white")
    canvas.pack(fill="both", expand=True)

    max_val = max(values) if values else 1
    spacing = 150 
    
    TOTAL_WIDTH = (len(values) - 1) * spacing
    START_X = 650 - (TOTAL_WIDTH / 2) 

    PLOT_HEIGHT = 350
    Y_BOTTOM = 500 

    canvas.create_text(650, 40, text=title_text, font=("Arial", 20, "bold"), fill="black")

    points = []
    for i, val in enumerate(values):
        x = START_X + i * spacing
        y = Y_BOTTOM - (val / max_val) * PLOT_HEIGHT if max_val > 0 else Y_BOTTOM
        points.append((x, y))

        canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill=color)
        canvas.create_text(x, y - 25, text=f"{val:.1f}", font=("Arial", 12, "bold"))
        canvas.create_text(x, Y_BOTTOM + 20, text=labels[i], font=("Arial", 12, "bold")) 
        
    for i in range(len(points) - 1):
        canvas.create_line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1],
                           fill=color, width=4)

def plot_unemployment():
    recalculate_economic_data() 
    draw_bar_chart(df["Unemployment_Rate (%)"].tolist(), df["Age_Group"].tolist(), "Youth Unemployment Rate (%) (Dynamic)", "red")

def plot_underemployment():
    recalculate_economic_data() 
    draw_bar_chart(df["Underemployment_Rate (%)"].tolist(), df["Age_Group"].tolist(), "Youth Underemployment Rate (%)", "orange")

def plot_neet():
    recalculate_economic_data() 
    draw_line_chart(df["NEET_Rate (%)"].tolist(), df["Age_Group"].tolist(), "Youth NEET Rate (%) (Dynamic)", "blue")

def plot_wages():
    recalculate_economic_data() 
    draw_bar_chart(df["Average_Monthly_Wage (PHP)"].tolist(), df["Age_Group"].tolist(), "Average Youth Monthly Wage (PHP)", "green")

def show_table_only():
    recalculate_economic_data() 
    clear_frame()
    
    table_wrapper = tk.Frame(plot_frame, bg="#f5e6c4")
    table_wrapper.pack(expand=True, fill="both", padx=20, pady=20)
    
    table = ttk.Treeview(table_wrapper)
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 14, "bold"))
    style.configure("Treeview", font=("Arial", 12), rowheight=30)
    
    cols = list(df.columns)
    table["columns"] = cols
    table["show"] = "headings"
    
    table.column("Age_Group", width=150, anchor="w")
    table.column("Unemployment_Rate (%)", width=200, anchor="center")
    table.column("Underemployment_Rate (%)", width=200, anchor="center")
    table.column("NEET_Rate (%)", width=150, anchor="center")
    table.column("Average_Monthly_Wage (PHP)", width=250, anchor="center")
    
    for col in cols:
        table.heading(col, text=col)

    
    for _, row in df.iterrows():
        display_row = [row['Age_Group'], f"{row['Unemployment_Rate (%)']:.1f}", 
                       f"{row['Underemployment_Rate (%)']:.1f}", f"{row['NEET_Rate (%)']:.1f}", 
                       row['Average_Monthly_Wage (PHP)']]
        table.insert("", "end", values=display_row)
        
    table.pack(fill="both", expand=True) 
    
def show_table():
    recalculate_economic_data() 
    clear_frame()
    tk.Button(plot_frame, text="Back to Dashboard", font=("Arial", 14), command=open_dashboard_view).pack(side="bottom", pady=20)

    table_wrapper = tk.Frame(plot_frame, bg="#f5e6c4")
    table_wrapper.pack(expand=True, fill="both", padx=20, pady=20)
    
    table = ttk.Treeview(table_wrapper)
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 14, "bold"))
    style.configure("Treeview", font=("Arial", 12), rowheight=30)
    
    cols = list(df.columns)
    table["columns"] = cols
    table["show"] = "headings"
    
    table.column("Age_Group", width=150, anchor="w")
    table.column("Unemployment_Rate (%)", width=200, anchor="center")
    table.column("Underemployment_Rate (%)", width=200, anchor="center")
    table.column("NEET_Rate (%)", width=150, anchor="center")
    table.column("Average_Monthly_Wage (PHP)", width=250, anchor="center")
    
    for col in cols:
        table.heading(col, text=col)
    
    for _, row in df.iterrows():
        display_row = [row['Age_Group'], f"{row['Unemployment_Rate (%)']:.1f}", 
                       f"{row['Underemployment_Rate (%)']:.1f}", f"{row['NEET_Rate (%)']:.1f}", 
                       row['Average_Monthly_Wage (PHP)']]
        table.insert("", "end", values=display_row)
        
    table.pack(fill="both", expand=True)

# ---------------------------
# JOB PORTAL 
# ---------------------------
JOB_LIST = [
    ("Cashier (Local Store)", 12000, "18–30 y/o"),
    ("Service Crew", 10000, "18–30 y/o"),
    ("Data Encoder", 14000, "18–30 y/o"),
    ("Barangay Support Staff", 11000, "18–30 y/o"),
    ("Warehouse Helper", 13000, "18–30 y/o"),
    ("Factory Worker (Santa Barbara)", 14000, "18–30 y/o"),
    ("Rice Mill Operator", 16000, "18–30 y/o"),
    ("Tricycle Driver", 12000, "18–30 y/o"),
    ("Municipal Office Clerk", 15000, "18–30 y/o"),
    ("Farm Laborer (Iloilo)", 13000, "18–30 y/o"),
    ("Produce Sorter (Warehouse)", 14500, "18–30 y/o"),
    ("Logistics Helper", 15500, "18–30 y/o"),
    ("Construction Worker", 17000, "18–30 y/o"),
    ("Security Guard (Local)", 18000, "18–30 y/o"),
    ("Retail Store Cashier", 15000, "18–30 y/o"),
    ("Call Center Trainee (Iloilo City)", 18000, "18–30 y/o"),
    ("IT Assistant Intern", 12000, "18–30 y/o"),
    ("Retail Stock Clerk", 12500, "18–30 y/o"),
    ("Motorcycle Delivery Rider", 16000, "18–30 y/o"),
    ("Grocery Bagger", 10000, "18–30 y/o"),
]

def open_job_portal():
    clear_frame()
    tk.Button(plot_frame, text="Back to Dashboard", font=("Arial", 14), command=open_dashboard_view).pack(side="bottom", pady=20)

    tk.Label(plot_frame, text="Available Jobs in Santa Barbara (SDG 8)", font=("Arial", 18, "bold"), bg="#f5e6c4", fg="black").pack(pady=10)

    search_frame = tk.Frame(plot_frame, bg="#f5e6c4")
    search_frame.pack(pady=5)

    tk.Label(search_frame, text="Search Job:", font=("Arial", 14), bg="#f5e6c4").grid(row=0, column=0, padx=5)
    search_entry = tk.Entry(search_frame, width=30, font=("Arial", 14))
    search_entry.grid(row=0, column=1, padx=5)

    job_table = ttk.Treeview(plot_frame)
    job_table["columns"] = ("Job", "Salary", "Qualification")
    job_table["show"] = "headings"

    job_table.heading("Job", text="Job Title")
    job_table.heading("Salary", text="Monthly Salary")
    job_table.heading("Qualification", text="Age Requirement")

    job_table.column("Job", width=400)
    job_table.column("Salary", width=150)
    job_table.column("Qualification", width=150)

    job_table.pack(fill="both", expand=True, padx=20, pady=10)

    def load_jobs(jobs):
        for row in job_table.get_children():
            job_table.delete(row)
        for job, pay, q in jobs:
            job_table.insert("", "end", values=(job, pay, q))

    load_jobs(JOB_LIST)

    def search_jobs():
        key = search_entry.get().lower()
        filtered = [j for j in JOB_LIST if key in j[0].lower()]
        load_jobs(filtered)

    tk.Button(search_frame, text="Search", font=("Arial", 12), command=search_jobs).grid(row=0, column=2, padx=5)

    tk.Button(plot_frame,
              text="Submit Resume / Apply for Job",
              font=("Arial", 14, "bold"),
              bg="lightblue",
              command=lambda: open_applicant_form(JOB_LIST)
              ).pack(pady=10)

# ---------------------------
# APPLICANT FORM + JOB RECOMMENDATIONS 
# ---------------------------
def open_applicant_form(job_list=None):
    clear_frame()
    tk.Button(plot_frame, text="Back", font=("Arial", 14), command=open_job_portal if job_list else open_dashboard_view).pack(side="bottom", pady=20) 

    tk.Label(plot_frame, text="Applicant Resume Form", font=("Arial", 18, "bold"), bg="#f5e6c4", fg="black").pack(pady=10)

    fields = ["Full Name", "Age", "Address", "Skills (comma separated)", "Education", "Work Experience (years)"]
    entries = {}

    for field in fields:
        frame = tk.Frame(plot_frame, bg="#f5e6c4")
        frame.pack(fill="x", padx=10, pady=5)
        tk.Label(frame, text=field+":", width=25, anchor="w", font=("Arial", 14), bg="#f5e6c4").pack(side="left")
        ent = tk.Entry(frame, width=30, font=("Arial", 14))
        ent.pack(side="left")
        entries[field] = ent

    result_label = tk.Label(plot_frame, text="", font=("Arial", 14, "bold"), bg="#f5e6c4")
    result_label.pack(pady=5)

    jobs_listbox = tk.Listbox(plot_frame, width=60, height=8, font=("Arial", 14))
    jobs_listbox.pack(pady=5)

    interview_label = tk.Label(plot_frame, text="", font=("Arial", 14), fg="green", bg="#f5e6c4")
    interview_label.pack(pady=10)

    def recommend_jobs():
        jobs_listbox.delete(0, tk.END)
        interview_label.config(text="")
        result_label.config(text="")

        try:
            age = int(entries["Age"].get())
        except ValueError:
            result_label.config(text="Invalid age.", fg="red")
            return

        age_group = get_age_group(age)
        if not age_group:
            result_label.config(text="Sorry, age not qualified (18–30).", fg="red")
            return

        skills = entries["Skills (comma separated)"].get().lower().split(",")
        try:
            exp = int(entries["Work Experience (years)"].get())
        except ValueError:
            exp = 0

        # --- Resume Submission Logic ---
        # For job portal use, we insert the resume details again (or update existing based on user session)
        # Note: In a real application, you'd update the record linked to the currently logged-in user. 
        # Here, we insert a new record for demonstration, which also drives the rate calculation.
        cursor.execute("""
            INSERT INTO applicants (full_name, age, age_group, address, skills, education, experience)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entries["Full Name"].get(), age, age_group, entries["Address"].get(),
              entries["Skills (comma separated)"].get(),
              entries["Education"].get(), exp))
        conn.commit()

        recalculate_economic_data() 
        # --- End Logic ---
        
        matches = []
        for job, salary, _ in (job_list or JOB_LIST):
            score = 0
            for s in skills:
                if s.strip() in job.lower():
                    score += 2
            score += exp
            if score > 0:
                matches.append((score, job, salary))

        messagebox.showinfo("Success", "Resume submitted and saved! Rates updated (DECREASED, with greater impact on younger age groups).")

        if not matches:
            result_label.config(text="No suitable jobs found.", fg="red")
            return

        matches.sort(reverse=True)
        result_label.config(text="Recommended Jobs:", fg="black")
        for score, job, sal in matches[:5]:
            jobs_listbox.insert(tk.END, f"{job}  -  PHP {sal}/month")

    def select_job(event):
        try:
            selected = jobs_listbox.get(jobs_listbox.curselection())
            job_name = selected.split("  -  ")[0]
            interview_label.config(text=f"Interview scheduled for:\n\n{job_name}\n📅 Tomorrow at 9:00 AM")
        except:
            return

    jobs_listbox.bind("<<ListboxSelect>>", select_job)

    tk.Button(plot_frame,
              text="Submit Resume / Get Recommendations",
              font=("Arial", 14, "bold"),
              bg="lightblue",
              command=recommend_jobs
              ).pack(pady=15)

# ---------------------------
# ADMIN VIEW + DELETE 
# ---------------------------
def view_applicants():
    # Enforce Admin Role Check
    if current_role != "Admin":
        messagebox.showerror("Access Denied", "Only Admin users can view the Applicant Database.")
        open_dashboard_view()
        return
        
    clear_frame()
    recalculate_economic_data()
    
    tk.Button(plot_frame, text="Back to Dashboard", font=("Arial", 14), command=open_dashboard_view).pack(side="bottom", pady=20)

    tk.Label(plot_frame, text="Applicant Database (Admin Panel)", font=("Arial", 18, "bold"), bg="#f5e6c4", fg="black").pack(pady=10)

    table = ttk.Treeview(plot_frame)
    table["columns"] = ("ID","Name","Age","Age Group","Address","Skills","Education","Experience")
    table["show"] = "headings"

    for col in table["columns"]:
        table.heading(col, text=col)
        table.column(col, width=120)
    table.column("ID", width=50)

    table.pack(fill="both", expand=True, padx=20, pady=10)

    cursor.execute("SELECT id, full_name, age, age_group, address, skills, education, experience FROM applicants")
    for row in cursor.fetchall():
        table.insert("", "end", values=row)

    def delete_selected():
        selected = table.selection()
        if not selected:
            messagebox.showinfo("Error", "No applicant selected.")
            return
        
        item = table.item(selected)
        applicant_id = item["values"][0]
        
        # Delete from both tables
        cursor.execute("DELETE FROM applicants WHERE id=?", (applicant_id,))
        cursor.execute("DELETE FROM applicant_credentials WHERE applicant_id=?", (applicant_id,))
        conn.commit()
        table.delete(selected)
        
        recalculate_economic_data()
        
        messagebox.showinfo("Deleted", f"Applicant ID {applicant_id} removed. Rates have been updated (INCREASED, with greater impact on younger age groups).")

    tk.Button(plot_frame, text="Delete Selected Applicant (Increases Rates)", bg="red", fg="white",
              font=("Arial", 14, "bold"), command=delete_selected).pack(pady=10)

# ---------------------------
# INTRO SCREEN FUNCTION (UPDATED)
# ---------------------------
def open_intro_screen():
    global logo_ref
    
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel):
            widget.destroy()

    if root.winfo_viewable():
        root.withdraw() 
    
    intro = tk.Toplevel(root)
    intro.title("Introduction")
    intro.attributes("-fullscreen", True)
    bg_color = "#f5e6c4" 
    intro.configure(bg=bg_color)
    intro.bind("<Escape>", lambda e: intro.destroy() and open_login_screen())

    center_frame = tk.Frame(intro, bg=bg_color)
    center_frame.pack(expand=True)
    
     # 1. Main Title
    tk.Label(center_frame, 
             text="SDG 8: DECENT WORK AND ECONOMIC GROWTH", 
             font=("Arial", 28, "bold"), 
             bg=bg_color, 
             fg="#333").pack(pady=(20, 5))

    # 2. Sub Title
    tk.Label(center_frame, 
             text="Supporting Youth Economic Data Dashboard - PESO Santa Barbara", 
             font=("Arial", 20, "italic"), 
             bg=bg_color, 
             fg="#004d40").pack(pady=(0, 30)) 
    
    # 3. Logo
    try:
        # NOTE: Make sure this path is correct on your computer
        img = Image.open(r"C:\Users\saveo\Desktop\SDG8\logo.png")
        img = img.resize((350, 350))
        logo = ImageTk.PhotoImage(img)

        logo_label = tk.Label(center_frame, image=logo, bg=bg_color)
        logo_label.image = logo
        logo_label.pack(pady=(10, 20))
    except Exception as e:
        tk.Label(center_frame, text="(Logo not found)", fg="gray", bg=bg_color, font=("Arial", 16)).pack(pady=20)
        print("Error loading logo:", e)
        
    # 4. NEW EXPLANATION LABEL 
    tk.Label(center_frame, 
             text="This aims to create safe, fair, and productive jobs for everyone while\n helping economies grow sustainably. It focuses on protecting workers’ rights,\n supporting businesses, reducing unemployment, and ensuring equal opportunities for all.", 
             font=("Arial", 18), 
             bg=bg_color, 
             fg="black", 
             justify=tk.CENTER 
             ).pack(pady=(10, 50)) 
        
    # 5. Action Buttons Frame 
    action_frame = tk.Frame(center_frame, bg=bg_color)
    action_frame.pack(pady=10) 
    
    def proceed_to_login():
        intro.destroy()
        open_login_screen()
        
    tk.Button(action_frame, 
              text="Click to Proceed to Login", 
              font=("Arial", 15, "bold"), 
              bg="#66bb6a", 
              fg="white", 
              padx=0, pady=0, 
              command=proceed_to_login).grid(row=0, column=0, padx=20)
              
    tk.Button(action_frame, 
              text="Exit Application", 
              font=("Arial", 16), 
              bg="#ff6666", 
              fg="white", 
              padx=0, pady=0, 
              command=root.destroy).grid(row=0, column=1, padx=20)
    
# ---------------------------
# STARTUP WIDGET INITIALIZATION 
# ---------------------------

root = tk.Tk()
root.title("Youth Economic Data Dashboard - Peso Santa Barbara")
root.attributes("-fullscreen", True)
root.configure(bg="#f5e6c4")
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

# Frames
title = tk.Label(root, text="Youth Economic Data Dashboard - Peso Santa Barbara", 
                 font=("Arial", 24, "bold"), bg="#f5e6c4", fg="#333")
button_frame = tk.Frame(root, bg="#f5e6c4") 
plot_frame = tk.Frame(root, bg="#f5e6c4") 

# Global Button Objects
btn_font = ("Arial", 14)
btn1 = tk.Button(button_frame, text="Unemployment Rate", width=25, height=2, font=btn_font, command=plot_unemployment)
btn2 = tk.Button(button_frame, text="Underemployment Rate", width=25, height=2, font=btn_font, command=plot_underemployment)
btn3 = tk.Button(button_frame, text="NEET Rate", width=25, height=2, font=btn_font, command=plot_neet)
btn4 = tk.Button(button_frame, text="Youth Wages", width=25, height=2, font=btn_font, command=plot_wages)
btn5 = tk.Button(button_frame, text="View Data Table", width=25, height=2, font=btn_font, command=show_table)
btn6 = tk.Button(button_frame, text="Job Hiring (SDG 8)", width=25, height=2, font=btn_font, command=open_job_portal)
btn7 = tk.Button(button_frame, text="Admin - View Applicants", width=25, height=2, font=btn_font, command=view_applicants)

btn_logout = tk.Button(button_frame, text="Logout / Back to Login", width=25, height=2, 
                        font=btn_font, bg="tomato", fg="white", command=open_login_screen)


# ---------------------------
# START THE APPLICATION
# ---------------------------
recalculate_economic_data() 
root.after(200, open_intro_screen)
root.mainloop()
