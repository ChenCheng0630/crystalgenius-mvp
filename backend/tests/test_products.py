"""Tests for products endpoints."""

import pytest
from unittest.mock import patch


def test_list_products_default(client, setup_test_data):
    """Test listing products with default parameters."""
    response = client.get("/api/v1/products")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "products" in data
    assert "meta" in data
    
    products = data["products"]
    assert isinstance(products, list)
    assert len(products) <= 20  # Default page size
    
    # Check product structure
    for product in products:
        assert "id" in product
        assert "name" in product
        assert "price" in product
        assert "image" in product
        assert isinstance(product["id"], int)
        assert isinstance(product["name"], str)
        assert isinstance(product["price"], (int, float))
        assert isinstance(product["image"], str)


def test_list_products_with_pagination(client, setup_test_data):
    """Test products listing with pagination."""
    response = client.get("/api/v1/products?page=1&page_size=2")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "meta" in data
    meta = data["meta"]
    
    assert meta["page"] == 1
    assert meta["page_size"] == 2
    assert "total" in meta
    assert "pages" in meta
    
    products = data["products"]
    assert len(products) <= 2


def test_list_products_with_color_filter(client, setup_test_data):
    """Test products listing with color filter."""
    response = client.get("/api/v1/products?color=紫色")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    # Should contain purple crystal from our mock data
    assert len(products) >= 1
    
    # Find the purple crystal
    purple_products = [p for p in products if "紫" in p["name"]]
    assert len(purple_products) >= 1


def test_list_products_with_material_filter(client, setup_test_data):
    """Test products listing with material filter."""
    response = client.get("/api/v1/products?material=紫水晶")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    # Should contain purple crystal from our mock data
    assert len(products) >= 1


def test_list_products_with_price_range(client, setup_test_data):
    """Test products listing with price range filter."""
    response = client.get("/api/v1/products?min_price=50&max_price=100")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    for product in products:
        assert 50 <= product["price"] <= 100


def test_list_products_with_multiple_filters(client, setup_test_data):
    """Test products listing with multiple filters."""
    response = client.get("/api/v1/products?color=紫色&material=紫水晶&max_price=100")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    for product in products:
        assert product["price"] <= 100


def test_list_products_with_sort(client, setup_test_data):
    """Test products listing with sorting."""
    response = client.get("/api/v1/products?sort=price_asc")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    if len(products) > 1:
        for i in range(len(products) - 1):
            assert products[i]["price"] <= products[i + 1]["price"]


def test_list_products_with_query(client, setup_test_data):
    """Test products listing with search query."""
    response = client.get("/api/v1/products?q=水晶")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    # Should find products containing "水晶" in name
    assert len(products) > 0
    
    for product in products:
        assert "水晶" in product["name"]


def test_search_products_basic(client, setup_test_data):
    """Test basic product search."""
    response = client.get("/api/v1/products/search?q=紫水晶")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "analysis" in data
    assert "products" in data
    assert "meta" in data
    
    analysis = data["analysis"]
    assert "query" in analysis
    assert "summary" in analysis
    assert "filters" in analysis
    
    assert analysis["query"] == "紫水晶"
    
    products = data["products"]
    # Should find purple crystal
    assert len(products) >= 1


def test_search_products_with_analysis(client, setup_test_data):
    """Test product search with query analysis."""
    response = client.get("/api/v1/products/search?q=紫色水晶手串")
    
    assert response.status_code == 200
    data = response.json()
    
    analysis = data["analysis"]
    filters = analysis["filters"]
    
    # Should analyze color and material
    assert "colors" in filters
    assert "materials" in filters
    assert "category_names" in filters
    assert "price_range" in filters


def test_search_products_with_price_query(client, setup_test_data):
    """Test product search with price in query."""
    response = client.get("/api/v1/products/search?q=100元以下的水晶")
    
    assert response.status_code == 200
    data = response.json()
    
    analysis = data["analysis"]
    price_range = analysis["filters"]["price_range"]
    
    # Should extract price limit
    if price_range:
        assert "max" in price_range
        # Note: This depends on the query resolver implementation


def test_search_products_with_explicit_filters(client, setup_test_data):
    """Test search with both query and explicit filters."""
    response = client.get("/api/v1/products/search?q=水晶&color=紫色&max_price=100")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    for product in products:
        assert product["price"] <= 100
        assert "水晶" in product["name"]


def test_get_product_by_id(client, setup_test_data):
    """Test getting a specific product by ID."""
    response = client.get("/api/v1/products/1")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should be serialized product with include_detail=True
    assert data["id"] == 1
    assert data["name"] == "紫水晶手串"
    assert data["price"] == 88.0
    assert "description" in data
    assert data["description"] == "天然紫水晶，助眠宁神"


def test_get_product_not_found(client, setup_test_data):
    """Test getting non-existent product."""
    response = client.get("/api/v1/products/999")
    
    assert response.status_code == 404
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert "not found" in data["error"]["message"].lower()


def test_products_meta_structure(client, setup_test_data):
    """Test that products meta has correct structure."""
    response = client.get("/api/v1/products?page=1&page_size=5")
    
    assert response.status_code == 200
    data = response.json()
    
    meta = data["meta"]
    required_fields = ["page", "page_size", "total", "pages"]
    
    for field in required_fields:
        assert field in meta
        assert isinstance(meta[field], int)
        assert meta[field] >= 0
    
    assert meta["page"] >= 1
    assert meta["page_size"] >= 1


def test_products_serialization_structure(client, setup_test_data):
    """Test that products are properly serialized."""
    response = client.get("/api/v1/products")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    
    for product in products:
        # Required fields
        required_fields = ["id", "name", "price", "image"]
        for field in required_fields:
            assert field in product
            assert product[field] is not None
        
        # Optional fields
        optional_fields = ["description", "rating", "reviews", "sold", "compare_at"]
        for field in optional_fields:
            if field in product and product[field] is not None:
                if field == "rating":
                    assert isinstance(product[field], (int, float))
                    assert 0 <= product[field] <= 5
                elif field == "reviews":
                    assert isinstance(product[field], int)
                    assert product[field] >= 0
                elif field in ["price", "compare_at"]:
                    assert isinstance(product[field], (int, float))
                    assert product[field] > 0
                else:
                    assert isinstance(product[field], str)


def test_products_empty_result(client, setup_test_data):
    """Test products endpoint with filters that return no results."""
    response = client.get("/api/v1/products?color=不存在的颜色")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["products"] == []
    assert data["meta"]["total"] == 0
    assert data["meta"]["pages"] == 0


def test_products_large_page_number(client, setup_test_data):
    """Test products with page number beyond available data."""
    response = client.get("/api/v1/products?page=999&page_size=10")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["products"] == []
    assert data["meta"]["page"] == 999


def test_products_sort_options(client, setup_test_data):
    """Test various sort options."""
    sort_options = ["popular", "price_asc", "price_desc", "newest", "relevance"]
    
    for sort_option in sort_options:
        if sort_option == "relevance":
            # Relevance requires a query
            response = client.get(f"/api/v1/products?q=水晶&sort={sort_option}")
        else:
            response = client.get(f"/api/v1/products?sort={sort_option}")
        
        assert response.status_code == 200
        data = response.json()
        
        products = data["products"]
        # Just check that it returns products without error
        assert isinstance(products, list)


def test_products_invalid_sort(client, setup_test_data):
    """Test products with invalid sort parameter."""
    response = client.get("/api/v1/products?sort=invalid_sort")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should still work, just ignore invalid sort
    assert isinstance(data["products"], list)


def test_products_category_filter(client, setup_test_data):
    """Test products with category filter."""
    response = client.get("/api/v1/products?category_id=101")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    # Should find products in category 101
    if len(products) > 0:
        # Verify products have category 101
        for product in products:
            # Note: This depends on how categories are serialized in products
            assert "category_id" in product or "categories" in product


def test_products_multiple_category_filter(client, setup_test_data):
    """Test products with multiple category filters."""
    response = client.get("/api/v1/products?category_id=101&category_id=102")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should work with multiple category IDs
    assert isinstance(data["products"], list)


def test_products_category_name_filter(client, setup_test_data):
    """Test products with category name filter."""
    response = client.get("/api/v1/products?category_name=紫水晶系列")
    
    assert response.status_code == 200
    data = response.json()
    
    products = data["products"]
    # Should find products in the purple crystal category
    assert len(products) >= 1


def test_search_analysis_summary_format(client, setup_test_data):
    """Test that search analysis summary is properly formatted."""
    response = client.get("/api/v1/products/search?q=紫色水晶100元以下")
    
    assert response.status_code == 200
    data = response.json()
    
    analysis = data["analysis"]
    summary = analysis["summary"]
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    
    # Should contain information about filters found
    if analysis["filters"]["colors"]:
        assert "颜色" in summary
    if analysis["filters"]["price_range"]:
        assert "价格" in summary


def test_products_concurrent_filters(client, setup_test_data):
    """Test products with overlapping filters."""
    response = client.get("/api/v1/products?color=紫色&material=紫水晶&category_name=紫水晶系列")
    
    assert response.status_code == 200
    data = response.json()
    
    # All filters should be applied together
    products = data["products"]
    # Should find the purple crystal that matches all criteria
    assert len(products) >= 1


@patch('services.query_resolver.HeuristicQueryResolver.resolve')
def test_products_query_resolver_fallback(mock_resolve, client, setup_test_data):
    """Test products endpoint with query resolver error fallback."""
    # Make resolver throw an error
    mock_resolve.side_effect = Exception("Resolver error")
    
    response = client.get("/api/v1/products?q=test query")
    
    # Should still work but without query analysis
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data["products"], list)


def test_product_detail_fields(client, setup_test_data):
    """Test that product detail includes all expected fields."""
    response = client.get("/api/v1/products/1")
    
    assert response.status_code == 200
    product = response.json()
    
    # Should include detailed information
    expected_fields = ["id", "name", "price", "image", "description"]
    for field in expected_fields:
        assert field in product
        assert product[field] is not None
    
    # Optional fields should be present if available
    if "extra_images" in product:
        assert isinstance(product["extra_images"], list)
    
    if "category_id" in product:
        assert isinstance(product["category_id"], list)


def test_products_performance_large_page_size(client, setup_test_data):
    """Test products endpoint with large page size."""
    response = client.get("/api/v1/products?page_size=100")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should handle large page sizes gracefully
    assert isinstance(data["products"], list)
    assert len(data["products"]) <= 100
