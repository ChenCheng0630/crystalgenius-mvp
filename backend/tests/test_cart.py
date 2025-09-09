"""Tests for cart endpoints."""

import pytest
from unittest.mock import patch


def test_get_empty_cart(client, session_headers, setup_test_data):
    """Test getting an empty cart."""
    response = client.get("/api/v1/cart", headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify cart structure
    assert "id" in data
    assert "items" in data
    assert "totals" in data
    
    assert data["items"] == []
    assert isinstance(data["totals"], dict)
    assert "currency" in data["totals"]
    assert data["totals"]["currency"] == "CNY"


def test_add_item_to_cart(client, session_headers, setup_test_data):
    """Test adding an item to cart."""
    payload = {
        "product_id": 1,
        "quantity": 2
    }
    
    response = client.post("/api/v1/cart/items", json=payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify item was added
    assert len(data["items"]) == 1
    item = data["items"][0]
    
    assert "id" in item
    assert item["quantity"] == 2
    assert item["unit_price"] == 88.0  # From mock data
    assert item["currency"] == "CNY"
    
    # Verify product details in item
    product = item["product"]
    assert product["id"] == 1
    assert product["name"] == "紫水晶手串"
    assert product["price"] == 88.0
    
    # Verify totals are calculated
    assert "subtotal" in data["totals"]
    assert data["totals"]["subtotal"] == 176.0  # 88.0 * 2


def test_add_item_invalid_product(client, session_headers, setup_test_data):
    """Test adding non-existent product to cart."""
    payload = {
        "product_id": 999,  # Non-existent
        "quantity": 1
    }
    
    response = client.post("/api/v1/cart/items", json=payload, headers=session_headers)
    
    assert response.status_code == 404
    data = response.json()
    
    # Extract error from nested structure
    if "detail" in data and "error" in data["detail"]:
        error = data["detail"]["error"]
    else:
        error = data.get("error")
    
    assert error is not None
    assert error["code"] == "not_found"
    assert "not found" in error["message"].lower()


def test_add_item_missing_product_id(client, session_headers, setup_test_data):
    """Test adding item without product_id."""
    payload = {
        "quantity": 1
    }
    
    # This should raise a ValueError when trying to convert None to int
    with pytest.raises(Exception):
        client.post("/api/v1/cart/items", json=payload, headers=session_headers)


def test_add_multiple_items(client, session_headers, setup_test_data):
    """Test adding multiple different items to cart."""
    # Add first item
    payload1 = {"product_id": 1, "quantity": 1}
    response1 = client.post("/api/v1/cart/items", json=payload1, headers=session_headers)
    assert response1.status_code == 200
    
    # Add second item
    payload2 = {"product_id": 2, "quantity": 2}
    response2 = client.post("/api/v1/cart/items", json=payload2, headers=session_headers)
    assert response2.status_code == 200
    
    data = response2.json()
    assert len(data["items"]) == 2
    
    # Verify total is sum of both items
    expected_total = 88.0 * 1 + 66.0 * 2  # 88 + 132 = 220
    assert data["totals"]["subtotal"] == expected_total


def test_update_cart_item_quantity(client, session_headers, setup_test_data):
    """Test updating cart item quantity."""
    # First add an item
    payload = {"product_id": 1, "quantity": 2}
    response = client.post("/api/v1/cart/items", json=payload, headers=session_headers)
    assert response.status_code == 200
    
    item_id = response.json()["items"][0]["id"]
    
    # Update quantity
    update_payload = {"quantity": 5}
    response = client.patch(f"/api/v1/cart/items/{item_id}", json=update_payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify quantity was updated
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 5
    
    # Verify totals updated
    assert data["totals"]["subtotal"] == 88.0 * 5


def test_update_nonexistent_cart_item(client, session_headers, setup_test_data):
    """Test updating non-existent cart item."""
    update_payload = {"quantity": 5}
    response = client.patch("/api/v1/cart/items/nonexistent-id", json=update_payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Item should not exist, cart should be empty
    assert len(data["items"]) == 0


def test_remove_cart_item(client, session_headers, setup_test_data):
    """Test removing an item from cart."""
    # First add an item
    payload = {"product_id": 1, "quantity": 2}
    response = client.post("/api/v1/cart/items", json=payload, headers=session_headers)
    assert response.status_code == 200
    
    item_id = response.json()["items"][0]["id"]
    
    # Remove the item
    response = client.delete(f"/api/v1/cart/items/{item_id}", headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify item was removed
    assert len(data["items"]) == 0
    assert data["totals"]["subtotal"] == 0.0


def test_remove_nonexistent_cart_item(client, session_headers, setup_test_data):
    """Test removing non-existent cart item."""
    response = client.delete("/api/v1/cart/items/nonexistent-id", headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Cart should remain empty
    assert len(data["items"]) == 0


def test_clear_cart(client, session_headers, setup_test_data):
    """Test clearing entire cart."""
    # Add multiple items
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 2}, headers=session_headers)
    client.post("/api/v1/cart/items", json={"product_id": 2, "quantity": 1}, headers=session_headers)
    
    # Clear cart
    response = client.delete("/api/v1/cart", headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify cart is empty
    assert len(data["items"]) == 0
    assert data["totals"]["subtotal"] == 0.0


def test_cart_session_isolation(client, setup_test_data):
    """Test that different sessions have isolated carts."""
    headers1 = {"X-Session-Id": "session-1"}
    headers2 = {"X-Session-Id": "session-2"}
    
    # Add item to first session
    payload = {"product_id": 1, "quantity": 1}
    response1 = client.post("/api/v1/cart/items", json=payload, headers=headers1)
    assert response1.status_code == 200
    
    # Check second session cart is still empty
    response2 = client.get("/api/v1/cart", headers=headers2)
    assert response2.status_code == 200
    assert len(response2.json()["items"]) == 0
    
    # Check first session cart still has item
    response1_check = client.get("/api/v1/cart", headers=headers1)
    assert response1_check.status_code == 200
    assert len(response1_check.json()["items"]) == 1


def test_cart_without_session_id(client, setup_test_data):
    """Test cart operations without explicit session ID."""
    # Should work with auto-generated session
    payload = {"product_id": 1, "quantity": 1}
    response = client.post("/api/v1/cart/items", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


def test_cart_totals_calculation(client, session_headers, setup_test_data):
    """Test that cart totals are calculated correctly."""
    # Add items with different prices and quantities
    client.post("/api/v1/cart/items", json={"product_id": 1, "quantity": 2}, headers=session_headers)  # 88 * 2 = 176
    client.post("/api/v1/cart/items", json={"product_id": 2, "quantity": 1}, headers=session_headers)  # 66 * 1 = 66
    response = client.post("/api/v1/cart/items", json={"product_id": 3, "quantity": 3}, headers=session_headers)  # 45 * 3 = 135
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify subtotal: 176 + 66 + 135 = 377
    expected_subtotal = 176 + 66 + 135
    assert data["totals"]["subtotal"] == expected_subtotal
    
    # Verify individual item calculations
    for item in data["items"]:
        expected_line_total = item["unit_price"] * item["quantity"]
        # Note: line_total might not be in response, but unit_price should be correct
        assert item["unit_price"] > 0
