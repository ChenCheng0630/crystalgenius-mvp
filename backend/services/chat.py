"""Simple in-memory chat service used by the demo endpoints."""

from __future__ import annotations

import uuid
from typing import List, Dict

from ..models import ChatMessage


CHATS: Dict[str, List[ChatMessage]] = {}


SCRIPTED_REPLY = (
    "你好，我是小晶，有关水晶的问题都可以问我～"
)


def get_history(session_id: str) -> List[ChatMessage]:
    return CHATS.setdefault(session_id, [])


def add_message(session_id: str, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(id=str(uuid.uuid4()), role=role, content=content)
    get_history(session_id).append(msg)
    return msg


def handle_user_message(session_id: str, content: str) -> List[ChatMessage]:
    messages = get_history(session_id)
    user_msg = add_message(session_id, "user", content)
    if len(messages) == 1:
        # First message; provide intro reply
        reply_content = SCRIPTED_REPLY
    else:
        reply_content = f"你说的是：{content}"
    add_message(session_id, "assistant", reply_content)
    return messages
