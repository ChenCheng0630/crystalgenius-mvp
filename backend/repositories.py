"""Utility functions for querying and serialising domain objects."""

from __future__ import annotations

from typing import Iterable, List, Tuple, Dict

from . import data_loader
from .models import Product, Category, ParentCategory, Cart


# ---------------------------------------------------------------------------
# Pagination

def paginate(items: List, page: int = 1, size: int = 20) -> Tuple[List, Dict[str, int]]:
    """Return a slice of ``items`` with pagination metadata."""

    total = len(items)
    start = (page - 1) * size
    end = start + size
    return items[start:end], {"page": page, "page_size": size, "total": total}


# ---------------------------------------------------------------------------
# Filtering and sorting helpers

def tokenize(q: str) -> List[str]:
    return [tok.lower() for tok in q.split() if tok]


def apply_filters(items: Iterable[Product], filters: dict) -> List[Product]:
    """Apply colour/material/price/category filters to ``items``."""

    color = set(filters.get("color") or [])
    material = set(filters.get("material") or [])
    cat_names = set(filters.get("category_name") or [])
    cat_ids = set(int(c) for c in filters.get("category_id") or [])
    min_price = float(filters.get("min_price")) if filters.get("min_price") else None
    max_price = float(filters.get("max_price")) if filters.get("max_price") else None

    def ok(p: Product) -> bool:
        if min_price is not None and p.price < min_price:
            return False
        if max_price is not None and p.price > max_price:
            return False
        cats = data_loader.PRODUCT_TO_CATEGORIES.get(p.id, [])
        if color and not {c.color for c in cats if c.color}.intersection(color):
            return False
        if material and not {c.material for c in cats if c.material}.intersection(material):
            return False
        if cat_names and not {c.category_name for c in cats if c.category_name}.intersection(cat_names):
            return False
        if cat_ids and not {c.id for c in cats}.intersection(cat_ids):
            return False
        return True

    return [p for p in items if ok(p)]


def apply_relevance(items: List[Product], q: str) -> List[Product]:
    tokens = tokenize(q)

    def score(p: Product) -> int:
        s = 0
        name = (p.name or "").lower()
        for tok in tokens:
            if tok in name:
                s += 3
        for c in data_loader.PRODUCT_TO_CATEGORIES.get(p.id, []):
            line = " ".join(filter(None, [c.color, c.material, c.category_name])).lower()
            for tok in tokens:
                if tok in line:
                    s += 1
        return s

    return sorted(items, key=score, reverse=True)


def apply_sort(items: List[Product], sort: str) -> List[Product]:
    if sort == "price_asc":
        return sorted(items, key=lambda p: p.price)
    if sort == "price_desc":
        return sorted(items, key=lambda p: p.price, reverse=True)
    if sort == "newest":
        return sorted(items, key=lambda p: p.id, reverse=True)
    if sort == "popular":
        return sorted(
            items,
            key=lambda p: (getattr(p, "rating", 0), getattr(p, "reviews", 0)),
            reverse=True,
        )
    return items


# ---------------------------------------------------------------------------
# Serialisers

def serialize_product(p: Product, include_detail: bool = False) -> dict:
    cats = data_loader.PRODUCT_TO_CATEGORIES.get(p.id, [])
    data = {
        "id": p.id,
        "reference_id": p.reference_id,
        "name": p.name,
        "price": p.price,
        "currency": "CNY",
        "image": p.image,
        "compare_at": p.compare_at,
        "rating": p.rating,
        "reviews": p.reviews,
        "sold": p.sold,
    }
    if include_detail:
        data.update(
            {
                "extra_images": p.extra_images,
                "description": p.description,
                "categories": [serialize_category(c) for c in cats],
            }
        )
    return data


def serialize_category(c: Category) -> dict:
    return {
        "id": c.id,
        "reference_id": c.reference_id,
        "category_name": c.category_name,
        "parent_id": c.parent_id,
        "color": c.color,
        "material": c.material,
        "image": c.image,
    }


def serialize_parent(pc: ParentCategory) -> dict:
    return {
        "id": pc.reference_id,
        "reference_id": pc.reference_id,
        "name": pc.name,
        "image": pc.image,
    }


def serialize_cart(cart: Cart) -> dict:
    return {
        "id": cart.id,
        "items": [
            {
                "id": i.id,
                "product": serialize_product(i.product),
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "currency": i.currency,
            }
            for i in cart.items
        ],
        "totals": cart.totals,
    }


def recompute_totals(cart: Cart) -> Cart:
    subtotal = sum(i.unit_price * i.quantity for i in cart.items)
    cart.totals = {"subtotal": round(subtotal, 2), "currency": cart.currency}
    return cart
