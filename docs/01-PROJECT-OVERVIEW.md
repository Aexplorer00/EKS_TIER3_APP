# EKS 3-Tier Application - Project Overview

> A production-ready 3-tier web application designed for Kubernetes deployment with modern DevOps practices.

---

## 📋 Table of Contents

- [Project Summary](#project-summary)
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [What We Built](#what-we-built)

---

## 🎯 Project Summary

This project demonstrates a **3-tier architecture** deployed on Kubernetes, featuring:

| Tier | Component | Technology | Purpose |
|------|-----------|------------|---------|
| **Presentation** | Frontend | Nginx + HTML/CSS | Static UI, API proxy |
| **Application** | Backend | Flask + Python | REST API for business logic |
| **Data** | Database | Redis | In-memory data store (visit counter) |

### Key Learning Outcomes

1. **Containerization**: Building and optimizing Docker images
2. **Kubernetes Deployment**: Deploying multi-tier apps with K8s manifests
3. **Service Discovery**: Internal DNS resolution in Kubernetes
4. **Reverse Proxy**: Nginx configuration for API routing
5. **GitOps Ready**: ArgoCD configuration for automated deployments

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           KUBERNETES CLUSTER                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Namespace: eks-3tier-app                    │  │
│  │                                                                │  │
│  │  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐   │  │
│  │  │  FRONTEND   │      │   BACKEND   │      │    REDIS    │   │  │
│  │  │  (Nginx)    │─────▶│   (Flask)   │─────▶│  (Cache)    │   │  │
│  │  │             │      │             │      │             │   │  │
│  │  │  Port: 80   │      │  Port: 5000 │      │  Port: 6379 │   │  │
│  │  │  Replicas:2 │      │  Replicas:2 │      │  Replicas:1 │   │  │
│  │  └─────────────┘      └─────────────┘      └─────────────┘   │  │
│  │         │                    │                               │  │
│  │         ▼                    ▼                               │  │
│  │  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐   │  │
│  │  │  Service    │      │  Service    │      │  Service    │   │  │
│  │  │  ClusterIP  │      │  ClusterIP  │      │  ClusterIP  │   │  │
│  │  └─────────────┘      └─────────────┘      └─────────────┘   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                  │                                   │
│                                  ▼                                   │
│                        ┌─────────────────┐                          │
│                        │    NodePort /   │                          │
│                        │  Port-Forward   │                          │
│                        └─────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                           ┌───────────┐
                           │   USER    │
                           │  Browser  │
                           └───────────┘
```

### Traffic Flow

1. **User** → Accesses `http://localhost:8080` (via port-forward)
2. **Frontend (Nginx)** → Serves static HTML/CSS
3. **Frontend** → Proxies `/api/*` requests to Backend
4. **Backend (Flask)** → Processes API requests
5. **Backend** → Stores/retrieves data from Redis
6. **Redis** → Persists visit counter

---

## 🛠️ Technology Stack

### Application Layer

| Component | Image | Version | Size |
|-----------|-------|---------|------|
| Frontend | `nginx:alpine` | Latest | ~23MB |
| Backend | `python:3.11-slim` | 3.11 | ~120MB |
| Redis | `redis:alpine` | Latest | ~30MB |

### Container & Orchestration

| Tool | Purpose | Version Used |
|------|---------|--------------|
| Docker | Containerization | 20.x+ |
| Docker Compose | Local development | 3.8 |
| Kubernetes | Container orchestration | 1.28+ |
| Minikube | Local K8s cluster | 1.32+ |
| kubectl | K8s CLI | 1.28+ |

### CI/CD & GitOps (Planned)

| Tool | Purpose | Status |
|------|---------|--------|
| Docker Hub | Image registry | ✅ Configured |
| ArgoCD | GitOps deployments | 📋 Manifest ready |
| GitHub Actions | CI pipeline | 📋 Planned |

---

## 📁 Project Structure

```
EKS-3Tier-App/
├── 📄 README.md                    # Project overview
├── 📄 docker-compose.yml           # Local development setup
│
├── 📂 app/                         # Application source code
│   ├── 📂 frontend/
│   │   ├── 📄 Dockerfile           # Nginx container build
│   │   ├── 📄 index.html           # Main UI
│   │   ├── 📄 styles.css           # Dark theme styling
│   │   └── 📄 nginx.conf           # API proxy configuration
│   │
│   └── 📂 backend/
│       ├── 📄 Dockerfile           # Python container build
│       ├── 📄 app.py               # Flask REST API
│       └── 📄 requirements.txt     # Python dependencies
│
├── 📂 k8s/                         # Kubernetes manifests
│   ├── 📄 namespace.yaml           # eks-3tier-app namespace
│   ├── 📄 hpa.yaml                 # Horizontal Pod Autoscaler
│   ├── 📄 ingress.yaml             # ALB Ingress (for EKS)
│   │
│   ├── 📂 frontend/
│   │   ├── 📄 deployment.yaml      # Frontend pods
│   │   └── 📄 service.yaml         # Frontend service
│   │
│   ├── 📂 backend/
│   │   ├── 📄 deployment.yaml      # Backend pods
│   │   └── 📄 service.yaml         # Backend service
│   │
│   └── 📂 redis/
│       ├── 📄 deployment.yaml      # Redis pod
│       └── 📄 service.yaml         # Redis service
│
├── 📂 argocd/                      # GitOps configuration
│   └── 📄 application.yaml         # ArgoCD Application CRD
│
├── 📂 monitoring/                  # Observability
│   └── 📄 servicemonitor.yaml      # Prometheus ServiceMonitor
│
└── 📂 docs/                        # Documentation (you are here!)
    ├── 📄 01-PROJECT-OVERVIEW.md
    ├── 📄 02-PHASE1-APPLICATION.md
    ├── 📄 03-PHASE2-KUBERNETES.md
    ├── 📄 04-GITOPS-ARGOCD.md
    └── 📄 05-INTERVIEW-GUIDE.md
```

---

## ✅ What We Built

### Phase 1: Application Development ✅

- Flask backend with Redis integration for visit counting
- Nginx frontend with modern dark-themed UI
- Docker Compose setup for local development
- API proxy configuration in Nginx

### Phase 2: Kubernetes Deployment ✅

- Docker images built and pushed to Docker Hub
- Kubernetes manifests for all components
- Successfully deployed to Minikube cluster
- All 5 pods running (2 frontend + 2 backend + 1 redis)

### Future Phases (Ready but Not Deployed)

| Phase | Component | Status | Notes |
|-------|-----------|--------|-------|
| 3 | AWS EKS Deployment | 📋 Ready | Manifests prepared, skipped for cost |
| 4 | ArgoCD GitOps | 📋 Ready | Can try on Minikube |
| 5 | Prometheus/Grafana | 📋 Ready | ServiceMonitor configured |

---

## 📅 Project Timeline

| Date | Milestone | Duration |
|------|-----------|----------|
| Jan 14, 2026 | Project planning, structure setup | 2 hours |
| Jan 15, 2026 | Phase 1 complete (App + Docker) | 3 hours |
| Jan 15, 2026 | Phase 2 complete (K8s deployment) | 4 hours |
| Pending | GitOps with ArgoCD on Minikube | ~1 hour |

---

*Continue to [Phase 1: Application Development](./02-PHASE1-APPLICATION.md) →*
