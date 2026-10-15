import pytest
from unittest.mock import patch, MagicMock
from AI.verify_application import verify_application_url


def test_verify_application_url_invalid_input():
    assert verify_application_url("") is False
    assert verify_application_url(None) is False
    assert verify_application_url("not-a-url") is False
    assert verify_application_url("ftp://example.com") is False


def test_verify_application_url_social_domains():
    assert verify_application_url("https://www.instagram.com/p/123") is False
    assert verify_application_url("https://twitter.com/jobs/123") is False
    assert verify_application_url("https://facebook.com/careers/123") is False


def test_verify_application_url_generic_search_patterns():
    assert verify_application_url("https://careers.company.com/jobs/search?q=intern") is False
    assert verify_application_url("https://company.com/login") is False


@patch("AI.verify_application.requests.get")
def test_verify_application_url_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://careers.google.com/jobs/results/12345"
    mock_response.text = "<html><body><h1>Software Engineer Intern</h1><button>Apply</button></body></html>"
    mock_get.return_value = mock_response

    assert verify_application_url("https://careers.google.com/jobs/results/12345") is True


@patch("AI.verify_application.requests.get")
def test_verify_application_url_soft_404_expired(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://jobs.example.com/posting/999"
    mock_response.text = "<html><body><h1>Notice</h1><p>This job has expired</p></body></html>"
    mock_get.return_value = mock_response

    assert verify_application_url("https://jobs.example.com/posting/999") is False


@patch("AI.verify_application.requests.get")
def test_verify_application_url_redirect_to_login(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://jobs.example.com/auth/login"
    mock_response.text = "<html><body><h1>Please Login</h1></body></html>"
    mock_get.return_value = mock_response

    assert verify_application_url("https://jobs.example.com/apply/123") is False


@patch("AI.verify_application.requests.get")
def test_verify_application_url_network_error(mock_get):
    import requests
    mock_get.side_effect = requests.RequestException("Connection timed out")
    assert verify_application_url("https://timeout.example.com/apply") is False
