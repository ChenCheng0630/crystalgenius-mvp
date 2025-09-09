"""Tests for main application endpoints."""

import pytest


def test_health_check(client, setup_test_data):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["service"] == "crystalgenius-backend"
    assert data["version"] == "0.1.0"
    assert "products_loaded" in data
    assert "categories_loaded" in data
    assert data["products_loaded"] == 3  # From our mock data
    assert data["categories_loaded"] == 3  # From our mock data


def test_health_check_structure(client, setup_test_data):
    """Test that health check returns expected structure."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    required_fields = ["status", "service", "version", "products_loaded", "categories_loaded"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    assert isinstance(data["products_loaded"], int)
    assert isinstance(data["categories_loaded"], int)
    assert data["products_loaded"] >= 0
    assert data["categories_loaded"] >= 0
