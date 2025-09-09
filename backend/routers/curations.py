"""Routers exposing curated product lists."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

import data_loader
from utils import raise_error_response
from repositories import serialize_product, paginate, apply_sort

router = APIRouter(prefix="/curations", tags=["curations"])


@router.get("")
async def list_curations() -> dict:
    cfg = data_loader.CURATIONS_CONFIG or {}
    curations = [
        {"slug": slug, "title": val.get("title", slug)}
        for slug, val in cfg.items()
    ]
    
    # Add fallback curations if no config is provided
    if not curations:
        curations = [
            {"slug": "flash-deals", "title": "她的秒杀商品"},
            {"slug": "weekly-picks", "title": "她的本周推荐"},
        ]
    
    return {"curations": curations}


@router.get("/{slug}")
async def get_curation(slug: str, page: int = 1, page_size: int = 20) -> dict:
    cfg = (data_loader.CURATIONS_CONFIG or {}).get(slug)
    products = list(data_loader.PRODUCTS.values())
    
    if cfg:
        # Use configured curation
        if cfg.get("product_ids"):
            products = [data_loader.PRODUCTS[pid] for pid in cfg["product_ids"] if pid in data_loader.PRODUCTS]
        sort = cfg.get("rules", {}).get("sort", "popular")
        limit = cfg.get("rules", {}).get("limit")
        title = cfg.get("title", slug)
    else:
        # Fallback logic for default curations
        if slug == "flash-deals":
            # Show cheapest products, optionally only discounted ones
            products = [p for p in products if getattr(p, "compare_at", p.price + 0.01) > p.price]
            products = sorted(products, key=lambda p: p.price)
            sort = "price_asc"
            limit = 12
            title = "她的秒杀商品"
        elif slug == "weekly-picks":
            # Show popular products based on reviews/rating
            products = sorted(products, key=lambda p: (getattr(p, "rating", 0), getattr(p, "reviews", 0)), reverse=True)
            sort = "popular"
            limit = 12
            title = "她的本周推荐"
        else:
            raise_error_response("not_found", "Unknown curation", status_code=404)
    
    products = apply_sort(products, sort)
    if limit:
        products = products[:limit]
    products_slice, meta = paginate(products, page, page_size)
    return {
        "curation": {
            "slug": slug,
            "title": title,
            "products": [serialize_product(p) for p in products_slice],
        },
        "meta": meta,
    }
