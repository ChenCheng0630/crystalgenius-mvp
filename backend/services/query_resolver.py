"""Query resolver interface.

The resolver translates a free-form natural language query into a
structured filter object that the product repository understands.

This module provides two resolvers:
- ``HeuristicQueryResolver``: local parsing only (no network calls)
- ``LLMQueryResolver``: optional OpenAI-backed parsing gated by env

If OpenAI is unavailable or an error occurs, the LLM resolver gracefully
falls back to the heuristic implementation.
"""

from __future__ import annotations

from typing import Dict, Any
import json
import os

import data_loader

from services.search import parse_query


class HeuristicQueryResolver:
    """Resolve queries using local heuristics."""

    def resolve(self, q: str) -> Dict[str, Any]:
        return parse_query(q)


class LLMQueryResolver(HeuristicQueryResolver):
    """OpenAI-backed resolver using the Responses API.

    This implementation asks the model to return a strict JSON object with
    keys: ``colors``, ``materials``, ``category_names``, ``price_range``.
    Returned values are intersected with the allowed sets derived from
    in-memory data to ensure safety and consistency.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        # Defer import so the module can be imported without the dependency
        try:  # pragma: no cover - import side-effect
            from openai import OpenAI  # type: ignore
        except Exception:  # pragma: no cover - no openai installed
            self._client_cls = None
        else:
            self._client_cls = OpenAI

    def resolve(self, q: str) -> Dict[str, Any]:  # pragma: no cover
        # If not properly configured, fallback to heuristic
        if not self.api_key or not self._client_cls:
            return super().resolve(q)

        allowed_colors = sorted([c for c in data_loader.COLOR_VALUES if c])
        allowed_materials = sorted([m for m in data_loader.MATERIAL_VALUES if m])
        allowed_cat_names = sorted(
            list({n for s in data_loader.CATEGORY_NAME_VALUES_BY_PARENT.values() for n in s if n})
        )

        system = (
            "You extract crystal shopping filters from a Chinese user query. "
            "Respond ONLY with a JSON object with keys: colors (array), materials (array), "
            "category_names (array), price_range (object with optional min/max numbers). "
            "Use only allowed values; never invent new labels."
        )

        # Ask for JSON output explicitly; we will validate and intersect.
        prompt_allowed = {
            "colors": allowed_colors,
            "materials": allowed_materials,
            "category_names": allowed_cat_names,
        }

        client = self._client_cls(api_key=self.api_key)

        try:
            resp = client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": q},
                    {
                        "role": "assistant",
                        "content": "Allowed values: "
                        + json.dumps(prompt_allowed, ensure_ascii=False),
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )

            # The SDK exposes output text convenience; fall back to raw contents if needed
            text = getattr(resp, "output_text", None)
            if not text:
                # Best-effort extraction if SDK shape differs
                try:
                    # responses API typically has .output with content items
                    parts = []
                    for item in getattr(resp, "output", []) or []:
                        if getattr(item, "type", None) == "message":
                            for c in getattr(item, "content", []) or []:
                                if getattr(c, "type", None) == "output_text":
                                    parts.append(getattr(c, "text", ""))
                    text = "\n".join(p for p in parts if p)
                except Exception:
                    text = None

            data: Dict[str, Any] = {}
            if text:
                try:
                    data = json.loads(text)
                except Exception:
                    data = {}

            # Build result; always intersect with allowed sets
            colors = [v for v in (data.get("colors") or []) if v in allowed_colors]
            materials = [v for v in (data.get("materials") or []) if v in allowed_materials]
            category_names = [v for v in (data.get("category_names") or []) if v in allowed_cat_names]
            price_range = data.get("price_range") or {}
            pr = {
                k: float(price_range[k])
                for k in ("min", "max")
                if k in price_range and isinstance(price_range[k], (int, float))
            }

            result: Dict[str, Any] = {"summary": q}
            if colors:
                result["colors"] = colors
            if materials:
                result["materials"] = materials
            if category_names:
                result["category_names"] = category_names
            if pr:
                result["price_range"] = pr
            # If model returned nothing useful, fallback to heuristic
            if not (colors or materials or category_names or pr):
                return super().resolve(q)
            return result

        except Exception:
            # Any failure → heuristic fallback
            return super().resolve(q)
