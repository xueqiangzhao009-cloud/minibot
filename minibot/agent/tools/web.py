"""Web tools."""

import aiohttp
from typing import Optional, List, Dict, Any
from minibot.config.schema import WebSearchConfig


class WebSearchTool:
    """Tool for web search."""

    name = "search"
    description = "Search the web for information"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "count": {
                "type": "integer",
                "description": "Number of results to return"
            }
        },
        "required": ["query"]
    }

    def __init__(self, config: WebSearchConfig, proxy: Optional[str] = None):
        self.config = config
        self.proxy = proxy

    async def run(self, query: str, count: int = 5) -> str:
        """Run the tool."""
        try:
            # For demonstration, return a mock response
            # In a real implementation, you would use a search API
            results = [
                f"Result {i+1}: https://example.com/result{i+1} - This is a mock search result for '{query}'"
                for i in range(count)
            ]
            return "\n\n".join(results)
        except Exception as e:
            return f"Error searching web: {str(e)}"


class WebFetchTool:
    """Tool for fetching web content."""

    name = "fetch"
    description = "Fetch content from a web URL"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to fetch"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds"
            }
        },
        "required": ["url"]
    }

    def __init__(self, proxy: Optional[str] = None):
        self.proxy = proxy

    async def run(self, url: str, timeout: int = 30) -> str:
        """Run the tool."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Return first 1000 characters to avoid exceeding token limits
                        return content[:1000] + ("..." if len(content) > 1000 else "")
                    else:
                        return f"Error fetching URL: HTTP {response.status}"
        except Exception as e:
            return f"Error fetching URL: {str(e)}"
