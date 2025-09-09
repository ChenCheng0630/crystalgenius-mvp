"""FastAPI application for the CrystalGenius MVP backend."""

from __future__ import annotations

from fastapi import FastAPI
import os
from pathlib import Path


def _load_env_file() -> None:
    """Load environment variables from backend/.env if present.

    Avoids adding a dependency on python-dotenv while keeping config simple.
    Existing environment variables are not overridden.
    """
    try:
        backend_dir = Path(__file__).resolve().parent
        env_path = backend_dir / ".env"
        if not env_path.exists():
            return
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            # Strip optional quotes around values
            value = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
    except Exception:
        # Best-effort; silently ignore .env parsing issues
        pass


_load_env_file()

import data_loader
from routers import assistant, curations, products, chat, cart, checkout, meta


def create_app() -> FastAPI:
    app = FastAPI(title="CrystalGenius API", version="0.1.0")

    @app.on_event("startup")
    async def _startup() -> None:
        data_loader.load_all()

    @app.get("/health")
    async def health_check() -> dict:
        """Simple health check endpoint."""
        return {
            "status": "healthy",
            "service": "crystalgenius-backend",
            "version": "0.1.0",
            "products_loaded": len(data_loader.PRODUCTS),
            "categories_loaded": len(data_loader.CATEGORIES)
        }

    # Register routers
    app.include_router(assistant.router, prefix="/api/v1")
    app.include_router(curations.router, prefix="/api/v1")
    app.include_router(products.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(cart.router, prefix="/api/v1")
    app.include_router(checkout.router, prefix="/api/v1")
    app.include_router(meta.router, prefix="/api/v1")

    return app


app = create_app()
