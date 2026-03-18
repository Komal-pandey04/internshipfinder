# db.py — Handles database operations for Internship Finder App

import sqlite3       # For SQLite database
import json           # For JSON data storage
from datetime import datetime  # For timestamps

# Database file path
DB_PATH = "internship_ai.db"

# ---------------- Get DB Connection ---------------- #
def get_connection():
    conn = sqlite3.connect(DB_PATH)   # Connect to database file
    return conn                       # Return connection object

# ---------------- Initialize Tables ---------------- #
def init_db():
    conn = get_connection()           # Open DB connection
    cur = conn.cursor()               # Create cursor to run SQL commands

    # ----- Create Users Table -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Auto ID
            name TEXT NOT NULL,                     -- User name
            email TEXT UNIQUE NOT NULL,             -- Unique email
            password TEXT NOT NULL                  -- User password
        )
    """)

    # ----- Create Uploads Table -----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Auto ID
            user_id INTEGER NOT NULL,               -- Linked user
            resume_name TEXT NOT NULL,              -- File name
            top_internships TEXT,                   -- JSON data
            skill_matches TEXT,                     -- JSON data
            timestamp TEXT,                         -- Upload time
            FOREIGN KEY (user_id) REFERENCES users(id)  -- Relation
        )
    """)

    conn.commit()                      # Save changes
    conn.close()                       # Close DB
    print("Database initialized successfully.")

# ---------------- Add New User ---------------- #
def add_user(name, email, password):
    conn = get_connection()             # Open DB
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, password)         # Insert user safely
    )
    conn.commit()                       # Save
    conn.close()                        # Close

# ---------------- Get User by Email ---------------- #
def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))  # Search email
    user = cur.fetchone()              # Get one result
    conn.close()
    return user                        # Return user data

# ---------------- Save Upload Info ---------------- #
def save_upload(user_id, resume_name, top_internships, skill_matches):
    conn = get_connection()
    cur = conn.cursor()

    # Convert unsupported objects to string (for JSON safety)
    def safe_json(obj):
        if isinstance(obj, (int, float, str, list, dict, bool)) or obj is None:
            return obj
        return str(obj)

    # Convert Python data → JSON text
    top_internships_json = json.dumps(top_internships, default=safe_json)
    skill_matches_json = json.dumps(skill_matches, default=safe_json)

    # Insert upload data
    cur.execute("""
        INSERT INTO uploads (user_id, resume_name, top_internships, skill_matches, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (int(user_id), resume_name, top_internships_json, skill_matches_json,
          datetime.utcnow().isoformat()))  # Save with timestamp

    conn.commit()                       # Save
    conn.close()                        # Close

# ---------------- Get All Uploads for a User #
def get_user_uploads(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT resume_name, top_internships, skill_matches, timestamp FROM uploads WHERE user_id = ?",
        (user_id,)
    )
    rows = cur.fetchall()               # Get all uploads
    conn.close()

    uploads = []                        # Store clean results
    for r in rows:
        uploads.append({
            'resume_name': r[0],
            'top_internships': json.loads(r[1]),   # Convert JSON → dict
            'skill_matches': json.loads(r[2]),
            'timestamp': r[3]
        })
    return uploads                      # Return list of uploads

#Auto Run to Create Tables
if __name__ == "__main__":
    init_db()   # Run only when executed directly
