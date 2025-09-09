"""Tests for assistant endpoints."""

import pytest


def test_get_assistant_profile(client):
    """Test getting assistant profile."""
    response = client.get("/api/v1/assistant/profile")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify required fields are present
    required_fields = ["name", "avatar", "intro_short", "domains", "styles", "stats"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    # Verify data types and content
    assert data["name"] == "小晶"
    assert isinstance(data["avatar"], str)
    assert isinstance(data["intro_short"], str)
    assert isinstance(data["domains"], list)
    assert isinstance(data["styles"], list)
    assert isinstance(data["stats"], dict)
    
    # Verify stats structure
    stats_fields = ["monthly_sales", "gmv", "positive_rate"]
    for field in stats_fields:
        assert field in data["stats"], f"Missing stats field: {field}"
        assert isinstance(data["stats"][field], str)


def test_assistant_profile_content(client):
    """Test assistant profile content matches expected values."""
    response = client.get("/api/v1/assistant/profile")
    
    assert response.status_code == 200
    data = response.json()
    
    # Test specific expected values
    assert data["name"] == "小晶"
    assert "水晶" in data["intro_short"]
    assert len(data["domains"]) > 0
    assert len(data["styles"]) > 0
    
    # Test that domains and styles are non-empty strings
    for domain in data["domains"]:
        assert isinstance(domain, str)
        assert len(domain) > 0
    
    for style in data["styles"]:
        assert isinstance(style, str)
        assert len(style) > 0
    
    # Test stats values are properly formatted
    assert "K+" in data["stats"]["monthly_sales"] or "+" in data["stats"]["monthly_sales"]
    assert "￥" in data["stats"]["gmv"] or "M" in data["stats"]["gmv"]
    assert "%" in data["stats"]["positive_rate"]


def test_assistant_profile_immutable(client):
    """Test that assistant profile is static/immutable."""
    # Make multiple requests
    response1 = client.get("/api/v1/assistant/profile")
    response2 = client.get("/api/v1/assistant/profile")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Responses should be identical
    assert response1.json() == response2.json()
