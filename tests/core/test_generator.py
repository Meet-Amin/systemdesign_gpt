from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from core.generator import DesignGenerator
from core.schemas import UsageMetrics


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_design_generator_initialization():
    """Test that the DesignGenerator can be initialized."""
    try:
        DesignGenerator()
    except Exception as e:
        pytest.fail(f"DesignGenerator initialization failed: {e}")


def test_extract_usage_metrics():
    """Test the _extract_usage_metrics method."""
    mock_response = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 200
    mock_response.usage.total_tokens = 300
    latency_ms = 500

    metrics = DesignGenerator._extract_usage_metrics(mock_response, latency_ms)

    assert isinstance(metrics, UsageMetrics)
    assert metrics.prompt_tokens == 100
    assert metrics.completion_tokens == 200
    assert metrics.total_tokens == 300
    assert metrics.latency_ms == 500
    assert metrics.estimated_cost_usd > 0


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_parse_json():
    """Test the _parse_json method."""
    generator = DesignGenerator(model="test-model")
    valid_json = '{"key": "value"}'
    invalid_json = '{"key": "value"'

    parsed = generator._parse_json(valid_json)
    assert parsed == {"key": "value"}

    with pytest.raises(ValueError):
        generator._parse_json(invalid_json)


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_normalize_design_payload():
    """Test the _normalize_design_payload method."""
    generator = DesignGenerator(model="test-model")
    payload = {
        "high_level_architecture": " ",
        "components": [
            {"name": "  component1  ", "type": "  type1  ", "description": "  desc1  "}
        ],
        "assumptions": [" assumption1 ", None],
    }

    normalized = generator._normalize_design_payload(payload)

    assert normalized["high_level_architecture"] == ""
    assert normalized["components"][0]["name"] == "component1"
    assert normalized["assumptions"] == ["assumption1"]
