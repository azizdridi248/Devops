# DevOps API Project

A production-ready microservices project with CI/CD, observability, security, and Kubernetes deployment.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GitHub Actions CI/CD                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ Checkout │→│  Test    │→│  SAST    │→│  Build   │→│ Push & Deploy │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                               │
│  ┌────────────────────────────┐    ┌────────────────────────────┐       │
│  │      API Service           │    │     Worker Service         │       │
│  │  ┌──────────────────────┐  │    │  ┌──────────────────────┐  │       │
│  │  │ Pod 1    │  Pod 2    │  │    │  │ Pod 1    │  Pod 2    │  │       │
│  │  └──────────────────────┘  │    │  └──────────────────────┘  │       │
│  │        Port: 8000          │    │        Port: 8001          │       │
│  └────────────────────────────┘    └────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Services

| Service | Description | Port | Endpoints |
|---------|-------------|------|-----------|
| **API** | REST API for items CRUD | 8000 | `/health`, `/items`, `/metrics` |
| **Worker** | Background task processor | 8001 | `/health`, `/tasks`, `/status`, `/metrics` |

## Project Structure

```
devops-api/
├── .github/workflows/ci-cd.yml    # CI/CD pipeline
├── docs/                          # Documentation
├── k8s/                           # Kubernetes manifests
├── services/
│   ├── api/                       # API service
│   │   ├── src/main.py
│   │   ├── tests/test_api.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── worker/                    # Worker service
│       ├── src/main.py
│       ├── tests/test_worker.py
│       ├── Dockerfile
│       └── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## Quick Start

### Local Development

```bash
# API Service
cd services/api
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# Worker Service (separate terminal)
cd services/worker
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8001
```

### Docker

```bash
# Build and run all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Kubernetes (minikube)

```bash
# Start minikube
minikube start

# Build images in minikube
eval $(minikube docker-env)
docker build -t devops-api:latest ./services/api
docker build -t devops-worker:latest ./services/worker

# Deploy
kubectl apply -f k8s/

# Access services
minikube service devops-api-service
minikube service devops-worker-service
```

---

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"api"}
```

### Create Item
```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name":"Widget","description":"A useful widget"}'
```

### Get Items
```bash
curl http://localhost:8000/items
# [{"id":"uuid","name":"Widget","description":"A useful widget"}]
```

### Worker Status
```bash
curl http://localhost:8001/status
# {"total_tasks":0,"pending":0,"completed":0}
```

### Create Task
```bash
curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"name":"ProcessData","payload":{"key":"value"}}'
```

---

## Observability

### Metrics (Prometheus)

Both services expose `/metrics` in Prometheus format:

```bash
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
```

**Available Metrics:**
- `api_requests_total` / `worker_requests_total` - Request counter
- `api_request_latency_seconds` / `worker_request_latency_seconds` - Latency histogram
- `worker_active_tasks` - Active tasks gauge

### Logs (Structured JSON)

Logs are output in structured JSON format:

```json
{
  "asctime": "2024-01-15 10:30:00",
  "levelname": "INFO",
  "name": "api-service",
  "message": "Request processed",
  "method": "GET",
  "path": "/items",
  "status": 200,
  "latency": 0.0012
}
```

### Tracing (OpenTelemetry)

Traces are output to console by default. For production, configure an exporter (Jaeger, Zipkin).

**Verify Locally:**
```bash
# Run service and watch console output for traces
uvicorn src.main:app --reload --port 8000
# Make requests and observe span output
```

---

## Security

### SAST (Bandit)

```bash
pip install bandit
bandit -r services/api/src/ services/worker/src/ -f txt
```

**Sample Output:**
```
Run started:2024-01-15 10:00:00
Files in scope: 2
Files excluded: 0

No issues identified.

Code scanned: 120 lines
```

### DAST (OWASP ZAP)

```bash
# Run services
docker-compose up -d

# Run ZAP baseline scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://host.docker.internal:8000
```

**Sample Output Explanation:**
- `PASS`: No vulnerabilities found
- `WARN`: Low-risk issues (informational)
- `FAIL`: Security issues requiring attention

---

## CI/CD Pipeline

The GitHub Actions pipeline includes:

| Stage | Description |
|-------|-------------|
| **Test** | Run pytest on both services |
| **SAST** | Bandit security scan |
| **Build** | Build Docker images |
| **Push** | Push to Docker Hub (main branch only) |
| **Deploy** | Deploy to Kubernetes cluster |
| **DAST** | OWASP ZAP baseline scan |

### Required Secrets

Configure in GitHub repository settings:
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password/token
- `KUBE_CONFIG` - Base64 encoded kubeconfig

---

## Image Naming Convention

```
<registry>/<username>/<service>:<tag>

Examples:
docker.io/myuser/devops-api:latest
docker.io/myuser/devops-api:abc123
docker.io/myuser/devops-worker:v1.0.0
```

---

## Running Tests

```bash
# API tests
cd services/api
pytest tests/ -v

# Worker tests
cd services/worker
pytest tests/ -v

# Both with coverage
pytest tests/ -v --cov=src --cov-report=html
```

---

## License

MIT License
