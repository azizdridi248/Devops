"""
DevOps API Service - Main Application
A FastAPI REST API with observability (metrics, logs, tracing)
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pythonjsonlogger import jsonlogger
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure structured JSON logging
logger = logging.getLogger("api-service")
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Configure OpenTelemetry tracing
trace.set_tracer_provider(TracerProvider())
tracer_provider = trace.get_tracer_provider()
tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
tracer = trace.get_tracer(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter("api_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "Request latency", ["endpoint"])

# In-memory storage
items_db: dict[str, dict] = {}


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None


class Item(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API service starting up")
    yield
    logger.info("API service shutting down")


app = FastAPI(title="DevOps API Service", version="1.0.0", lifespan=lifespan)
FastAPIInstrumentor.instrument_app(app)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(latency)
    
    logger.info("Request processed", extra={
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency": round(latency, 4)
    })
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api"}


@app.get("/items", response_model=list[Item])
async def get_items():
    """Get all items"""
    with tracer.start_as_current_span("get_items"):
        return list(items_db.values())


@app.post("/items", response_model=Item, status_code=201)
async def create_item(item: ItemCreate):
    """Create a new item"""
    with tracer.start_as_current_span("create_item"):
        item_id = str(uuid.uuid4())
        new_item = {"id": item_id, "name": item.name, "description": item.description}
        items_db[item_id] = new_item
        logger.info("Item created", extra={"item_id": item_id, "item_name": item.name})
        return new_item


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
