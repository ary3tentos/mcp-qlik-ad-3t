import jwt
import httpx
import os
import logging
from typing import Optional, Dict, Any
from jwt.exceptions import InvalidTokenError, DecodeError

logger = logging.getLogger(__name__)

class JWTValidator:
    def __init__(self):
        # Aceita ambos os nomes de variável (compatibilidade)
        # Prioriza JWT_SECRET_KEY (mesmo nome do backend) ou AI_POCS_JWT_SECRET
        self.jwt_secret = os.getenv("JWT_SECRET_KEY") or os.getenv("AI_POCS_JWT_SECRET")
        self.backend_url = os.getenv("AI_POCS_BACKEND_URL", "http://localhost:3001")
        self.validation_endpoint = os.getenv("AI_POCS_JWT_VALIDATION_ENDPOINT", "/api/auth/validate")
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        logger.debug(f"Validating JWT token (length: {len(token)}, has_secret: {bool(self.jwt_secret)})")
        
        # Primeiro tenta validação local (mais rápido)
        if self.jwt_secret:
            try:
                decoded = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                logger.debug(f"✅ JWT validated locally - user_id: {decoded.get('sub')}")
                return decoded
            except (InvalidTokenError, DecodeError) as e:
                logger.debug(f"❌ Local JWT validation failed: {str(e)}")
        
        # Fallback: validação via endpoint do backend
        logger.debug(f"Attempting JWT validation via backend: {self.backend_url}{self.validation_endpoint}")
        try:
            async with httpx.AsyncClient() as client:
                # O endpoint espera o token no header Authorization
                response = await client.post(
                    f"{self.backend_url}{self.validation_endpoint}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0
                )
                logger.debug(f"Backend validation response: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    # O endpoint retorna TokenValidationResponse com user info
                    if data.get("valid") and data.get("user"):
                        user = data.get("user", {})
                        # Reconstrói o payload do JWT a partir dos dados do user
                        decoded = {
                            "sub": user.get("id") or user.get("user_id"),
                            "email": user.get("email"),
                            "upn": user.get("upn"),
                            "name": user.get("name")
                        }
                        logger.debug(f"✅ JWT validated via backend - user_id: {decoded.get('sub')}")
                        return decoded
                    else:
                        logger.warning(f"Backend validation returned invalid: {data}")
        except Exception as e:
            logger.warning(f"JWT validation via endpoint failed: {str(e)}")
            import traceback
            logger.debug(traceback.format_exc())
        
        logger.warning("❌ JWT validation failed - all methods exhausted")
        return None
    
    def extract_user_id(self, decoded_token: Dict[str, Any]) -> Optional[str]:
        return decoded_token.get("sub") or decoded_token.get("user_id") or decoded_token.get("email")
    
    def extract_email(self, decoded_token: Dict[str, Any]) -> Optional[str]:
        return decoded_token.get("email") or decoded_token.get("upn")
