"""
Conflict Zero - Main FastAPI Application
Backend v2.0 (Demo Mode)
"""

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import time

from app.core.database import init_db, test_connection
from app.core.rate_limit import add_rate_limit_headers
from app.routers import (
    founder_applications,
    founder_compliance,
    api_v2,
    compare,
    auth,
    verifications,
    company,
    dashboard,
    webhooks,
    invites
)
from app.services.digital_signature_v2 import signature_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Conflict Zero API v2.0")
    
    # Test database connection
    if test_connection():
        # Initialize tables
        init_db()
    else:
        print("⚠️  Database not available - some features may not work")
    
    # Initialize signature service
    if signature_service.is_ready():
        print(f"🔐 Signature service ready (mode: {signature_service.cert_mode})")
        if signature_service.is_demo_mode():
            print("⚠️  DEMO MODE: PDFs will have watermarks")
    else:
        print("⚠️  Signature service not ready - PDF generation disabled")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Conflict Zero API")


# Create FastAPI app
app = FastAPI(
    title="Conflict Zero API",
    description="Verificación de Riesgo para Constructoras - API v2.0",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENV") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENV") != "production" else None,
    lifespan=lifespan
)

# CORS - Allow founders.czperu.com and czperu.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://czperu.com",
        "https://www.czperu.com",
        "https://founders.czperu.com",
        "http://localhost:3000",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check for Render/Docker"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "mode": signature_service.cert_mode,
        "timestamp": time.time()
    }


# Status endpoint with more detail
@app.get("/api/v2/status", tags=["Status"])
async def api_status():
    """Detailed API status"""
    return {
        "api_version": "2.0.0",
        "mode": signature_service.cert_mode,
        "signature_service": {
            "ready": signature_service.is_ready(),
            "is_demo": signature_service.is_demo_mode(),
            "cert_info": signature_service.get_cert_info()
        },
        "features": {
            "founder_applications": True,
            "founder_compliance": True,
            "public_verification": True,
            "pdf_generation": signature_service.is_ready(),
            "email_notifications": os.getenv("CERT_MODE") == "production",  # Disabled in demo
            "webhooks": True,
            "invites": True
        }
    }


# Include routers
app.include_router(founder_applications.router, prefix="/api/v2")
app.include_router(founder_compliance.router, prefix="/api/v2")
app.include_router(api_v2.router, prefix="/api/v2")
app.include_router(compare.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(verifications.router, prefix="/api/v1")
app.include_router(company.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(invites.router, prefix="/api/v2")


# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("ENV") != "production" else "Contact support"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
