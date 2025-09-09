"""Checkout endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..services import checkout
from ..deps import get_session_id

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/sessions")
async def create_session(payload: dict, session_id: str = Depends(get_session_id)) -> dict:
    return checkout.create_session(
        session_id, payload.get("return_url", ""), payload.get("cancel_url", "")
    )


@router.get("/sessions/{checkout_id}")
async def get_session(checkout_id: str) -> dict:
    return checkout.get_session(checkout_id)
