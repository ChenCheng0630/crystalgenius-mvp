# Troubleshooting Guide

## Common Issues and Solutions

### Docker Issues

#### "docker-compose: No such file or directory"
**Problem**: The system is looking for the old `docker-compose` command.

**Solution**: The Makefile has been updated to use the modern `docker compose` command. If you're still seeing this error:

1. Make sure you have the latest version of this repository
2. Try running directly: `docker compose up --build`
3. If that doesn't work, install Docker Compose:
   - **macOS/Windows**: Update Docker Desktop to the latest version
   - **Linux**: Follow [Docker Compose installation guide](https://docs.docker.com/compose/install/)

#### "Docker is not running"
**Problem**: Docker daemon is not started.

**Solution**:
1. **macOS/Windows**: Start Docker Desktop application
2. **Linux**: Start Docker service: `sudo systemctl start docker`
3. Verify Docker is running: `docker info`

#### "Permission denied" errors
**Problem**: Docker requires elevated permissions.

**Solution**:
1. **macOS/Windows**: Make sure Docker Desktop is running
2. **Linux**: Add your user to docker group:
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### Backend Issues

#### "OpenAI API key not found"
**Problem**: Missing or invalid OpenAI API key.

**Solution**:
1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Edit `backend/.env`:
   ```bash
   OPENAI_API_KEY=your_actual_api_key_here
   ```
3. Restart the services: `make restart`

#### "Module not found" errors
**Problem**: Python dependencies not installed.

**Solution**:
1. **Docker**: Rebuild containers: `make build`
2. **Local development**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

#### "CSV files not found"
**Problem**: Data files are missing.

**Solution**:
1. Ensure these files exist in the `data/` directory:
   - `products_full.csv`
   - `category.csv`
   - `parent_category.csv`
2. Check file permissions: `ls -la data/`

### Frontend Issues

#### "npm install" fails
**Problem**: Node.js dependencies installation issues.

**Solution**:
1. Check Node.js version: `node --version` (requires 18+)
2. Clear npm cache: `npm cache clean --force`
3. Delete node_modules: `rm -rf frontend/node_modules`
4. Reinstall: `cd frontend && npm install`

#### "Cannot connect to backend"
**Problem**: Frontend can't reach backend API.

**Solution**:
1. Check if backend is running: `curl http://localhost:8000/health`
2. Check Docker network: `docker compose ps`
3. Verify backend logs: `make logs`

#### "CORS errors" in browser
**Problem**: Cross-origin request blocked.

**Solution**: This shouldn't happen with the Docker setup, but if it does:
1. Check if both services are running in the same Docker network
2. Verify the proxy configuration in `package.json`

### Network Issues

#### "Port already in use"
**Problem**: Ports 3000 or 8000 are occupied.

**Solution**:
1. Find what's using the port: `lsof -i :3000` or `lsof -i :8000`
2. Stop the conflicting service
3. Or change ports in `docker-compose.yml`:
   ```yaml
   ports:
     - "3001:80"  # Frontend on port 3001
     - "8001:8000" # Backend on port 8001
   ```

#### "Connection refused" errors
**Problem**: Services can't communicate.

**Solution**:
1. Check if all services are up: `make status`
2. Check logs: `make logs`
3. Restart services: `make restart`

### Data Issues

#### "No products displayed"
**Problem**: Product data not loading.

**Solution**:
1. Check backend logs: `docker compose logs backend`
2. Verify CSV files are present and readable
3. Test API directly: `curl http://localhost:8000/api/v1/products`

#### "Search not working"
**Problem**: Search functionality not responding.

**Solution**:
1. Check if OpenAI API key is configured
2. Test without LLM features by setting in `backend/.env`:
   ```bash
   ENABLE_LLM_FILTERS=false
   ENABLE_LLM_CHAT=false
   ```
3. Restart: `make restart`

## Debugging Commands

### Check Service Status
```bash
make status          # Docker service status
make health          # Health check endpoints
docker compose logs  # All service logs
docker compose logs backend  # Backend logs only
docker compose logs frontend # Frontend logs only
```

### Manual Testing
```bash
# Test backend directly
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/assistant/profile

# Test frontend
curl http://localhost:3000/health
```

### Clean Restart
```bash
make clean   # Remove all containers and images
make build   # Rebuild everything
make up      # Start fresh
```

## Getting Help

If you're still experiencing issues:

1. Check the logs: `make logs`
2. Verify your setup matches the requirements in README.md
3. Try a clean restart: `make clean && make build && make up`
4. Check if there are any updates to the repository

## Common Environment Variables

Make sure these are set in `backend/.env`:

```bash
# Required for AI features
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Feature flags
ENABLE_LLM_CHAT=true
ENABLE_LLM_FILTERS=true
```

## Port Reference

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Checks**: 
  - Frontend: http://localhost:3000/health
  - Backend: http://localhost:8000/health
