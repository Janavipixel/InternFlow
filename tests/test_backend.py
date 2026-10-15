import pytest
from unittest.mock import patch
from backend import app
from database import create_database, get_db_connection


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_api.db")
    monkeypatch.setenv("DATABASE_PATH", test_db)
    monkeypatch.setenv("AUTOMATION_TOKEN", "test_secret_token")
    create_database(test_db)

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_save_preferences_endpoint(client):
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "student_skills": ["Python", "Django"],
        "preferred_domain": "Backend",
        "locations": ["Bangalore", "Remote"],
        "minimum_stipend": 15000,
        "email_frequency": "Daily",
    }
    response = client.post("/save-preferences", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert "saved successfully" in data["message"]
    assert data.get("welcome_email_triggered") is True

    # Verify invalid email rejected
    bad_response = client.post("/save-preferences", json={"name": "No Email"})
    assert bad_response.status_code == 400


def test_internships_crud(client):
    # Add internship
    post_resp = client.post("/internships", json={
        "company": "Acme Corp",
        "role": "Software Intern",
        "skills": "Python, SQL",
        "location": "Mumbai",
        "stipend": "₹20,000",
        "deadline": "2026-11-30",
        "eligibility": "B.Tech students",
        "application_link": "https://acme.com/careers/1"
    })
    assert post_resp.status_code == 201

    # Get internships
    get_resp = client.get("/internships")
    assert get_resp.status_code == 200
    internships = get_resp.get_json()
    assert len(internships) >= 1
    internship_id = internships[0]["id"]

    # Update status
    put_resp = client.put(f"/internships/{internship_id}/status", json={"status": "Applied"})
    assert put_resp.status_code == 200

    # Save internship
    save_resp = client.put(f"/internships/{internship_id}/save")
    assert save_resp.status_code == 200


def test_automation_endpoints_security(client):
    # Without token -> 401
    resp_no_token = client.get("/automation/students")
    assert resp_no_token.status_code == 401

    # With wrong token -> 401
    resp_wrong = client.get(
        "/automation/students",
        headers={"X-Automation-Token": "wrong_token"}
    )
    assert resp_wrong.status_code == 401

    # With correct token -> 200
    resp_ok = client.get(
        "/automation/students",
        headers={"X-Automation-Token": "test_secret_token"}
    )
    assert resp_ok.status_code == 200
    assert isinstance(resp_ok.get_json(), list)


def test_get_preferences_endpoint(client):
    # Save a student
    payload = {
        "name": "Alice Bob",
        "email": "alice@example.com",
        "student_skills": ["Python", "python", "C", "c"],
        "preferred_domain": "Cybersecurity",
        "locations": ["Mumbai", "Remote"],
        "minimum_stipend": 12000,
        "email_frequency": "Weekly",
    }
    save_resp = client.post("/save-preferences", json=payload)
    assert save_resp.status_code == 200

    # Retrieve preferences
    get_resp = client.get("/preferences?email=alice@example.com")
    assert get_resp.status_code == 200
    data = get_resp.get_json()
    assert data["found"] is True
    assert data["preferences"]["name"] == "Alice Bob"
    # Verify skill deduplication: Python and C only (case variants removed)
    assert "Python" in data["preferences"]["student_skills"]
    assert "C" in data["preferences"]["student_skills"]
    assert len(data["preferences"]["student_skills"]) == 2

    # Non-existent user -> 404
    not_found_resp = client.get("/preferences?email=nonexistent@example.com")
    assert not_found_resp.status_code == 404
    assert not_found_resp.get_json()["found"] is False

    # Invalid email -> 400
    bad_req = client.get("/preferences?email=invalidemail")
    assert bad_req.status_code == 400


def test_student_email_status_endpoint(client):
    # Save a student first
    client.post("/save-preferences", json={
        "name": "Status User",
        "email": "status@example.com",
        "student_skills": ["Python"],
        "preferred_domain": "Data Science",
        "locations": ["Remote"],
        "minimum_stipend": 5000,
        "email_frequency": "Weekly",
    })

    # Retrieve email status
    resp = client.get("/student/email-status?email=status@example.com")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["email"] == "status@example.com"
    assert data["email_frequency"] == "Weekly"
    assert "recent_logs" in data

    # Missing email parameter -> 400
    assert client.get("/student/email-status?email=").status_code == 400


@patch("automation.process_student")
def test_trigger_test_email_endpoint(mock_process, client):
    # Student not in DB -> 404
    resp_404 = client.post("/automation/trigger-test", json={"email": "nobody@example.com"})
    assert resp_404.status_code == 404

    # Save student in DB
    client.post("/save-preferences", json={
        "name": "Test Runner",
        "email": "runner@example.com",
        "student_skills": ["Python"],
        "preferred_domain": "Web Development",
        "locations": ["Remote"],
        "minimum_stipend": 0,
        "email_frequency": "Daily",
    })

    # Mock process_student returning success
    mock_process.reset_mock()
    mock_process.return_value = "accepted_by_provider"
    resp_success = client.post("/automation/trigger-test", json={"email": "runner@example.com"})
    assert resp_success.status_code == 200
    data = resp_success.get_json()
    assert data["success"] is True
    assert "successfully sent" in data["message"]
    mock_process.assert_called_once()


