"""Message tools."""

from typing import Optional, List, Dict, Any, Callable, Awaitable
from minibot.bus.message import OutboundMessage


class MessageTool:
    """Tool for sending messages."""

    name = "message"
    description = "Send a message to a channel"
    parameters = {
        "type": "object",
        "properties": {
            "channel": {
                "type": "string",
                "description": "Channel to send the message to"
            },
            "chat_id": {
                "type": "string",
                "description": "Chat ID to send the message to"
            },
            "content": {
                "type": "string",
                "description": "Content of the message"
            }
        },
        "required": ["content"]
    }

    def __init__(self, send_callback: Callable[[OutboundMessage], Awaitable[None]]):
        self.send_callback = send_callback

    async def run(self, channel: str = "cli", chat_id: Optional[str] = None, content: str = "") -> str:
        """Run the tool."""
        try:
            message = OutboundMessage(
                channel=channel,
                chat_id=chat_id,
                content=content
            )
            await self.send_callback(message)
            return f"Message sent successfully to {channel}"
        except Exception as e:
            return f"Error sending message: {str(e)}"
