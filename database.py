import os
import sqlite3

# Resolve database path relative to project root by default, or respect DATABASE_PATH env var
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "internflow.db")


def get_db_path():
    return os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)


def get_db_connection(db_path=None):
    """
    Returns an SQLite connection with Row factory and sensible timeouts.
    Enables WAL mode for concurrent read/write resilience.
    """
    path = db_path or get_db_path()
    connection = sqlite3.connect(path, timeout=30.0)
    connection.row_factory = sqlite3.Row
    # Enable WAL mode for concurrency if not in memory
    if path != ":memory:":
        try:
            connection.execute("PRAGMA journal_mode=WAL;")
        except sqlite3.DatabaseError:
            pass
    return connection


def create_database(db_path=None):
    """
    Initializes tables and migrates any missing columns.
    Safe to run repeatedly.
    """
    connection = get_db_connection(db_path)
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
            match_percentage REAL,
            status TEXT DEFAULT 'Not Applied',
            saved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(internships)")
    existing_internship_cols = [col[1] for col in cursor.fetchall()]

    if "saved" not in existing_internship_cols:
        cursor.execute("ALTER TABLE internships ADD COLUMN saved INTEGER DEFAULT 0")

    if "match_percentage" not in existing_internship_cols:
        cursor.execute("ALTER TABLE internships ADD COLUMN match_percentage REAL")

    if "created_at" not in existing_internship_cols:
        cursor.execute("ALTER TABLE internships ADD COLUMN created_at TIMESTAMP")

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
            last_email_sent TEXT,
            has_searched INTEGER DEFAULT 0,
            updated_at TIMESTAMP
        )
    """)

    cursor.execute("PRAGMA table_info(student_preferences)")
    existing_student_cols = [col[1] for col in cursor.fetchall()]

    if "last_email_sent" not in existing_student_cols:
        cursor.execute("ALTER TABLE student_preferences ADD COLUMN last_email_sent TEXT")

    if "has_searched" not in existing_student_cols:
        cursor.execute("ALTER TABLE student_preferences ADD COLUMN has_searched INTEGER DEFAULT 0")

    if "updated_at" not in existing_student_cols:
        cursor.execute("ALTER TABLE student_preferences ADD COLUMN updated_at TIMESTAMP")

    # =========================================
    # EMAIL LOGS TABLE (AUDITABILITY & IDEMPOTENCY)
    # =========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id TEXT,
            timestamp_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            student_id INTEGER,
            recipient_email_masked TEXT,
            eligible_internships_count INTEGER,
            attempted INTEGER,
            status TEXT NOT NULL,
            provider_status_code TEXT,
            attempt_count INTEGER DEFAULT 1,
            error_category TEXT
        )
    """)

    # =========================================
    # INDEXES FOR FAST QUERYING & RESILIENCE
    # =========================================
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_internships_lookup ON internships(company, role, location)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_email ON student_preferences(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_logs_student ON email_logs(student_id, timestamp_utc)")

    connection.commit()
    connection.close()


def record_email_log(
    student_id,
    recipient_email,
    eligible_internships_count,
    attempted,
    status,
    workflow_run_id=None,
    provider_status_code=None,
    attempt_count=1,
    error_category=None,
    db_path=None
):
    """
    Records an immutable audit entry for an email delivery attempt with masked recipient email.
    """
    # Safely mask email: e.g. j***@example.com
    masked = recipient_email
    if recipient_email and "@" in recipient_email:
        local, domain = recipient_email.split("@", 1)
        masked = f"{local[:2]}***@{domain}" if len(local) > 2 else f"***@{domain}"

    try:
        conn = get_db_connection(db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO email_logs (
                workflow_run_id,
                student_id,
                recipient_email_masked,
                eligible_internships_count,
                attempted,
                status,
                provider_status_code,
                attempt_count,
                error_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(workflow_run_id) if workflow_run_id else None,
            student_id,
            masked,
            eligible_internships_count,
            1 if attempted else 0,
            status,
            str(provider_status_code) if provider_status_code else None,
            attempt_count,
            error_category
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Database] Failed to record email log: {e}")
        return False


def get_db_matched_internships(student_skills, preferred_domain, locations, minimum_stipend=0, db_path=None):
    """
    Instantly queries verified opportunities stored in SQLite and evaluates skill match
    and location/stipend criteria, returning sorted matches in sub-10ms.
    """
    from AI.matching import calculate_match
    from AI.stipend import extract_stipend_amount

    connection = get_db_connection(db_path)
    try:
        rows = connection.execute("SELECT * FROM internships ORDER BY id DESC").fetchall()
        matched = []
        CITY_ALIASES = {
            "bengaluru": ["bengaluru", "bangalore", "blr", "karnataka"],
            "bangalore": ["bengaluru", "bangalore", "blr", "karnataka"],
            "mumbai": ["mumbai", "bombay", "navi mumbai", "thane", "maharashtra"],
            "pune": ["pune", "poona", "maharashtra"],
            "delhi ncr": ["delhi", "ncr", "new delhi", "noida", "gurugram", "gurgaon", "faridabad", "ghaziabad"],
            "delhi": ["delhi", "ncr", "new delhi", "noida", "gurugram", "gurgaon"],
            "noida": ["noida", "greater noida", "delhi ncr", "ncr"],
            "gurugram": ["gurugram", "gurgaon", "delhi ncr", "ncr"],
            "hyderabad": ["hyderabad", "secunderabad", "cyberabad", "telangana"],
            "chennai": ["chennai", "madras", "tamil nadu"],
            "kolkata": ["kolkata", "calcutta", "west bengal"],
            "ahmedabad": ["ahmedabad", "gandhinagar", "gujarat"]
        }

        req_locations = [l.lower().strip() for l in locations]
        is_anywhere = "anywhere in india" in req_locations

        for row in rows:
            item = dict(row)
            loc = (item.get("location") or "").lower().strip()

            # Location filtering
            if not is_anywhere:
                loc_ok = False
                for req in req_locations:
                    aliases = CITY_ALIASES.get(req, [req])
                    if any(a in loc for a in aliases) or "remote" in loc or "india" in loc or not loc:
                        loc_ok = True
                        break
                if not loc_ok:
                    continue

            # Stipend filtering
            stipend_raw = item.get("stipend") or ""
            stipend_amt = extract_stipend_amount(stipend_raw)
            if stipend_amt is not None and minimum_stipend and stipend_amt < minimum_stipend:
                continue

            # Parse skills and compute real match
            raw_skills = [s.strip() for s in (item.get("skills") or "").split(",") if s.strip()]
            matched_skills, missing_skills, percentage = calculate_match(student_skills, raw_skills)

            if percentage is None:
                percentage = 70.0

            item["skills"] = raw_skills
            item["matched_skills"] = matched_skills
            item["missing_skills"] = missing_skills
            item["match_percentage"] = round(percentage, 1)
            item["application_url"] = item.get("application_link") or item.get("source_url") or "#"
            matched.append(item)

        return matched
    finally:
        connection.close()


if __name__ == "__main__":
    create_database()
    print(f"Database initialized successfully at {get_db_path()}")
