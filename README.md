# CrystalGenius MVP

This repository contains a very small mobile-shopping prototype.  The new
`backend/` package implements a FastAPI application that serves product
data from CSV files and exposes endpoints defined in
[`docs/api-spec.md`](docs/api-spec.md).

## Running the backend

```bash
uvicorn backend.app:app --reload
```

The application loads CSV data on start-up and keeps state (cart, chat and
checkout sessions) in memory.  It is therefore suitable only for
experimenting with the MVP locally.

## Endpoints

The API is mounted under `/api/v1`.  Highlights:

- `GET /assistant/profile` – static assistant information.
- `GET /curations` and `/curations/{slug}` – curated product lists.
- `GET /products` and `/products/{id}` – product listing and details with
  filtering and basic relevance sorting.
- `POST /chat/messages` – toy chat implementation using in-memory state.
- `GET /cart` and related `/cart/items` operations.
- `POST /checkout/sessions` – mock checkout returning a placeholder URL.
- `GET /categories` and `GET /parent-categories` – metadata helpers.

Refer to the API specification document for the full contract and query
parameters.
