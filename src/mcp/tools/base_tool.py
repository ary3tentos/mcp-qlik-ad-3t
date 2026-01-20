from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def execute(self, user_id: str, arguments: Dict[str, Any]) -> Any:
        pass
