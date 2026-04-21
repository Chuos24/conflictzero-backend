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


class PublicRateLimiter:
    """
    Rate limiting por IP para endpoints públicos.
    Usa contadores en memoria (para producción: Redis).
    """

    # Configuración por defecto: 10 requests por hora por IP
    DEFAULT_HOURLY_LIMIT = 10
    DEFAULT_DAILY_LIMIT = 50

    # Contadores: {ip_hash: {"hourly": int, "daily": int, "hour_reset": datetime, "day_reset": datetime}}
    _counters = {}

    @classmethod
    def _get_client_ip(cls, request: Request) -> str:
        """Obtiene la IP real del cliente considerando proxies"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"

    @classmethod
    def _hash_ip(cls, ip: str) -> str:
        """Hashea la IP para privacidad"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    @classmethod
    def is_allowed(cls, request: Request) -> tuple[bool, dict]:
        """
        Verifica si la IP puede hacer una request pública.
        Retorna: (permitido, info_dict)
        """
        ip = cls._get_client_ip(request)
        ip_hash = cls._hash_ip(ip)
        now = datetime.utcnow()

        if ip_hash not in cls._counters:
            cls._counters[ip_hash] = {
                "hourly": 0,
                "daily": 0,
                "hour_reset": now + timedelta(hours=1),
                "day_reset": now + timedelta(days=1)
            }

        counter = cls._counters[ip_hash]

        # Resetear si pasó el período
        if now >= counter["hour_reset"]:
            counter["hourly"] = 0
            counter["hour_reset"] = now + timedelta(hours=1)

        if now >= counter["day_reset"]:
            counter["daily"] = 0
            counter["day_reset"] = now + timedelta(days=1)

        # Verificar límites
        if counter["hourly"] >= cls.DEFAULT_HOURLY_LIMIT:
            return False, {
                "limit_type": "hourly",
                "hourly_limit": cls.DEFAULT_HOURLY_LIMIT,
                "hourly_used": counter["hourly"],
                "daily_limit": cls.DEFAULT_DAILY_LIMIT,
                "daily_used": counter["daily"],
                "hour_reset_at": counter["hour_reset"].isoformat(),
                "day_reset_at": counter["day_reset"].isoformat(),
                "message": "Límite horario excedido. Regístrate para consultas ilimitadas."
            }

        if counter["daily"] >= cls.DEFAULT_DAILY_LIMIT:
            return False, {
                "limit_type": "daily",
                "hourly_limit": cls.DEFAULT_HOURLY_LIMIT,
                "hourly_used": counter["hourly"],
                "daily_limit": cls.DEFAULT_DAILY_LIMIT,
                "daily_used": counter["daily"],
                "hour_reset_at": counter["hour_reset"].isoformat(),
                "day_reset_at": counter["day_reset"].isoformat(),
                "message": "Límite diario excedido. Regístrate para consultas ilimitadas."
            }

        # Incrementar contadores
        counter["hourly"] += 1
        counter["daily"] += 1

        return True, {
            "hourly_limit": cls.DEFAULT_HOURLY_LIMIT,
            "hourly_used": counter["hourly"],
            "hourly_remaining": cls.DEFAULT_HOURLY_LIMIT - counter["hourly"],
            "daily_limit": cls.DEFAULT_DAILY_LIMIT,
            "daily_used": counter["daily"],
            "daily_remaining": cls.DEFAULT_DAILY_LIMIT - counter["daily"],
            "hour_reset_at": counter["hour_reset"].isoformat(),
            "day_reset_at": counter["day_reset"].isoformat()
        }

    @classmethod
    def get_usage(cls, request: Request) -> dict:
        """Obtiene uso actual sin incrementar"""
        ip = cls._get_client_ip(request)
        ip_hash = cls._hash_ip(ip)
        counter = cls._counters.get(ip_hash, {
            "hourly": 0,
            "daily": 0,
            "hour_reset": datetime.utcnow() + timedelta(hours=1),
            "day_reset": datetime.utcnow() + timedelta(days=1)
        })
        return {
            "hourly_limit": cls.DEFAULT_HOURLY_LIMIT,
            "hourly_used": counter["hourly"],
            "hourly_remaining": max(0, cls.DEFAULT_HOURLY_LIMIT - counter["hourly"]),
            "daily_limit": cls.DEFAULT_DAILY_LIMIT,
            "daily_used": counter["daily"],
            "daily_remaining": max(0, cls.DEFAULT_DAILY_LIMIT - counter["daily"]),
            "hour_reset_at": counter["hour_reset"].isoformat() if isinstance(counter["hour_reset"], datetime) else counter["hour_reset"],
            "day_reset_at": counter["day_reset"].isoformat() if isinstance(counter["day_reset"], datetime) else counter["day_reset"]
        }


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
