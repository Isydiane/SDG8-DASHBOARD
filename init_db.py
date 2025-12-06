import sqlite3

conn = sqlite3.connect("applicants.db")
cursor = conn.cursor()

# --- Applicant credentials table ---
cursor.execute("""
    CREATE TABLE IF NOT EXISTS applicant_credentials (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
""")

# --- Applicants table ---
cursor.execute("""
    CREATE TABLE IF NOT EXISTS applicants (
        full_name TEXT,
        age INTEGER,
        age_group TEXT,
        address TEXT,
        skills TEXT,
        education TEXT,
        experience INTEGER
    )
""")

# --- Insert sample applicant account (for testing) ---
cursor.execute("INSERT OR IGNORE INTO applicant_credentials (username, password) VALUES (?, ?)", ("faith", "1234"))

conn.commit()
conn.close()
