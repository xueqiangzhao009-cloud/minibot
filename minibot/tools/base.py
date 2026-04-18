from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseTool(ABC):
    name: str
    description: str
    parameters: Dict[str, Any]

    async def run(self, **kwargs) -> Any:
        """Run the tool with the given arguments."""
        raise NotImplementedError("Subclasses must implement run method")

