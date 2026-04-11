"""
Conflict Zero - Rate Limiting Middleware
Rate limiting por plan mensual y por minuto
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import hashlib

from app.core.database import get_db
from app.core.security import RateLimiter
from app.models_v2 import Company, ApiKey

security = HTTPBearer(auto_error=False)


class MonthlyRateLimiter:
    """
    Rate limiting mensual por plan de empresa.
    Almacena contadores en memoria (para producción usar Redis).
    """
    
    # Límites por plan tier
    PLAN_LIMITS = {
        "bronze": 1000,
        "silver": 5000,
        "gold": 100000,
        "founder": float('inf')  # Ilimitado
    }
    
    # Contadores en memoria: {company_id: {"count": int, "reset_at": datetime}}
    _counters = {}
    
    @classmethod
    def get_limit(cls, plan_tier: str) -> int:
        """Obtiene el límite mensual para un plan"""
        return cls.PLAN_LIMITS.get(plan_tier, 1000)
    
    @classmethod
    def is_allowed(cls, company_id: str, plan_tier: str) -> tuple[bool, dict]:
        """
        Verifica si la empresa puede hacer una request.
        Retorna: (permitido, info_dict)
        """
        limit = cls.get_limit(plan_tier)
        
        # Founders tienen acceso ilimitado
        if plan_tier == "founder":
            return True, {
                "limit": "unlimited",
                "used": cls._counters.get(company_id, {}).get("count", 0),
                "remaining": "unlimited"
            }
        
        now = datetime.utcnow()
        
        # Inicializar o resetear contador si es necesario
        if company_id not in cls._counters:
            cls._counters[company_id] = {
                "count": 0,
                "reset_at": now + timedelta(days=30)
            }
        
        counter = cls._counters[company_id]
        
        # Resetear si pasó el período
        if now >= counter["reset_at"]:
            counter["count"] = 0
            counter["reset_at"] = now + timedelta(days=30)
        
        # Verificar límite
        if counter["count"] >= limit:
            return False, {
                "limit": limit,
                "used": counter["count"],
                "remaining": 0,
                "reset_at": counter["reset_at"].isoformat()
            }
        
        # Incrementar contador
        counter["count"] += 1
        
        return True, {
            "limit": limit,
            "used": counter["count"],
            "remaining": limit - counter["count"],
            "reset_at": counter["reset_at"].isoformat()
        }
    
    @classmethod
    def increment(cls, company_id: str) -> dict:
        """Incrementa el contador y retorna info actualizada"""
        now = datetime.utcnow()
        
        if company_id not in cls._counters:
            cls._counters[company_id] = {
                "count": 1,
                "reset_at": now + timedelta(days=30)
            }
        else:
            cls._counters[company_id]["count"] += 1
        
        return cls._counters[company_id]
    
    @classmethod
    def get_usage(cls, company_id: str, plan_tier: str) -> dict:
        """Obtiene el uso actual sin incrementar"""
        limit = cls.get_limit(plan_tier)
        counter = cls._counters.get(company_id, {"count": 0})
        
        if plan_tier == "founder":
            return {
                "plan": plan_tier,
                "limit": "unlimited",
                "used": counter.get("count", 0),
                "remaining": "unlimited"
            }
        
        return {
            "plan": plan_tier,
            "limit": limit,
            "used": counter.get("count", 0),
            "remaining": max(0, limit - counter.get("count", 0))
        }


class PlanRateLimitMiddleware:
    """
    Middleware para rate limiting basado en plan.
    Se aplica a endpoints específicos que consumen cuota mensual.
    """
    
    # Endpoints que consumen cuota mensual
    QUOTA_ENDPOINTS = [
        "/api/v1/verify",
        "/api/v1/compare",
        "/api/v2/verify",
    ]
    
    @classmethod
    def should_check_quota(cls, path: str) -> bool:
        """Determina si el endpoint debe verificar cuota mensual"""
        for endpoint in cls.QUOTA_ENDPOINTS:
            if path.startswith(endpoint):
                return True
        return False
    
    @classmethod
    async def check_and_apply(
        cls,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
    ) -> Optional[Company]:
        """
        Verifica rate limiting y autentica.
        Retorna la empresa si todo está OK.
        """
        # Si no es endpoint de cuota, solo autenticar
        if not cls.should_check_quota(request.url.path):
            return await cls._authenticate(credentials, db)
        
        # Autenticar
        company = await cls._authenticate(credentials, db)
        
        # Verificar cuota mensual
        allowed, info = MonthlyRateLimiter.is_allowed(
            str(company.id),
            company.plan_tier
        )
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Monthly quota exceeded",
                    "message": f"Has excedido tu límite mensual de {info['limit']} verificaciones",
                    "usage": info,
                    "upgrade_url": "/settings/upgrade"
                }
            )
        
        # Agregar headers de rate limit a la respuesta
        request.state.rate_limit_info = info
        
        return company
    
    @staticmethod
    async def _authenticate(
        credentials: HTTPAuthorizationCredentials,
        db: Session
    ) -> Company:
        """Autentica usuario por JWT o API Key"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication provided",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = credentials.credentials
        from app.core.security import decode_token
        
        # Intentar JWT
        payload = decode_token(token)
        if payload:
            from jose import jwt
            from app.core.security import SECRET_KEY, ALGORITHM
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                company_id = payload.get("sub")
                if company_id:
                    company = db.query(Company).filter(
                        Company.id == company_id,
                        Company.deleted_at.is_(None)
                    ).first()
                    if company:
                        return company
            except:
                pass
        
        # Intentar API Key
        if token.startswith("cz_live_"):
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            api_key = db.query(ApiKey).filter(
                ApiKey.key_hash == token_hash,
                ApiKey.is_active == True,
                ApiKey.deleted_at.is_(None)
            ).first()
            
            if api_key:
                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="API key expired"
                    )
                
                company = db.query(Company).filter(
                    Company.id == api_key.company_id,
                    Company.deleted_at.is_(None)
                ).first()
                
                if company:
                    return company
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


# Dependencia para usar en routers
async def rate_limited_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Company:
    """
    Dependencia que aplica rate limiting mensual basado en plan.
    Usar en endpoints que consumen cuota.
    """
    return await PlanRateLimitMiddleware.check_and_apply(request, credentials, db)


def add_rate_limit_headers(response, info: dict):
    """Agrega headers de rate limit a la respuesta"""
    if info.get("limit") == "unlimited":
        response.headers["X-RateLimit-Limit"] = "unlimited"
        response.headers["X-RateLimit-Remaining"] = "unlimited"
    else:
        response.headers["X-RateLimit-Limit"] = str(info.get("limit", ""))
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", ""))
        if info.get("reset_at"):
            response.headers["X-RateLimit-Reset"] = info["reset_at"]
