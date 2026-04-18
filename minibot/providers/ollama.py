"""Ollama provider for local LLM inference."""

import json
from typing import Any, Dict, List, Optional

import httpx

from minibot.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    """
    Ollama provider for local LLM inference.

    Ollama runs LLMs locally with an OpenAI-compatible API.
    """

    def __init__(
        self,
        api_base: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: float = 120.0,
    ):
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_base,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a response using Ollama."""
        client = await self._get_client()

        ollama_messages = self._convert_messages(messages)

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
        }

        try:
            response = await client.post("/v1/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            assistant_message = data.get("choices", [{}])[0].get("message", {})
            result = {
                "content": assistant_message.get("content", ""),
            }

            if assistant_message.get("tool_calls"):
                result["tool_calls"] = [
                    {
                        "name": tc.get("function", {}).get("name", ""),
                        "arguments": tc.get("function", {}).get("arguments", ""),
                    }
                    for tc in assistant_message["tool_calls"]
                ]

            return result

        except httpx.HTTPStatusError as e:
            return {"content": f"HTTP error: {e.response.status_code}", "error": str(e)}
        except Exception as e:
            return {"content": f"Error calling Ollama: {e}", "error": str(e)}

    async def generate_stream(self, messages: List[Dict[str, Any]]):
        """Generate a streaming response using Ollama."""
        client = await self._get_client()

        ollama_messages = self._convert_messages(messages)

        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
        }

        try:
            async with client.stream("POST", "/v1/chat/completions", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue
                    elif line.startswith("{"):
                        try:
                            data = json.loads(line)
                            delta = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            yield f"HTTP error: {e.response.status_code}"
        except Exception as e:
            yield f"Error calling Ollama: {e}"

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages to Ollama format."""
        ollama_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, list):
                text_content = ""
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_content += item.get("text", "")
                        elif item.get("type") == "image_url":
                            image_url = item.get("image_url", {})
                            if isinstance(image_url, dict):
                                text_content += f"[image: {image_url.get('url', '')}]"
                            else:
                                text_content += f"[image: {image_url}]"
                content = text_content
            elif not isinstance(content, str):
                content = str(content)

            if role == "system":
                role = "system"
            elif role == "assistant":
                role = "assistant"
            else:
                role = "user"

            ollama_messages.append({"role": role, "content": content})

        return ollama_messages

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model

    async def list_models(self) -> List[str]:
        """List available models on the Ollama server."""
        client = await self._get_client()
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
