from typing import List, Dict, Any, Optional
import anthropic
from minibot.providers.base import BaseProvider

class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, default_model: str = "claude-3-opus-20240229", extra_headers: Optional[Dict[str, str]] = None):
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key,
            base_url=api_base,
            default_headers=extra_headers
        )
        self.model = default_model

    async def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "user":
                anthropic_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                anthropic_messages.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "tool":
                anthropic_messages.append({"role": "user", "content": f"Tool response: {msg['content']}"})
            elif msg["role"] == "system":
                anthropic_messages.append({"role": "system", "content": msg["content"]})

        # Call Anthropic API
        response = await self.client.messages.create(
            model=self.model,
            messages=anthropic_messages
        )

        # Convert response to dict format
        result = {}
        if response.content and len(response.content) > 0:
            content = ""
            tool_calls = []
            for item in response.content:
                if item.type == "text":
                    content += item.text
                elif item.type == "tool_use":
                    tool_calls.append({
                        "name": item.name,
                        "arguments": item.input
                    })
            result["content"] = content
            if tool_calls:
                result["tool_calls"] = tool_calls
        else:
            result["content"] = ""

        return result

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model


