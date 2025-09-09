"""Tests for curations endpoints."""

import pytest
from unittest.mock import patch


def test_list_curations_with_config(client, setup_test_data):
    """Test listing curations when config is available."""
    response = client.get("/api/v1/curations")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "curations" in data
    curations = data["curations"]
    
    # Should have our mock curation
    assert len(curations) >= 1
    
    for curation in curations:
        assert "slug" in curation
        assert "title" in curation
        assert isinstance(curation["slug"], str)
        assert isinstance(curation["title"], str)
        assert len(curation["slug"]) > 0
        assert len(curation["title"]) > 0


def test_list_curations_fallback():
    """Test listing curations when no config is available (fallback)."""
    with patch('data_loader.CURATIONS_CONFIG', None):
        from fastapi.testclient import TestClient
        from app import create_app
        
        client = TestClient(create_app())
        response = client.get("/api/v1/curations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "curations" in data
        curations = data["curations"]
        
        # Should have fallback curations
        assert len(curations) >= 2
        
        slugs = [c["slug"] for c in curations]
        assert "flash-deals" in slugs
        assert "weekly-picks" in slugs


def test_get_configured_curation(client, setup_test_data):
    """Test getting a specific configured curation."""
    response = client.get("/api/v1/curations/flash-deals")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "curation" in data
    assert "meta" in data
    
    curation = data["curation"]
    assert curation["slug"] == "flash-deals"
    assert curation["title"] == "她的秒杀商品"
    assert "products" in curation
    assert isinstance(curation["products"], list)
    
    # Should contain products from our config (product IDs 1 and 2)
    if len(curation["products"]) > 0:
        for product in curation["products"]:
            assert "id" in product
            assert "name" in product
            assert "price" in product
            assert product["id"] in [1, 2]


def test_get_fallback_curation_flash_deals(client, setup_test_data):
    """Test getting flash-deals with fallback logic."""
    with patch('data_loader.CURATIONS_CONFIG', None):
        response = client.get("/api/v1/curations/flash-deals")
        
        assert response.status_code == 200
        data = response.json()
        
        curation = data["curation"]
        assert curation["slug"] == "flash-deals"
        assert curation["title"] == "她的秒杀商品"
        
        # Products should be sorted by price (cheapest first)
        products = curation["products"]
        if len(products) > 1:
            for i in range(len(products) - 1):
                assert products[i]["price"] <= products[i + 1]["price"]


def test_get_fallback_curation_weekly_picks(client, setup_test_data):
    """Test getting weekly-picks with fallback logic."""
    with patch('data_loader.CURATIONS_CONFIG', None):
        response = client.get("/api/v1/curations/weekly-picks")
        
        assert response.status_code == 200
        data = response.json()
        
        curation = data["curation"]
        assert curation["slug"] == "weekly-picks"
        assert curation["title"] == "她的本周推荐"
        
        # Should have products (popular items)
        assert len(curation["products"]) > 0


def test_get_nonexistent_curation(client, setup_test_data):
    """Test getting non-existent curation."""
    response = client.get("/api/v1/curations/nonexistent")
    
    assert response.status_code == 404
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert "unknown" in data["error"]["message"].lower()


def test_curation_pagination(client, setup_test_data):
    """Test curation pagination."""
    response = client.get("/api/v1/curations/flash-deals?page=1&page_size=1")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "meta" in data
    meta = data["meta"]
    
    assert "page" in meta
    assert "page_size" in meta
    assert "total" in meta
    assert "pages" in meta
    
    assert meta["page"] == 1
    assert meta["page_size"] == 1
    
    # Products should be limited to 1
    products = data["curation"]["products"]
    assert len(products) <= 1


def test_curation_pagination_second_page(client, setup_test_data):
    """Test getting second page of curation."""
    # First get total count
    response1 = client.get("/api/v1/curations/flash-deals?page_size=1")
    total = response1.json()["meta"]["total"]
    
    if total > 1:
        response2 = client.get("/api/v1/curations/flash-deals?page=2&page_size=1")
        
        assert response2.status_code == 200
        data = response2.json()
        
        assert data["meta"]["page"] == 2
        # Should have products if there are enough total products
        if total > 1:
            assert len(data["curation"]["products"]) > 0


def test_curation_large_page_size(client, setup_test_data):
    """Test curation with large page size."""
    response = client.get("/api/v1/curations/flash-deals?page_size=100")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return all products, but limited by curation limit (12 for flash-deals)
    products = data["curation"]["products"]
    assert len(products) <= 12  # Fallback flash-deals limit


def test_curation_invalid_page(client, setup_test_data):
    """Test curation with invalid page number."""
    response = client.get("/api/v1/curations/flash-deals?page=999")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return empty results for page beyond available data
    assert data["meta"]["page"] == 999
    assert len(data["curation"]["products"]) == 0


def test_curation_product_structure(client, setup_test_data):
    """Test that curation products have correct structure."""
    response = client.get("/api/v1/curations/flash-deals")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["curation"]["products"]
    
    for product in products:
        # Check required fields
        required_fields = ["id", "name", "price", "image"]
        for field in required_fields:
            assert field in product, f"Missing field: {field}"
        
        # Check data types
        assert isinstance(product["id"], int)
        assert isinstance(product["name"], str)
        assert isinstance(product["price"], (int, float))
        assert isinstance(product["image"], str)
        
        # Check optional fields if present
        if "rating" in product:
            assert isinstance(product["rating"], (int, float))
            assert 0 <= product["rating"] <= 5
        
        if "reviews" in product:
            assert isinstance(product["reviews"], int)
            assert product["reviews"] >= 0


def test_curations_meta_structure(client, setup_test_data):
    """Test that curations meta has correct structure."""
    response = client.get("/api/v1/curations/flash-deals?page=1&page_size=5")
    
    assert response.status_code == 200
    data = response.json()
    
    meta = data["meta"]
    required_fields = ["page", "page_size", "total", "pages"]
    
    for field in required_fields:
        assert field in meta, f"Missing meta field: {field}"
        assert isinstance(meta[field], int), f"Meta field {field} should be int"
        assert meta[field] >= 0, f"Meta field {field} should be non-negative"
    
    # Logical checks
    assert meta["page"] >= 1
    assert meta["page_size"] >= 1
    assert meta["pages"] >= 0
    
    if meta["total"] > 0:
        expected_pages = (meta["total"] - 1) // meta["page_size"] + 1
        assert meta["pages"] == expected_pages


def test_curation_empty_config_products(client, setup_test_data):
    """Test curation with empty product list in config."""
    empty_config = {
        "empty-curation": {
            "title": "Empty Curation",
            "product_ids": [],
            "rules": {"sort": "popular", "limit": 10}
        }
    }
    
    with patch('data_loader.CURATIONS_CONFIG', empty_config):
        response = client.get("/api/v1/curations/empty-curation")
        
        assert response.status_code == 200
        data = response.json()
        
        curation = data["curation"]
        assert curation["slug"] == "empty-curation"
        assert curation["title"] == "Empty Curation"
        assert len(curation["products"]) == 0


def test_curation_with_invalid_product_ids(client, setup_test_data):
    """Test curation with invalid product IDs in config."""
    invalid_config = {
        "invalid-products": {
            "title": "Invalid Products",
            "product_ids": [999, 1000, 1],  # 999 and 1000 don't exist, 1 exists
            "rules": {"sort": "popular", "limit": 10}
        }
    }
    
    with patch('data_loader.CURATIONS_CONFIG', invalid_config):
        response = client.get("/api/v1/curations/invalid-products")
        
        assert response.status_code == 200
        data = response.json()
        
        products = data["curation"]["products"]
        # Should only include valid products (product ID 1)
        assert len(products) == 1
        assert products[0]["id"] == 1
