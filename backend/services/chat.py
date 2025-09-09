"""Chat service with optional OpenAI-backed replies.

Falls back to a scripted reply when LLM is disabled or unavailable.
"""

from __future__ import annotations

import uuid
from typing import List, Dict, Any, Optional, Tuple
import os
import json

from models import ChatMessage
import data_loader
from repositories import apply_filters, apply_sort, serialize_product
from services.query_resolver import HeuristicQueryResolver, LLMQueryResolver


CHATS: Dict[str, List[ChatMessage]] = {}


SCRIPTED_REPLY = "你好，我是小晶，有关水晶的问题都可以问我～"

CHAT_SYSTEM_PROMPT = (
    "你是一个水晶购物助理。用自然、真诚的方式交流。"
    "当用户提出具体偏好（如颜色、材质、风格、价格）或需要推荐时，再调用 filter_products 工具展示卡片。"
    "选择一个合适的父分类：831(按颜色材质) / 832(按款式风格) / 834(按手串类型)。"
    "831 时，优先 color/material 作为二级筛选；832/834 时，用 category_name。"
    "回复文字里不要硬编码商品信息，商品卡片由工具返回。"
)

_OPENAI_CLIENT_CLS = None
try:  # pragma: no cover - optional dependency
    from openai import OpenAI as _OpenAI

    _OPENAI_CLIENT_CLS = _OpenAI
except Exception:  # pragma: no cover - no SDK installed
    _OPENAI_CLIENT_CLS = None


def get_history(session_id: str) -> List[ChatMessage]:
    return CHATS.setdefault(session_id, [])


def ensure_session(session_id: str) -> None:
    """Ensure a chat session exists for the given session_id."""
    CHATS.setdefault(session_id, [])


def add_message(session_id: str, role: str, content: str) -> ChatMessage:
    msg = ChatMessage(id=str(uuid.uuid4()), role=role, content=content)
    get_history(session_id).append(msg)
    return msg


def handle_user_message(session_id: str, content: str) -> List[ChatMessage]:
    messages = get_history(session_id)
    add_message(session_id, "user", content)

    # Use LLM if enabled and available
    if _should_use_llm():
        reply = _llm_reply_with_tools(history=messages, user_text=content)
        add_message(session_id, "assistant", reply)
        return messages

    # Fallback scripted behaviour
    reply_content = SCRIPTED_REPLY if len(messages) == 1 else f"你说的是：{content}"
    add_message(session_id, "assistant", reply_content)
    return messages


def _should_use_llm() -> bool:
    if os.getenv("ENABLE_LLM_CHAT", "false").lower() != "true":
        return False
    if not os.getenv("OPENAI_API_KEY"):
        return False
    if _OPENAI_CLIENT_CLS is None:
        return False
    return True


def _llm_reply_with_tools(history: List[ChatMessage], user_text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Generate LLM reply with tool calling support."""
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = _OPENAI_CLIENT_CLS(api_key=api_key)

    # Build conversation with system prompt
    convo = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}] + [
        {"role": m.role, "content": m.content} for m in history
    ] + [{"role": "user", "content": user_text}]

    # Prepare tools
    tools = [filter_products_tool_schema(_allowed_values())]

    try:
        # First call with tools
        resp = client.responses.create(
            model=model,
            input=convo,
            tools=tools,
            temperature=0.6,
        )

        # Extract tool calls and text
        tool_calls = _extract_tool_calls(resp)
        text = _extract_text(resp)

        suggestions = None
        if tool_calls:
            # Execute tool calls
            for call in tool_calls:
                if call.get("name") == "filter_products":
                    result = execute_filter_products(call.get("arguments", {}))
                    suggestions = {
                        "products": [serialize_product(p) for p in result["products"]],
                        "reason": result.get("reason") or call.get("arguments", {}).get("reason")
                    }
                    
                    # Send tool result back to model for refined response
                    tool_result_msg = {
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "content": json.dumps(result, ensure_ascii=False)
                    }
                    convo.append(tool_result_msg)
                    
                    # Get refined response
                    refined_resp = client.responses.create(
                        model=model,
                        input=convo,
                        temperature=0.6,
                    )
                    text = _extract_text(refined_resp)

        return text or "我已经收到你的需求，可以再具体一点吗？", suggestions

    except Exception:
        return "抱歉，我这边暂时没连上智能助手，但我仍然可以帮你看看基础筛选。", None


def _extract_tool_calls(resp) -> List[Dict[str, Any]]:
    """Extract tool calls from OpenAI response."""
    tool_calls = []
    try:
        # Try to extract from response structure
        for item in getattr(resp, "output", []) or []:
            if getattr(item, "type", None) == "message":
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", None) == "tool_call":
                        tool_calls.append({
                            "id": getattr(c, "id", ""),
                            "name": getattr(c, "name", ""),
                            "arguments": json.loads(getattr(c, "arguments", "{}"))
                        })
    except Exception:
        pass
    return tool_calls


def _extract_text(resp) -> str:
    """Extract text content from OpenAI response."""
    try:
        text = getattr(resp, "output_text", None)
        if not text:
            # Best-effort extraction if SDK shape differs
            parts = []
            for item in getattr(resp, "output", []) or []:
                if getattr(item, "type", None) == "message":
                    for c in getattr(item, "content", []) or []:
                        if getattr(c, "type", None) == "output_text":
                            parts.append(getattr(c, "text", ""))
            text = "\n".join(p for p in parts if p)
        return text
    except Exception:
        return None


def _get_query_resolver():
    """Pick LLM-backed resolver for filter extraction when enabled."""
    if os.getenv("ENABLE_LLM_FILTERS", "false").lower() == "true" and os.getenv("OPENAI_API_KEY"):
        return LLMQueryResolver()
    return HeuristicQueryResolver()


def _analysis_reason(analysis: Dict[str, Any]) -> str:
    parts: List[str] = []
    if analysis.get("colors"):
        parts.append(f"颜色: {'/'.join(analysis['colors'])}")
    if analysis.get("materials"):
        parts.append(f"材质: {'/'.join(analysis['materials'])}")
    if analysis.get("category_names"):
        parts.append(f"分类: {'/'.join(analysis['category_names'])}")
    pr = analysis.get("price_range") or {}
    if pr.get("min") is not None or pr.get("max") is not None:
        rng = []
        if pr.get("min") is not None:
            rng.append(f"≥{pr['min']}")
        if pr.get("max") is not None:
            rng.append(f"≤{pr['max']}")
        parts.append("价格 " + "-".join(rng))
    return "；".join(parts)


def _parent_for_analysis(analysis: Dict[str, Any]) -> int:
    cat_names = set(analysis.get("category_names") or [])
    if not cat_names:
        return 831
    names_832 = data_loader.CATEGORY_NAME_VALUES_BY_PARENT.get(832, set())
    names_834 = data_loader.CATEGORY_NAME_VALUES_BY_PARENT.get(834, set())
    if cat_names.intersection(names_832) and not cat_names.intersection(names_834):
        return 832
    if cat_names.intersection(names_834) and not cat_names.intersection(names_832):
        return 834
    # Mixed or unknown → default to 832 (style) for better UX
    return 832


def generate_message_with_suggestions(session_id: str, user_text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Generate an assistant reply and optional product suggestions.

    - Uses LLM with tool calling when enabled; otherwise scripted.
    - Tool calling allows the model to decide when to show products.
    """

    if _should_use_llm():
        history = get_history(session_id)
        reply, suggestions = _llm_reply_with_tools(history, user_text)
        return reply, suggestions
    else:
        # Fallback scripted behavior
        history = get_history(session_id)
        reply = SCRIPTED_REPLY if len(history) <= 1 else f"你说的是：{user_text}"
        
        # Build suggestions using heuristic resolver as fallback
        resolver = _get_query_resolver()
        analysis = resolver.resolve(user_text)
        has_filters = any(
            analysis.get(k) for k in ("colors", "materials", "category_names")
        ) or bool((analysis.get("price_range") or {}))
        suggestions: Optional[Dict[str, Any]] = None
        if has_filters:
            payload = {
                "parent_category_id": _parent_for_analysis(analysis),
                "filters": {
                    "color": analysis.get("colors", []),
                    "material": analysis.get("materials", []),
                    "category_name": analysis.get("category_names", []),
                    "price_range": analysis.get("price_range", {}),
                    "sort": "popular",
                    "limit": 6,
                },
                "reason": _analysis_reason(analysis) or "为你挑选的人气款",
            }
            result = execute_filter_products(payload)
            suggestions = {
                "products": [serialize_product(p) for p in result["products"]],
                "reason": result.get("reason"),
            }
        return reply, suggestions


# Convenience used by router
def build_chat_history_messages(session_id: str) -> List[Dict[str, str]]:
    return [{"role": m.role, "content": m.content} for m in get_history(session_id)]


def filter_products_tool_schema(allowed: Dict[str, List[str]]) -> Dict[str, Any]:
    return {
        "name": "filter_products",
        "description": "Select parent category and filters, then fetch matching crystal products.",
        "parameters": {
            "type": "object",
            "properties": {
                "parent_category_id": {"type": "integer", "enum": [831, 832, 834]},
                "filters": {
                    "type": "object",
                    "properties": {
                        "color": {
                            "type": "array",
                            "items": {"type": "string", "enum": allowed.get("colors", [])},
                        },
                        "material": {
                            "type": "array",
                            "items": {"type": "string", "enum": allowed.get("materials", [])},
                        },
                        "category_name": {
                            "type": "array",
                            "items": {"type": "string", "enum": allowed.get("category_names", [])},
                        },
                        "category_id": {"type": "array", "items": {"type": "integer"}},
                        "price_range": {
                            "type": "object",
                            "properties": {"min": {"type": "number"}, "max": {"type": "number"}},
                        },
                        "sort": {
                            "type": "string",
                            "enum": ["popular", "price_asc", "price_desc", "newest", "relevance"],
                        },
                        "limit": {"type": "integer"},
                    },
                },
                "reason": {"type": "string"},
            },
            "required": ["parent_category_id"],
        },
    }


# ---------------------------------------------------------------------------
# Optional product suggestion helpers (not yet wired to tool-calling)

def _allowed_values() -> Dict[str, List[str]]:
    return {
        "colors": sorted([c for c in data_loader.COLOR_VALUES if c]),
        "materials": sorted([m for m in data_loader.MATERIAL_VALUES if m]),
        "category_names": sorted(
            list({n for s in data_loader.CATEGORY_NAME_VALUES_BY_PARENT.values() for n in s if n})
        ),
    }


def _llm_stream_with_tools(history: List[ChatMessage], user_text: str):
    """Generate streaming LLM response with tool calling support."""
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = _OPENAI_CLIENT_CLS(api_key=api_key)

    # Build conversation with system prompt
    convo = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}] + [
        {"role": m.role, "content": m.content} for m in history
    ] + [{"role": "user", "content": user_text}]

    # Prepare tools
    tools = [filter_products_tool_schema(_allowed_values())]

    try:
        # Start streaming with tools
        stream = client.responses.stream(
            model=model,
            input=convo,
            tools=tools,
            temperature=0.6,
        )

        product_payload = None
        full_text = ""

        for event in stream.events():
            if hasattr(event, 'type'):
                if event.type == "tool_call" and hasattr(event, 'name') and event.name == "filter_products":
                    # Execute tool call immediately
                    result = execute_filter_products(getattr(event, 'arguments', {}))
                    product_payload = {
                        "products": [serialize_product(p) for p in result["products"]],
                        "reason": result.get("reason") or getattr(event, 'arguments', {}).get("reason")
                    }
                    # Send tool result back to model
                    tool_result_msg = {
                        "role": "tool",
                        "tool_call_id": getattr(event, 'id', ''),
                        "content": json.dumps(result, ensure_ascii=False)
                    }
                    convo.append(tool_result_msg)
                    
                elif event.type == "content" and hasattr(event, 'delta'):
                    # Stream content
                    delta = event.delta
                    full_text += delta
                    yield {
                        "type": "assistant_message",
                        "data": {"id": str(uuid.uuid4()), "role": "assistant", "content": delta}
                    }

        # Emit product suggestions if tool was used
        if product_payload:
            yield {
                "type": "product_suggestions", 
                "data": product_payload
            }

        # End stream
        yield {"type": "done", "data": {}}

        return full_text

    except Exception:
        # Fallback to non-streaming
        reply, suggestions = _llm_reply_with_tools(history, user_text)
        yield {
            "type": "assistant_message",
            "data": {"id": str(uuid.uuid4()), "role": "assistant", "content": reply}
        }
        if suggestions:
            yield {
                "type": "product_suggestions",
                "data": suggestions
            }
        yield {"type": "done", "data": {}}
        return reply


def execute_filter_products(payload: Dict[str, Any]) -> Dict[str, Any]:
    f = payload.get("filters", {}) if isinstance(payload, dict) else {}
    pr = f.get("price_range", {}) if isinstance(f, dict) else {}
    filters = {
        "color": f.get("color", []) or [],
        "material": f.get("material", []) or [],
        "category_name": f.get("category_name", []) or [],
        "category_id": f.get("category_id", []) or [],
        "min_price": pr.get("min"),
        "max_price": pr.get("max"),
    }
    items = list(data_loader.PRODUCTS.values())
    items = apply_filters(items, filters)
    items = apply_sort(items, f.get("sort", "popular"))
    limit = int(f.get("limit", 6)) if isinstance(f.get("limit", 6), (int, float)) else 6
    items = items[:limit]
    return {
        "products": items,
        "reason": payload.get("reason") if isinstance(payload, dict) else None,
    }
