"""Product listing and detail routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
import os

import data_loader
from utils import raise_error_response
from repositories import (
    serialize_product,
    paginate,
    apply_filters,
    apply_sort,
    apply_relevance,
)
from services.query_resolver import HeuristicQueryResolver, LLMQueryResolver

router = APIRouter(prefix="/products", tags=["products"])

# Enable OpenAI-backed resolver when flagged and API key present
if os.getenv("ENABLE_LLM_FILTERS", "false").lower() == "true" and os.getenv("OPENAI_API_KEY"):
    resolver = LLMQueryResolver(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
else:
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
        "color": color or [],
        "material": material or [],
        "category_name": category_name or [],
        "category_id": category_id or [],
        "min_price": min_price,
        "max_price": max_price,
    }
    if q:
        parsed = resolver.resolve(q) or {}
        filters["color"].extend(parsed.get("colors", []))
        filters["material"].extend(parsed.get("materials", []))
        filters["category_name"].extend(parsed.get("category_names", []))
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


@router.get("/search")
async def search_products(
    q: str,
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
    """Search products with query analysis."""
    # Parse the query to get analysis
    analysis = resolver.resolve(q)
    
    # Build filters from analysis and explicit parameters
    filters = {
        "color": color or [],
        "material": material or [],
        "category_name": category_name or [],
        "category_id": category_id or [],
        "min_price": min_price,
        "max_price": max_price,
    }
    
    # Apply analysis-derived filters (only if not explicitly provided)
    if analysis.get("colors") and not color:
        filters["color"] = analysis["colors"]
    if analysis.get("materials") and not material:
        filters["material"] = analysis["materials"]
    if analysis.get("category_names") and not category_name:
        filters["category_name"] = analysis["category_names"]
    if analysis.get("price_range"):
        price_range = analysis["price_range"]
        if price_range.get("min") is not None and min_price is None:
            filters["min_price"] = price_range["min"]
        if price_range.get("max") is not None and max_price is None:
            filters["max_price"] = price_range["max"]
    
    products = list(data_loader.PRODUCTS.values())
    products = apply_filters(products, filters)
    
    # Apply relevance scoring if query provided
    if q:
        products = apply_relevance(products, q)
        sort = sort or "relevance"
    elif not sort:
        sort = "popular"
    
    if sort != "relevance":
        products = apply_sort(products, sort)
    
    products_slice, meta = paginate(products, page, page_size)
    
    # Build analysis summary
    analysis_summary = _build_analysis_summary(analysis)
    
    return {
        "analysis": {
            "query": q,
            "summary": analysis_summary,
            "filters": {
                "colors": analysis.get("colors", []),
                "materials": analysis.get("materials", []),
                "category_names": analysis.get("category_names", []),
                "price_range": analysis.get("price_range", {})
            }
        },
        "products": [serialize_product(p) for p in products_slice],
        "meta": meta
    }


@router.get("/{product_id}")
async def get_product(product_id: int) -> dict:
    product = data_loader.PRODUCTS.get(product_id)
    if not product:
        raise_error_response("not_found", "Product not found", status_code=404)
    return serialize_product(product, include_detail=True)


def _build_analysis_summary(analysis: dict) -> str:
    """Build a human-readable summary of the query analysis."""
    parts = []
    if analysis.get("colors"):
        parts.append(f"颜色: {'/'.join(analysis['colors'])}")
    if analysis.get("materials"):
        parts.append(f"材质: {'/'.join(analysis['materials'])}")
    if analysis.get("category_names"):
        parts.append(f"分类: {'/'.join(analysis['category_names'])}")
    if analysis.get("price_range"):
        pr = analysis["price_range"]
        price_parts = []
        if pr.get("min") is not None:
            price_parts.append(f"≥{pr['min']}")
        if pr.get("max") is not None:
            price_parts.append(f"≤{pr['max']}")
        if price_parts:
            parts.append("价格 " + "-".join(price_parts))
    
    return " · ".join(parts) if parts else "解析：未识别到特定条件，展示人气单品"
