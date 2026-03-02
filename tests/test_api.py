from __future__ import annotations

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app

os.environ["OPENAI_API_KEY"] = "test-key"


def test_health():
    """Test the health check endpoint."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@patch.dict(os.environ, {"API_KEY": "test-api-key", "OPENAI_API_KEY": "test-key"})
@patch("api.generator_instance")
def test_clarify_endpoint_success(mock_generator):
    """Test the /clarify endpoint success path."""
    mock_generator.generate_clarifying_questions.return_value = {
        "questions": ["q1", "q2", "q3"]
    }
    with TestClient(app) as client:
        response = client.post(
            "/clarify",
            json={"question": "test question"},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == 200
        assert "questions" in response.json()


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_clarify_endpoint_no_api_key():
    """Test the /clarify endpoint without an API key."""
    with TestClient(app) as client:
        response = client.post("/clarify", json={"question": "test question"})
        assert response.status_code == 401


@patch.dict(os.environ, {"API_KEY": "test-api-key", "OPENAI_API_KEY": "test-key"})
def test_clarify_endpoint_wrong_api_key():
    """Test the /clarify endpoint with a wrong API key."""
    with TestClient(app) as client:
        response = client.post(
            "/clarify",
            json={"question": "test question"},
            headers={"X-API-Key": "wrong-api-key"},
        )
        assert response.status_code == 401
