# CrystalGenius Backend (Python) – Implementation Plan + Pseudocode

Goal: Implement the API defined in `docs/api-spec.md` using Python (FastAPI), backed by CSV data files for products, categories, and parent categories. MVP stores state in memory. Enrich missing display attributes (compare_at, reviews, sold, rating) at load time to support the mobile UI.

## Stack & Structure

- Framework: FastAPI (+ Starlette for SSE), Uvicorn for ASGI
- Data: Load from CSVs at startup
  - `data/products_full.csv` (products)
  - `data/category.csv` (categories)
  - `data/parent_category.csv` (parent groups)
- State: In-memory dicts for chat sessions, carts, checkout sessions, telemetry
- Models: Pydantic-like models for responses (or simple dicts)
- SSE: Server-Sent Events for `GET /chat/stream`
- Curations: Configurable via YAML/env; heuristic fallback if not configured
- AI Query Parsing: Pluggable resolver; default heuristic + optional OpenAI LLM-backed resolver (feature-flagged)

Suggested project layout:

```
backend/
  app.py                # FastAPI app entry
  models.py             # Pydantic models (optional for MVP)
  data_loader.py        # CSV loading + joins
  repositories.py       # Query helpers, filtering + pagination
  services/
    search.py           # parse_query + relevance scoring
    query_resolver.py   # HeuristicQueryResolver and LLMQueryResolver (OpenAI)
    chat.py             # chat state & scripted replies
    cart.py             # cart state & operations
    checkout.py         # mock checkout flow
  routers/
    assistant.py
    curations.py
    products.py
    chat.py
    cart.py
    checkout.py
    meta.py             # categories & parent-categories, telemetry
```

## Data Model (from CSV)

- Product (CSV: products_full.csv)
  - id: int
  - reference_id: str
  - name: str
  - price: float
  - image: str
  - extra_images: str (pipe `|` separated → list[str])
  - description: str
  - category_id: str (pipe `|` separated category IDs → list[int])

- Category (CSV: category.csv)
  - id: int
  - reference_id: int
  - color: str | null
  - material: str | null
  - category_name: str | null
  - parent_id: int (831/832/834)
  - image: str | null

- ParentCategory (CSV: parent_category.csv)
  - id: int
  - reference_id: int
  - name: str (e.g., 按颜色材质 / 按款式风格 / 按手串类型)
  - image: str | null

Derived, in memory at startup:
- `PRODUCTS: dict[int, Product]`
- `CATEGORIES: dict[int, Category]`
- `PARENT_CATEGORIES: dict[int, ParentCategory]`
- `PRODUCT_TO_CATEGORIES: dict[int, list[Category]]`
- `CATEGORIES_BY_PARENT: dict[int, list[Category]]`
- `COLOR_VALUES`: set[str] from categories where parent_id=831
- `MATERIAL_VALUES`: set[str] from categories where parent_id=831
- `CATEGORY_NAME_VALUES_BY_PARENT: dict[int, set[str]]` for 832/834
- `CURATIONS_CONFIG`: optional dict loaded from `config/curations.yaml` or env

### Runtime Data Enrichment (for frontend display)

Enrich each product deterministically using a seeded RNG (stable per product across runs):

```
def enrich_product(p):
    rng = random.Random(p.id)  # stable seed
    # compare_at: 5%–25% above current price, rounded to 1 decimal; ensure > price
    markup = rng.uniform(0.05, 0.25)
    p.compare_at = round(p.price * (1 + markup), 2)
    if p.compare_at <= p.price:
        p.compare_at = round(p.price * 1.1, 2)

    # rating: 3.9–5.0 biased high
    p.rating = round(min(5.0, max(3.9, rng.gauss(4.6, 0.25))), 1)

    # reviews: 10–600
    p.reviews = int(rng.triangular(10, 600, 180))

    # sold: produce a friendly "123+" string
    sold_raw = int(rng.triangular(50, 3500, 500))
    p.sold = f"{sold_raw}+"
```

Attach these fields to the in-memory product dict so all serializers can expose them.

## Cross-Cutting Concerns

- Session handling:
  - Read `session_id` from cookie `session_id` or header `X-Session-Id`.
  - If missing: generate UUID4 and set cookie on response.

- Pagination helper:
  - `paginate(items: list[T], page: int = 1, size: int = 20) -> (list[T], meta)`

- Sorting helper:
  - `apply_sort(items, sort)` where sort in `relevance | price_asc | price_desc | popular | newest`
  - For MVP: `popular` by `sold` if available else by review count or random; `newest` by id desc.

- Error envelope:
  - `error_response(code: str, message: str, details: any = None)` → `{ "error": { code, message, details } }`

- Natural language parsing (crystals):
  - Resolver interface used by `/products` and `/search/products` when `q` provided.
    - `HeuristicQueryResolver`: local parsing (as before)
    - `LLMQueryResolver`: calls OpenAI to extract filters with JSON-structured output
  - Feature flag: `ENABLE_LLM_FILTERS=true|false` (env). If enabled and API key configured, use LLM; else fallback to heuristic.

## Filtering Rules Recap

- Default `parent_category_id=831` (按颜色材质)
- If `parent_category_id=831`: accept `color[]`, `material[]`, `min_price`, `max_price` (+ q/sort/pagination)
- If `parent_category_id=832 or 834`: accept `category_name[]` (or `category_id[]`), `min_price`, `max_price` (+ q/sort/pagination)
- Multi-select semantics: AND across dimensions, OR within a dimension

---

## AI Chat Orchestration & Tool Use

We replace scripted replies with an LLM-driven assistant that can optionally use a tool to fetch product suggestions. The model decides when to show products.

### Tool: filter_products (called by the LLM)

Purpose: Let the assistant choose a parent category and the appropriate secondary filters, then fetch products.

Parameters (JSON Schema):
- `parent_category_id` (enum: 831 | 832 | 834) – choose the primary filter mode.
- `filters` (object):
  - When 831: `color[]`, `material[]` (arrays of strings from allowed values)
  - When 832/834: `category_name[]` (array of strings) or `category_id[]` (array of ints)
  - Optional for any: `price_range` `{ min?: number, max?: number }`, `sort` (`popular|price_asc|price_desc|newest|relevance`), `limit` (default 6)
- `reason` (string): short rationale that can be shown in UI

Tool behavior (server-side):
- Validate `parent_category_id` and normalize `filters` based on the chosen parent.
- Apply filtering rules (see Filtering Rules) against in-memory products.
- Rank by `sort` (default `popular`) and return up to `limit` items.
- Response shape:
  - `{ products: Product[], used: { parent_category_id, filters }, reason?: string }`

### Chat System Prompt (guidance)

- Role: Helpful AI shopping assistant for crystals. Speak naturally and concisely.
- Decide when to display product cards: only when the user asks for recommendations, mentions preferences (color/material/style/price), or it clearly helps move the purchase forward.
- If asking exploratory questions, you may reply without products.
- Use the `filter_products` tool to fetch products. Choose exactly one `parent_category_id` (831: 按颜色材质, 832: 按款式风格, 834: 按手串类型), then provide secondary filters accordingly.
- Prefer multi-select filters when the user mentions multiple preferences.
- Keep reply text separate from cards; do not include product data in the message text.

### Explore Search vs. Chat

- Explore search input: always run a filter using the query (AI or heuristic resolver). Show results and an analysis banner.
- Chat: the assistant decides whether to call `filter_products`. If it does, we also emit a `product_suggestions` payload.

---

## Pseudocode by Endpoint

Notation: Python-like pseudocode. Some library specifics omitted for clarity.

### GET /assistant/profile

```
def get_assistant_profile(request):
    # Could be from config or DB; static for MVP
    profile = {
        "name": "小晶",
        "avatar": "https://example.com/crystal-expert.jpg",
        "intro_short": "专注天然水晶与能量手串，按寓意与体感为你精准配搭。",
        "domains": ["天然水晶手串", "寓意/能量配对"],
        "styles": ["温柔疗愈", "专业配搭", "寓意解读"],
        "stats": {"monthly_sales": "2.8K+ 单", "gmv": "￥1.9M/月", "positive_rate": "99% 好评"},
        "ctas": [{"label": "点击对话", "action": "chat"}]
    }
    return profile
```

### GET /curations

```
def list_curations():
    return {"curations": [
        {"slug": "flash-deals", "title": "她的秒杀商品"},
        {"slug": "weekly-picks", "title": "她的本周推荐"},
    ]}
```

### GET /curations/:slug

```
def get_curation(slug: str, page: int = 1, page_size: int = 20):
    # 1) Configurable picks
    cfg = CURATIONS_CONFIG.get(slug) if CURATIONS_CONFIG else None
    if cfg and cfg.get("product_ids"):
        items = [PRODUCTS[pid] for pid in cfg["product_ids"] if pid in PRODUCTS]
    else:
        # 2) Rule-based fallback
        items = list(PRODUCTS.values())
        if slug == "flash-deals":
            # cheapest first; optionally only discounted (price < compare_at)
            items = [p for p in items if p.price < getattr(p, "compare_at", p.price + 0.01)]
            items = sorted(items, key=lambda p: p.price)
        elif slug == "weekly-picks":
            # popular (reviews/sold/rating)
            items = sorted(items, key=lambda p: (getattr(p, "rating", 0), getattr(p, "reviews", 0)), reverse=True)
        else:
            return error_response("not_found", "Unknown curation")

    page_items, meta = paginate(items, page, page_size)
    return {"curation": {"slug": slug, "title": map_slug_to_title(slug), "products": page_items}, "meta": meta}
```

### GET /products

```
def list_products(request):
    q = request.query.get("q")
    parent = int(request.query.get("parent_category_id", 831))
    colors = request.query.getlist("color[]")  # repeatable
    materials = request.query.getlist("material[]")
    cat_names = request.query.getlist("category_name[]")
    cat_ids = [int(x) for x in request.query.getlist("category_id[]")]
    min_price = float_or_none(request.query.get("min_price"))
    max_price = float_or_none(request.query.get("max_price"))
    sort = request.query.get("sort", default_sort_for(q))
    page = int(request.query.get("page", 1))
    page_size = int(request.query.get("page_size", 20))

    items = list(PRODUCTS.values())

    # Pre-index: product -> categories
    def match_product(p):
        cats = PRODUCT_TO_CATEGORIES.get(p.id, [])

        # Price filter
        if min_price is not None and p.price < min_price:
            return False
        if max_price is not None and p.price > max_price:
            return False

        if parent == 831:
            # Color dimension (OR)
            if colors:
                prod_colors = {c.color for c in cats if c.parent_id == 831 and c.color}
                if not prod_colors.intersection(set(colors)):
                    return False
            # Material dimension (OR)
            if materials:
                prod_mats = {c.material for c in cats if c.parent_id == 831 and c.material}
                if not prod_mats.intersection(set(materials)):
                    return False

        elif parent in (832, 834):
            # Category name dimension (OR)
            if cat_names:
                prod_names = {c.category_name for c in cats if c.parent_id in (832, 834) and c.category_name}
                if not prod_names.intersection(set(cat_names)):
                    return False
            # Or category ids
            if cat_ids:
                prod_cat_ids = {c.id for c in cats}
                if not prod_cat_ids.intersection(set(cat_ids)):
                    return False
        # If neither colors/materials nor cat_names/cat_ids provided, product passes (only price/q apply)
        return True

    items = [p for p in items if match_product(p)]

    # q-based filtering / scoring via resolver
    if q:
        analysis = QUERY_RESOLVER.resolve(q, options={
            "color_values": COLOR_VALUES,
            "material_values": MATERIAL_VALUES,
            "category_values": CATEGORY_NAME_VALUES_BY_PARENT,
        })
        items = apply_analysis_filters(items, analysis, parent, explicit={
            "colors": bool(colors), "materials": bool(materials), "cat_names": bool(cat_names), "cat_ids": bool(cat_ids)
        })
        items = apply_relevance(items, q) if sort == "relevance" else items

    items = apply_sort(items, sort)
    page_items, meta = paginate(items, page, page_size)
    return {"products": [serialize_product(p) for p in page_items], "meta": meta}
```

### GET /products/:id

```
def get_product_detail(id: int):
    p = PRODUCTS.get(id)
    if not p:
        return error_response("not_found", "Product not found")
    prod = serialize_product(p, include_detail=True)
    return prod
```

### GET /search/products

```
def search_products(request):
    q = request.query.get("q", "")
    parent = int(request.query.get("parent_category_id", 831))
    # Accept explicit filters (same as /products)
    colors = request.query.getlist("color[]")
    materials = request.query.getlist("material[]")
    cat_names = request.query.getlist("category_name[]")
    cat_ids = [int(x) for x in request.query.getlist("category_id[]")]
    min_price = float_or_none(request.query.get("min_price"))
    max_price = float_or_none(request.query.get("max_price"))
    sort = request.query.get("sort", default_sort_for(q))
    page = int(request.query.get("page", 1))
    page_size = int(request.query.get("page_size", 20))

    analysis = QUERY_RESOLVER.resolve(q, options={
        "color_values": COLOR_VALUES,
        "material_values": MATERIAL_VALUES,
        "category_values": CATEGORY_NAME_VALUES_BY_PARENT,
    })
    items = list(PRODUCTS.values())

    # Apply analysis-derived filters, overridden by explicit params when provided
    items = apply_analysis_filters(items, analysis, parent, explicit={
        "colors": bool(colors), "materials": bool(materials), "cat_names": bool(cat_names), "cat_ids": bool(cat_ids)
    })

    # Then apply explicit filters (same logic as /products)
    items = apply_explicit_filters(items, parent, colors, materials, cat_names, cat_ids, min_price, max_price)

    items = apply_relevance(items, q) if sort == "relevance" else apply_sort(items, sort)
    page_items, meta = paginate(items, page, page_size)

    return {
        "analysis": serialize_analysis(analysis),
        "products": [serialize_product(p) for p in page_items],
        "meta": meta
    }
```

### GET /parent-categories

```
def list_parent_categories():
    return {"parent_categories": [serialize_parent(pc) for pc in PARENT_CATEGORIES.values()]}
```

### GET /categories

```
def list_categories(parent_id: int | None = None):
    cats = list(CATEGORIES.values())
    if parent_id is not None:
        cats = [c for c in cats if c.parent_id == parent_id]
    return {"categories": [serialize_category(c) for c in cats]}
```

### POST /chat/sessions

```
CHAT_SESSIONS = {}  # session_id -> { messages: [ChatMessage], created_at }

def create_chat_session(request):
    session_id = get_or_create_session_id(request)
    if session_id not in CHAT_SESSIONS:
        CHAT_SESSIONS[session_id] = {"messages": [], "created_at": now_iso()}
    return {"session_id": session_id}  # also set cookie if new
```

### POST /chat/messages (LLM-driven with optional tool use)

```
def post_chat_message(request):
    session_id = get_or_create_session_id(request)
    body = request.json()
    user_text = body.get("message", "").strip()
    context = body.get("context", {})
    if not user_text:
        return error_response("validation_error", "message is required")

    # Persist user message
    append_message(session_id, role="user", content=user_text)

    # Prepare LLM call with tool(s)
    tools = [filter_products_tool_schema(allowed_values())]
    messages = build_chat_history(session_id) + [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    # Non-streaming Responses API with tool-calling
    llm_resp = openai.responses.create(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        input=messages,
        tools=tools,
        temperature=0.6,
    )

    tool_calls = extract_tool_calls(llm_resp)
    suggestions = None
    if tool_calls:
        for call in tool_calls:
            if call.name == "filter_products":
                payload = call.arguments  # { parent_category_id, filters, reason? }
                result = execute_filter_products(payload)
                suggestions = {"products": [serialize_product(p) for p in result.products],
                               "reason": result.reason or payload.get("reason")}
                # Optionally send tool result back to the model for a refined final message
                llm_resp = openai.responses.create(
                    model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
                    input=messages + [tool_result_msg(call.id, result)],
                    temperature=0.6,
                )

    reply_text = extract_text(llm_resp)

    # Persist assistant message
    append_message(session_id, role="assistant", content=reply_text)

    resp = {"messages": [
        {"id": gen_id(), "role": "user", "content": user_text},
        {"id": gen_id(), "role": "assistant", "content": reply_text}
    ]}
    if suggestions:
        resp["suggestions"] = suggestions
    return resp
```

### GET /chat/stream (SSE; LLM streaming + optional tool use)

```
def stream_chat(request):
    session_id = get_or_create_session_id(request)
    user_text = request.query.get("message", "").strip()
    if not user_text:
        return error_response("validation_error", "message is required")

    # Persist user message
    append_message(session_id, role="user", content=user_text)

    def event_stream():
        tools = [filter_products_tool_schema(allowed_values())]
        messages = build_chat_history(session_id) + [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]

        # Start streaming from LLM (pseudo streaming API)
        stream = openai.responses.stream(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            input=messages,
            tools=tools,
            temperature=0.6,
        )

        product_payload = None

        for ev in stream.events():
            if ev.type == "tool_call" and ev.name == "filter_products":
                # Execute immediately and send back to model
                result = execute_filter_products(ev.arguments)
                product_payload = {"products": [serialize_product(p) for p in result.products],
                                   "reason": result.reason or ev.arguments.get("reason")}
                stream.input(tool_result_msg(ev.id, result))
            elif ev.type == "content" and ev.delta:
                yield sse_event("assistant_message", {"id": gen_id(), "role": "assistant", "content": ev.delta})

        # Emit suggestions if tool was used
        if product_payload:
            yield sse_event("product_suggestions", product_payload)

        # End
        yield sse_event("done", {})

        # Persist full assistant text (assembled from deltas)
        final_text = stream.full_text()
        append_message(session_id, role="assistant", content=final_text)

    return sse_response(event_stream())
```

### Supporting pieces for chat

```
def allowed_values():
    return {
        "colors": sorted(list(COLOR_VALUES)),
        "materials": sorted(list(MATERIAL_VALUES)),
        "category_names_832": sorted(list(CATEGORY_NAME_VALUES_BY_PARENT.get(832, []))),
        "category_names_834": sorted(list(CATEGORY_NAME_VALUES_BY_PARENT.get(834, []))),
    }

def filter_products_tool_schema(allowed):
    # Build JSON schema using allowed values to constrain model outputs
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
                        "color": {"type": "array", "items": {"type": "string", "enum": allowed["colors"]}},
                        "material": {"type": "array", "items": {"type": "string", "enum": allowed["materials"]}},
                        "category_name": {"type": "array", "items": {"type": "string", "enum": list(set(allowed["category_names_832"]) | set(allowed["category_names_834"]))}},
                        "category_id": {"type": "array", "items": {"type": "integer"}},
                        "price_range": {"type": "object", "properties": {"min": {"type": "number"}, "max": {"type": "number"}}},
                        "sort": {"type": "string", "enum": ["popular", "price_asc", "price_desc", "newest", "relevance"]},
                        "limit": {"type": "integer"}
                    }
                },
                "reason": {"type": "string"}
            },
            "required": ["parent_category_id"]
        }
    }

def execute_filter_products(payload):
    parent = int(payload["parent_category_id"]) if payload.get("parent_category_id") else 831
    f = payload.get("filters", {})
    colors = f.get("color", []) if parent == 831 else []
    materials = f.get("material", []) if parent == 831 else []
    cat_names = f.get("category_name", []) if parent in (832, 834) else []
    cat_ids = f.get("category_id", []) if parent in (832, 834) else []
    pr = f.get("price_range", {})
    min_price = pr.get("min"); max_price = pr.get("max")
    sort = f.get("sort", "popular")
    limit = int(f.get("limit", 6))

    items = list(PRODUCTS.values())
    items = apply_explicit_filters(items, parent, colors, materials, cat_names, cat_ids, min_price, max_price)
    items = apply_sort(items, sort)
    items = items[:limit]
    return SimpleNamespace(products=items, reason=payload.get("reason"))

CHAT_SYSTEM_PROMPT = (
    "你是一个水晶购物助理。用自然、真诚的方式交流。" \
    "当用户提出具体偏好（如颜色、材质、风格、价格）或需要推荐时，再调用 filter_products 工具展示卡片。" \
    "选择一个合适的父分类：831(按颜色材质) / 832(按款式风格) / 834(按手串类型)。" \
    "831 时，优先 color/material 作为二级筛选；832/834 时，用 category_name。" \
    "回复文字里不要硬编码商品信息，商品卡片由工具返回。"
)
```

### Cart APIs

```
CARTS = {}  # session_id -> { items: [CartItem], totals }

def get_cart(request):
    session_id = get_or_create_session_id(request)
    cart = CARTS.setdefault(session_id, {"items": [], "totals": {"subtotal": 0.0, "currency": "CNY"}})
    return serialize_cart(cart)

def add_cart_item(request):
    session_id = get_or_create_session_id(request)
    body = request.json()
    product_id = int(body.get("product_id"))
    qty = int(body.get("quantity", 1))
    product = PRODUCTS.get(product_id)
    if not product:
        return error_response("not_found", "Product not found")
    cart = CARTS.setdefault(session_id, {"items": [], "totals": {"subtotal": 0.0, "currency": "CNY"}})
    # If already exists, update qty
    for item in cart["items"]:
        if item["product"]["id"] == product_id:
            item["quantity"] += qty
            return serialize_cart(recompute_totals(cart))
    # else, append new item
    cart["items"].append({
        "id": gen_id(),
        "product": serialize_product(product),
        "quantity": qty,
        "unit_price": product.price,
        "currency": "CNY"
    })
    return serialize_cart(recompute_totals(cart))

def update_cart_item(request, item_id: str):
    session_id = get_or_create_session_id(request)
    qty = int(request.json().get("quantity"))
    cart = CARTS.setdefault(session_id, {"items": [], "totals": {"subtotal": 0.0, "currency": "CNY"}})
    for item in cart["items"]:
        if item["id"] == item_id:
            if qty <= 0:
                cart["items"].remove(item)
            else:
                item["quantity"] = qty
            return serialize_cart(recompute_totals(cart))
    return error_response("not_found", "Cart item not found")

def delete_cart_item(request, item_id: str):
    session_id = get_or_create_session_id(request)
    cart = CARTS.setdefault(session_id, {"items": [], "totals": {"subtotal": 0.0, "currency": "CNY"}})
    cart["items"] = [i for i in cart["items"] if i["id"] != item_id]
    return serialize_cart(recompute_totals(cart))

def clear_cart(request):
    session_id = get_or_create_session_id(request)
    CARTS[session_id] = {"items": [], "totals": {"subtotal": 0.0, "currency": "CNY"}}
    return serialize_cart(CARTS[session_id])
```

### Checkout APIs (Mock)

```
CHECKOUTS = {}  # checkout_id -> { status, session_id, created_at }

def create_checkout_session(request):
    session_id = get_or_create_session_id(request)
    body = request.json()
    return_url = body.get("return_url")
    cancel_url = body.get("cancel_url")
    if not return_url or not cancel_url:
        return error_response("validation_error", "return_url and cancel_url required")

    # Simple validation: ensure cart has items
    cart = CARTS.get(session_id, {"items": []})
    if not cart["items"]:
        return error_response("bad_request", "Cart is empty")

    checkout_id = f"co_{gen_id()}"
    CHECKOUTS[checkout_id] = {"status": "paid", "session_id": session_id, "created_at": now_iso()}
    checkout_url = f"https://mockpay.local/checkout/{checkout_id}"
    return {"checkout_id": checkout_id, "checkout_url": checkout_url, "expires_at": in_minutes_iso(30)}

def get_checkout_session(id: str):
    co = CHECKOUTS.get(id)
    if not co:
        return error_response("not_found", "Checkout not found")
    resp = {"status": co["status"]}
    if co["status"] == "paid":
        resp["order_id"] = f"ord_{id}"
    return resp
```

### Telemetry

```
EVENTS = []

def post_event(request):
    body = request.json()
    event = body.get("event")
    payload = body.get("payload", {})
    EVENTS.append({"event": event, "payload": payload, "ts": now_iso()})
    return {"ok": True}
```

---

## Utilities (Pseudocode)

```
def load_data():
    PRODUCTS.clear(); CATEGORIES.clear(); PARENT_CATEGORIES.clear()
    # Load categories
    for row in csv_read("data/category.csv"):
        c = Category(
            id=int(row["id"]), reference_id=int_or_none(row["reference_id"]),
            color=row.get("color") or None, material=row.get("material") or None,
            category_name=row.get("category_name") or None, parent_id=int(row["parent_id"]),
            image=row.get("image") or None
        )
        CATEGORIES[c.id] = c

    # Load parent categories
    for row in csv_read("data/parent_category.csv"):
        PARENT_CATEGORIES[int(row["id"])] = ParentCategory(
            id=int(row["id"]), reference_id=int(row["reference_id"]), name=row["name"], image=row.get("image")
        )

    # Load products
    for row in csv_read("data/products_full.csv"):
        cat_ids = [int(x) for x in (row["category_id"].split("|") if row.get("category_id") else [])]
        p = Product(
            id=int(row["id"]), reference_id=str(row["reference_id"]), name=row["name"],
            price=float(row["price"]), image=row.get("image"),
            extra_images=[x for x in row.get("extra_images", "").split("|") if x],
            description=row.get("description"), category_ids=cat_ids
        )
        PRODUCTS[p.id] = p
        enrich_product(p)  # generate compare_at, rating, reviews, sold

    # Build reverse indexes
    for pid, p in PRODUCTS.items():
        PRODUCT_TO_CATEGORIES[pid] = [CATEGORIES[cid] for cid in p.category_ids if cid in CATEGORIES]

    CATEGORIES_BY_PARENT.clear()
    for c in CATEGORIES.values():
        CATEGORIES_BY_PARENT.setdefault(c.parent_id, []).append(c)

    COLOR_VALUES = {c.color for c in CATEGORIES_BY_PARENT.get(831, []) if c.color}
    MATERIAL_VALUES = {c.material for c in CATEGORIES_BY_PARENT.get(831, []) if c.material}
    CATEGORY_NAME_VALUES_BY_PARENT = {
        832: {c.category_name for c in CATEGORIES_BY_PARENT.get(832, []) if c.category_name},
        834: {c.category_name for c in CATEGORIES_BY_PARENT.get(834, []) if c.category_name},
    }

    # Load curations config (optional)
    CURATIONS_CONFIG = load_curations_config()

def parse_query(q: str) -> Analysis:
    t = normalize(q)
    colors = [c for c in COLOR_VALUES if c in t]
    materials = [m for m in MATERIAL_VALUES if m in t]
    names = []
    for parent in (832, 834):
        for n in CATEGORY_NAME_VALUES_BY_PARENT[parent]:
            if n in t:
                names.append(n)
    budget = extract_budget(t)  # returns dict(min?/max?) based on keywords 以内/以上
    summary_parts = []
    if colors: summary_parts.append(f"颜色: {'/'.join(colors)}")
    if materials: summary_parts.append(f"材质: {'/'.join(materials)}")
    if names: summary_parts.append(f"分类: {'/'.join(names)}")
    if budget: summary_parts.append(f"价格 {format_budget(budget)}")
    return Analysis(colors=colors, materials=materials, category_names=names, price_range=budget,
                    summary=" · ".join(summary_parts) or "解析：未识别到特定条件，展示人气单品")

# LLM-backed resolver (optional) -------------------------------------------------

class LLMQueryResolver:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)  # pseudocode client
        self.model = model

    def resolve(self, q: str, options) -> Analysis:
        # Provide allowed values to constrain choices
        allowed = {
            "colors": sorted(list(options["color_values"])),
            "materials": sorted(list(options["material_values"])),
            "category_names_832": sorted(list(options["category_values"].get(832, []))),
            "category_names_834": sorted(list(options["category_values"].get(834, []))),
        }

        # Prefer structured output via tool/JSON schema rather than free-form text
        tool_schema = {
            "name": "extract_filters",
            "description": "Extract crystal shopping filters from a user query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "colors": {"type": "array", "items": {"type": "string", "enum": allowed["colors"]}},
                    "materials": {"type": "array", "items": {"type": "string", "enum": allowed["materials"]}},
                    "category_names": {"type": "array", "items": {"type": "string", "enum": list(set(allowed["category_names_832"]) | set(allowed["category_names_834"]))}},
                    "price_range": {"type": "object", "properties": {"min": {"type": "number"}, "max": {"type": "number"}}}
                }
            }
        }

        # Pseudocode for calling OpenAI Responses with tool calling
        resp = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": "You extract filters for crystal products. Only return tool calls with allowed values; never invent new labels."},
                {"role": "user", "content": q},
                {"role": "assistant", "content": f"Allowed values: {json.dumps(allowed, ensure_ascii=False)}"}
            ],
            tools=[tool_schema],
            tool_choice={"type": "tool", "name": "extract_filters"}
        )

        args = parse_tool_args(resp)  # colors/materials/category_names/price_range

        summary_parts = []
        if args.get("colors"): summary_parts.append(f"颜色: {'/'.join(args['colors'])}")
        if args.get("materials"): summary_parts.append(f"材质: {'/'.join(args['materials'])}")
        if args.get("category_names"): summary_parts.append(f"分类: {'/'.join(args['category_names'])}")
        pr = args.get("price_range") or {}
        if pr.get("min") or pr.get("max"):
            summary_parts.append("价格 " + format_budget(pr))

        return Analysis(colors=args.get("colors", []), materials=args.get("materials", []),
                        category_names=args.get("category_names", []), price_range=pr,
                        summary=" · ".join(summary_parts) or "解析：为你推荐人气水晶单品")

class HeuristicQueryResolver:
    def resolve(self, q: str, options) -> Analysis:
        return parse_query(q)  # reuse local heuristic

# Factory
def build_query_resolver():
    if os.getenv("ENABLE_LLM_FILTERS", "false").lower() == "true" and os.getenv("OPENAI_API_KEY"):
        return LLMQueryResolver(api_key=os.getenv("OPENAI_API_KEY"), model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    return HeuristicQueryResolver()

QUERY_RESOLVER = build_query_resolver()

def apply_analysis_filters(items, analysis, parent, explicit):
    # Only apply a dimension from analysis if not explicitly provided by client
    if parent == 831:
        if analysis.colors and not explicit.get("colors"):
            items = [p for p in items if any((c.color in analysis.colors) for c in PRODUCT_TO_CATEGORIES[p.id] if c.parent_id == 831)]
        if analysis.materials and not explicit.get("materials"):
            items = [p for p in items if any((c.material in analysis.materials) for c in PRODUCT_TO_CATEGORIES[p.id] if c.parent_id == 831)]
    else:  # 832/834
        if analysis.category_names and not (explicit.get("cat_names") or explicit.get("cat_ids")):
            items = [p for p in items if any((c.category_name in analysis.category_names) for c in PRODUCT_TO_CATEGORIES[p.id] if c.parent_id in (832, 834))]
    if analysis.price_range:
        min_price = analysis.price_range.get("min"); max_price = analysis.price_range.get("max")
        items = [p for p in items if (min_price is None or p.price >= min_price) and (max_price is None or p.price <= max_price)]
    return items

def apply_explicit_filters(items, parent, colors, materials, cat_names, cat_ids, min_price, max_price):
    def ok(p):
        if min_price is not None and p.price < min_price: return False
        if max_price is not None and p.price > max_price: return False
        cats = PRODUCT_TO_CATEGORIES[p.id]
        if parent == 831:
            if colors:
                if not {c.color for c in cats if c.parent_id == 831}.intersection(set(colors)): return False
            if materials:
                if not {c.material for c in cats if c.parent_id == 831}.intersection(set(materials)): return False
        else:
            if cat_names:
                if not {c.category_name for c in cats if c.parent_id in (832,834)}.intersection(set(cat_names)): return False
            if cat_ids:
                if not {c.id for c in cats}.intersection(set(cat_ids)): return False
        return True
    return [p for p in items if ok(p)]

def apply_relevance(items, q):
    # Simple score: name contains tokens + category match
    tokens = tokenize(q)
    def score(p):
        s = 0
        name = (p.name or "").lower()
        for tok in tokens:
            if tok in name: s += 3
        for c in PRODUCT_TO_CATEGORIES[p.id]:
            line = " ".join(filter(None, [c.color, c.material, c.category_name]))
            for tok in tokens:
                if tok in line: s += 1
        return s
    return sorted(items, key=score, reverse=True)

def apply_sort(items, sort):
    if sort == "price_asc": return sorted(items, key=lambda p: p.price)
    if sort == "price_desc": return sorted(items, key=lambda p: p.price, reverse=True)
    if sort == "newest": return sorted(items, key=lambda p: p.id, reverse=True)
    if sort == "popular":
        # Use enriched fields (reviews/rating/sold)
        return sorted(items, key=lambda p: (getattr(p, "rating", 0), getattr(p, "reviews", 0)), reverse=True)
    return items  # relevance handled separately

def serialize_product(p, include_detail=False):
    cats = PRODUCT_TO_CATEGORIES.get(p.id, [])
    data = {
        "id": p.id,
        "reference_id": p.reference_id,
        "name": p.name,
        "price": p.price,
        "currency": "CNY",
        "image": p.image,
    }
    # Always include enriched summary fields for frontend cards
    data.update({
        "compare_at": getattr(p, "compare_at", None),
        "rating": getattr(p, "rating", None),
        "reviews": getattr(p, "reviews", None),
        "sold": getattr(p, "sold", None),
    })
    if include_detail:
        data.update({
            "extra_images": p.extra_images,
            "description": p.description,
            "categories": [serialize_category(c) for c in cats]
        })
    return data

def serialize_category(c):
    return {
        "id": c.id,
        "reference_id": c.reference_id,
        "category_name": c.category_name,
        "parent_id": c.parent_id,
        "color": c.color,
        "material": c.material,
        "image": c.image,
    }

def serialize_parent(pc):
    return {"id": pc.id, "reference_id": pc.reference_id, "name": pc.name, "image": pc.image}

def serialize_cart(cart):
    return cart | {"totals": cart["totals"]}

def recompute_totals(cart):
    subtotal = sum(i["unit_price"] * i["quantity"] for i in cart["items"])
    cart["totals"] = {"subtotal": round(subtotal, 2), "currency": "CNY"}
    return cart

# Curations config --------------------------------------------------------------

def load_curations_config():
    path = os.getenv("CURATIONS_CONFIG", "config/curations.yaml")
    try:
        with open(path, "r", encoding="utf-8") as f:
            y = yaml.safe_load(f) or {}
            # Expected:
            # flash-deals:
            #   product_ids: [1,2,3]
            #   rules: { sort: price_asc, limit: 12 }
            # weekly-picks:
            #   rules: { sort: popular, limit: 12 }
            return y
    except FileNotFoundError:
        return None
```

---

## OpenAI Agent SDK vs. Responses API (Recommendation)

- For this MVP, structured filter extraction is simpler and more reliable with the OpenAI Responses API using tool-calling or JSON Schema mode. It constrains outputs to allowed `colors/materials/category_names` derived from CSV and keeps product selection server-side.
- The OpenAI Agent SDK (Agents API) is suitable if we later need multi-step tool use, retrieval, or persistent agent memory, but it adds orchestration overhead for a task that only needs one structured extraction step.
- Recommendation: Start with `LLMQueryResolver` implemented via Responses API tool-calling; keep interface pluggable so we can swap to Agent SDK without touching routers.

Security/Cost Notes:
- Gate with `ENABLE_LLM_FILTERS` and `OPENAI_API_KEY`. Add per-IP/session rate limit and short result caching (e.g., LRU) for repeated queries.
- Never send full product catalog to the model; only send allowed value lists to bound outputs.

```

---

## Notes & Next Steps

- MVP uses in-memory stores; for production, migrate to SQLite/Postgres and proper ORM.
- SSE endpoint requires proper streaming response headers; use `sse-starlette` or manual generator with FastAPI.
- Consider rate limits for chat endpoints.
- Add basic input validation (pydantic models) and CORS settings for the frontend.
- Unit tests for parsing, filtering, and pagination.
