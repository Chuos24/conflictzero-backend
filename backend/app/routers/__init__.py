# app/routers/__init__.py
from .founder_applications import router as founder_applications_router
from .founder_compliance import router as founder_compliance_router
from .api_v2 import router as api_v2_router
from .compare import router as compare_router
from .auth import router as auth_router

__all__ = [
    "founder_applications_router",
    "founder_compliance_router",
    "api_v2_router",
    "compare_router",
    "auth_router"
]
