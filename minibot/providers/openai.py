from typing import List, Dict, Any, Optional
import openai
from minibot.providers.base import BaseProvider

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, default_model: str = "gpt-4-turbo", extra_headers: Optional[Dict[str, str]] = None):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=api_base,
            default_headers=extra_headers
        )
        self.model = default_model

    async def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        # Convert response to dict format
        assistant_message = response.choices[0].message
        result = {
            "content": assistant_message.content or ""
        }

        if assistant_message.tool_calls:
            result["tool_calls"] = [
                {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
                for tc in assistant_message.tool_calls
            ]

        return result

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model


