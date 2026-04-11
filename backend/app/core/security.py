"""
Conflict Zero - Security Module
Autenticación y autorización con JWT + API Keys
"""

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Union
import os
import secrets
import hashlib

from app.core.database import get_db
from app.models_v2 import Company, ApiKey

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica contraseña contra hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera hash de contraseña"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea JWT token para autenticación"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decodifica y valida JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> tuple[str, str]:
    """
    Genera una API key segura.
    Retorna: (api_key completa, hash para almacenar)
    """
    # Generar key aleatoria: cz_live_xxxxxxxxxxxx
    key = "cz_live_" + secrets.token_urlsafe(32)
    
    # Calcular hash para almacenar
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    
    return key, key_hash


def verify_api_key(key: str, key_hash: str) -> bool:
    """Verifica API key contra su hash"""
    computed_hash = hashlib.sha256(key.encode()).hexdigest()
    return secrets.compare_digest(computed_hash, key_hash)


async def get_current_company(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> Company:
    """
    Dependencia para obtener la empresa autenticada.
    Soporta:
    - Bearer Token (JWT)
    - Bearer API Key (cz_live_xxx)
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication provided",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    # Intentar como JWT primero
    payload = decode_token(token)
    if payload:
        company_id = payload.get("sub")
        if company_id:
            company = db.query(Company).filter(
                Company.id == company_id,
                Company.deleted_at.is_(None),
                Company.status == "active"
            ).first()
            if company:
                # Actualizar last_login
                company.last_login_at = datetime.utcnow()
                db.commit()
                return company
    
    # Intentar como API Key (cz_live_xxx)
    if token.startswith("cz_live_"):
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        api_key = db.query(ApiKey).filter(
            ApiKey.key_hash == token_hash,
            ApiKey.is_active == True,
            ApiKey.deleted_at.is_(None)
        ).first()
        
        if api_key:
            # Verificar expiración
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key expired"
                )
            
            # Actualizar uso
            api_key.last_used_at = datetime.utcnow()
            api_key.usage_count += 1
            
            company = db.query(Company).filter(
                Company.id == api_key.company_id,
                Company.deleted_at.is_(None)
            ).first()
            
            if company:
                db.commit()
                return company
    
    raise credentials_exception


async def get_current_founder(
    current_company: Company = Depends(get_current_company)
) -> Company:
    """
    Verifica que la empresa actual sea un Founder.
    """
    if not current_company.is_founder:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires Founder status"
        )
    return current_company


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> bool:
    """
    Verifica credenciales de admin (para panel administrativo).
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required"
        )
    
    # Admin token simple (para MVP)
    admin_token = os.getenv("ADMIN_TOKEN", "admin-dev-token")
    
    if credentials.credentials != admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials"
        )
    
    return True


class RateLimiter:
    """
    Rate limiting simple basado en memoria.
    Para producción, usar Redis.
    """
    _storage = {}
    
    @classmethod
    def is_allowed(cls, key: str, limit: int, window_seconds: int = 60) -> bool:
        """
        Verifica si una key está dentro del rate limit.
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Limpiar entradas antiguas
        if key in cls._storage:
            cls._storage[key] = [
                t for t in cls._storage[key] 
                if t > window_start
            ]
        else:
            cls._storage[key] = []
        
        # Verificar límite
        if len(cls._storage[key]) >= limit:
            return False
        
        # Registrar request
        cls._storage[key].append(now)
        return True


def rate_limit_requests(key: str, limit: int = 60, window: int = 60):
    """
    Decorator/función para rate limiting.
    """
    if not RateLimiter.is_allowed(key, limit, window):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {limit} per {window}s"
        )
