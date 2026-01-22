from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any], api_key: str) -> Any:
        pass
