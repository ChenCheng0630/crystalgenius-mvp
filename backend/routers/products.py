"""Product listing and detail routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .. import data_loader
from ..repositories import (
    serialize_product,
    paginate,
    apply_filters,
    apply_sort,
    apply_relevance,
)
from ..services.query_resolver import HeuristicQueryResolver

router = APIRouter(prefix="/products", tags=["products"])
resolver = HeuristicQueryResolver()


@router.get("")
async def list_products(
    q: str | None = None,
    parent_category_id: int = 831,
    color: list[str] | None = Query(None),
    material: list[str] | None = Query(None),
    category_name: list[str] | None = Query(None),
    category_id: list[int] | None = Query(None),
    min_price: float | None = None,
    max_price: float | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    products = list(data_loader.PRODUCTS.values())
    filters = {
        "color": color,
        "material": material,
        "category_name": category_name,
        "category_id": category_id,
        "min_price": min_price,
        "max_price": max_price,
    }
    if q:
        parsed = resolver.resolve(q)
        filters.setdefault("color", []).extend(parsed.get("colors", []))
        filters.setdefault("material", []).extend(parsed.get("materials", []))
        filters.setdefault("category_name", []).extend(parsed.get("category_names", []))
        if price := parsed.get("price_range"):
            if price.get("min") is not None:
                filters["min_price"] = price["min"]
            if price.get("max") is not None:
                filters["max_price"] = price["max"]
        products = apply_relevance(products, q)
        sort = sort or "relevance"

    products = apply_filters(products, filters)
    if sort and sort != "relevance":
        products = apply_sort(products, sort)
    elif not q:
        products = apply_sort(products, sort or "popular")

    products_slice, meta = paginate(products, page, page_size)
    return {"products": [serialize_product(p) for p in products_slice], "meta": meta}


@router.get("/{product_id}")
async def get_product(product_id: int) -> dict:
    product = data_loader.PRODUCTS.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="not found")
    return serialize_product(product, include_detail=True)
