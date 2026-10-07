"""
LLM-Powered Secure Code Review Assistant
FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import projects, scans, findings, reports, system

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Secure Code Review Assistant backend…")
    init_db()
    logger.info("Database initialised.")
    yield
    logger.info("Backend shutting down.")


app = FastAPI(
    title="Secure Code Review Assistant",
    description="LLM-Powered security scanning for student projects.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(projects.router)
app.include_router(scans.router)
app.include_router(findings.router)
app.include_router(reports.router)
app.include_router(system.router)


@app.get("/")
def root():
    return {
        "name": "Secure Code Review Assistant",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
