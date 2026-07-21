import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# ---------------- USERS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ---------------- UPLOADS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS uploads(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    filename TEXT,
    filepath TEXT,
    file_size REAL,
    rows INTEGER,
    columns INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# ---------------- ANALYSIS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS analysis(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER,

    total_records INTEGER,
    total_columns INTEGER,

    average REAL,
    maximum REAL,
    minimum REAL,
    median REAL,

    missing_values INTEGER,
    duplicate_rows INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(upload_id) REFERENCES uploads(id)
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")