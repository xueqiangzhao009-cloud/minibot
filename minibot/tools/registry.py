from typing import Dict, Type
from minibot.tools.base import BaseTool

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        return self.tools.get(name)

    def list_tools(self) -> list:
        return list(self.tools.values())
