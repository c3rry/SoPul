"""Pulse2026 FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import markets_router, pipeline_router, races_router
from api.scheduler import VelocityScheduler
from db.database import init_models

scheduler = VelocityScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context initializing schemas and background schedulers."""
    await init_models()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Pulse2026 Election Forecasting & Arbitrage Engine",
    description="Zero-cost multi-modal quantitative election forecasting engine for the 2026 U.S. Midterms.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST Routers under /api/v1
app.include_router(races_router, prefix="/api/v1")
app.include_router(markets_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Health check and engine status."""
    return {
        "engine": "Pulse2026 (SoPul)",
        "status": "online",
        "circuit_breaker_state": scheduler.state.value,
        "social_layer_active": scheduler.is_social_active(),
        "documentation": "/docs",
    }
