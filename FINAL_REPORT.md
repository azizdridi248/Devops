# DevOps API Project - Final Report

## Executive Summary

This document provides a comprehensive overview of the DevOps API project, a production-ready microservices implementation featuring two FastAPI services with complete CI/CD, observability, security scanning, and Kubernetes deployment.

**Author:** Dridi Mohamed Aziz  
**Date:** January 2026  
**Version:** 1.0.0

---

## 1. Architecture

### System Design

The project implements a microservices architecture with two independent services:

- **API Service**: Handles REST API operations for items management (CRUD)
- **Worker Service**: Processes background tasks asynchronously

Both services are stateless, use in-memory storage, and communicate via HTTP. The architecture supports horizontal scaling through Kubernetes replicas.

### Architecture Diagram

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
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Monitoring Stack (namespace: monitoring)      │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────────┐│    │
│  │  │Prometheus │ │  Grafana  │ │   Loki    │ │      Tempo        ││    │
│  │  │ (Metrics) │ │(Dashboard)│ │  (Logs)   │ │    (Tracing)      ││    │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────────────┘│    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12 |
| Framework | FastAPI |
| Metrics | prometheus-client |
| Logging | python-json-logger |
| Tracing | OpenTelemetry |
| Containerization | Docker (multi-stage) |
| Orchestration | Kubernetes |
| CI/CD | GitHub Actions |

---

## 2. CI/CD Pipeline

The pipeline implements a complete DevSecOps workflow:

```
Checkout → Test → SAST → Build → Push → Deploy → DAST
```

### Pipeline Stages

| Stage | Tool | Description |
|-------|------|-------------|
| Test | pytest | Unit tests for both services |
| SAST | Bandit | Static security analysis |
| Build | Docker | Multi-stage image builds |
| Push | Docker Hub | Image registry |
| Deploy | kubectl | Kubernetes deployment |
| DAST | OWASP ZAP | Dynamic security testing |

### Key Features

1. **Matrix Testing**: Both services tested in parallel
2. **Security-First**: SAST runs before build, DAST after deployment
3. **Multi-Stage Builds**: Efficient Docker images (~100MB)
4. **Automated Deployment**: Direct K8s deployment from CI

### Pipeline Execution Time

| Stage | Duration |
|-------|----------|
| Test | ~45s |
| SAST | ~15s |
| Build | ~60s |
| Deploy | ~30s |
| **Total** | ~2.5 min |

---

## 3. Observability

### Monitoring Stack

The project includes a complete observability stack deployed in Kubernetes:

| Component | Purpose | Port |
|-----------|---------|------|
| Prometheus | Metrics collection | 9090 |
| Grafana | Visualization & dashboards | 3000 |
| Loki | Log aggregation | 3100 |
| Tempo | Distributed tracing | 3200, 4317 |
| Promtail | Log shipping | 9080 |

### Metrics

Prometheus metrics exposed at `/metrics`:
- Request counters (by method, endpoint, status)
- Latency histograms (P50, P90, P99)
- Active tasks gauge (worker only)

### Logging

Structured JSON logs enable:
- Easy parsing by log aggregators (ELK, Loki)
- Correlation via request IDs
- Performance analysis via latency fields

### Tracing

OpenTelemetry integration provides:
- Distributed trace context propagation
- Span tracking for database/external calls
- Service dependency mapping
- Export to Tempo via OTLP

---

## 4. Security

### Static Analysis (SAST)

**Tool**: Bandit (Python)  
**Coverage**: All source files in both services  
**Integration**: Runs on every PR and push

Bandit scans for:
- Hardcoded passwords
- SQL injection risks
- Unsafe deserialization
- Weak cryptographic functions

### Dynamic Analysis (DAST)

**Tool**: OWASP ZAP Baseline  
**Coverage**: All HTTP endpoints  
**Integration**: Post-deployment scan

ZAP tests for:
- Cross-site scripting (XSS)
- SQL injection
- Security header misconfigurations
- Information disclosure

---

## 5. Kubernetes Setup

### Deployment Configuration

| Resource | API Service | Worker Service |
|----------|------------|----------------|
| Replicas | 2 | 2 |
| CPU Request | 100m | 100m |
| CPU Limit | 500m | 500m |
| Memory Request | 128Mi | 128Mi |
| Memory Limit | 256Mi | 256Mi |

### Health Probes

- **Liveness**: `/health` (15s interval)
- **Readiness**: `/health` (10s interval)

### Access

Services exposed via NodePort:
- API: Dynamic port via `minikube service devops-api-service`
- Worker: Dynamic port via `minikube service devops-worker-service`

---

## 6. API Endpoints

### API Service (Port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |
| GET | `/items` | List all items |
| POST | `/items` | Create item |
| POST | `/process` | Distributed processing |
| GET | `/metrics` | Prometheus metrics |

### Worker Service (Port 8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/status` | Queue status |
| POST | `/tasks` | Create task |
| GET | `/tasks/{id}` | Get task |
| GET | `/metrics` | Prometheus metrics |

---

## 7. Lessons Learned

### What Worked Well

1. **FastAPI**: Excellent developer experience, automatic OpenAPI docs
2. **Multi-stage Docker**: Reduced image size by 60%
3. **GitHub Actions Matrix**: Parallel testing saved CI time
4. **OpenTelemetry**: Vendor-neutral tracing abstraction
5. **Grafana Stack**: Unified observability with Loki and Tempo

### Challenges

1. **OpenTelemetry Instrumentation**: Required careful configuration to avoid performance impact
2. **DAST Timing**: ZAP scans needed service warmup delay
3. **K8s Image Pull**: Required `imagePullPolicy: IfNotPresent` for local images
4. **ConfigMap Formatting**: Separate config files needed to be embedded in deployments

### Future Improvements

1. Add Helm charts for parameterized deployments
2. Implement service mesh (Istio) for advanced traffic management
3. Add integration tests in CI pipeline
4. Configure Jaeger/Zipkin for production tracing
5. Add Grafana dashboards for metrics visualization

---

## 8. Conclusion

This project demonstrates a complete DevOps implementation following industry best practices:

- **Clean Code**: Under 180 lines per service
- **Security**: SAST + DAST in CI pipeline
- **Observability**: Metrics, logs, and traces with Grafana stack
- **Automation**: Full CI/CD with zero manual steps
- **Scalability**: Kubernetes-ready with health probes and replicas

The architecture is production-ready and can be extended with additional services, databases, and integrations as requirements grow.

---

**Author**: Dridi Mohamed Aziz  
**Date**: January 2026  
**Version**: 1.0.0
