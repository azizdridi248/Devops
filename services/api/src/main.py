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
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from pythonjsonlogger import jsonlogger
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
import httpx

# Configure structured JSON logging
logger = logging.getLogger("api-service")
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(trace_id)s %(span_id)s"
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initial instrumentation for logging (must be done before creating tracer)
LoggingInstrumentor().instrument(set_logging_format=True)

# Configure OpenTelemetry tracing
resource = Resource.create(attributes={"service.name": "devops-api"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

# Export to Tempo (OTLP) (Default: http://tempo.monitoring.svc.cluster.local:4317)
import os
if os.getenv("OTEL_TRACES_EXPORTER") == "console":
    tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
else:
    otlp_exporter = OTLPSpanExporter(endpoint="http://tempo.monitoring.svc.cluster.local:4317", insecure=True)
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

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
HTTPXClientInstrumentor().instrument()


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


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


@app.post("/process", status_code=202)
async def process_task(item: ItemCreate):
    """
    Simulate a distributed process by calling the Worker service.
    This generates a distributed trace in Tempo.
    """
    with tracer.start_as_current_span("process_task"):
        worker_url = "http://devops-worker-service:8001/tasks"
        logger.info(f"Calling worker at {worker_url}")
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    worker_url,
                    json={"name": f"Processed: {item.name}", "payload": {"source": "api"}}
                )
            
            if response.status_code == 201:
                logger.info("Worker successfully processed task")
                return {"status": "accepted", "worker_response": response.json()}
            else:
                logger.error(f"Worker failed with status {response.status_code}")
                return Response(content="Worker error", status_code=500)
        except Exception as e:
            logger.error(f"Failed to call worker: {str(e)}")
            return Response(content=f"Worker unreachable: {str(e)}", status_code=503)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
