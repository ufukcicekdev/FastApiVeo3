from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
import secrets
import hashlib
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.api_key = settings.api_key
        self.require_auth = settings.require_auth
        
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, provided_key: str) -> bool:
        """Verify if the provided API key is valid"""
        if not self.require_auth:
            return True
            
        if not self.api_key:
            logger.warning("API_KEY not configured but authentication is required")
            return False
            
        # Support both direct comparison and hashed comparison
        if provided_key == self.api_key:
            return True
            
        # Check if stored key is hashed and compare hashes
        if len(self.api_key) == 64:  # SHA256 hash length
            return self.hash_api_key(provided_key) == self.api_key
            
        return False

# Global auth service
auth_service = AuthService()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify the API token from Authorization header
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        The verified token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not settings.require_auth:
        return "no-auth-required"
        
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    if not auth_service.verify_api_key(token):
        logger.warning(f"Invalid API key attempt: {token[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token

async def optional_verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Optional token verification - allows access without token in development
    """
    try:
        return await verify_token(credentials)
    except HTTPException:
        if settings.environment == "development":
            logger.info("Development mode: allowing access without token")
            return "development-access"
        raise

# Dependency for protected endpoints
require_auth = Depends(verify_token)
optional_auth = Depends(optional_verify_token)