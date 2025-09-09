"""Search utilities and query parsing."""

from __future__ import annotations

import re
from typing import Dict, Any

from .. import data_loader
from ..repositories import tokenize


PRICE_PATTERN = re.compile(r"(\d+)(?:元)?(以内|以下|以下|以内|以上)?")


def parse_query(q: str) -> Dict[str, Any]:
    """Very small heuristic query parser.

    Extracts colours, materials, category names and a price range from the
    free-form query ``q``.
    """

    tokens = tokenize(q)
    colors = [t for t in tokens if t in data_loader.COLOR_VALUES]
    materials = [t for t in tokens if t in data_loader.MATERIAL_VALUES]
    all_cat_names = set().union(*data_loader.CATEGORY_NAME_VALUES_BY_PARENT.values())
    cat_names = [t for t in tokens if t in all_cat_names]

    price_min = price_max = None
    for tok in tokens:
        m = PRICE_PATTERN.fullmatch(tok)
        if not m:
            continue
        value = float(m.group(1))
        suffix = m.group(2)
        if suffix in ("以内", "以下"):
            price_max = value
        elif suffix == "以上":
            price_min = value

    result: Dict[str, Any] = {"summary": q}
    if colors:
        result["colors"] = colors
    if materials:
        result["materials"] = materials
    if cat_names:
        result["category_names"] = cat_names
    if price_min is not None or price_max is not None:
        result["price_range"] = {"min": price_min, "max": price_max}
    return result
