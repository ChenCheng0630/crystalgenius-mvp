"""Shared test fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Import the modules we need to test
from app import create_app
import data_loader
from models import Product, Category, ParentCategory


@pytest.fixture(scope="session")
def app():
    """Create FastAPI app for testing."""
    return create_app()


@pytest.fixture(scope="function")
def client(app):
    """Create test client with fresh state for each test."""
    # Clear any existing state before each test
    with patch('services.cart.CARTS', {}), \
         patch('services.chat.CHATS', {}), \
         patch('services.checkout.CHECKOUTS', {}), \
         patch('services.events.EVENTS', []):
        yield TestClient(app)


@pytest.fixture(scope="function")
def mock_data():
    """Mock data for testing."""
    # Mock products
    test_products = {
        1: Product(
            id=1,
            reference_id="PROD001",
            name="紫水晶手串",
            price=88.0,
            image="https://example.com/amethyst.jpg",
            description="天然紫水晶，助眠宁神",
            category_id=[101],
            compare_at=120.0,
            rating=4.8,
            reviews=156,
            sold="已售800+件"
        ),
        2: Product(
            id=2,
            reference_id="PROD002", 
            name="粉水晶手串",
            price=66.0,
            image="https://example.com/rose-quartz.jpg",
            description="粉色水晶，招桃花",
            category_id=[102],
            compare_at=88.0,  # Set a compare_at value to fix curation tests
            rating=4.6,
            reviews=89,
            sold="已售500+件"
        ),
        3: Product(
            id=3,
            reference_id="PROD003",
            name="白水晶手串", 
            price=45.0,
            image="https://example.com/clear-quartz.jpg",
            description="透明水晶，净化能量",
            category_id=[103],
            compare_at=55.0,  # Set a compare_at value to fix curation tests
            rating=4.5,
            reviews=67,
            sold="已售300+件"
        )
    }

    # Mock categories
    test_categories = {
        101: Category(
            id=101,
            reference_id=101,
            color="紫色",
            material="紫水晶",
            category_name="紫水晶系列",
            parent_id=831,
            image="https://example.com/cat-amethyst.jpg"
        ),
        102: Category(
            id=102,
            reference_id=102,
            color="粉色",
            material="粉水晶",
            category_name="粉水晶系列",
            parent_id=831,
            image="https://example.com/cat-rose-quartz.jpg"
        ),
        103: Category(
            id=103,
            reference_id=103,
            color="透明",
            material="白水晶",
            category_name="白水晶系列",
            parent_id=831,
            image="https://example.com/cat-clear-quartz.jpg"
        )
    }

    # Mock parent categories
    test_parent_categories = {
        831: ParentCategory(
            id=831,
            reference_id=831,
            name="按颜色材质",
            image="https://example.com/color-material.jpg"
        ),
        832: ParentCategory(
            id=832,
            reference_id=832,
            name="按款式风格",
            image="https://example.com/style.jpg"
        ),
        834: ParentCategory(
            id=834,
            reference_id=834,
            name="按手串类型",
            image="https://example.com/bracelet-type.jpg"
        )
    }

    return {
        "products": test_products,
        "categories": test_categories,
        "parent_categories": test_parent_categories
    }


@pytest.fixture(scope="function")
def setup_test_data(mock_data):
    """Setup test data in data_loader before each test."""
    with patch.object(data_loader, 'PRODUCTS', mock_data["products"]), \
         patch.object(data_loader, 'CATEGORIES', mock_data["categories"]), \
         patch.object(data_loader, 'PARENT_CATEGORIES', mock_data["parent_categories"]), \
         patch.object(data_loader, 'CATEGORIES_BY_PARENT', {831: list(mock_data["categories"].values())}), \
         patch.object(data_loader, 'COLOR_VALUES', {"紫色", "粉色", "透明"}), \
         patch.object(data_loader, 'MATERIAL_VALUES', {"紫水晶", "粉水晶", "白水晶"}), \
         patch.object(data_loader, 'CATEGORY_NAME_VALUES_BY_PARENT', {
             831: {"紫水晶系列", "粉水晶系列", "白水晶系列"},
             832: {"经典款", "时尚款"},
             834: {"单圈", "多圈"}
         }), \
         patch.object(data_loader, 'CURATIONS_CONFIG', {
             "flash-deals": {
                 "title": "她的秒杀商品",
                 "product_ids": [1, 2],
                 "rules": {"sort": "price_asc", "limit": 12}
             }
         }):
        yield


@pytest.fixture
def session_headers():
    """Headers with session ID for testing."""
    return {"X-Session-Id": "test-session-123"}


@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing LLM features."""
    with patch('services.chat._OPENAI_CLIENT_CLS') as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Mock typical response structure
        mock_response = MagicMock()
        mock_response.output_text = "Based on your preferences, here are some recommendations."
        mock_client.responses.create.return_value = mock_response
        
        yield mock_client


@pytest.fixture
def disable_llm():
    """Disable LLM features for testing."""
    with patch.dict(os.environ, {'ENABLE_LLM_CHAT': 'false', 'ENABLE_LLM_FILTERS': 'false'}):
        yield


@pytest.fixture
def enable_llm():
    """Enable LLM features for testing."""
    with patch.dict(os.environ, {
        'ENABLE_LLM_CHAT': 'true', 
        'ENABLE_LLM_FILTERS': 'true',
        'OPENAI_API_KEY': 'test-key-123'
    }):
        yield


def extract_error_from_response(response_data):
    """Helper function to extract error from nested response structure."""
    if "detail" in response_data and "error" in response_data["detail"]:
        return response_data["detail"]["error"]
    elif "error" in response_data:
        return response_data["error"]
    else:
        return None