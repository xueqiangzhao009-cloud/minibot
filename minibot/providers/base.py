from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    async def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a response from the provider."""
        raise NotImplementedError("Subclasses must implement generate method")

