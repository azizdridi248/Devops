# GitHub Issues Breakdown

This document outlines the suggested GitHub Issues for implementing the DevOps API project.

---

## Issue #1: Project Setup and Structure
**Labels:** `setup`, `priority: high`

**Description:**
Initialize project structure with folders for services, k8s manifests, CI/CD, and documentation.

**Acceptance Criteria:**
- [ ] Create folder structure
- [ ] Add .gitignore
- [ ] Initialize requirements files

---

## Issue #2: Implement API Service
**Labels:** `feature`, `backend`, `priority: high`

**Description:**
Create FastAPI REST API with health check, items CRUD endpoints, and observability.

**Acceptance Criteria:**
- [ ] GET /health endpoint
- [ ] GET /items endpoint  
- [ ] POST /items endpoint
- [ ] GET /metrics endpoint (Prometheus)
- [ ] Structured JSON logging
- [ ] OpenTelemetry tracing
- [ ] Unit tests (>80% coverage)

---

## Issue #3: Implement Worker Service
**Labels:** `feature`, `backend`, `priority: high`

**Description:**
Create FastAPI worker service for background task processing with observability.

**Acceptance Criteria:**
- [ ] GET /health endpoint
- [ ] GET /status endpoint
- [ ] POST /tasks endpoint
- [ ] GET /metrics endpoint
- [ ] Structured JSON logging
- [ ] Unit tests

---

## Issue #4: Containerization
**Labels:** `devops`, `docker`, `priority: high`

**Description:**
Create Dockerfiles for both services and docker-compose for local development.

**Acceptance Criteria:**
- [ ] Multi-stage Dockerfile for API
- [ ] Multi-stage Dockerfile for Worker
- [ ] docker-compose.yml 
- [ ] Health checks configured
- [ ] Non-root user in containers

---

## Issue #5: CI/CD Pipeline
**Labels:** `devops`, `ci-cd`, `priority: high`

**Description:**
Implement GitHub Actions workflow with testing, security scanning, and deployment.

**Acceptance Criteria:**
- [ ] Checkout, install, test stages
- [ ] Bandit SAST scan
- [ ] Docker build and push
- [ ] Kubernetes deployment
- [ ] OWASP ZAP DAST scan

---

## Issue #6: Kubernetes Deployment
**Labels:** `devops`, `kubernetes`, `priority: medium`

**Description:**
Create Kubernetes manifests for deploying both services to a local cluster.

**Acceptance Criteria:**
- [ ] API Deployment + Service
- [ ] Worker Deployment + Service
- [ ] Resource limits
- [ ] Liveness/readiness probes
- [ ] Compatible with minikube/kind

---

## Issue #7: Documentation
**Labels:** `documentation`, `priority: medium`

**Description:**
Create comprehensive documentation including README and final report.

**Acceptance Criteria:**
- [ ] README with architecture diagram
- [ ] Local run instructions
- [ ] Docker instructions
- [ ] Kubernetes instructions
- [ ] API examples with curl
- [ ] Final report
