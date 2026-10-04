"""
FastAPI Main Application Entry Point.
Adaptive AI Trading Decision-Support System Backend API.
"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.logging import get_logger
from .api.v1.market import router as market_router
from .api.v1.assets import router as assets_router
from .api.v1.regime import router as regime_router
from .api.v1.news import router as news_router
from .api.v1.portfolio import router as portfolio_router
from .api.v1.decisions import router as decisions_router
from .api.v1.memory import router as memory_router
from .api.v1.backtest import router as backtest_router
from .api.v1.system import router as system_router

logger = get_logger("main")

DASHBOARD_PATH = Path(__file__).parent / "templates" / "dashboard.html"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Adaptive AI Financial Intelligence & Trading Decision-Support Platform API.",
    version="2.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware for Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 Routers
api_v1 = settings.API_V1_PREFIX
app.include_router(market_router, prefix=api_v1)
app.include_router(assets_router, prefix=api_v1)
app.include_router(regime_router, prefix=api_v1)
app.include_router(news_router, prefix=api_v1)
app.include_router(portfolio_router, prefix=api_v1)
app.include_router(decisions_router, prefix=api_v1)
app.include_router(memory_router, prefix=api_v1)
app.include_router(backtest_router, prefix=api_v1)
app.include_router(system_router, prefix=api_v1)


@app.get("/")
def root(request: Request):
    accept = request.headers.get("accept", "")
    # If explicitly requested by a browser navigating directly
    if "text/html" in accept and "application/json" not in accept:
        if DASHBOARD_PATH.exists():
            return HTMLResponse(content=DASHBOARD_PATH.read_text(encoding="utf-8"))
    return {
        "system": settings.PROJECT_NAME,
        "status": "OPERATIONAL",
        "documentation": "/docs",
        "api_v1": api_v1,
        "dashboard": "/dashboard",
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    if DASHBOARD_PATH.exists():
        return HTMLResponse(content=DASHBOARD_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h1>Adaptive AI Trading Decision-Support System</h1><p>Dashboard template not found.</p>"
    )


@app.get("/api/status")
def api_status():
    return {
        "system": settings.PROJECT_NAME,
        "status": "OPERATIONAL",
        "documentation": "/docs",
        "api_v1": api_v1,
    }


