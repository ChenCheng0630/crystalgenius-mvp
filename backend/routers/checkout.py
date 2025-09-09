"""Checkout endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from services import checkout
from utils import raise_error_response
from deps import get_session_id

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("/sessions")
async def create_session(payload: dict, session_id: str = Depends(get_session_id)) -> dict:
    try:
        return checkout.create_session(
            session_id, payload.get("return_url", ""), payload.get("cancel_url", "")
        )
    except ValueError as e:
        if "required" in str(e):
            raise_error_response("validation_error", str(e))
        elif "empty" in str(e):
            raise_error_response("bad_request", str(e))
        else:
            raise_error_response("bad_request", str(e))


@router.get("/sessions/{checkout_id}")
async def get_session(checkout_id: str) -> dict:
    return checkout.get_session(checkout_id)
