"""Tests for Sarvam AI client, error recovery, and demo mode."""

import pytest
from unittest.mock import patch, MagicMock
import httpx
from fitvoice.clients.sarvam import SarvamClient, SarvamAPIError


def test_demo_mode_client():
    client = SarvamClient(api_key="mock_key")
    with patch("fitvoice.config.settings.demo_mode", True):
        res = client.speech_to_text(language_code="en-IN")
        assert "transcript" in res
        assert res["is_live_inference"] is False
        assert "demo" in res["model"]


def test_bounded_retries_on_transient_failure():
    client = SarvamClient(api_key="live_key_test", max_retries=2, timeout=1.0)
    with patch("fitvoice.config.settings.demo_mode", False):
        with patch("httpx.Client.post") as mock_post:
            # Simulate transient 500 error
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response

            with pytest.raises(SarvamAPIError) as exc:
                client.chat_completion([{"role": "user", "content": "hi"}])
            assert exc.value.status_code == 500
            # Check that it attempted retries
            assert mock_post.call_count == 2
