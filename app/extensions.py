"""Application extensions initialized via init_app pattern."""
from flask_socketio import SocketIO

socketio = SocketIO(
    async_mode="threading",
    cors_allowed_origins="*",
    ping_interval=20,
    ping_timeout=60,
)
