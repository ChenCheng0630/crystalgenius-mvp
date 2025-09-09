"""Cart API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from repositories import serialize_cart
from utils import raise_error_response
from services import cart as cart_service
from deps import get_session_id

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("")
async def get_cart(session_id: str = Depends(get_session_id)) -> dict:
    cart = cart_service.get_cart(session_id)
    return serialize_cart(cart)


@router.post("/items")
async def add_item(payload: dict, session_id: str = Depends(get_session_id)) -> dict:
    product_id = int(payload.get("product_id"))
    quantity = int(payload.get("quantity", 1))
    try:
        cart = cart_service.add_item(session_id, product_id, quantity)
    except KeyError:
        raise_error_response("not_found", "Product not found", status_code=404)
    return serialize_cart(cart)


@router.patch("/items/{item_id}")
async def update_item(
    item_id: str, payload: dict, session_id: str = Depends(get_session_id)
) -> dict:
    quantity = int(payload.get("quantity", 1))
    cart = cart_service.update_item(session_id, item_id, quantity)
    return serialize_cart(cart)


@router.delete("/items/{item_id}")
async def remove_item(item_id: str, session_id: str = Depends(get_session_id)) -> dict:
    cart = cart_service.remove_item(session_id, item_id)
    return serialize_cart(cart)


@router.delete("")
async def clear_cart(session_id: str = Depends(get_session_id)) -> dict:
    """Clear the entire cart."""
    cart = cart_service.clear_cart(session_id)
    return serialize_cart(cart)
