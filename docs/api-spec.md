# CrystalGenius API (Mobile MVP)

This document defines the frontend ↔ backend API for the mobile-first MVP of the AI shopping assistant for crystals (水晶). It supports: Profile (assistant) page, Chat, Explore/Search, Product Listing/Detail, Cart, and Checkout.

## Base & Conventions

- Base URL: `/api/v1`
- Format: JSON, UTF-8; timestamps ISO-8601 (UTC)
- Auth/Session: Anonymous browsing supported. Server issues a `session_id` cookie on first request, or accepts `X-Session-Id` header to associate chat, cart, and checkout.
- Locale/Currency: Defaults to `zh-CN` + `CNY`; amounts are numbers in minor-less precision (e.g., 146.0 for ¥146)
- Pagination: `page` (default 1), `page_size` (default 20). Responses include a `meta` object.
- Errors: Consistent error envelope with machine-readable `code`.

### Error Envelope

```json
{ "error": { "code": "string", "message": "string", "details": {} } }
```

Common `code`: `bad_request`, `not_found`, `validation_error`, `rate_limited`, `internal`.

## Core Schemas

- Product
  - `{ id: number, reference_id: string, name: string, price: number, currency: "CNY", compare_at?: number, image: string, extra_images?: string[], description?: string, categories?: Category[], sold?: string, rating?: number, reviews?: number, tags?: string[] }`
  - Category
  - `{ id: number, reference_id: number, category_name: string, parent_id: number, color?: string, material?: string, image?: string }`
  - ParentCategory
  - `{ id: number, reference_id: number, name: string, image?: string }`
  - AssistantProfile
  - `{ name: string, avatar: string, intro_short: string, domains: string[], styles: string[], stats: { monthly_sales: string, gmv: string, positive_rate: string }, ctas?: { label: string, action: "chat" | "explore" }[] }`
  - Curation
  - `{ slug: string, title: string, description?: string, products: Product[] }`
  - SearchAnalysis
  - `{ summary: string, colors?: string[], materials?: string[], category_names?: string[], price_range?: { min?: number, max?: number } }`
  - Cart
  - `{ id: string, items: CartItem[], totals: { subtotal: number, currency: "CNY" } }`
- CartItem
  - `{ id: string, product: Product, quantity: number, unit_price: number, currency: "CNY" }`
- ChatMessage
  - `{ id: string, role: "user" | "assistant" | "system", content: string }`

---

## Assistant & Curations

### GET `/assistant/profile`
Returns content for the Shopping Assistant Profile screen.

Response: `AssistantProfile`

Example (crystals):
```json
{
  "name": "小晶",
  "avatar": "https://.../crystal-expert.jpg",
  "intro_short": "专注天然水晶与能量手串，按寓意与体感为你精准配搭。",
  "domains": ["天然水晶手串", "寓意/能量配对"],
  "styles": ["温柔疗愈", "专业配搭", "寓意解读"],
  "stats": {"monthly_sales":"2.8K+ 单","gmv":"￥1.9M/月","positive_rate":"99% 好评"}
}
```

### GET `/curations`
Lists available curated collections (e.g., Flash Deals, Weekly Picks).

Response:
```json
{ "curations": [ { "slug": "flash-deals", "title": "她的秒杀商品" }, { "slug": "weekly-picks", "title": "她的本周推荐" } ] }
```

### GET `/curations/:slug`
Fetches a specific curation.

Path params: `slug` in `flash-deals | weekly-picks`

Query: `page?`, `page_size?`

Response:
```json
{
  "curation": { "slug": "flash-deals", "title": "她的秒杀商品", "products": [/* Product[] */] },
  "meta": { "page": 1, "page_size": 20, "total": 123 }
}
```

---

## Products & Search (Crystals)

### GET `/products`
Product listing with filters and sorting, aligned to CSV columns and parent-category rules.

Query params:
- `q?`: natural language query (e.g., "红色 能量手串 300以内")
- `parent_category_id?`: number; one of `831`(按颜色材质), `832`(按款式风格), `834`(按手串类型). Defaults to `831` when omitted.
- For `parent_category_id=831` (按颜色材质):
  - `color[]?`: repeatable string; values like `红, 橙, 黄, 粉, 绿, 蓝, 紫, 黑, 白, 灰, 棕, 其他` (from `category.csv.color`).
  - `material[]?`: repeatable string; values from `category.csv.material` (e.g., `白水晶, 黄水晶, 绿幽灵, 海蓝宝, ...`).
- For `parent_category_id=832` or `834`:
  - `category_name[]?`: repeatable string; values from `category.csv.category_name` under that parent (e.g., `贵气温柔精致`, `男士手串`, `魔盒款`, ...).
- `category_id[]?`: optional repeatable numeric IDs from `category.csv.id` (useful when client already resolved names to IDs).
- `min_price?`, `max_price?`: number (CNY)
- `sort?`: `relevance | price_asc | price_desc | popular | newest` (default `relevance` if `q` present, else `popular`)
- `page?`, `page_size?`

Response:
```json
{ "products": [/* Product[] */], "meta": {"page":1, "page_size":20, "total":300} }
```

### GET `/products/:id`
Product detail.

Response: `Product` (with `extra_images`, `description`, `categories` filled)

### GET `/search/products`
Natural-language search with parsed analysis (used by Explore page) for crystals.

Query: Same as `/products` (use `q`), plus optional explicit filters; explicit filters override what is inferred from `q`.

Response:
```json
{
  "analysis": {
    "summary": "颜色: 红 · 材质: 白水晶 · 价格 ≤ 300",
    "colors": ["红"],
    "materials": ["白水晶"],
    "category_names": [],
    "price_range": { "max": 300 }
  },
  "products": [/* Product[] */],
  "meta": { "page": 1, "page_size": 20, "total": 42 }
}
```

### GET `/parent-categories`
Returns parent category groups: `831`(按颜色材质), `832`(按款式风格), `834`(按手串类型).

Response: `{ "parent_categories": [ ParentCategory, ... ] }`

### GET `/categories`
Returns categories, optionally filtered by parent. Fields align with CSV (`category_name`, `color`, `material`).

Query: `parent_id?`

Response: `{ "categories": [ Category, ... ] }`

---

## Chat

### POST `/chat/sessions`
Start a conversation (optional; server can auto-create on first message).

Body:
```json
{ "metadata": { "source": "profile|explore|product", "product_id": 123 } }
```

Response: `{ "session_id": "string" }` (and `Set-Cookie: session_id=...` if new)

### POST `/chat/messages`
Non-streaming chat turn with optional product suggestions for in-conversation cards.

Body:
```json
{ "session_id": "string", "message": "string", "context": { "product_id": 123 } }
```

Response:
```json
{
  "messages": [ {"id": "m1", "role": "user", "content": "..."}, {"id": "m2", "role": "assistant", "content": "..."} ],
  "suggestions": { "products": [/* Product[] */], "reason": "根据预算与颜色筛选" }
}
```

### GET `/chat/stream`
SSE streaming of assistant replies and dynamic product cards.

Query: `session_id`, `message`

Events (`text/event-stream`):
- `event: assistant_message` data: `{ id, role: "assistant", content }`
- `event: product_suggestions` data: `{ products: [/* Product[] */], reason?: string }`
- `event: done` data: `{}`

Notes: Frontend should prefer streaming, and fallback to `/chat/messages` if SSE not available. Product suggestions reflect crystal items based on `colors/materials/category_names/price` context.

---

## Cart

### GET `/cart`
Fetch current cart (by `session_id` cookie/header).

Response: `Cart`

### POST `/cart/items`
Add item to cart.

Body:
```json
{ "product_id": 123, "quantity": 1 }
```

Response: `Cart`

### PATCH `/cart/items/:item_id`
Update quantity.

Body: `{ "quantity": 2 }`

Response: `Cart`

### DELETE `/cart/items/:item_id`
Remove item. Response: `Cart` (remaining)

### POST `/cart/clear`
Empty the cart. Response: `Cart` (now empty)

---

## Checkout

### POST `/checkout/sessions`
Begin checkout for the current cart.

Body:
```json
{ "return_url": "https://...", "cancel_url": "https://..." }
```

Response:
```json
{ "checkout_id": "co_123", "checkout_url": "https://...", "expires_at": "2025-09-01T12:00:00Z" }
```

### GET `/checkout/sessions/:id`
Poll checkout status.

Response:
```json
{ "status": "pending|paid|canceled|expired", "order_id": "ord_123" }
```

Notes: MVP may mock payment and return `paid` immediately.

---

## Telemetry

### POST `/events`
Lightweight UX events for tuning.

Body:
```json
{ "event": "chat_opened|product_clicked|add_to_cart|checkout_started|checkout_completed", "payload": {} }
```

Response: `{ "ok": true }`

---

## Status Codes

- 200: Success
- 201: Created (cart item, checkout session)
- 204: No Content (delete)
- 400/422: Invalid params or payload
- 404: Not found
- 429: Rate limited
- 500: Server error

---

## Frontend Integration Notes

- Profile screen: `GET /assistant/profile` + `GET /curations/:slug` for "秒杀/本周推荐" tabs (curations are crystal picks).
- Explore: `GET /search/products?q=...` and display `analysis.summary` banner; show results grid of crystals.
- Chat: Prefer `GET /chat/stream`; fallback to `POST /chat/messages`.
- Product list/detail: `GET /products`, `GET /products/:id`. Default `parent_category_id=831` to show color/material rows.
- Filters UI: 
  - Primary tabs map to parent categories `831/832/834`.
  - When `831`: fetch `GET /categories?parent_id=831` and split chips visually by `color` row and `material` row; send selected values via `color[]`/`material[]`.
  - When `832` or `834`: fetch `GET /categories?parent_id=...` and send selections via `category_name[]` (or resolved `category_id[]`).
- Price range: send `min_price`/`max_price` alongside any filter mode.
- Cart/Checkout: `/cart` + `/checkout/sessions` using `session_id`.

---

## Filtering Rules (Server-side)

- If `parent_category_id` is omitted, treat as `831` (按颜色材质).
- When `parent_category_id=831`, only `color[]`, `material[]`, `min_price`, `max_price`, `q`, `sort`, and pagination apply; ignore `category_name[]` in this mode.
- When `parent_category_id=832` or `834`, only `category_name[]`/`category_id[]`, `min_price`, `max_price`, `q`, `sort`, and pagination apply; ignore `color[]`/`material[]` in this mode.
- All filters are multi-select; a product matches if it satisfies at least one selected value within each active dimension (e.g., any of the chosen colors) and all active dimensions together (AND of dimensions, OR within a dimension).
- Products derive their color/material/category_name via their `category_ids` (parsed from CSV `category_id` pipe-separated list) joined to `category.csv`.

---

## Example Payloads (Crystals)

- Products list (condensed):
```json
{
  "products": [
    {
      "id": 1,
      "reference_id": "8476",
      "name": "红胶花白水晶绿幽灵魔盒手串BAC576x",
      "price": 146.0,
      "currency": "CNY",
      "image": "https://aurayou2.lot-lot.com/image/32/2025/06/2e52b7...jpg",
      "description": "▫️▪️红胶花白水晶绿幽灵魔盒手串 - 材质&尺寸：...",
      "categories": [ { "id": 871, "reference_id": 871, "category_name": "【红】红胶花", "parent_id": 831, "color": "红", "material": "红胶花" } ]
    }
  ],
  "meta": { "page": 1, "page_size": 20, "total": 300 }
}
```

- Product detail:
```json
{
  "id": 1,
  "reference_id": "8476",
  "name": "红胶花白水晶绿幽灵魔盒手串BAC576x",
  "price": 146.0,
  "currency": "CNY",
  "image": "https://...jpg",
  "extra_images": ["https://...jpg", "https://...jpg"],
  "description": "▫️▪️...",
  "sold": "320+",
  "rating": 5,
  "reviews": 87,
  "categories": [ /* as above */ ]
}
```

