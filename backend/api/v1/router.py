"""
api/v1/router.py

Mounts all v1 API routes under /api/v1.
Adding a new endpoint means adding one line here.
"""

from fastapi import APIRouter
from api.v1 import chat, health

router = APIRouter(prefix="/api/v1")

router.include_router(chat.router,   tags=["chat"])
router.include_router(health.router, tags=["health"])