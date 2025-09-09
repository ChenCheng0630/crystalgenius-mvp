"""Tests for chat endpoints."""

import pytest
from unittest.mock import patch, MagicMock
import json
from .test_utils import assert_error_response


def test_create_chat_session(client, session_headers, setup_test_data):
    """Test creating a chat session."""
    response = client.post("/api/v1/chat/sessions", headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "session_id" in data
    assert data["session_id"] == "test-session-123"  # From our session headers


def test_get_empty_chat_messages(client, session_headers, setup_test_data):
    """Test getting messages from empty chat."""
    response = client.get("/api/v1/chat/messages", headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "messages" in data
    assert data["messages"] == []


def test_post_chat_message_disabled_llm(client, session_headers, setup_test_data, disable_llm):
    """Test posting a message with LLM disabled (fallback mode)."""
    payload = {
        "message": "Hello, I'm looking for crystals"
    }
    
    response = client.post("/api/v1/chat/messages", json=payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "messages" in data
    assert len(data["messages"]) == 2  # user message + assistant reply
    
    # Check user message
    user_msg = data["messages"][0]
    assert user_msg["role"] == "user"
    assert user_msg["content"] == "Hello, I'm looking for crystals"
    assert "id" in user_msg
    
    # Check assistant reply (should be scripted reply for first message)
    assistant_msg = data["messages"][1]
    assert assistant_msg["role"] == "assistant"
    assert "小晶" in assistant_msg["content"]
    assert "id" in assistant_msg


def test_post_chat_message_follow_up(client, session_headers, setup_test_data, disable_llm):
    """Test posting a follow-up message (not first message)."""
    # First message
    client.post("/api/v1/chat/messages", json={"message": "Hello"}, headers=session_headers)
    
    # Follow-up message
    payload = {"message": "Tell me about crystals"}
    response = client.post("/api/v1/chat/messages", json=payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["messages"]) == 4  # 2 from first + 2 from second
    
    # Check latest assistant reply (should echo the message in fallback mode)
    latest_msg = data["messages"][-1]
    assert latest_msg["role"] == "assistant"
    assert "Tell me about crystals" in latest_msg["content"]


def test_post_empty_message(client, session_headers, setup_test_data):
    """Test posting empty message."""
    payload = {"message": ""}
    
    response = client.post("/api/v1/chat/messages", json=payload, headers=session_headers)
    
    assert response.status_code == 400
    data = response.json()
    
    assert_error_response(data, "validation_error", "required")


def test_post_message_missing_field(client, session_headers, setup_test_data):
    """Test posting message without message field."""
    payload = {}
    
    response = client.post("/api/v1/chat/messages", json=payload, headers=session_headers)
    
    assert response.status_code == 400
    data = response.json()
    
    assert_error_response(data, "validation_error")


def test_post_message_with_content_field(client, session_headers, setup_test_data, disable_llm):
    """Test posting message using 'content' field instead of 'message'."""
    payload = {"content": "Hello with content field"}
    
    response = client.post("/api/v1/chat/messages", json=payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    user_msg = data["messages"][0]
    assert user_msg["content"] == "Hello with content field"


def test_chat_session_isolation(client, setup_test_data, disable_llm):
    """Test that different sessions have isolated chats."""
    headers1 = {"X-Session-Id": "session-1"}
    headers2 = {"X-Session-Id": "session-2"}
    
    # Send message in first session
    client.post("/api/v1/chat/messages", json={"message": "Message in session 1"}, headers=headers1)
    
    # Check second session is empty
    response2 = client.get("/api/v1/chat/messages", headers=headers2)
    assert response2.status_code == 200
    assert len(response2.json()["messages"]) == 0
    
    # Check first session has messages
    response1 = client.get("/api/v1/chat/messages", headers=headers1)
    assert response1.status_code == 200
    assert len(response1.json()["messages"]) == 2  # user + assistant


@patch('services.chat._should_use_llm')
def test_post_message_with_llm_enabled(mock_should_use_llm, client, session_headers, setup_test_data, mock_openai):
    """Test posting message with LLM enabled."""
    mock_should_use_llm.return_value = True
    
    payload = {"message": "I want purple crystals"}
    response = client.post("/api/v1/chat/messages", json=payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["messages"]) == 2
    assistant_msg = data["messages"][-1]
    assert assistant_msg["role"] == "assistant"
    assert len(assistant_msg["content"]) > 0


def test_chat_stream_endpoint_empty_message(client, session_headers, setup_test_data):
    """Test streaming endpoint with empty message."""
    response = client.get("/api/v1/chat/stream?message=", headers=session_headers)
    
    assert response.status_code == 400
    data = response.json()
    
    assert_error_response(data, "validation_error")


def test_chat_stream_endpoint_disabled_llm(client, session_headers, setup_test_data, disable_llm):
    """Test streaming endpoint with LLM disabled."""
    response = client.get("/api/v1/chat/stream?message=Hello", headers=session_headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # For streaming responses, we need to consume the iterator
    content = response.content.decode('utf-8')
    assert "event: assistant_message" in content
    assert "event: done" in content


def test_message_structure(client, session_headers, setup_test_data, disable_llm):
    """Test that messages have correct structure."""
    payload = {"message": "Test message structure"}
    response = client.post("/api/v1/chat/messages", json=payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    for message in data["messages"]:
        assert "id" in message
        assert "role" in message
        assert "content" in message
        
        assert isinstance(message["id"], str)
        assert message["role"] in ["user", "assistant"]
        assert isinstance(message["content"], str)
        assert len(message["id"]) > 0
        assert len(message["content"]) > 0


@patch('services.chat._should_use_llm')
def test_chat_with_product_suggestions(mock_should_use_llm, client, session_headers, setup_test_data, disable_llm):
    """Test chat that might return product suggestions."""
    # Even with LLM disabled, heuristic resolver might trigger suggestions
    payload = {"message": "I want purple crystals under 100 yuan"}
    response = client.post("/api/v1/chat/messages", json=payload, headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check if suggestions are present (might be based on heuristics)
    if "suggestions" in data:
        suggestions = data["suggestions"]
        assert "products" in suggestions
        assert "reason" in suggestions
        assert isinstance(suggestions["products"], list)
        
        for product in suggestions["products"]:
            assert "id" in product
            assert "name" in product
            assert "price" in product


def test_chat_message_persistence(client, session_headers, setup_test_data, disable_llm):
    """Test that messages persist across requests."""
    # Send first message
    client.post("/api/v1/chat/messages", json={"message": "First message"}, headers=session_headers)
    
    # Send second message
    response2 = client.post("/api/v1/chat/messages", json={"message": "Second message"}, headers=session_headers)
    
    assert response2.status_code == 200
    data = response2.json()
    
    # Should have all 4 messages (2 user + 2 assistant)
    assert len(data["messages"]) == 4
    
    # Check message order and content
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "First message"
    assert data["messages"][1]["role"] == "assistant"
    assert data["messages"][2]["role"] == "user"
    assert data["messages"][2]["content"] == "Second message"
    assert data["messages"][3]["role"] == "assistant"


def test_get_messages_after_posting(client, session_headers, setup_test_data, disable_llm):
    """Test getting messages after posting them."""
    # Post a message
    client.post("/api/v1/chat/messages", json={"message": "Test message"}, headers=session_headers)
    
    # Get messages separately
    response = client.get("/api/v1/chat/messages", headers=session_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["messages"]) == 2  # user + assistant
    assert data["messages"][0]["content"] == "Test message"


@patch('services.chat._should_use_llm')
@patch('services.chat._OPENAI_CLIENT_CLS')
def test_llm_error_fallback(mock_openai_cls, mock_should_use_llm, client, session_headers, setup_test_data):
    """Test that LLM errors fall back to scripted responses."""
    mock_should_use_llm.return_value = True
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    
    # Make LLM throw an error
    mock_client.responses.create.side_effect = Exception("API Error")
    
    payload = {"message": "Test message"}
    response = client.post("/api/v1/chat/messages", json=payload, headers=session_headers)
    
    # Should still succeed with fallback response
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["messages"]) == 2
    assistant_msg = data["messages"][-1]
    assert "抱歉" in assistant_msg["content"] or "暂时" in assistant_msg["content"]
