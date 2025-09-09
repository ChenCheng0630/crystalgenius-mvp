"""Mock checkout flow used by the mobile demo."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

from ..models import Cart
from .cart import get_cart


CHECKOUTS: Dict[str, Dict] = {}


def create_session(session_id: str, return_url: str, cancel_url: str) -> Dict:
    cart = get_cart(session_id)
    checkout_id = str(uuid.uuid4())
    expires = datetime.now(tz=timezone.utc) + timedelta(minutes=10)
    data = {
        "checkout_id": checkout_id,
        "checkout_url": f"https://example.com/checkout/{checkout_id}",
        "expires_at": expires.isoformat(),
    }
    CHECKOUTS[checkout_id] = {"status": "paid", "order_id": f"ord_{checkout_id[:8]}"}
    return data


def get_session(checkout_id: str) -> Dict:
    return CHECKOUTS.get(checkout_id, {"status": "not_found"})
