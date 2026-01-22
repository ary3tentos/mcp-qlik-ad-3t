import os
from typing import Optional

class QlikAuth:
    """QlikAuth using API key from master user"""
    def __init__(self):
        self.api_key = os.getenv("QLIK_CLOUD_API_KEY")
        self.tenant_url = os.getenv("QLIK_CLOUD_TENANT_URL", "").rstrip("/")
    
    def get_api_key(self) -> str:
        """Get Qlik Cloud API key from environment"""
        if not self.api_key:
            raise Exception("QLIK_CLOUD_API_KEY not configured. Please set it in environment variables.")
        return self.api_key
