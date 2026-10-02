import sqlite3


def create_database():
    connection = sqlite3.connect("internflow.db")

    cursor = connection.cursor()

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
            status TEXT DEFAULT 'Not Applied'
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")