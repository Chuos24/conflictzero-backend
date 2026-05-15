# app/routers/__init__.py
from .founder_applications import router as founder_applications_router
from .founder_compliance import router as founder_compliance_router
from .api_v2 import router as api_v2_router
from .compare import router as compare_router
from .auth import router as auth_router
from .admin import router as admin_router
from .network import router as network_router
from .company import router as company_router
from .dashboard import router as dashboard_router
from .invites import router as invites_router
from .ml_scoring import router as ml_scoring_router
from .monitoring import router as monitoring_router
from .notifications import router as notifications_router
from .payments import router as payments_router
from .push import router as push_router
from .verifications import router as verifications_router
from .webhooks import router as webhooks_router

__all__ = [
    "founder_applications_router",
    "founder_compliance_router",
    "api_v2_router",
    "compare_router",
    "auth_router",
    "admin_router",
    "network_router",
    "company_router",
    "dashboard_router",
    "invites_router",
    "ml_scoring_router",
    "monitoring_router",
    "notifications_router",
    "payments_router",
    "push_router",
    "verifications_router",
    "webhooks_router"
]
