from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolResponse(BaseModel):
    tool_call_id: str
    result: Any

class Message(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None

class Agent:
    def __init__(self, provider, tools=None):
        self.provider = provider
        self.tools = tools or []
        self.memory = []

    def add_message(self, message: Message):
        self.memory.append(message)

    def process(self, user_input: str) -> str:
        # Add user message to memory
        user_message = Message(role="user", content=user_input)
        self.add_message(user_message)

        # Generate response
        response = self.provider.generate(self.memory, self.tools)
        
        # Handle tool calls if any
        if response.tool_calls:
            for tool_call in response.tool_calls:
                # Find and execute the tool
                tool = next((t for t in self.tools if t.name == tool_call.name), None)
                if tool:
                    try:
                        result = tool.run(**tool_call.arguments)
                        # Add tool response to memory
                        tool_response = Message(
                            role="tool",
                            content=str(result),
                            tool_call_id=tool_call.name
                        )
                        self.add_message(tool_response)
                        
                        # Generate follow-up response
                        follow_up = self.provider.generate(self.memory, self.tools)
                        self.add_message(follow_up)
                        return follow_up.content
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_call.name}: {e}")
                        error_message = Message(
                            role="tool",
                            content=f"Error: {str(e)}",
                            tool_call_id=tool_call.name
                        )
                        self.add_message(error_message)
                        follow_up = self.provider.generate(self.memory, self.tools)
                        self.add_message(follow_up)
                        return follow_up.content
        else:
            self.add_message(response)
            return response.content
