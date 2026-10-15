import pytest
import sqlite3
from database import create_database, get_db_connection, record_email_log


@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_internflow.db")
    create_database(db_file)
    return db_file


def test_database_initialization(temp_db):
    conn = get_db_connection(temp_db)
    cursor = conn.cursor()
    tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "internships" in tables
    assert "student_preferences" in tables
    assert "email_logs" in tables
    conn.close()


def test_record_email_log_masking(temp_db):
    record_email_log(
        student_id=1,
        recipient_email="alex.sharma@example.com",
        eligible_internships_count=3,
        attempted=True,
        status="accepted_by_provider",
        workflow_run_id="run-101",
        provider_status_code="250",
        attempt_count=1,
        db_path=temp_db,
    )

    conn = get_db_connection(temp_db)
    log = conn.execute("SELECT * FROM email_logs WHERE student_id=1").fetchone()
    assert log is not None
    assert log["workflow_run_id"] == "run-101"
    assert log["status"] == "accepted_by_provider"
    assert log["eligible_internships_count"] == 3
    # Check email masking: "al***@example.com"
    assert log["recipient_email_masked"] == "al***@example.com"
    conn.close()
