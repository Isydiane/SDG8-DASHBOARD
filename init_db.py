import sqlite3

conn = sqlite3.connect("applicants.db")
cursor = conn.cursor()

# Create applicant_credentials table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS applicant_credentials (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )
""")

# Create applicants table
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

# Optional: Insert sample applicant account
cursor.execute("INSERT OR IGNORE INTO applicant_credentials (username, password) VALUES (?, ?)", ("faith", "1234"))

conn.commit()
conn.close()
