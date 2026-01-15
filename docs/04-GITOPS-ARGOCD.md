# Phase 4: GitOps with ArgoCD

> Step-by-step guide for setting up GitOps deployments using ArgoCD on Minikube.

---

## 📋 Prerequisites

Before starting, ensure you have:

- [x] Phase 2 completed (K8s manifests working)
- [x] Minikube cluster running
- [x] kubectl configured
- [x] GitHub repository with your K8s manifests

---

## 🎯 What is GitOps?

GitOps is a deployment methodology where:

1. **Git is the single source of truth** for infrastructure and application configs
2. **Automated sync** between Git repo and cluster state
3. **Self-healing** - cluster drifts are automatically corrected
4. **Audit trail** - all changes tracked via Git commits

```
┌─────────────┐     Push      ┌─────────────┐     Sync      ┌─────────────┐
│  Developer  │ ────────────▶ │    GitHub   │ ────────────▶ │  ArgoCD     │
│             │              │   (Git Repo) │              │  (K8s)      │
└─────────────┘              └─────────────┘              └─────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────┐
                                                         │ Kubernetes  │
                                                         │   Cluster   │
                                                         └─────────────┘
```

---

## Step 1: Install ArgoCD on Minikube

### 1.1 Start Minikube (if not running)

```powershell
# Check if minikube is running
minikube status

# Start if not running
minikube start --driver=docker
```

### 1.2 Create ArgoCD Namespace

```powershell
kubectl create namespace argocd
```

### 1.3 Install ArgoCD

```powershell
# Install ArgoCD using official manifest
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for all pods to be ready (this may take 2-3 minutes)
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s

# Verify installation
kubectl get pods -n argocd
```

**Expected output**:
```
NAME                                               READY   STATUS    
argocd-application-controller-0                    1/1     Running   
argocd-applicationset-controller-xxx               1/1     Running   
argocd-dex-server-xxx                              1/1     Running   
argocd-notifications-controller-xxx                1/1     Running   
argocd-redis-xxx                                   1/1     Running   
argocd-repo-server-xxx                             1/1     Running   
argocd-server-xxx                                  1/1     Running   
```

---

## Step 2: Access ArgoCD UI

### 2.1 Port Forward to ArgoCD Server

```powershell
# Forward ArgoCD server to localhost
kubectl port-forward svc/argocd-server -n argocd 8443:443
```

> Keep this terminal open! ArgoCD UI will be available at **https://localhost:8443**

### 2.2 Get Initial Admin Password

```powershell
# Get the initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

Or on PowerShell with base64 decoding:
```powershell
$secret = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($secret))
```

### 2.3 Login to ArgoCD UI

1. Open browser: **https://localhost:8443**
2. Accept the self-signed certificate warning
3. Login with:
   - **Username**: `admin`
   - **Password**: (the password from Step 2.2)

---

## Step 3: Push Code to GitHub

### 3.1 Create GitHub Repository

1. Go to https://github.com/new
2. Create repository: `EKS-3Tier-App`
3. Make it **Public** (for ArgoCD to access without auth)

### 3.2 Initialize Git and Push

```powershell
cd EKS-3Tier-App

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: 3-tier app with K8s manifests"

# Add remote origin
git remote add origin https://github.com/YOUR_USERNAME/EKS-3Tier-App.git

# Push to main branch
git branch -M main
git push -u origin main
```

---

## Step 4: Create ArgoCD Application

### 4.1 Update ArgoCD Application Manifest

Edit `argocd/application.yaml` with your GitHub repo URL:

```yaml
# ArgoCD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: eks-3tier-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR_USERNAME/EKS-3Tier-App.git
    targetRevision: HEAD
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: eks-3tier-app
  syncPolicy:
    automated:
      prune: true      # Delete resources that are no longer in Git
      selfHeal: true   # Revert manual changes in cluster
    syncOptions:
    - CreateNamespace=true
```

### 4.2 Apply ArgoCD Application

```powershell
# First, make sure namespace exists
kubectl apply -f k8s/namespace.yaml

# Apply ArgoCD application
kubectl apply -f argocd/application.yaml

# Verify application was created
kubectl get applications -n argocd
```

---

## Step 5: Verify GitOps Sync

### 5.1 Check in ArgoCD UI

1. Go to https://localhost:8443
2. You should see `eks-3tier-app` application
3. Click on it to see the sync status
4. All resources should show as "Synced" and "Healthy"

### 5.2 Check via CLI

```powershell
# Get application status
kubectl get applications -n argocd eks-3tier-app -o yaml

# Or use argocd CLI (if installed)
# argocd app list
# argocd app get eks-3tier-app
```

### 5.3 Verify Pods are Running

```powershell
kubectl get pods -n eks-3tier-app

# Expected: 5 pods running (2 frontend + 2 backend + 1 redis)
```

---

## Step 6: Test GitOps in Action

### 6.1 Make a Change in Git

Let's scale the backend to 3 replicas:

```powershell
# Edit k8s/backend/deployment.yaml
# Change: replicas: 2 → replicas: 3
```

### 6.2 Commit and Push

```powershell
git add k8s/backend/deployment.yaml
git commit -m "Scale backend to 3 replicas"
git push
```

### 6.3 Watch ArgoCD Sync

1. Go to ArgoCD UI
2. Within ~3 minutes, ArgoCD will detect the change
3. It will automatically sync and scale backend to 3 pods

Or trigger manual sync:
```powershell
# Via kubectl
kubectl patch application eks-3tier-app -n argocd --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{}}}'
```

### 6.4 Verify Scaling

```powershell
kubectl get pods -n eks-3tier-app | grep backend
# Should now show 3 backend pods
```

---

## Step 7: Test Self-Healing

### 7.1 Make Manual Change in Cluster

```powershell
# Manually scale down backend (simulating drift)
kubectl scale deployment backend --replicas=1 -n eks-3tier-app

# Check pods
kubectl get pods -n eks-3tier-app | grep backend
# Shows 1 pod temporarily
```

### 7.2 Watch ArgoCD Self-Heal

With `selfHeal: true`, ArgoCD will detect the drift and restore to Git state:

```powershell
# Wait 1-2 minutes, then check again
kubectl get pods -n eks-3tier-app | grep backend
# Back to 2 (or 3) pods as defined in Git!
```

---

## ArgoCD CLI (Optional)

### Install ArgoCD CLI

```powershell
# Windows (with chocolatey)
choco install argocd-cli

# Or download from releases
# https://github.com/argoproj/argo-cd/releases
```

### CLI Commands

```powershell
# Login to ArgoCD
argocd login localhost:8443 --username admin --password <password> --insecure

# List applications
argocd app list

# Get application details
argocd app get eks-3tier-app

# Sync application manually
argocd app sync eks-3tier-app

# View application history
argocd app history eks-3tier-app
```

---

## 🐛 Troubleshooting

### Issue 1: Application stuck in "Unknown" or "Progressing"

**Cause**: ArgoCD can't access GitHub repo

**Solution**: Ensure repo is public or configure credentials
```powershell
# Check repo server logs
kubectl logs -n argocd deployment/argocd-repo-server
```

### Issue 2: Resources not syncing

**Check sync status**:
```powershell
kubectl describe application eks-3tier-app -n argocd
```

**Force sync**:
```powershell
# Delete and recreate application
kubectl delete -f argocd/application.yaml
kubectl apply -f argocd/application.yaml
```

### Issue 3: "namespace not found"

**Solution**: Add `CreateNamespace=true` to syncOptions or create namespace first
```yaml
syncOptions:
- CreateNamespace=true
```

---

## ✅ Phase 4 Checklist

- [ ] ArgoCD installed on Minikube
- [ ] ArgoCD UI accessible on localhost:8443
- [ ] Admin password retrieved and login working
- [ ] GitHub repository created and code pushed
- [ ] ArgoCD Application created
- [ ] Application synced and healthy
- [ ] GitOps tested (push change → auto deploy)
- [ ] Self-healing tested (manual change → auto revert)

---

## 📊 ArgoCD Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        ArgoCD                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   API Server   │  │  Repo Server   │  │  Application   │ │
│  │   (Web UI +    │  │ (Git Access)   │  │  Controller    │ │
│  │    REST API)   │  │                │  │  (Sync Logic)  │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
│           │                   │                   │          │
│           └───────────────────┴───────────────────┘          │
│                              │                               │
│                              ▼                               │
│                    ┌────────────────┐                       │
│                    │     Redis      │                       │
│                    │   (Caching)    │                       │
│                    └────────────────┘                       │
└──────────────────────────────────────────────────────────────┘
```

---

*Continue to [Interview Guide](./05-INTERVIEW-GUIDE.md) →*
