"""Routers exposing curated product lists."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .. import data_loader
from ..repositories import serialize_product, paginate, apply_sort

router = APIRouter(prefix="/curations", tags=["curations"])


@router.get("")
async def list_curations() -> dict:
    cfg = data_loader.CURATIONS_CONFIG or {}
    curations = [
        {"slug": slug, "title": val.get("title", slug)}
        for slug, val in cfg.items()
    ]
    return {"curations": curations}


@router.get("/{slug}")
async def get_curation(slug: str, page: int = 1, page_size: int = 20) -> dict:
    cfg = (data_loader.CURATIONS_CONFIG or {}).get(slug)
    if not cfg:
        raise HTTPException(status_code=404, detail="not found")
    products = list(data_loader.PRODUCTS.values())
    if cfg.get("product_ids"):
        products = [data_loader.PRODUCTS[pid] for pid in cfg["product_ids"] if pid in data_loader.PRODUCTS]
    sort = cfg.get("rules", {}).get("sort", "popular")
    limit = cfg.get("rules", {}).get("limit")
    products = apply_sort(products, sort)
    if limit:
        products = products[:limit]
    products_slice, meta = paginate(products, page, page_size)
    return {
        "curation": {
            "slug": slug,
            "title": cfg.get("title", slug),
            "products": [serialize_product(p) for p in products_slice],
        },
        "meta": meta,
    }
