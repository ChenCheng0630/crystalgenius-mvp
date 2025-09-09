"""Shared FastAPI dependencies."""

from __future__ import annotations

import uuid
from fastapi import Request, Response


def get_session_id(request: Request, response: Response) -> str:
    sid = request.headers.get("X-Session-Id") or request.cookies.get("session_id")
    if not sid:
        sid = uuid.uuid4().hex
        response.set_cookie("session_id", sid)
    return sid
