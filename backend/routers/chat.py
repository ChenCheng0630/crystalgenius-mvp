"""Chat endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..services import chat
from ..deps import get_session_id

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/messages")
async def get_messages(session_id: str = Depends(get_session_id)) -> dict:
    history = chat.get_history(session_id)
    return {"messages": [m.__dict__ for m in history]}


@router.post("/messages")
async def post_message(payload: dict, session_id: str = Depends(get_session_id)) -> dict:
    content = payload.get("content", "")
    history = chat.handle_user_message(session_id, content)
    return {"messages": [m.__dict__ for m in history]}
