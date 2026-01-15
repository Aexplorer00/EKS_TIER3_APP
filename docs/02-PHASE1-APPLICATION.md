# Phase 1: Application Development

> Step-by-step guide for building the 3-tier application with Flask, Nginx, and Redis.

---

## 📋 Prerequisites

Before starting, ensure you have:

- [x] Docker Desktop installed and running
- [x] Git installed
- [x] Text editor (VS Code recommended)
- [x] Basic understanding of Python and HTML

---

## 🎯 Phase 1 Objectives

1. Create Flask backend with Redis integration
2. Create Nginx frontend with modern UI
3. Configure Nginx to proxy API requests
4. Test locally with Docker Compose

---

## Step 1: Project Structure Setup

Create the project directory structure:

```powershell
# Create project folder
mkdir EKS-3Tier-App
cd EKS-3Tier-App

# Create app directories
mkdir -p app/frontend
mkdir -p app/backend
mkdir -p k8s/frontend
mkdir -p k8s/backend
mkdir -p k8s/redis
mkdir argocd
mkdir monitoring
mkdir docs
```

---

## Step 2: Backend Development (Flask API)

### 2.1 Create `app/backend/requirements.txt`

```txt
flask==3.0.0
flask-cors==4.0.0
redis==5.0.1
gunicorn==21.2.0
```

### 2.2 Create `app/backend/app.py`

```python
"""
EKS 3-Tier App - Flask Backend API
Connects to Redis for visit counter
"""

from flask import Flask, jsonify
from flask_cors import CORS
import redis
import os

app = Flask(__name__)
CORS(app)

# Redis connection - use MY_ prefix to avoid K8s service env var conflict
REDIS_HOST = os.environ.get('MY_REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('MY_REDIS_PORT', 6379))

def get_redis_client():
    """Get Redis client with retry logic"""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping()  # Test connection
        return client
    except redis.ConnectionError:
        return None

# Health check endpoint
@app.route('/health')
def health():
    """Health check for Kubernetes probes"""
    redis_client = get_redis_client()
    if redis_client:
        return jsonify({'status': 'healthy', 'redis': 'connected'}), 200
    return jsonify({'status': 'degraded', 'redis': 'disconnected'}), 200

# Root endpoint
@app.route('/')
def home():
    return jsonify({
        'app': 'EKS 3-Tier Backend',
        'version': '1.0.0',
        'endpoints': ['/health', '/api/counter']
    })

# Get counter value
@app.route('/api/counter', methods=['GET'])
def get_counter():
    """Get current visit count"""
    redis_client = get_redis_client()
    if redis_client:
        count = redis_client.get('visit_count') or 0
        return jsonify({'count': int(count)})
    return jsonify({'count': 0, 'error': 'Redis unavailable'})

# Increment counter
@app.route('/api/counter', methods=['POST'])
def increment_counter():
    """Increment visit count by 1"""
    redis_client = get_redis_client()
    if redis_client:
        count = redis_client.incr('visit_count')
        return jsonify({'count': count, 'message': 'Counter incremented'})
    return jsonify({'count': 0, 'error': 'Redis unavailable'})

# Info endpoint for debugging
@app.route('/api/info')
def info():
    """System info for debugging"""
    import socket
    return jsonify({
        'hostname': socket.gethostname(),
        'redis_host': REDIS_HOST,
        'redis_port': REDIS_PORT
    })

if __name__ == '__main__':
    print(f"Starting Flask app... Redis: {REDIS_HOST}:{REDIS_PORT}")
    app.run(host='0.0.0.0', port=5000, debug=True)
```

> [!IMPORTANT]
> **Why `MY_REDIS_HOST` instead of `REDIS_HOST`?**
> 
> Kubernetes automatically creates environment variables for services. When you create a service named `redis`, K8s auto-creates `REDIS_PORT=tcp://10.x.x.x:6379`. This conflicts with our integer port variable. Using `MY_` prefix avoids this collision.

### 2.3 Create `app/backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Expose port
EXPOSE 5000

# Run Flask directly (for debugging)
CMD ["python", "app.py"]
```

---

## Step 3: Frontend Development (Nginx)

### 3.1 Create `app/frontend/index.html`

```html
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EKS 3-Tier App</title>
    <link rel="stylesheet" href="styles.css">
</head>

<body>
    <div class="container">
        <header>
            <h1>🚀 EKS 3-Tier Application</h1>
            <p>A production-ready app deployed on AWS EKS</p>
        </header>

        <main>
            <section class="status-card">
                <h2>System Status</h2>
                <div id="status">
                    <p>Checking connection...</p>
                </div>
            </section>

            <section class="features">
                <h2>Architecture</h2>
                <div class="tier-grid">
                    <div class="tier">
                        <h3>🌐 Frontend</h3>
                        <p>Nginx (This page)</p>
                    </div>
                    <div class="tier">
                        <h3>⚙️ Backend</h3>
                        <p>Flask API</p>
                    </div>
                    <div class="tier">
                        <h3>💾 Database</h3>
                        <p>Redis Cache</p>
                    </div>
                </div>
            </section>

            <section class="counter-section">
                <h2>Visit Counter</h2>
                <div id="counter-display">
                    <span id="counter">--</span>
                    <p>Total Visits</p>
                </div>
                <button id="refresh-btn">Refresh Count</button>
            </section>
        </main>

        <footer>
            <p>Built for SRE Portfolio | Deployed on AWS EKS</p>
        </footer>
    </div>

    <script>
        const API_URL = '/api';

        async function getCounter() {
            try {
                const response = await fetch(`${API_URL}/counter`);
                const data = await response.json();
                document.getElementById('counter').textContent = data.count;
                document.getElementById('status').innerHTML =
                    '<p class="success">✅ Backend Connected</p>';
            } catch (error) {
                document.getElementById('status').innerHTML =
                    '<p class="error">❌ Backend Unavailable</p>';
                console.error('Error:', error);
            }
        }

        async function incrementCounter() {
            try {
                const response = await fetch(`${API_URL}/counter`, { method: 'POST' });
                const data = await response.json();
                document.getElementById('counter').textContent = data.count;
            } catch (error) {
                console.error('Error:', error);
            }
        }

        // Load on page load
        window.onload = () => {
            incrementCounter();
        };

        document.getElementById('refresh-btn').addEventListener('click', getCounter);
    </script>
</body>

</html>
```

### 3.2 Create `app/frontend/styles.css`

```css
/* Modern Dark Theme for EKS 3-Tier App */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #eee;
    min-height: 100vh;
}

.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
}

header {
    text-align: center;
    margin-bottom: 3rem;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    background: linear-gradient(90deg, #00d9ff, #00ff88);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

header p {
    color: #888;
    font-size: 1.1rem;
}

.status-card, .features, .counter-section {
    background: rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    border: 1px solid rgba(255,255,255,0.1);
}

h2 {
    margin-bottom: 1.5rem;
    color: #00d9ff;
}

.tier-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
}

.tier {
    background: rgba(0,217,255,0.1);
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
}

.tier h3 {
    font-size: 1.2rem;
    margin-bottom: 0.5rem;
}

.counter-section {
    text-align: center;
}

#counter {
    font-size: 4rem;
    font-weight: bold;
    color: #00ff88;
    display: block;
}

button {
    background: linear-gradient(90deg, #00d9ff, #00ff88);
    border: none;
    padding: 1rem 2rem;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    color: #1a1a2e;
    font-weight: 600;
    margin-top: 1rem;
    transition: transform 0.2s;
}

button:hover {
    transform: scale(1.05);
}

.success { color: #00ff88; }
.error { color: #ff6b6b; }

footer {
    text-align: center;
    color: #666;
    margin-top: 3rem;
}
```

### 3.3 Create `app/frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;

    # Serve static files
    location / {
        root /usr/share/nginx/html;
        index index.html;
    }

    # Proxy API requests to backend
    location /api {
        proxy_pass http://backend:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

> [!NOTE]
> **Why Nginx proxy?**
> 
> The frontend JavaScript runs in the browser and needs to make API calls. Without the proxy, browser would block cross-origin requests (CORS). Nginx proxies `/api/*` to the backend, making it appear as same-origin.

### 3.4 Create `app/frontend/Dockerfile`

```dockerfile
FROM nginx:alpine

# Copy custom HTML
COPY index.html /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/

# Copy custom nginx config for API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## Step 4: Docker Compose Setup

### 4.1 Create `docker-compose.yml`

```yaml
version: '3.8'

services:
  # Frontend - Nginx serving static files
  frontend:
    build: ./app/frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - app-network

  # Backend - Flask API
  backend:
    build: ./app/backend
    ports:
      - "5000:5000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
    networks:
      - app-network

  # Database - Redis
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

---

## Step 5: Local Testing

### 5.1 Build and Run

```powershell
# Navigate to project root
cd EKS-3Tier-App

# Build and start all services
docker-compose up --build

# Expected output:
# Creating network "eks-3tier-app_app-network" with driver "bridge"
# Building backend...
# Building frontend...
# Starting redis_1    ... done
# Starting backend_1  ... done
# Starting frontend_1 ... done
```

### 5.2 Test the Application

Open browser and go to: **http://localhost**

You should see:
- ✅ EKS 3-Tier Application header
- ✅ "Backend Connected" status
- ✅ Visit counter incrementing on each refresh

### 5.3 Test API Directly

```powershell
# Health check
curl http://localhost:5000/health
# Expected: {"redis":"connected","status":"healthy"}

# Get counter
curl http://localhost/api/counter
# Expected: {"count": 1}

# Increment counter
curl -X POST http://localhost/api/counter
# Expected: {"count": 2, "message": "Counter incremented"}
```

### 5.4 Stop Services

```powershell
# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

---

## 🐛 Troubleshooting

### Issue: Backend can't connect to Redis

```
Error: redis.exceptions.ConnectionError
```

**Solution**: Ensure Redis container is running:
```powershell
docker ps | grep redis
docker logs redis
```

### Issue: Frontend shows "Backend Unavailable"

**Possible causes**:
1. Backend not running - check `docker ps`
2. Nginx proxy misconfigured - verify `nginx.conf`
3. CORS issues - verify Flask-CORS is installed

**Debug**:
```powershell
# Check backend logs
docker logs eks-3tier-app_backend_1

# Test backend directly
curl http://localhost:5000/health
```

---

## ✅ Phase 1 Checklist

- [x] Flask backend with health check and counter APIs
- [x] Redis integration for data persistence
- [x] Nginx frontend with dark theme UI
- [x] Nginx proxy configuration for API routing
- [x] Docker Compose for local development
- [x] All services communicating correctly

---

*Continue to [Phase 2: Kubernetes Deployment](./03-PHASE2-KUBERNETES.md) →*
