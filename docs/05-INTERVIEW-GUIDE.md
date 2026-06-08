# 🎓 DevOps & SRE Interview Guide: EKS 3-Tier Application

> **Project Pitch**: "I designed and deployed a resilient 3-tier web application on Kubernetes using GitOps principles. It features a Flask REST API, Nginx frontend, and Redis caching layer, all automated via ArgoCD for zero-touch deployments."

---

## 🧠 Architectural Decisions: "The Why & How"

### 1. Why a 3-Tier Architecture?
**Context**: Most enterprise apps follow this pattern (Presentation, Logic, Data).
- **Efficiency**: Decoupling tiers allows independent scaling. If the backend is CPU-heavy, I can scale it to 10 replicas while keeping Redis at 1 replica.
- **Security**: The "Database" (Redis) is isolated in a private network, accessible only by the Backend, never the Frontend or public internet.

### 2. Why Kubernetes (Minikube/EKS) over Docker Compose?
- **Docker Compose** is great for *local development* (fast iteration), but it lacks self-healing and zero-downtime capabilities.
- **Kubernetes** provides:
    - **Self-Healing**: If a backend pod crashes, K8s restarts it instantly (CrashLoopBackOff handling).
    - **Service Discovery**: I don't need to hardcode IPs; I just use `http://backend` and K8s internal DNS handles the rest.
    - **Load Balancing**: The K8s Service automatically distributes traffic across all 3 backend replicas.

### 3. Why GitOps with ArgoCD?
**The "Efficiency" Winner.** 🏆
- **Traditional Way**: `kubectl apply -f deployment.yaml` (Manual, error-prone, no history).
- **GitOps Way**: "Git is the source of truth."
    - **Efficiency**: I push code to GitHub -> ArgoCD sees the change -> Updates cluster automatically in seconds.
    - **Security**: No need to give developers `kubectl` admin access. Access is controlled via Git permissions.
    - **Disaster Recovery**: If the cluster dies, I just point ArgoCD to the repo, and the entire infrastructure is rebuilt in minutes.

### 4. Why Nginx as a Reverse Proxy?
- **Problem**: Browsers block requests from Frontend (`localhost:80`) to Backend (`localhost:5000`) due to **CORS** (Cross-Origin Resource Sharing).
- **Solution**: Nginx sits in front.
    - User hits `/` -> Nginx serves Static Files (Line 6 in nginx.conf)
    - User hits `/api` -> Nginx proxies to Backend (Line 12 in nginx.conf)
- **Efficiency**: Nginx handles thousands of static file connections much faster than Python/Flask, freeing up the backend for actual logic.

### 5. Why Redis for Caching?
- **Performance**: Reading from memory (Redis) is microsecond-fast compared to recalculating data or querying a disk-based DB (Postgres/MySQL).
- **State Management**: Flask apps are "stateless" (so we can scale them). We need shared state (the visit counter) stored externally in Redis so all pods see the same number.

---

## 🎤 Interview Questions & Answers

### Q: "How did you handle configuration management?"
**A:** "I used **Environment Variables** for 12-Factor App compliance. For example, the backend doesn't hardcode the Redis host. It reads `MY_REDIS_HOST`. This allows the same container image to run in Dev, Staging, and Prod just by changing the K8s manifest values."

### Q: "How do you ensure zero downtime deployment?"
**A:** "Kubernetes **Rolling Updates** (default strategy). When ArgoCD syncs a new image version, K8s brings up new pods one by one and only kills old ones when the new ones pass their **Readiness Probes**."

### Q: "What was the most challenging technical hurdle?"
**A:** "Kubernetes Service Environment Variable conflicts. When I named my service `redis`, K8s injected `REDIS_PORT` as a TCP string (tcp://10.x.x.x:6379), which crashed my Python app expecting an integer. I solved this by using a custom env prefix `MY_REDIS_HOST` to avoid collisions with K8s auto-generated vars."

### Q: "Why is your image size so small?"
**A:** "I used **Multi-Stage Builds** and **Alpine/Slim** base images.
- Backend: `python:3.11-slim` (Removed build tools, kept only runtime).
- Frontend: `nginx:alpine` (Very lightweight, ~20MB).
- This reduces attack surface and speeds up deployment (faster `docker pull`)."

---

## 🚀 Scenario: "The Cluster Just Crashed. What do you do?"
1. **Diagnosis**: Check `kubectl get nodes` (Is node Ready?) and `kubectl get pods -A` (System pods running?).
2. **Recovery**: Since we use **GitOps**, I don't need to manually restore deployments. I ensure the cluster connectivity is back, and ArgoCD will automatically reconcile the state to match the GitHub repo.

