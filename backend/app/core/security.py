from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import secrets
import string

from .config import settings
from .database import get_db
from app.models_v2 import Company

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
ALGORITHM = "HS256"

# Security scheme for docs
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_company(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Company:
    """Get the current authenticated company from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    company_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    
    if company_id is None or token_type != "access":
        raise credentials_exception
    
    from uuid import UUID
    try:
        company_uuid = UUID(company_id)
    except ValueError:
        raise credentials_exception
    
    company = db.query(Company).filter(Company.id == company_uuid).first()
    if company is None:
        raise credentials_exception
    
    if company.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company account is not active"
        )
    
    return company

def get_current_active_company(current_company: Company = Depends(get_current_company)) -> Company:
    """Ensure company is active."""
    if current_company.status != "active":
        raise HTTPException(status_code=400, detail="Inactive company")
    return current_company

def generate_api_key():
    """Generate a new API key and its hash."""
    # Generate 48-char random string
    api_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(48))
    # Hash for storage
    api_key_hash = get_password_hash(api_key)
    return api_key, api_key_hash

def require_admin(current_company: Company = Depends(get_current_company)) -> Company:
    """Ensure company has admin privileges (founder or specific flag)."""
    # For now, founders have admin-like access
    if not current_company.is_founder:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_company

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Company:
    """
    Get current admin user.
    Validates that the user has admin privileges (is_admin flag or is_founder).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required"
    )
    
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    company_id: str = payload.get("sub")
    token_type: str = payload.get("type")
    is_admin: bool = payload.get("is_admin", False)
    
    if company_id is None or token_type != "access":
        raise credentials_exception
    
    from uuid import UUID
    try:
        company_uuid = UUID(company_id)
    except ValueError:
        raise credentials_exception
    
    company = db.query(Company).filter(Company.id == company_uuid).first()
    if company is None:
        raise credentials_exception
    
    # Check admin privileges (is_admin flag, is_founder, or email in admin list)
    admin_emails = ["tiagomunoz10@icloud.com", "admin@czperu.com"]  # Configurable admin list
    is_user_admin = (
        is_admin or 
        getattr(company, 'is_admin', False) or 
        getattr(company, 'is_founder', False) or
        company.email in admin_emails
    )
    
    if not is_user_admin:
        raise forbidden_exception
    
    return company
