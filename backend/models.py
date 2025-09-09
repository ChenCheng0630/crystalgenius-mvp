from __future__ import annotations

"""Data models for the CrystalGenius backend.

These are lightweight dataclasses used internally by the API.  The
frontend only receives serialised dictionaries, so we avoid the
additional dependency on Pydantic for the MVP implementation.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Product:
    """Represents a product loaded from ``products_full.csv``."""

    id: int
    reference_id: str
    name: str
    price: float
    image: str
    extra_images: List[str] = field(default_factory=list)
    description: str | None = None
    category_id: List[int] = field(default_factory=list)
    # Enriched fields used by the frontend
    compare_at: Optional[float] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    sold: Optional[str] = None


@dataclass
class Category:
    """Category information from ``category.csv``."""

    id: int
    reference_id: int
    color: Optional[str]
    material: Optional[str]
    category_name: Optional[str]
    parent_id: int
    image: Optional[str]


@dataclass
class ParentCategory:
    """Parent category (top level group) from ``parent_category.csv``."""

    id: int
    reference_id: int
    name: str
    image: Optional[str]


@dataclass
class CartItem:
    id: str
    product: Product
    quantity: int
    unit_price: float
    currency: str = "CNY"


@dataclass
class Cart:
    id: str
    items: List[CartItem] = field(default_factory=list)
    totals: Dict[str, float] = field(default_factory=dict)
    currency: str = "CNY"


@dataclass
class ChatMessage:
    id: str
    role: str
    content: str
