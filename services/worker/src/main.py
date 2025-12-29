"""
DevOps Worker Service - Background Task Processor
A FastAPI service for processing background tasks with observability
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from pythonjsonlogger import jsonlogger
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure structured JSON logging
logger = logging.getLogger("worker-service")
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
REQUEST_COUNT = Counter("worker_requests_total", "Total requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("worker_request_latency_seconds", "Request latency", ["endpoint"])
TASKS_PROCESSED = Counter("worker_tasks_processed_total", "Total tasks processed", ["status"])
ACTIVE_TASKS = Gauge("worker_active_tasks", "Currently active tasks")

# In-memory storage
tasks_db: dict[str, dict] = {}


class TaskCreate(BaseModel):
    name: str
    payload: Optional[dict] = None


class Task(BaseModel):
    id: str
    name: str
    status: str
    payload: Optional[dict] = None
    created_at: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Worker service starting up")
    yield
    logger.info("Worker service shutting down")


app = FastAPI(title="DevOps Worker Service", version="1.0.0", lifespan=lifespan)
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
    return {"status": "healthy", "service": "worker"}


@app.get("/status")
async def get_status():
    """Get worker status"""
    with tracer.start_as_current_span("get_status"):
        pending = sum(1 for t in tasks_db.values() if t["status"] == "pending")
        completed = sum(1 for t in tasks_db.values() if t["status"] == "completed")
        return {"total_tasks": len(tasks_db), "pending": pending, "completed": completed}


@app.get("/tasks", response_model=list[Task])
async def get_tasks():
    """Get all tasks"""
    with tracer.start_as_current_span("get_tasks"):
        return list(tasks_db.values())


@app.post("/tasks", response_model=Task, status_code=201)
async def create_task(task: TaskCreate):
    """Create a new task"""
    with tracer.start_as_current_span("create_task"):
        task_id = str(uuid.uuid4())
        new_task = {
            "id": task_id,
            "name": task.name,
            "status": "pending",
            "payload": task.payload,
            "created_at": datetime.utcnow().isoformat()
        }
        tasks_db[task_id] = new_task
        ACTIVE_TASKS.inc()
        logger.info("Task created", extra={"task_id": task_id, "name": task.name})
        return new_task


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
