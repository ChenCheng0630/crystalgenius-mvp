# CrystalGenius MVP

AI-powered crystal shopping assistant with intelligent product recommendations and real-time chat.

## Features

- 🤖 **AI Shopping Assistant**: LLM-powered chat with tool calling for product recommendations
- 🔍 **Smart Search**: Natural language search with intelligent filtering
- 🛒 **Shopping Cart**: Full cart management with persistent sessions
- 📱 **Mobile-First Design**: Optimized for mobile devices
- 🎯 **Product Curations**: Flash deals and weekly picks
- ⚡ **Real-time Chat**: Server-sent events for streaming responses
- 🐳 **Docker Ready**: Complete containerization for easy deployment

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd crystalgenius-mvp
   ```

2. **Set up environment variables:**
   ```bash
   # Copy example env file
   cp backend/.env.example backend/.env
   # Edit with your OpenAI API key
   nano backend/.env
   ```

3. **Start the application:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  FastAPI Backend│    │   CSV Data      │
│                 │    │                 │    │                 │
│ • TypeScript    │◄──►│ • Python 3.11   │◄──►│ • Products      │
│ • Tailwind CSS │    │ • OpenAI API    │    │ • Categories    │
│ • SSE Streaming │    │ • Tool Calling  │    │ • Parent Cats   │
│ • Mobile-First  │    │ • Session Mgmt  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Project Structure

```
crystalgenius-mvp/
├── backend/                 # FastAPI backend
│   ├── routers/            # API route handlers
│   ├── services/           # Business logic
│   ├── models.py           # Data models
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/         # Main pages
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types
│   ├── package.json       # Node dependencies
│   └── Dockerfile         # Frontend container
├── data/                   # CSV data files
│   ├── products_full.csv  # Product catalog
│   ├── category.csv       # Categories
│   └── parent_category.csv# Category hierarchy
├── docs/                   # Documentation
└── docker-compose.yml     # Main orchestration
```

## Configuration

### Backend Environment Variables

Create `backend/.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Feature Flags
ENABLE_LLM_CHAT=true
ENABLE_LLM_FILTERS=true

# Optional: Curations config
CURATIONS_CONFIG=config/curations.yaml
```

### Available Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key for LLM features |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `ENABLE_LLM_CHAT` | `false` | Enable LLM-powered chat |
| `ENABLE_LLM_FILTERS` | `false` | Enable LLM-powered query parsing |
| `CURATIONS_CONFIG` | - | Path to curations YAML config |

## API Endpoints

### Core Features
- `GET /api/v1/assistant/profile` - Assistant information
- `GET /api/v1/products` - Product listing with filters
- `GET /api/v1/products/search` - Smart search with analysis
- `POST /api/v1/chat/messages` - Chat with AI assistant
- `GET /api/v1/chat/stream` - Streaming chat responses

### Shopping
- `GET /api/v1/cart` - Shopping cart
- `POST /api/v1/cart/items` - Add to cart
- `POST /api/v1/checkout/sessions` - Create checkout

See [API Documentation](docs/api-spec.md) for complete details.

## Key Features

### 🤖 AI Chat Assistant
- **Tool Calling**: LLM decides when to show product recommendations
- **Streaming Responses**: Real-time chat with Server-Sent Events
- **Context Awareness**: Maintains conversation context and preferences
- **Product Integration**: Seamlessly recommends products within chat

### 🔍 Smart Search & Filtering
- **Natural Language**: Search with phrases like "红色能量手串300以内"
- **Intelligent Analysis**: Parses intent and extracts filters automatically
- **Multi-dimensional Filtering**: By color, material, style, price range
- **Category Hierarchy**: Supports 3-level category system

### 📱 Mobile-Optimized UI
- **Touch-First Design**: Optimized for mobile interactions
- **Responsive Layout**: Works on all screen sizes
- **Fast Loading**: Optimized images and lazy loading
- **Offline Support**: Progressive Web App features

## Data Model

The application uses a CSV-based data model:

- **Products** (`products_full.csv`): Product catalog with prices, images, descriptions
- **Categories** (`category.csv`): Color, material, and style categories
- **Parent Categories** (`parent_category.csv`): Top-level category groups

Products are enriched at runtime with:
- Compare prices (for discounts)
- Ratings and reviews
- Sales data
- Related categories

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
python run.py
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Running Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Deployment

### Production with Docker
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Health Checks
- Frontend: http://localhost:3000/health
- Backend: http://localhost:8000/health

## Monitoring

The application includes built-in health checks and logging:

- **Health Endpoints**: Both services expose `/health` endpoints
- **Structured Logging**: JSON-formatted logs for production
- **Error Tracking**: Comprehensive error handling and reporting
- **Performance Metrics**: Built-in performance monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For support and questions, please refer to the documentation in the `docs/` directory or contact the development team.