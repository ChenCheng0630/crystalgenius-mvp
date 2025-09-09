"""Tests for checkout endpoints."""

import pytest
from unittest.mock import patch


def test_create_checkout_session(client, session_headers, setup_test_data):
    """Test creating a checkout session with items in cart."""
    # First add items to cart
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 2}, headers=session_headers)
    
    payload = {
        "return_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }
    
    response = client.post("/api/v1/checkout/sessions", json=payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "checkout_id" in data
    assert "checkout_url" in data
    assert "expires_at" in data
    
    assert data["checkout_id"].startswith("co_")
    assert "mockpay.local" in data["checkout_url"]
    assert isinstance(data["expires_at"], str)


def test_create_checkout_session_empty_cart(client, session_headers, setup_test_data):
    """Test creating checkout session with empty cart."""
    payload = {
        "return_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }
    
    response = client.post("/api/v1/checkout/sessions", json=payload, headers=session_headers)
    
    assert response.status_code == 400
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "bad_request"
    assert "empty" in data["error"]["message"].lower()


def test_create_checkout_session_missing_return_url(client, session_headers, setup_test_data):
    """Test creating checkout session without return_url."""
    # Add item to cart first
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=session_headers)
    
    payload = {
        "cancel_url": "https://example.com/cancel"
    }
    
    response = client.post("/api/v1/checkout/sessions", json=payload, headers=session_headers)
    
    assert response.status_code == 400
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "validation_error"
    assert "required" in data["error"]["message"].lower()


def test_create_checkout_session_missing_cancel_url(client, session_headers, setup_test_data):
    """Test creating checkout session without cancel_url."""
    # Add item to cart first
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=session_headers)
    
    payload = {
        "return_url": "https://example.com/success"
    }
    
    response = client.post("/api/v1/checkout/sessions", json=payload, headers=session_headers)
    
    assert response.status_code == 400
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "validation_error"
    assert "required" in data["error"]["message"].lower()


def test_create_checkout_session_empty_urls(client, session_headers, setup_test_data):
    """Test creating checkout session with empty URLs."""
    # Add item to cart first
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=session_headers)
    
    payload = {
        "return_url": "",
        "cancel_url": ""
    }
    
    response = client.post("/api/v1/checkout/sessions", json=payload, headers=session_headers)
    
    assert response.status_code == 400
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "validation_error"
    assert "required" in data["error"]["message"].lower()


def test_get_checkout_session_success(client, session_headers, setup_test_data):
    """Test getting checkout session status - success case."""
    # Add item to cart and create checkout session
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=session_headers)
    
    create_response = client.post("/api/v1/checkout/sessions", json={
        "return_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }, headers=session_headers)
    
    assert create_response.status_code == 200
    checkout_id = create_response.json()["checkout_id"]
    
    # Get session status
    response = client.get(f"/api/v1/checkout/sessions/{checkout_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "paid"  # Mock immediately marks as paid
    assert "order_id" in data
    assert data["order_id"].startswith("ord_")


def test_get_checkout_session_not_found(client, setup_test_data):
    """Test getting non-existent checkout session."""
    response = client.get("/api/v1/checkout/sessions/nonexistent-id")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "not_found"
    assert "order_id" not in data


def test_checkout_session_id_format(client, session_headers, setup_test_data):
    """Test that checkout session ID has correct format."""
    # Add item and create session
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=session_headers)
    
    response = client.post("/api/v1/checkout/sessions", json={
        "return_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    checkout_id = data["checkout_id"]
    assert checkout_id.startswith("co_")
    assert len(checkout_id) > 3  # co_ + some ID
    
    # Checkout URL should include the ID
    assert checkout_id in data["checkout_url"]


def test_checkout_session_expiry_format(client, session_headers, setup_test_data):
    """Test that checkout session expiry is in correct format."""
    # Add item and create session
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=session_headers)
    
    response = client.post("/api/v1/checkout/sessions", json={
        "return_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    expires_at = data["expires_at"]
    # Should be ISO format datetime string
    assert "T" in expires_at
    assert expires_at.endswith("Z") or "+" in expires_at or expires_at.endswith(":00")


def test_multiple_checkout_sessions(client, setup_test_data):
    """Test creating multiple checkout sessions."""
    headers1 = {"X-Session-Id": "session-1"}
    headers2 = {"X-Session-Id": "session-2"}
    
    # Add items to both carts
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=headers1)
    client.post("/api/v1/cart/items", json={"product_id": 2, "quantity": 1}, headers=headers2)
    
    payload = {
        "return_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }
    
    # Create checkout sessions for both
    response1 = client.post("/api/v1/checkout/sessions", json=payload, headers=headers1)
    response2 = client.post("/api/v1/checkout/sessions", json=payload, headers=headers2)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Should have different checkout IDs
    checkout_id1 = response1.json()["checkout_id"]
    checkout_id2 = response2.json()["checkout_id"]
    assert checkout_id1 != checkout_id2


def test_checkout_session_persistence(client, session_headers, setup_test_data):
    """Test that checkout sessions persist between requests."""
    # Add item and create session
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=session_headers)
    
    create_response = client.post("/api/v1/checkout/sessions", json={
        "return_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }, headers=session_headers)
    
    checkout_id = create_response.json()["checkout_id"]
    
    # Check session multiple times
    response1 = client.get(f"/api/v1/checkout/sessions/{checkout_id}")
    response2 = client.get(f"/api/v1/checkout/sessions/{checkout_id}")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Both should return same status
    assert response1.json()["status"] == response2.json()["status"]
    if "order_id" in response1.json():
        assert response1.json()["order_id"] == response2.json()["order_id"]


@patch('services.checkout.datetime')
def test_checkout_session_timing(mock_datetime, client, session_headers, setup_test_data):
    """Test checkout session creation timing."""
    from datetime import datetime, timezone, timedelta
    
    # Mock current time
    mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_datetime.now.return_value = mock_now
    
    # Add item and create session
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 1}, headers=session_headers)
    
    response = client.post("/api/v1/checkout/sessions", json={
        "return_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel"
    }, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify expiry time is about 30 minutes from now
    expires_at = data["expires_at"]
    assert "2024-01-01" in expires_at
    assert "12:30:00" in expires_at  # Should be 30 minutes later
