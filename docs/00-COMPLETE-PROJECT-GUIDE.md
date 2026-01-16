# 🚀 EKS 3-Tier Application: Complete Project Guide

> A production-ready 3-tier web application deployed on Kubernetes with GitOps and Monitoring.

---

## 📋 Project Overview

| Aspect | Details |
|--------|---------|
| **Architecture** | 3-Tier (Frontend → Backend → Database) |
| **Frontend** | Nginx (Static files + Reverse Proxy) |
| **Backend** | Python Flask REST API |
| **Database** | Redis (In-memory cache) |
| **Orchestration** | Kubernetes (Minikube / Online Cluster) |
| **GitOps** | ArgoCD |
| **Monitoring** | Prometheus + Grafana |
| **Repository** | [GitHub - Aexplorer00/EKS_TIER3_APP](https://github.com/Aexplorer00/EKS_TIER3_APP) |

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        KUBERNETES CLUSTER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   FRONTEND   │───▶│   BACKEND    │───▶│    REDIS     │       │
│  │   (Nginx)    │    │   (Flask)    │    │  (Database)  │       │
│  │   Port: 80   │    │  Port: 5000  │    │  Port: 6379  │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────┐                                                │
│  │   INGRESS    │ ◀── External Traffic                          │
│  └──────────────┘                                                │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    MONITORING STACK                        │   │
│  │  ┌──────────────┐         ┌──────────────┐               │   │
│  │  │  PROMETHEUS  │────────▶│   GRAFANA    │               │   │
│  │  │  Port: 9090  │         │  Port: 3000  │               │   │
│  │  └──────────────┘         └──────────────┘               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────┐                                                │
│  │    ARGOCD    │ ◀── Syncs from GitHub                         │
│  │  Port: 8443  │                                                │
│  └──────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
EKS-3Tier-App/
├── app/
│   ├── backend/
│   │   ├── app.py              # Flask API
│   │   ├── Dockerfile          # Backend container
│   │   └── requirements.txt
│   └── frontend/
│       ├── index.html          # Static UI
│       ├── nginx.conf          # Reverse proxy config
│       └── Dockerfile          # Frontend container
├── k8s/
│   ├── namespace.yaml
│   ├── backend/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── frontend/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── redis/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── monitoring/
│   │   ├── 00-namespace.yaml
│   │   ├── 01-prometheus-config.yaml
│   │   ├── 02-prometheus-deployment.yaml
│   │   ├── 03-prometheus-service.yaml
│   │   ├── 04-grafana-deployment.yaml
│   │   └── 05-grafana-service.yaml
│   ├── hpa.yaml
│   └── ingress.yaml
├── argocd/
│   └── application.yaml        # GitOps config
├── docker-compose.yml          # Local development
└── docs/
    └── (documentation files)
```

---

## 🛠️ Phase 1: Application Development

### Backend (Flask API)

**File: `app/backend/app.py`**
- REST API with endpoints: `/health`, `/api/visits`, `/api/info`
- Connects to Redis using environment variables
- Increments visit counter on each request

**Key Code:**
```python
redis_client = redis.Redis(
    host=os.getenv('MY_REDIS_HOST', 'redis'),
    port=int(os.getenv('MY_REDIS_PORT', 6379))
)
```

### Frontend (Nginx)

**File: `app/frontend/nginx.conf`**
- Serves static files on `/`
- Proxies `/api` requests to backend

**Key Config:**
```nginx
location /api {
    proxy_pass http://backend:5000;
}
```

### Local Testing

```bash
docker-compose up --build
# Access: http://localhost:8080
```

---

## 🐳 Phase 2: Dockerization & Kubernetes

### Docker Images

```bash
# Build and push images
docker build -t <dockerhub>/eks3tier-backend:v4 ./app/backend
docker build -t <dockerhub>/eks3tier-frontend:v1 ./app/frontend
docker push <dockerhub>/eks3tier-backend:v4
docker push <dockerhub>/eks3tier-frontend:v1
```

### Kubernetes Deployment

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy all components
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/redis/
kubectl apply -f k8s/ingress.yaml

# Verify
kubectl get pods -n eks-3tier-app
```

### Key Kubernetes Concepts Used

| Resource | Purpose |
|----------|---------|
| **Deployment** | Manages pod replicas with rolling updates |
| **Service** | Internal load balancing and service discovery |
| **Ingress** | External HTTP routing |
| **HPA** | Auto-scaling based on CPU usage |
| **ConfigMap** | Externalized configuration |

---

## 🔄 Phase 3: GitOps with ArgoCD

### Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### Access ArgoCD UI

```bash
# Port forward
kubectl port-forward svc/argocd-server -n argocd 8443:443

# Get password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Login: https://localhost:8443 (admin / <password>)
```

### ArgoCD Application Configuration

**File: `argocd/application.yaml`**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: eks-3tier-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/Aexplorer00/EKS_TIER3_APP.git
    targetRevision: HEAD
    path: k8s
    directory:
      recurse: true  # ← Critical: Scans subdirectories
  destination:
    server: https://kubernetes.default.svc
    namespace: eks-3tier-app
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Key Learning: Recursive Directory Search
Without `directory.recurse: true`, ArgoCD only reads root-level files in `k8s/`, missing subdirectories like `k8s/backend/`.

---

## 📊 Phase 4: Monitoring Stack

### Deploy Prometheus & Grafana

```bash
kubectl apply -f k8s/monitoring/
```

### Expose Grafana (NodePort)

```bash
kubectl patch svc grafana -n monitoring -p '{"spec": {"type": "NodePort"}}'
kubectl get svc grafana -n monitoring  # Note the NodePort
```

### Access Grafana
- **URL**: `http://<NODE-IP>:<NodePort>`
- **Login**: admin / admin

### Configure Prometheus Data Source
1. Go to **Connections → Data Sources → Add → Prometheus**
2. URL: `http://prometheus-service.monitoring:9090`
3. Click **Save & Test**

---

## 🐛 Troubleshooting Encountered

### Issue 1: ArgoCD Sync Error - "Connection Refused"
**Cause**: `argocd-repo-server` pod was crash-looping after cluster restart.
**Solution**: 
```bash
kubectl rollout restart deployment argocd-repo-server -n argocd
kubectl rollout restart deployment argocd-redis -n argocd
```

### Issue 2: Minikube Network Timeouts
**Cause**: Local Docker/Minikube resource constraints.
**Solution**: Migrated to online cluster (KillerCoda/O'Reilly).

### Issue 3: ArgoCD Only Syncing Partial Resources
**Cause**: Missing `directory.recurse: true` in application.yaml.
**Solution**: Added recursive flag to scan all subdirectories.

### Issue 4: Redis Environment Variable Conflict
**Cause**: Kubernetes auto-generates `REDIS_PORT` as TCP string, conflicting with Python expecting integer.
**Solution**: Used custom prefix `MY_REDIS_HOST` and `MY_REDIS_PORT`.

---

## 🎤 Interview Talking Points

### "Describe the project architecture"
> "I built a 3-tier web application with a Flask REST API backend, Nginx frontend serving static files and acting as a reverse proxy, and Redis for session caching. Everything runs on Kubernetes with 2 replicas for high availability."

### "Why Kubernetes over Docker Compose?"
> "Docker Compose is great for local development, but Kubernetes provides self-healing (automatic pod restarts), horizontal scaling (HPA), service discovery via internal DNS, and rolling updates for zero-downtime deployments."

### "Explain your GitOps implementation"
> "I used ArgoCD to implement GitOps. The cluster state is defined in Git, and ArgoCD continuously monitors the repository. Any change pushed to GitHub is automatically deployed to the cluster within seconds. This provides audit trails, easy rollbacks, and eliminates manual kubectl commands."

### "How does monitoring work?"
> "Prometheus scrapes metrics from Kubernetes components and my application. Grafana visualizes these metrics in dashboards. This gives me visibility into CPU/memory usage, request rates, and error counts—essential for SRE practices."

### "What was the most challenging issue?"
> "The ArgoCD 'partial sync' issue where only some resources were deployed. I debugged by checking the Application status in the UI and discovered it wasn't recursively scanning subdirectories. Adding `directory.recurse: true` fixed it—a good lesson in reading the docs carefully."

---

## 🏆 Skills Demonstrated

- **Containerization**: Docker multi-stage builds, image optimization
- **Kubernetes**: Deployments, Services, Ingress, HPA, ConfigMaps
- **GitOps**: ArgoCD, declarative infrastructure, auto-sync
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Troubleshooting**: Debugging pod crashes, network issues, manifest errors
- **Cloud Migration**: Moving from local Minikube to online clusters

---

## 📚 Quick Reference Commands

```bash
# --- Deployment ---
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/backend/ -f k8s/frontend/ -f k8s/redis/
kubectl apply -f k8s/monitoring/

# --- Verification ---
kubectl get pods -A
kubectl get svc -A
kubectl logs <pod-name> -n <namespace>

# --- ArgoCD ---
kubectl port-forward svc/argocd-server -n argocd 8443:443

# --- Monitoring ---
kubectl patch svc grafana -n monitoring -p '{"spec": {"type": "NodePort"}}'
kubectl get svc grafana -n monitoring

# --- Debugging ---
kubectl describe pod <pod-name> -n <namespace>
kubectl rollout restart deployment <name> -n <namespace>
```

---

## ✅ Project Completion Checklist

- [x] Application Development (Flask + Nginx + Redis)
- [x] Dockerization with multi-stage builds
- [x] Local testing with Docker Compose
- [x] Kubernetes manifests (Deployment, Service, Ingress, HPA)
- [x] GitOps setup with ArgoCD
- [x] Monitoring with Prometheus & Grafana
- [x] Successful deployment on online cluster
- [x] Project documentation

---

**Congratulations! You have completed a production-grade DevOps/SRE project!** 🎉
