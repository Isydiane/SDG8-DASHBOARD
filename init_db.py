import sqlite3

# Connect to (or create) the database file
conn = sqlite3.connect("applicants.db")
cursor = conn.cursor()

# Create the applicants table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS applicants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age_group TEXT,
    region TEXT,
    job_interest TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Save and close the connection
conn.commit()
conn.close()
