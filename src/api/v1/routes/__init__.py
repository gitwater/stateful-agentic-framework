# Import all routers to make them available
from src.api.v1.routes import agents, sessions, health

__all__ = ['agents', 'sessions', 'health'] 