import sqlite3

def init_db():
    conn = sqlite3.connect("careerq.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            email TEXT,
            skills TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT,
            score INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()

def save_user(user_id, email, skills):
    conn = sqlite3.connect("careerq.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO users (user_id, email, skills)
        VALUES (?, ?, ?)
    """, (user_id, email, ",".join(skills)))
    conn.commit()
    conn.close()

def save_jobs(user_id, jobs):
    conn = sqlite3.connect("careerq.db")
    c = conn.cursor()
    
    # Insert new jobs
    for job in jobs:
        c.execute("""
            INSERT INTO jobs (user_id, title, company, location, url, score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("url", ""),
            job.get("score", 0)
        ))
    conn.commit()
    conn.close()

def get_jobs(user_id):
    conn = sqlite3.connect("careerq.db")
    c = conn.cursor()
    c.execute("SELECT title, company, location, url, score FROM jobs WHERE user_id=?", (user_id,))
    jobs = c.fetchall()
    conn.close()
    return jobs