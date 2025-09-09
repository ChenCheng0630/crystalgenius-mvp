"""Query resolver interface.

The resolver translates a free-form natural language query into a
structured filter object that the product repository understands.
The MVP includes a simple heuristic resolver; a future
`LLMQueryResolver` could use the OpenAI Responses API.
"""

from __future__ import annotations

from typing import Dict, Any

from .search import parse_query


class HeuristicQueryResolver:
    """Resolve queries using local heuristics."""

    def resolve(self, q: str) -> Dict[str, Any]:
        return parse_query(q)


class LLMQueryResolver(HeuristicQueryResolver):
    """Placeholder for a model-backed resolver."""

    def __init__(self, *_, **__):  # pragma: no cover - not used in MVP
        pass

    def resolve(self, q: str) -> Dict[str, Any]:  # pragma: no cover
        # In a real implementation this would call OpenAI and validate the
        # response.  We fallback to heuristic parsing for now.
        return super().resolve(q)
