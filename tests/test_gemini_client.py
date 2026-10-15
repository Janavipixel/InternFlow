import pytest
from unittest.mock import patch, MagicMock
from AI.gemini_client import ask_gemini


def test_ask_gemini_missing_key():
    with patch.dict("os.environ", {}, clear=True):
        assert ask_gemini("hello") is None


@patch("AI.gemini_client.get_gemini_client")
def test_ask_gemini_success(mock_get_client):
    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = '{"message": "success"}'
    mock_client.models.generate_content.return_value = mock_resp
    mock_get_client.return_value = mock_client

    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake_test_key"}):
        result = ask_gemini("test prompt")
        assert result == '{"message": "success"}'


@patch("AI.gemini_client.get_gemini_client")
def test_ask_gemini_quota_exhaustion_graceful_fail(mock_get_client):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
    mock_get_client.return_value = mock_client

    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake_test_key"}):
        # Should not crash, returns None after retries
        result = ask_gemini("test prompt", max_retries=1)
        assert result is None
