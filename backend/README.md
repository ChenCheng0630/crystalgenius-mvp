# CrystalGenius Backend

FastAPI-based backend for the CrystalGenius MVP application.

## Features

- **Product Management**: Browse and search crystal products with filtering
- **AI Chat Assistant**: LLM-powered chat with tool calling for product recommendations
- **Cart & Checkout**: Shopping cart management and mock checkout flow
- **Curations**: Configurable product collections with fallback logic
- **Real-time Streaming**: Server-sent events for chat responses

## Quick Start

### Using Docker (Recommended)

1. **Build and run with Docker Compose:**
   ```bash
   cd backend
   docker-compose up --build
   ```

2. **Access the API:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Local Development

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the development server:**
   ```bash
   python run.py
   ```

## Configuration

Create a `.env` file in the backend directory:

```bash
# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Feature Flags
ENABLE_LLM_CHAT=true
ENABLE_LLM_FILTERS=true

# Curations (optional)
CURATIONS_CONFIG=config/curations.yaml
```

## API Endpoints

### Core Endpoints
- `GET /api/v1/assistant/profile` - Assistant profile information
- `GET /api/v1/products` - List products with filtering
- `GET /api/v1/products/search` - Search products with analysis
- `GET /api/v1/products/{id}` - Product details

### Chat System
- `POST /api/v1/chat/sessions` - Create chat session
- `GET /api/v1/chat/messages` - Get chat history
- `POST /api/v1/chat/messages` - Send message (with tool calling)
- `GET /api/v1/chat/stream` - Streaming chat responses

### Shopping
- `GET /api/v1/cart` - Get cart contents
- `POST /api/v1/cart/items` - Add item to cart
- `PATCH /api/v1/cart/items/{id}` - Update cart item
- `DELETE /api/v1/cart/items/{id}` - Remove cart item
- `DELETE /api/v1/cart` - Clear entire cart

### Checkout
- `POST /api/v1/checkout/sessions` - Create checkout session
- `GET /api/v1/checkout/sessions/{id}` - Get checkout status

### Metadata
- `GET /api/v1/categories` - List categories by parent
- `GET /api/v1/parent-categories` - List parent categories
- `GET /api/v1/curations` - List available curations
- `GET /api/v1/curations/{slug}` - Get curation products

## Architecture

- **FastAPI**: Modern Python web framework with automatic API documentation
- **In-Memory Storage**: All data loaded from CSV files at startup
- **Tool Calling**: OpenAI function calling for intelligent product recommendations
- **SSE Streaming**: Real-time chat responses with Server-Sent Events
- **Session Management**: Cookie-based session handling

## Data Sources

The backend loads data from CSV files in the `../data/` directory:
- `products_full.csv` - Product catalog
- `category.csv` - Product categories
- `parent_category.csv` - Category hierarchy

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
isort .
```

### Type Checking
```bash
mypy .
```

## Docker Deployment

The included Dockerfile and docker-compose.yml provide a complete containerized setup:

- Multi-stage build for optimized image size
- Non-root user for security
- Health checks for monitoring
- Volume mounts for data and configuration
- Production-ready with proper logging

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key for LLM features |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `ENABLE_LLM_CHAT` | `false` | Enable LLM-powered chat |
| `ENABLE_LLM_FILTERS` | `false` | Enable LLM-powered query parsing |
| `CURATIONS_CONFIG` | - | Path to curations YAML config |
