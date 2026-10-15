import pytest
import smtplib
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import automation
from automation import (
    parse_skills,
    parse_deadline,
    should_send_email,
    get_email_internships,
    send_email,
    get_students,
)


def test_parse_skills():
    assert parse_skills(["Python", "SQL"]) == ["Python", "SQL"]
    assert parse_skills("Python, SQL, React") == ["Python", "SQL", "React"]
    assert parse_skills("") == []
    assert parse_skills(None) == []


def test_parse_deadline():
    today = date.today()
    assert parse_deadline(today) == today
    assert parse_deadline("2026-12-31") == date(2026, 12, 31)
    assert parse_deadline("31-12-2026") == date(2026, 12, 31)
    assert parse_deadline("N/A") is None
    assert parse_deadline("Not listed") is None
    assert parse_deadline(None) is None


def test_should_send_email_frequency():
    today = date.today()

    # Never sent before -> should send
    assert should_send_email({"email_frequency": "Daily", "last_email_sent": None}) is True

    # Daily frequency: sent today -> should NOT send
    assert should_send_email({"email_frequency": "Daily", "last_email_sent": today.isoformat()}) is False

    # Daily frequency: sent yesterday -> should send
    yesterday = today - timedelta(days=1)
    assert should_send_email({"email_frequency": "Daily", "last_email_sent": yesterday.isoformat()}) is True

    # Weekly frequency: sent 3 days ago -> should NOT send
    three_days_ago = today - timedelta(days=3)
    assert should_send_email({"email_frequency": "Weekly", "last_email_sent": three_days_ago.isoformat()}) is False

    # Weekly frequency: sent 7 days ago -> should send
    seven_days_ago = today - timedelta(days=7)
    assert should_send_email({"email_frequency": "Weekly", "last_email_sent": seven_days_ago.isoformat()}) is True

    # Paused / Never -> should NEVER send
    assert should_send_email({"email_frequency": "Paused", "last_email_sent": None}) is False
    assert should_send_email({"email_frequency": "Never", "last_email_sent": seven_days_ago.isoformat()}) is False


def test_get_email_internships_filters_expired():
    today = date.today()
    expired = (today - timedelta(days=2)).isoformat()
    upcoming = (today + timedelta(days=5)).isoformat()

    results = [
        {"company": "ExpiredCo", "role": "Intern", "deadline": expired},
        {"company": "ActiveCo", "role": "Intern", "deadline": upcoming},
        {"company": "OpenCo", "role": "Intern", "deadline": None},
    ]

    selected = get_email_internships(results)
    assert len(selected) == 2
    companies = [x["company"] for x in selected]
    assert "ExpiredCo" not in companies
    assert "ActiveCo" in companies
    assert "OpenCo" in companies


def test_send_email_test_mode(monkeypatch):
    monkeypatch.setattr(automation, "EMAIL_ADDRESS", "sender@example.com")
    monkeypatch.setattr(automation, "EMAIL_PASSWORD", "secret")
    monkeypatch.setattr(automation, "AUTOMATION_TEST_MODE", True)
    monkeypatch.setattr(automation, "TEST_EMAIL_RECIPIENT", None)

    student = {"name": "Test User", "email": "realstudent@example.com"}
    internships = [{"company": "Tech", "role": "Intern"}]

    # In test mode without TEST_EMAIL_RECIPIENT, does dry run
    success, code, err = send_email(student, internships)
    assert success is True
    assert code == "TEST_DRY_RUN"


@patch("smtplib.SMTP_SSL")
def test_send_email_mock_smtp_success(mock_smtp, monkeypatch):
    monkeypatch.setattr(automation, "EMAIL_ADDRESS", "sender@example.com")
    monkeypatch.setattr(automation, "EMAIL_PASSWORD", "secret")
    monkeypatch.setattr(automation, "AUTOMATION_TEST_MODE", False)

    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    student = {"name": "Test Student", "email": "student@example.com"}
    internships = [{"company": "Google", "role": "SWE Intern"}]

    success, code, err = send_email(student, internships)
    assert success is True
    assert "250" in code
    mock_server.login.assert_called_once_with("sender@example.com", "secret")
    mock_server.send_message.assert_called_once()


@patch("smtplib.SMTP_SSL")
def test_send_email_auth_failure(mock_smtp, monkeypatch):
    monkeypatch.setattr(automation, "EMAIL_ADDRESS", "sender@example.com")
    monkeypatch.setattr(automation, "EMAIL_PASSWORD", "wrongpass")
    monkeypatch.setattr(automation, "AUTOMATION_TEST_MODE", False)

    mock_server = MagicMock()
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")
    mock_smtp.return_value.__enter__.return_value = mock_server

    student = {"name": "Student", "email": "student@example.com"}
    internships = [{"company": "Meta", "role": "Intern"}]

    success, code, err = send_email(student, internships)
    assert success is False
    assert "AUTH_FAIL" in code
    assert err == "Authentication failure"


def test_get_students_fallback(monkeypatch):
    # Mock Render returning failure, local returning student
    mock_local_student = [{"id": 1, "name": "Local Student", "email": "local@test.com"}]
    monkeypatch.setattr(automation, "get_students_from_render", lambda: None)
    monkeypatch.setattr(automation, "get_students_from_local_db", lambda: mock_local_student)

    result = get_students()
    assert result == mock_local_student


def test_write_github_summary(tmp_path, monkeypatch):
    summary_file = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

    summary = {
        "processed": 5,
        "attempted": 2,
        "accepted": 2,
        "failed": 0,
        "skipped": {
            "already_sent": 1,
            "incomplete_preferences": 1,
            "no_matches": 1,
        },
    }

    automation.write_github_summary(summary, "test-run-42")
    assert summary_file.exists()
    content = summary_file.read_text(encoding="utf-8")
    assert "test-run-42" in content
    assert "Students Evaluated" in content
    assert "Accepted by Provider" in content
    assert "2" in content


def test_process_student_incomplete_preferences():
    student = {
        "id": 1,
        "email": "incomplete@example.com",
        "student_skills": "",  # Missing skills
        "preferred_domain": "Cybersecurity",
        "locations": "Mumbai",
    }
    outcome = automation.process_student(student)
    assert outcome == "skipped_incomplete_preferences"


@patch("smtplib.SMTP_SSL")
def test_send_email_test_mode_redirect(mock_smtp, monkeypatch):
    monkeypatch.setattr(automation, "EMAIL_ADDRESS", "sender@example.com")
    monkeypatch.setattr(automation, "EMAIL_PASSWORD", "secret")
    monkeypatch.setattr(automation, "AUTOMATION_TEST_MODE", True)
    monkeypatch.setattr(automation, "TEST_EMAIL_RECIPIENT", "tester@safe.com")

    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    student = {"name": "Real Student", "email": "realstudent@university.edu"}
    internships = [{"company": "SafeCo", "role": "Intern"}]

    success, code, err = send_email(student, internships)
    assert success is True
    assert "250" in code
    # Check that message was sent to tester@safe.com, NOT real student
    call_args = mock_server.send_message.call_args[0]
    sent_msg = call_args[0]
    assert sent_msg["To"] == "tester@safe.com"

