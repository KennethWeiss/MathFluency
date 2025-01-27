from flask_socketio import SocketIO

# Create SocketIO instance without initializing it
socketio = SocketIO(cors_allowed_origins="*")
