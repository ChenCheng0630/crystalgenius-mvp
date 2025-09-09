"""Mock checkout flow used by the mobile demo."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

from models import Cart
from services.cart import get_cart


CHECKOUTS: Dict[str, Dict] = {}


def create_session(session_id: str, return_url: str, cancel_url: str) -> Dict:
    """Create a checkout session with validation."""
    if not return_url or not cancel_url:
        raise ValueError("return_url and cancel_url are required")
    
    cart = get_cart(session_id)
    if not cart.items:
        raise ValueError("Cart is empty")
    
    checkout_id = f"co_{str(uuid.uuid4())[:8]}"
    expires = datetime.now(tz=timezone.utc) + timedelta(minutes=30)
    
    data = {
        "checkout_id": checkout_id,
        "checkout_url": f"https://mockpay.local/checkout/{checkout_id}",
        "expires_at": expires.isoformat(),
    }
    
    # Mock immediate payment success
    CHECKOUTS[checkout_id] = {
        "status": "paid", 
        "session_id": session_id, 
        "created_at": datetime.now(tz=timezone.utc).isoformat()
    }
    
    return data


def get_session(checkout_id: str) -> Dict:
    """Get checkout session status."""
    checkout = CHECKOUTS.get(checkout_id)
    if not checkout:
        return {"status": "not_found"}
    
    resp = {"status": checkout["status"]}
    if checkout["status"] == "paid":
        resp["order_id"] = f"ord_{checkout_id}"
    
    return resp
