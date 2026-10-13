from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.rate_limit import RateLimitMiddleware
from app.api.v1 import (
    audit,
    auth,
    datasets,
    experiments,
    gaps,
    health,
    hypotheses,
    lineage,
    literature,
    memory,
    projects,
    quantum,
)

app = FastAPI(
    title="ResearchMind-Q API",
    description="Evidence-grounded AI research assistant platform - AI / Cybersecurity / Quantum Computing.",
    version="0.1.0",
)

# Section 56/87: real per-IP rate limiting, not a documented-but-unwired
# intention. Disabled by default in this dev/test environment - see
# app/core/rate_limit.py.
app.add_middleware(RateLimitMiddleware)

# Section 82: real request-latency/count metrics, not a placeholder. Exposes
# GET /metrics in Prometheus text format - see infrastructure/prometheus.yml
# for the matching scrape config.
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(projects.router, prefix=API_PREFIX)
app.include_router(lineage.router, prefix=API_PREFIX)
app.include_router(hypotheses.router, prefix=API_PREFIX)
app.include_router(experiments.router, prefix=API_PREFIX)
app.include_router(datasets.router, prefix=API_PREFIX)
app.include_router(quantum.router, prefix=API_PREFIX)
app.include_router(literature.router, prefix=API_PREFIX)
app.include_router(gaps.router, prefix=API_PREFIX)
app.include_router(memory.router, prefix=API_PREFIX)
app.include_router(audit.router, prefix=API_PREFIX)
app.include_router(health.router, prefix=API_PREFIX)


@app.get("/")
def root():
    return {"name": "ResearchMind-Q", "docs": "/docs", "health": f"{API_PREFIX}/health"}
