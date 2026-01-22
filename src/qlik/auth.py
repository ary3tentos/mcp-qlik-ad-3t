import os
from typing import Optional

class QlikAuth:
    """QlikAuth using API key from master user"""
    def __init__(self):
        api_key_raw = os.getenv("QLIK_CLOUD_API_KEY")
        # Limpar espaços e quebras de linha que podem causar problemas
        self.api_key = api_key_raw.strip() if api_key_raw else None
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
    
    def get_api_key(self) -> Optional[str]:
        """Get Qlik Cloud API key from environment"""
        if not self.api_key:
            return None
        # Retornar API key limpa (sem espaços extras)
        return self.api_key.strip()
