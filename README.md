# DevOps API Project

A production-ready microservices project demonstrating CI/CD, observability, security scanning, and Kubernetes deployment.

[![CI/CD Pipeline](https://github.com/azizdridi248/Devops/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/azizdridi248/Devops/actions/workflows/ci-cd.yml)

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Local Development](#option-1-local-development)
  - [Docker Compose](#option-2-docker-compose)
  - [Kubernetes (Minikube)](#option-3-kubernetes-minikube)
- [API Reference](#api-reference)
- [Monitoring & Observability](#monitoring--observability)
- [Security](#security)
- [CI/CD Pipeline](#cicd-pipeline)
- [Running Tests](#running-tests)

---

## Prerequisites

Before running the project, ensure you have the following installed:

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Runtime for services |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Multi-container orchestration |
| Minikube | 1.30+ | Local Kubernetes cluster |
| kubectl | 1.28+ | Kubernetes CLI |
| Git | 2.40+ | Version control |

---

## Project Structure

```
devops-api/
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions CI/CD pipeline
├── .zap/
│   └── rules.tsv              # OWASP ZAP scan rules
├── k8s/                        # Kubernetes manifests
│   ├── api-deployment.yaml
│   ├── api-service.yaml
│   ├── worker-deployment.yaml
│   ├── worker-service.yaml
│   └── monitoring/            # Observability stack
│       ├── namespace.yaml
│       ├── grafana-deployment.yaml
│       ├── prometheus-*.yaml
│       ├── loki-deployment.yaml
│       └── tempo-*.yaml
├── services/
│   ├── api/                   # REST API service
│   │   ├── src/main.py
│   │   ├── tests/test_api.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── worker/                # Background worker service
│       ├── src/main.py
│       ├── tests/test_worker.py
│       ├── Dockerfile
│       └── requirements.txt
├── docker-compose.yml
├── FINAL_REPORT.md
└── README.md
```

---

## Quick Start

### Option 1: Local Development

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/azizdridi248/Devops.git
   cd Devops
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies for API service:**
   ```powershell
   cd services/api
   pip install -r requirements.txt
   ```

4. **Run the API service:**
   ```powershell
   uvicorn src.main:app --reload --port 8000
   ```

5. **In a new terminal, run the Worker service:**
   ```powershell
   cd services/worker
   pip install -r requirements.txt
   uvicorn src.main:app --reload --port 8001
   ```

6. **Access the services:**
   - API: http://localhost:8000
   - API Docs (Swagger): http://localhost:8000/docs
   - Worker: http://localhost:8001

---

### Option 2: Docker Compose

The simplest way to run both services together.

1. **Build and start all services:**
   ```powershell
   docker-compose up -d --build
   ```

2. **View logs:**
   ```powershell
   docker-compose logs -f
   ```

3. **Access the services:**
   - API: http://localhost:8000
   - Worker: http://localhost:8001

4. **Stop services:**
   ```powershell
   docker-compose down
   ```

---

### Option 3: Kubernetes (Minikube)

Full production-like deployment with monitoring stack.

1. **Start Minikube:**
   ```powershell
   minikube start --driver=docker
   ```

2. **Build images inside Minikube:**
   ```powershell
   # Switch to Minikube's Docker daemon
   minikube docker-env | Invoke-Expression
   
   # Build images
   docker build -t devops-api:latest ./services/api
   docker build -t devops-worker:latest ./services/worker
   ```

3. **Deploy the application:**
   ```powershell
   # Create monitoring namespace
   kubectl apply -f k8s/monitoring/namespace.yaml
   
   # Deploy application services
   kubectl apply -f k8s/
   
   # Deploy monitoring stack
   kubectl apply -f k8s/monitoring/
   ```

4. **Access the services:**
   ```powershell
   minikube service devops-api-service
   minikube service devops-worker-service
   ```

5. **Access Grafana dashboard:**
   ```powershell
   kubectl port-forward -n monitoring svc/grafana 3000:3000
   # Open http://localhost:3000 (admin/admin)
   ```

---

## API Reference

### API Service (Port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI documentation |
| GET | `/items` | List all items |
| POST | `/items` | Create a new item |
| POST | `/process` | Trigger distributed processing |
| GET | `/metrics` | Prometheus metrics |

### Worker Service (Port 8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Task queue status |
| POST | `/tasks` | Create a new task |
| GET | `/tasks/{id}` | Get task by ID |
| GET | `/metrics` | Prometheus metrics |

---

## API Examples

### Health Check
```bash
curl http://localhost:8000/health
```
**Response:**
```json
{"status": "healthy", "service": "api"}
```

### Create an Item
```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "description": "A useful widget"}'
```
**Response:**
```json
{"id": "uuid-here", "name": "Widget", "description": "A useful widget"}
```

### List All Items
```bash
curl http://localhost:8000/items
```
**Response:**
```json
[{"id": "uuid-here", "name": "Widget", "description": "A useful widget"}]
```

### Create a Task (Worker)
```bash
curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "ProcessData", "payload": {"key": "value"}}'
```
**Response:**
```json
{"id": "task-uuid", "name": "ProcessData", "status": "pending"}
```

### Get Task Status
```bash
curl http://localhost:8001/status
```
**Response:**
```json
{"total_tasks": 1, "pending": 0, "completed": 1}
```

---

## Monitoring & Observability

The project includes a complete observability stack:

| Component | Purpose | Access |
|-----------|---------|--------|
| **Prometheus** | Metrics collection | `kubectl port-forward -n monitoring svc/prometheus 9090:9090` |
| **Grafana** | Dashboards & visualization | `kubectl port-forward -n monitoring svc/grafana 3000:3000` |
| **Loki** | Log aggregation | Accessed via Grafana |
| **Tempo** | Distributed tracing | Accessed via Grafana |

### Metrics

Both services expose `/metrics` in Prometheus format:
- `api_requests_total` - Request counter by method, endpoint, status
- `api_request_latency_seconds` - Request latency histogram
- `worker_active_tasks` - Active tasks gauge (Worker only)

### Logs

Logs are output in structured JSON format for easy parsing by Loki.

### Tracing

OpenTelemetry traces are exported to Tempo. View traces in Grafana under **Explore > Tempo**.

---

## Security

### SAST (Static Application Security Testing)

**Tool:** Bandit (Python security linter)

```bash
pip install bandit
bandit -r services/api/src/ services/worker/src/ -f txt
```

### DAST (Dynamic Application Security Testing)

**Tool:** OWASP ZAP Baseline Scan

```bash
docker-compose up -d
docker run -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t http://host.docker.internal:8000
```

---

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/ci-cd.yml`) implements:

| Stage | Description |
|-------|-------------|
| **Test** | Run pytest on both services |
| **SAST** | Bandit security scan |
| **Build** | Build Docker images |
| **Push** | Push to Docker Hub (main branch only) |
| **Deploy Ready** | Prepare K8s manifests |
| **DAST** | OWASP ZAP baseline scan |

### Required GitHub Secrets

Configure in **Settings > Secrets and variables > Actions**:
- `DOCKER_PASSWORD` - Docker Hub access token

---

## Running Tests

```powershell
# API tests
cd services/api
pytest tests/ -v

# Worker tests
cd services/worker
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=src --cov-report=html
```

---

## Author

**Dridi Mohamed Aziz**  
January 2026

---

## License

MIT License
