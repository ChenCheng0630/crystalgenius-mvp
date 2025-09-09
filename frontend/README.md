# CrystalGenius Frontend

React TypeScript frontend for the CrystalGenius MVP application.

## Features

- **Modern React with TypeScript**: Type-safe development with React 18
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Mobile-First Design**: Optimized for mobile devices with responsive design
- **Real-time Chat**: SSE-based streaming chat with fallback to REST API
- **Product Management**: Browse, search, and add products to cart
- **AI Assistant Integration**: LLM-powered shopping assistant with product recommendations

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Backend server running on port 8000

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm start
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - The app will proxy API requests to http://localhost:8000

### Production Build

```bash
npm run build
```

The build folder will contain the production-ready static files.

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ProductCard.tsx
│   │   ├── ProductGrid.tsx
│   │   └── Stars.tsx
│   ├── hooks/              # Custom React hooks
│   │   └── useCart.ts
│   ├── pages/              # Main page components
│   │   ├── ProfilePage.tsx
│   │   ├── ExplorePage.tsx
│   │   └── ChatPage.tsx
│   ├── services/           # API client and services
│   │   └── api.ts
│   ├── types/              # TypeScript type definitions
│   │   └── api.ts
│   ├── App.tsx             # Main app component
│   ├── App.css             # Global styles
│   └── index.tsx           # App entry point
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

## Key Features

### 1. **Assistant Profile Page**
- Display AI assistant information and stats
- Show curated product collections (flash deals, weekly picks)
- Quick chat input for immediate assistance

### 2. **Explore Page**
- Natural language product search
- Real-time search analysis display
- Masonry grid layout for product display

### 3. **Chat Page**
- Real-time streaming chat with AI assistant
- Product recommendations within chat
- Visual chat interface with background and captions

### 4. **Shopping Cart Integration**
- Add products to cart from any page
- Real-time cart updates
- Persistent cart state across sessions

## API Integration

The frontend communicates with the backend through a comprehensive API client:

- **Product Management**: Browse, search, and get product details
- **Chat System**: Real-time chat with SSE streaming and REST fallback
- **Shopping Cart**: Full cart management (add, update, remove, clear)
- **Curations**: Access to curated product collections
- **Session Management**: Automatic session handling with cookies

## Styling

- **Tailwind CSS**: Utility-first CSS framework
- **Mobile-First**: Responsive design optimized for mobile devices
- **Custom Components**: Reusable styled components
- **Dark Mode Support**: Ready for dark mode implementation

## Performance

- **Code Splitting**: Automatic code splitting with React
- **Image Optimization**: Optimized image loading and display
- **Lazy Loading**: Efficient loading of components and data
- **Error Boundaries**: Graceful error handling

## Development

### Available Scripts

- `npm start`: Start development server
- `npm build`: Build for production
- `npm test`: Run tests
- `npm run eject`: Eject from Create React App (not recommended)

### Environment Variables

The app uses a proxy configuration in `package.json` to forward API requests to the backend server. For production, you may need to configure the API base URL.

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- Progressive Web App features ready

## Deployment

The frontend can be deployed as static files to any web server or CDN:

1. Build the production version: `npm run build`
2. Deploy the `build/` folder contents
3. Configure your web server to serve `index.html` for all routes (SPA routing)
4. Ensure API requests are properly routed to your backend server
