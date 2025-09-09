"""FastAPI application for the CrystalGenius MVP backend."""

from __future__ import annotations

from fastapi import FastAPI

from . import data_loader
from .routers import assistant, curations, products, chat, cart, checkout, meta


def create_app() -> FastAPI:
    app = FastAPI(title="CrystalGenius API", version="0.1.0")

    @app.on_event("startup")
    async def _startup() -> None:
        data_loader.load_all()

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
