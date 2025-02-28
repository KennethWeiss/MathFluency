workers = 1  # For WebSocket applications, multiple workers can cause issues
worker_class = 'eventlet'  # Use eventlet worker class for WebSocket support
timeout = 300  # Increase timeout to handle long-running connections
keepalive = 65
bind = "0.0.0.0:10000"  # Adjust as needed
