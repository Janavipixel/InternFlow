import sqlite3


def create_database():

    connection = sqlite3.connect("internflow.db")
    cursor = connection.cursor()

    # =========================================
    # INTERNSHIPS TABLE
    # =========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            skills TEXT,
            location TEXT,
            stipend TEXT,
            deadline TEXT,
            eligibility TEXT,
            application_link TEXT,
            match_percentage INTEGER,
            status TEXT DEFAULT 'Not Applied',
            saved INTEGER DEFAULT 0
        )
    """)

    # Add saved column if old database doesn't have it
    cursor.execute("PRAGMA table_info(internships)")
    columns = [column[1] for column in cursor.fetchall()]

    if "saved" not in columns:
        cursor.execute("""
            ALTER TABLE internships
            ADD COLUMN saved INTEGER DEFAULT 0
        """)

    if "match_percentage" not in columns:
            cursor.execute("""
            ALTER TABLE internships
            ADD COLUMN match_percentage INTEGER
        """)

    # =========================================
    # STUDENT PREFERENCES TABLE
    # =========================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            student_skills TEXT,
            preferred_domain TEXT,
            internship_type TEXT,
            locations TEXT,
            minimum_stipend INTEGER,
            maximum_duration TEXT,
            payment_type TEXT,
            work_mode TEXT,
            study_year TEXT,
            availability TEXT,
            deadline_preference TEXT,
            company_preference TEXT,
            email_frequency TEXT,
            last_email_sent TEXT
        )
    """)

    # Add last_email_sent if old database doesn't have it
    cursor.execute("PRAGMA table_info(student_preferences)")
    columns = [column[1] for column in cursor.fetchall()]

    if "last_email_sent" not in columns:
        cursor.execute("""
            ALTER TABLE student_preferences
            ADD COLUMN last_email_sent TEXT
        """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")
