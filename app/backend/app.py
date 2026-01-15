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
