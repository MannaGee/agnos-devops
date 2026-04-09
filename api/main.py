import structlog
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import os

# --- Structured JSON logger setup ---
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# --- App init ---
app = FastAPI(title="Agnos API Service")

# --- Prometheus metrics (auto-instruments all routes) ---
Instrumentator().instrument(app).expose(app)

# --- Environment info (injected via Docker/K8s env vars) ---
ENV = os.getenv("APP_ENV", "dev")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


@app.on_event("startup")
async def startup():
    logger.info("api_startup", env=ENV, version=APP_VERSION)


@app.get("/health")
async def health():
    logger.info("health_check", status="ok", env=ENV)
    return {
        "status": "ok",
        "env": ENV,
        "version": APP_VERSION
    }
