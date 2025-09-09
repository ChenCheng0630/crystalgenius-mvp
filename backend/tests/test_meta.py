"""Tests for meta endpoints (categories, parent categories, events)."""

import pytest
from unittest.mock import patch


def test_list_categories_success(client, setup_test_data):
    """Test listing categories for a valid parent ID."""
    response = client.get("/api/v1/categories?parent_id=831")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "categories" in data
    categories = data["categories"]
    
    assert len(categories) == 3  # From our mock data
    
    for category in categories:
        # Check required fields
        assert "id" in category
        assert "reference_id" in category
        assert "parent_id" in category
        
        # Check data types
        assert isinstance(category["id"], int)
        assert isinstance(category["reference_id"], int)
        assert isinstance(category["parent_id"], int)
        assert category["parent_id"] == 831
        
        # Check optional fields
        for optional_field in ["color", "material", "category_name", "image"]:
            if optional_field in category and category[optional_field] is not None:
                assert isinstance(category[optional_field], str)


def test_list_categories_missing_parent_id(client, setup_test_data):
    """Test listing categories without parent_id parameter."""
    response = client.get("/api/v1/categories")
    
    # Should return 422 for missing required parameter
    assert response.status_code == 422


def test_list_categories_invalid_parent_id(client, setup_test_data):
    """Test listing categories for non-existent parent ID."""
    response = client.get("/api/v1/categories?parent_id=999")
    
    assert response.status_code == 404
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert "parent category not found" in data["error"]["message"].lower()


def test_list_categories_specific_fields(client, setup_test_data):
    """Test that categories contain expected specific data."""
    response = client.get("/api/v1/categories?parent_id=831")
    
    assert response.status_code == 200
    data = response.json()
    
    categories = data["categories"]
    category_ids = [cat["id"] for cat in categories]
    
    # Should contain our mock categories
    assert 101 in category_ids
    assert 102 in category_ids
    assert 103 in category_ids
    
    # Check specific category data
    purple_cat = next(cat for cat in categories if cat["id"] == 101)
    assert purple_cat["color"] == "紫色"
    assert purple_cat["material"] == "紫水晶"
    assert purple_cat["category_name"] == "紫水晶系列"


def test_list_parent_categories(client, setup_test_data):
    """Test listing parent categories."""
    response = client.get("/api/v1/parent-categories")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "parent_categories" in data
    parent_categories = data["parent_categories"]
    
    assert len(parent_categories) == 3  # From our mock data
    
    for parent_cat in parent_categories:
        # Check required fields
        assert "id" in parent_cat
        assert "reference_id" in parent_cat
        assert "name" in parent_cat
        
        # Check data types
        assert isinstance(parent_cat["id"], int)
        assert isinstance(parent_cat["reference_id"], int)
        assert isinstance(parent_cat["name"], str)
        
        # Check optional fields
        if "image" in parent_cat and parent_cat["image"] is not None:
            assert isinstance(parent_cat["image"], str)


def test_parent_categories_specific_data(client, setup_test_data):
    """Test parent categories contain expected specific data."""
    response = client.get("/api/v1/parent-categories")
    
    assert response.status_code == 200
    data = response.json()
    
    parent_categories = data["parent_categories"]
    parent_ids = [pc["id"] for pc in parent_categories]
    
    # Should contain our mock parent categories
    assert 831 in parent_ids
    assert 832 in parent_ids
    assert 834 in parent_ids
    
    # Check specific names
    names = [pc["name"] for pc in parent_categories]
    assert "按颜色材质" in names
    assert "按款式风格" in names
    assert "按手串类型" in names


def test_post_event_success(client):
    """Test posting an event."""
    event_data = {
        "type": "product_view",
        "product_id": 123,
        "user_id": "user-456",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    response = client.post("/api/v1/events", json=event_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True


def test_post_event_empty_payload(client):
    """Test posting empty event."""
    response = client.post("/api/v1/events", json={})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True


def test_post_event_complex_payload(client):
    """Test posting complex event payload."""
    event_data = {
        "type": "checkout_complete",
        "order_id": "order-789",
        "items": [
            {"product_id": 1, "quantity": 2, "price": 88.0},
            {"product_id": 2, "quantity": 1, "price": 66.0}
        ],
        "total": 242.0,
        "payment_method": "alipay",
        "timestamp": "2024-01-01T12:00:00Z",
        "metadata": {
            "source": "mobile_app",
            "version": "1.2.3"
        }
    }
    
    response = client.post("/api/v1/events", json=event_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True


def test_post_event_null_values(client):
    """Test posting event with null values."""
    event_data = {
        "type": "user_action",
        "user_id": None,
        "action": "search",
        "query": "purple crystals",
        "results": None
    }
    
    response = client.post("/api/v1/events", json=event_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True


def test_post_event_string_payload(client):
    """Test posting event with string values."""
    event_data = {
        "message": "User searched for crystals",
        "level": "info",
        "category": "user_behavior"
    }
    
    response = client.post("/api/v1/events", json=event_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["ok"] is True


def test_events_storage(client):
    """Test that events are stored correctly."""
    from services import events
    
    # Clear any existing events
    events.EVENTS.clear()
    
    event_data = {"type": "test_event", "data": "test_data"}
    response = client.post("/api/v1/events", json=event_data)
    
    assert response.status_code == 200
    
    # Check that event was stored
    assert len(events.EVENTS) == 1
    stored_event = events.EVENTS[0]
    assert stored_event["type"] == "test_event"
    assert stored_event["data"] == "test_data"


def test_multiple_events_storage(client):
    """Test storing multiple events."""
    from services import events
    
    # Clear any existing events
    events.EVENTS.clear()
    
    # Post multiple events
    for i in range(3):
        event_data = {"type": f"event_{i}", "index": i}
        response = client.post("/api/v1/events", json=event_data)
        assert response.status_code == 200
    
    # Check that all events were stored
    assert len(events.EVENTS) == 3
    
    for i, event in enumerate(events.EVENTS):
        assert event["type"] == f"event_{i}"
        assert event["index"] == i


def test_categories_empty_result(client, setup_test_data):
    """Test categories endpoint with parent that has no children."""
    # Mock empty categories for a parent
    with patch('data_loader.CATEGORIES_BY_PARENT', {999: []}):
        response = client.get("/api/v1/categories?parent_id=999")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["categories"] == []


def test_parent_categories_empty_result(client, setup_test_data):
    """Test parent categories endpoint with no data."""
    with patch('data_loader.PARENT_CATEGORIES', {}):
        response = client.get("/api/v1/parent-categories")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["parent_categories"] == []


def test_categories_serialization(client, setup_test_data):
    """Test that categories are properly serialized."""
    response = client.get("/api/v1/categories?parent_id=831")
    
    assert response.status_code == 200
    data = response.json()
    
    categories = data["categories"]
    
    for category in categories:
        # All values should be JSON serializable
        assert isinstance(category, dict)
        
        # No None values should be present for required fields
        assert category["id"] is not None
        assert category["reference_id"] is not None
        assert category["parent_id"] is not None
        
        # Optional fields can be None, but if present should be proper types
        for field_name, field_value in category.items():
            if field_value is not None:
                assert isinstance(field_value, (int, str, float, bool, list, dict))


def test_parent_categories_serialization(client, setup_test_data):
    """Test that parent categories are properly serialized."""
    response = client.get("/api/v1/parent-categories")
    
    assert response.status_code == 200
    data = response.json()
    
    parent_categories = data["parent_categories"]
    
    for parent_cat in parent_categories:
        # All values should be JSON serializable
        assert isinstance(parent_cat, dict)
        
        # Required fields should not be None
        assert parent_cat["id"] is not None
        assert parent_cat["reference_id"] is not None
        assert parent_cat["name"] is not None
        
        # Check field types
        for field_name, field_value in parent_cat.items():
            if field_value is not None:
                assert isinstance(field_value, (int, str, float, bool, list, dict))
