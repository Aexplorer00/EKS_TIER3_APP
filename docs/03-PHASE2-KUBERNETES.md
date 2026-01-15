# Phase 2: Kubernetes Deployment

> Step-by-step guide for deploying the 3-tier application to Kubernetes (Minikube).

---

## 📋 Prerequisites

Before starting, ensure you have:

- [x] Phase 1 completed (application working locally)
- [x] Docker Desktop running
- [x] Minikube installed (`winget install minikube`)
- [x] kubectl installed (`winget install kubectl`)
- [x] Docker Hub account (for image registry)

---

## 🎯 Phase 2 Objectives

1. Build Docker images and push to Docker Hub
2. Create Kubernetes manifests for all components
3. Deploy to Minikube cluster
4. Access and test the application

---

## Step 1: Start Minikube Cluster

```powershell
# Start minikube with Docker driver (recommended for Windows)
minikube start --driver=docker

# Verify cluster is running
minikube status

# Expected output:
# minikube
# type: Control Plane
# host: Running
# kubelet: Running
# apiserver: Running
# kubeconfig: Configured

# Verify kubectl works
kubectl cluster-info
kubectl get nodes
```

---

## Step 2: Build and Push Docker Images

### 2.1 Login to Docker Hub

```powershell
docker login
# Enter your Docker Hub username and password
```

### 2.2 Build Images

```powershell
# Navigate to project root
cd EKS-3Tier-App

# Build backend image
docker build -t YOUR_DOCKERHUB_USERNAME/eks3tier-backend:v4 ./app/backend

# Build frontend image  
docker build -t YOUR_DOCKERHUB_USERNAME/eks3tier-frontend:v1 ./app/frontend

# List images to verify
docker images | grep eks3tier
```

> [!NOTE]
> Replace `YOUR_DOCKERHUB_USERNAME` with your actual Docker Hub username (e.g., `lucky0066`)

### 2.3 Push Images to Docker Hub

```powershell
# Push backend
docker push YOUR_DOCKERHUB_USERNAME/eks3tier-backend:v4

# Push frontend
docker push YOUR_DOCKERHUB_USERNAME/eks3tier-frontend:v1
```

### 2.4 Verify on Docker Hub

Go to https://hub.docker.com and verify your images are uploaded:
- `YOUR_USERNAME/eks3tier-backend:v4`
- `YOUR_USERNAME/eks3tier-frontend:v1`

---

## Step 3: Create Kubernetes Manifests

### 3.1 Namespace (`k8s/namespace.yaml`)

```yaml
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: eks-3tier-app
```

### 3.2 Redis Deployment (`k8s/redis/deployment.yaml`)

```yaml
# Redis Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: eks-3tier-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:alpine
        ports:
        - containerPort: 6379
```

### 3.3 Redis Service (`k8s/redis/service.yaml`)

```yaml
# Redis Service
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: eks-3tier-app
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

### 3.4 Backend Deployment (`k8s/backend/deployment.yaml`)

```yaml
# Backend Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: eks-3tier-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: lucky0066/eks3tier-backend:v4
        ports:
        - containerPort: 5000
        env:
        - name: MY_REDIS_HOST
          value: redis
        - name: MY_REDIS_PORT
          value: "6379"
```

> [!IMPORTANT]
> **Critical: Use `MY_REDIS_HOST` and `MY_REDIS_PORT`**
> 
> Kubernetes automatically creates service discovery env vars like `REDIS_PORT=tcp://10.x.x.x:6379`. If your code uses `REDIS_PORT` expecting an integer, it will crash with:
> ```
> ValueError: invalid literal for int() with base 10: 'tcp://10.100.x.x:6379'
> ```
> Solution: Use a unique prefix like `MY_` to avoid collision.

### 3.5 Backend Service (`k8s/backend/service.yaml`)

```yaml
# Backend Service
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: eks-3tier-app
spec:
  selector:
    app: backend
  ports:
  - port: 5000
    targetPort: 5000
  type: ClusterIP
```

### 3.6 Frontend Deployment (`k8s/frontend/deployment.yaml`)

```yaml
# Frontend Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: eks-3tier-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: lucky0066/eks3tier-frontend:v1
        ports:
        - containerPort: 80
```

### 3.7 Frontend Service (`k8s/frontend/service.yaml`)

```yaml
# Frontend Service
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: eks-3tier-app
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: NodePort
```

### 3.8 Horizontal Pod Autoscaler (`k8s/hpa.yaml`)

```yaml
# HPA for auto-scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: eks-3tier-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Step 4: Deploy to Kubernetes

### 4.1 Apply Manifests (Order Matters!)

```powershell
# 1. Create namespace first
kubectl apply -f k8s/namespace.yaml

# 2. Deploy Redis (database layer)
kubectl apply -f k8s/redis/

# 3. Deploy Backend (depends on Redis)
kubectl apply -f k8s/backend/

# 4. Deploy Frontend (depends on Backend)
kubectl apply -f k8s/frontend/

# 5. (Optional) Apply HPA
kubectl apply -f k8s/hpa.yaml
```

### 4.2 Verify Deployment

```powershell
# Check all resources in namespace
kubectl get all -n eks-3tier-app

# Expected output:
# NAME                            READY   STATUS    RESTARTS   AGE
# pod/backend-xxxxx-xxxxx         1/1     Running   0          1m
# pod/backend-xxxxx-xxxxx         1/1     Running   0          1m
# pod/frontend-xxxxx-xxxxx        1/1     Running   0          1m
# pod/frontend-xxxxx-xxxxx        1/1     Running   0          1m
# pod/redis-xxxxx-xxxxx           1/1     Running   0          1m
#
# NAME               TYPE        CLUSTER-IP       PORT(S)
# service/backend    ClusterIP   10.100.x.x       5000/TCP
# service/frontend   NodePort    10.100.x.x       80:3xxxx/TCP
# service/redis      ClusterIP   10.100.x.x       6379/TCP
```

### 4.3 Check Pod Status

```powershell
# Watch pods come up
kubectl get pods -n eks-3tier-app -w

# Check logs if any pod has issues
kubectl logs -n eks-3tier-app deployment/backend
kubectl logs -n eks-3tier-app deployment/frontend
```

---

## Step 5: Access the Application

### 5.1 Method 1: Port Forward (Recommended for Windows)

```powershell
# Forward frontend service to local port 8080
kubectl port-forward service/frontend 8080:80 -n eks-3tier-app

# Now access: http://localhost:8080
```

> [!TIP]
> Port-forward is more reliable than `minikube service` on Windows with Docker Desktop.

### 5.2 Method 2: Minikube Service

```powershell
# Get service URL
minikube service frontend -n eks-3tier-app --url

# This opens a tunnel and provides a URL like:
# http://127.0.0.1:xxxxx
```

### 5.3 Test the Application

1. Open browser: `http://localhost:8080`
2. You should see:
   - ✅ EKS 3-Tier Application UI
   - ✅ "Backend Connected" status
   - ✅ Visit counter incrementing

### 5.4 Test Backend Directly

```powershell
# Port forward to backend for direct testing
kubectl port-forward service/backend 5000:5000 -n eks-3tier-app

# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/api/counter
curl -X POST http://localhost:5000/api/counter
```

---

## Step 6: Useful kubectl Commands

### Viewing Resources

```powershell
# List all pods with details
kubectl get pods -n eks-3tier-app -o wide

# Describe a specific pod
kubectl describe pod -n eks-3tier-app <pod-name>

# Get pod logs
kubectl logs -n eks-3tier-app <pod-name>

# Follow logs in real-time
kubectl logs -n eks-3tier-app -f deployment/backend
```

### Scaling

```powershell
# Scale backend to 3 replicas
kubectl scale deployment backend --replicas=3 -n eks-3tier-app

# Check HPA status
kubectl get hpa -n eks-3tier-app
```

### Troubleshooting

```powershell
# Get events (useful for debugging)
kubectl get events -n eks-3tier-app --sort-by='.lastTimestamp'

# Execute into a pod
kubectl exec -it -n eks-3tier-app <pod-name> -- /bin/sh

# Check service endpoints
kubectl get endpoints -n eks-3tier-app
```

---

## 🐛 Troubleshooting

### Issue 1: CrashLoopBackOff on Backend

```
STATUS: CrashLoopBackOff
```

**Debug**:
```powershell
kubectl logs -n eks-3tier-app <backend-pod-name>
```

**Common Cause**: Kubernetes service env var conflict

**Solution**: Use `MY_REDIS_HOST` and `MY_REDIS_PORT` instead of `REDIS_HOST` and `REDIS_PORT`

---

### Issue 2: ImagePullBackOff

```
STATUS: ImagePullBackOff
```

**Cause**: Kubernetes can't pull image from Docker Hub

**Solutions**:
1. Verify image name in deployment.yaml matches Docker Hub
2. Check if image is public on Docker Hub
3. Make sure you pushed the image

```powershell
# Verify image exists locally
docker images | grep eks3tier

# Push again if needed
docker push YOUR_USERNAME/eks3tier-backend:v4
```

---

### Issue 3: Service Not Accessible (Connection Refused)

**Cause**: Docker Desktop networking with Minikube

**Solution**: Use port-forward instead of minikube service

```powershell
kubectl port-forward service/frontend 8080:80 -n eks-3tier-app
```

---

### Issue 4: Backend Can't Connect to Redis

**Check Redis is running**:
```powershell
kubectl get pods -n eks-3tier-app | grep redis
```

**Test Redis connectivity from backend pod**:
```powershell
# Exec into backend pod
kubectl exec -it -n eks-3tier-app deployment/backend -- /bin/sh

# Inside the pod, test connection
python -c "import socket; s = socket.create_connection(('redis', 6379)); print('Connected!')"
```

---

## Step 7: Cleanup

```powershell
# Delete all resources in namespace
kubectl delete all --all -n eks-3tier-app

# Or delete the namespace (deletes everything in it)
kubectl delete namespace eks-3tier-app

# Stop minikube
minikube stop

# Delete minikube cluster (full reset)
minikube delete
```

---

## ✅ Phase 2 Checklist

- [x] Docker images built and tagged
- [x] Images pushed to Docker Hub
- [x] Minikube cluster running
- [x] Namespace created
- [x] Redis deployed and accessible
- [x] Backend deployed with correct env vars
- [x] Frontend deployed with NodePort
- [x] Application accessible via port-forward
- [x] All 5 pods running healthy

---

## 📊 Resource Summary

| Component | Replicas | Image | Port |
|-----------|----------|-------|------|
| Frontend | 2 | lucky0066/eks3tier-frontend:v1 | 80 |
| Backend | 2 | lucky0066/eks3tier-backend:v4 | 5000 |
| Redis | 1 | redis:alpine | 6379 |

**Total Pods**: 5

---

*Continue to [GitOps with ArgoCD](./04-GITOPS-ARGOCD.md) →*
