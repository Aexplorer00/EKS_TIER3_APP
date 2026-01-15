# EKS 3-Tier Application

A production-ready 3-tier web application deployed on Kubernetes with monitoring and GitOps.

---

## 🏗️ Architecture

![EKS 3-Tier Architecture](./architecture.png)

---

## 📦 Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Nginx + HTML/CSS | Static UI, API proxy |
| Backend | Flask + Gunicorn | REST API |
| Database | Redis | Visit counter storage |
| Container | Docker | Containerization |
| Orchestration | Kubernetes | Container orchestration |
| Registry | Docker Hub | Image storage |

---

## 📁 Project Structure

```
EKS-3Tier-App/
├── app/
│   ├── frontend/
│   │   ├── Dockerfile
│   │   ├── index.html
│   │   ├── styles.css
│   │   └── nginx.conf       # API proxy config
│   └── backend/
│       ├── Dockerfile
│       ├── app.py
│       └── requirements.txt
├── k8s/
│   ├── namespace.yaml
│   ├── frontend/
│   ├── backend/
│   ├── redis/
│   ├── hpa.yaml
│   └── ingress.yaml
├── monitoring/
│   └── servicemonitor.yaml
├── argocd/
│   └── application.yaml
├── docker-compose.yml
└── README.md
```

---

## ✅ What We Accomplished

### Phase 1: Application Code ✅
- [x] Created Flask backend with Redis integration
- [x] Created Nginx frontend with modern dark UI
- [x] Configured nginx.conf for API proxying
- [x] Tested locally with docker-compose

### Phase 2: Kubernetes Deployment ✅
- [x] Built Docker images (v4)
- [x] Pushed to Docker Hub (lucky0066/eks3tier-*)
- [x] Created K8s manifests (deployments, services)
- [x] Deployed to Minikube successfully
- [x] All 5 pods running!

### Phase 3 & 4: Pending
- [ ] Deploy to AWS EKS (optional, costs $$$)
- [ ] Install ArgoCD for GitOps
- [ ] Add Prometheus + Grafana monitoring

---

## 🐛 Issues Encountered & Solutions

### Issue 1: Backend Unavailable (Frontend → Backend)
```
Problem: Frontend couldn't reach backend API
Root Cause: No proxy configuration in Nginx
Solution: Added nginx.conf to proxy /api → backend:5000
```

### Issue 2: CrashLoopBackOff
```
Problem: Backend pods kept crashing
Root Cause: Kubernetes auto-creates REDIS_PORT env var 
           as "tcp://10.100.x.x:6379" which conflicted with our code
           
Error: ValueError: invalid literal for int() with base 10: 'tcp://...'

Solution: Renamed env vars to MY_REDIS_HOST and MY_REDIS_PORT
```

### Issue 3: Minikube Service Not Accessible
```
Problem: minikube service gave port but connection refused
Root Cause: Docker Desktop networking conflicts
Solution: Used kubectl port-forward instead
```

---

## 🚀 Quick Start

### Local Development (docker-compose)
```bash
cd EKS-3Tier-App
docker-compose up --build
# Access: http://localhost:80
```

### Kubernetes (Minikube)
```bash
# Start minikube
minikube start --driver=docker

# Deploy
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/redis/
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/

# Access
kubectl port-forward service/frontend 8080:80 -n eks-3tier-app
# Open: http://localhost:8080
```

---

## 🔑 Key Learnings

1. **K8s auto-creates env vars** for services (SERVICE_NAME_PORT)
2. **Nginx proxy** is needed for frontend to reach backend
3. **kubectl port-forward** is more reliable than minikube service on Windows
4. **Docker images** must be rebuilt and pushed after code changes

---

## 📊 Resume Bullets

After completing this project, use these on your resume:

- Deployed 3-tier application on Kubernetes with **HPA scaling 2-10 pods**
- Built CI/CD pipeline with **Docker Hub** for containerized deployments
- Configured **Nginx reverse proxy** for frontend-backend communication
- Implemented **Redis caching layer** with Kubernetes persistent services

---

## 📅 Timeline

| Date | Milestone |
|------|-----------|
| Jan 14 | Project structure, implementation plan |
| Jan 15 | Phase 1 complete, Phase 2 complete |
| Pending | ArgoCD, Monitoring |

---

*Built as part of SRE/DevOps Learning Journey*
