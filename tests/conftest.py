from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api import app


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the API."""
    with patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "test-key", "API_KEY": "test-api-key"},
    ):
        with TestClient(app) as c:
            yield c
