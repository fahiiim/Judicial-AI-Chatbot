"""API module for web interface"""
from .chat_api import app, ChatRequest, ChatResponse

__all__ = ["app", "ChatRequest", "ChatResponse"]
