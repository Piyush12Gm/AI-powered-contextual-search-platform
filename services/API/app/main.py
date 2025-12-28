from fastapi import FastAPI
from app.routes import products, search, events
from loguru import logger
import time
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

app = FastAPI(title="Contextual Search API", version="0.1.0")

_metrics = {
    "requests_total": 0,
    "avg_latency_ms": 0.0,
    "search_requests": 0,
}

@app.middleware("http")
async def add_timing(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    _metrics["requests_total"] += 1
    # moving average
    n = _metrics["requests_total"]
    _metrics["avg_latency_ms"] = ((_metrics["avg_latency_ms"] * (n - 1)) + duration_ms) / n
    logger.info(f"{request.method} {request.url.path} {duration_ms:.2f}ms")
    return response

@app.get("/metrics")
async def metrics():
    return _metrics

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Serve static UI at /ui
app.mount("/ui", StaticFiles(directory="app/static", html=True), name="static")
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(events.router, prefix="/events", tags=["events"])