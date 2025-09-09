"""Miscellaneous endpoints for categories and telemetry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

import data_loader
from utils import raise_error_response
from repositories import serialize_category, serialize_parent
from services import events

router = APIRouter(tags=["meta"])


@router.get("/categories")
async def list_categories(parent_id: int = Query(..., alias="parent_id")) -> dict:
    cats = data_loader.CATEGORIES_BY_PARENT.get(parent_id)
    if cats is None:
        raise_error_response("not_found", "Parent category not found", status_code=404)
    return {"categories": [serialize_category(c) for c in cats]}


@router.get("/parent-categories")
async def list_parent_categories() -> dict:
    pcs = [serialize_parent(pc) for pc in data_loader.PARENT_CATEGORIES.values()]
    return {"parent_categories": pcs}


@router.post("/events")
async def post_event(payload: dict) -> dict:
    events.record(payload)
    return {"ok": True}
