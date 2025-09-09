"""Chat endpoints.

Adds LLM-driven POST /chat/messages with optional product suggestions and
SSE streaming at GET /chat/stream.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse
import json

from services import chat
from utils import raise_error_response
from repositories import serialize_product
from deps import get_session_id

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions")
async def create_chat_session(session_id: str = Depends(get_session_id)) -> dict:
    """Create a new chat session."""
    chat.ensure_session(session_id)
    return {"session_id": session_id}


@router.get("/messages")
async def get_messages(session_id: str = Depends(get_session_id)) -> dict:
    history = chat.get_history(session_id)
    return {"messages": [m.__dict__ for m in history]}


@router.post("/messages")
async def post_message(payload: dict, session_id: str = Depends(get_session_id)) -> dict:
    user_text = (payload.get("message") or payload.get("content") or "").strip()
    if not user_text:
        raise_error_response("validation_error", "message is required")

    # Persist user message
    chat.add_message(session_id, "user", user_text)

    # Generate reply and optional suggestions
    reply_text, suggestions = chat.generate_message_with_suggestions(session_id, user_text)
    chat.add_message(session_id, "assistant", reply_text)

    history = chat.get_history(session_id)
    resp = {"messages": [m.__dict__ for m in history]}
    if suggestions:
        # Ensure products are serialised dicts
        if suggestions.get("products") and suggestions["products"] and isinstance(suggestions["products"][0], dict):
            resp["suggestions"] = suggestions
        else:
            resp["suggestions"] = {
                "products": [serialize_product(p) for p in (suggestions.get("products") or [])],
                "reason": suggestions.get("reason"),
            }
    return resp


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\n" + "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"


@router.get("/stream")
async def stream(request: Request, message: str, session_id: str = Depends(get_session_id)):
    user_text = (message or "").strip()
    if not user_text:
        raise_error_response("validation_error", "message is required")

    # Persist user message
    chat.add_message(session_id, "user", user_text)

    def gen():
        if chat._should_use_llm():
            # Use streaming LLM with tool calling
            history = chat.get_history(session_id)
            full_text = ""
            for event in chat._llm_stream_with_tools(history, user_text):
                if event["type"] == "assistant_message":
                    full_text += event["data"]["content"]
                    yield _sse_event("assistant_message", event["data"])
                elif event["type"] == "product_suggestions":
                    yield _sse_event("product_suggestions", event["data"])
                elif event["type"] == "done":
                    yield _sse_event("done", event["data"])
            
            # Persist the complete assistant message
            if full_text:
                chat.add_message(session_id, "assistant", full_text)
        else:
            # Fallback to non-streaming
            reply_text, suggestions = chat.generate_message_with_suggestions(session_id, user_text)
            assistant_msg = chat.add_message(session_id, "assistant", reply_text)
            yield _sse_event("assistant_message", {"id": assistant_msg.id, "role": assistant_msg.role, "content": assistant_msg.content})
            if suggestions:
                # Ensure serialised products
                products = suggestions.get("products") or []
                if products and not isinstance(products[0], dict):
                    products = [serialize_product(p) for p in products]
                yield _sse_event("product_suggestions", {"products": products, "reason": suggestions.get("reason")})
            yield _sse_event("done", {})

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)
