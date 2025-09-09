"""Utilities for loading CSV data into in-memory structures.

The application keeps all data in memory.  This module provides helper
functions to load the CSV files at start-up and to enrich product data
with deterministic randomised attributes required by the mobile UI.
"""

from __future__ import annotations

import csv
import os
import random
from pathlib import Path
from typing import Dict, List

from models import Product, Category, ParentCategory

# Public containers populated at start-up.  The names mirror those used in
# ``docs/backend-api-pseudo-code.md``.
PRODUCTS: Dict[int, Product] = {}
CATEGORIES: Dict[int, Category] = {}
PARENT_CATEGORIES: Dict[int, ParentCategory] = {}
PRODUCT_TO_CATEGORIES: Dict[int, List[Category]] = {}
CATEGORIES_BY_PARENT: Dict[int, List[Category]] = {}
COLOR_VALUES: set[str] = set()
MATERIAL_VALUES: set[str] = set()
CATEGORY_NAME_VALUES_BY_PARENT: Dict[int, set[str]] = {}
CURATIONS_CONFIG: dict | None = None

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def enrich_product(p: Product) -> None:
    """Populate pseudo fields for display purposes.

    The enrichment is deterministic by seeding ``random`` with the product
    ID, ensuring that the generated values remain stable across reloads.
    """

    rng = random.Random(p.id)
    markup = rng.uniform(0.05, 0.25)
    p.compare_at = round(p.price * (1 + markup), 2)
    if p.compare_at <= p.price:
        p.compare_at = round(p.price * 1.1, 2)
    p.rating = round(min(5.0, max(3.9, rng.gauss(4.6, 0.25))), 1)
    p.reviews = int(rng.triangular(10, 600, 180))
    sold_raw = int(rng.triangular(50, 3500, 500))
    p.sold = f"{sold_raw}+"


def load_products() -> Dict[int, Product]:
    path = DATA_DIR / "products_full.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            product = Product(
                id=int(row["id"]),
                reference_id=row["reference_id"],
                name=row["name"],
                price=float(row["price"]),
                image=row["image"],
                extra_images=[img for img in row["extra_images"].split("|") if img],
                description=row.get("description", ""),
                category_id=[int(cid) for cid in row["category_id"].split("|") if cid],
            )
            enrich_product(product)
            PRODUCTS[product.id] = product
    return PRODUCTS


def load_categories() -> Dict[int, Category]:
    path = DATA_DIR / "category.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            c = Category(
                id=int(row["id"]),
                reference_id=int(row["reference_id"]),
                color=row.get("color") or None,
                material=row.get("material") or None,
                category_name=row.get("category_name") or None,
                parent_id=int(row["parent_id"]),
                image=row.get("image") or None,
            )
            CATEGORIES[c.id] = c
            CATEGORIES_BY_PARENT.setdefault(c.parent_id, []).append(c)
            PRODUCT_TO_CATEGORIES.setdefault(c.id, [])  # placeholder
            if c.parent_id == 831:
                if c.color:
                    COLOR_VALUES.add(c.color)
                if c.material:
                    MATERIAL_VALUES.add(c.material)
            else:
                CATEGORY_NAME_VALUES_BY_PARENT.setdefault(c.parent_id, set()).add(
                    c.category_name or ""
                )
    return CATEGORIES


def load_parent_categories() -> Dict[int, ParentCategory]:
    path = DATA_DIR / "parent_category.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pc = ParentCategory(
                id=int(row["id"]),
                reference_id=int(row["reference_id"]),
                name=row["name"],
                image=row.get("image") or None,
            )
            PARENT_CATEGORIES[pc.id] = pc
    return PARENT_CATEGORIES


def load_curations_config() -> dict | None:
    """Load optional product curation configuration from YAML."""

    try:
        import yaml  # type: ignore
    except Exception:
        return None

    path = os.getenv("CURATIONS_CONFIG", str(Path("config/curations.yaml")))
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data
    except FileNotFoundError:
        return None


def build_relationships() -> None:
    """Create the ``PRODUCT_TO_CATEGORIES`` mapping after all data is loaded."""

    for p in PRODUCTS.values():
        cats = [CATEGORIES[cid] for cid in p.category_id if cid in CATEGORIES]
        PRODUCT_TO_CATEGORIES[p.id] = cats


def load_all() -> None:
    """Load every CSV file and construct helper mappings."""

    load_products()
    load_categories()
    load_parent_categories()
    build_relationships()
    global CURATIONS_CONFIG
    CURATIONS_CONFIG = load_curations_config()
