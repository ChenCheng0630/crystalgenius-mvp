"""Cart management using in-memory storage."""

from __future__ import annotations

import uuid
from typing import Dict

from models import Cart, CartItem
import data_loader
from repositories import recompute_totals


CARTS: Dict[str, Cart] = {}


def get_cart(session_id: str) -> Cart:
    cart = CARTS.setdefault(session_id, Cart(id=session_id))
    recompute_totals(cart)
    return cart


def add_item(session_id: str, product_id: int, quantity: int) -> Cart:
    cart = get_cart(session_id)
    product = data_loader.PRODUCTS.get(product_id)
    if not product:
        raise KeyError("product not found")
    item = CartItem(
        id=str(uuid.uuid4()),
        product=product,
        quantity=quantity,
        unit_price=product.price,
    )
    cart.items.append(item)
    recompute_totals(cart)
    return cart


def update_item(session_id: str, item_id: str, quantity: int) -> Cart:
    cart = get_cart(session_id)
    for item in cart.items:
        if item.id == item_id:
            item.quantity = quantity
            break
    recompute_totals(cart)
    return cart


def remove_item(session_id: str, item_id: str) -> Cart:
    cart = get_cart(session_id)
    cart.items = [i for i in cart.items if i.id != item_id]
    recompute_totals(cart)
    return cart


def clear_cart(session_id: str) -> Cart:
    """Clear all items from the cart."""
    cart = get_cart(session_id)
    cart.items = []
    recompute_totals(cart)
    return cart
