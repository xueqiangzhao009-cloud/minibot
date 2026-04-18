"""CLI channel for minibot."""

import asyncio
import sys

from minibot.bus.bus import MessageBus
from minibot.bus.events import InboundMessage, OutboundMessage
from minibot.channels.base import BaseChannel


class CLIChannel(BaseChannel):
    """
    CLI channel for minibot.
    """

    name: str = "cli"
    display_name: str = "CLI"

    def __init__(self, config: dict = None, bus: MessageBus = None):
        """
        Initialize the CLI channel.

        Args:
            config: Channel configuration.
            bus: The message bus for communication.
        """
        super().__init__(config or {}, bus)
        self._input_queue = asyncio.Queue()

    async def start(self) -> None:
        """Start the CLI channel."""
        self._running = True
        # Start input listener task
        asyncio.create_task(self._listen_for_input())

    async def stop(self) -> None:
        """Stop the CLI channel."""
        self._running = False

    async def send(self, msg: OutboundMessage) -> None:
        """Send a message through the CLI channel."""
        print(f"\nminibot: {msg.content}")

    async def receive_message(self) -> InboundMessage:
        """Receive a message from the CLI."""
        content = await self._input_queue.get()
        return InboundMessage(
            channel=self.name,
            sender_id="user",
            chat_id="direct",
            content=content,
            media=[],
            metadata={},
        )

    async def _listen_for_input(self) -> None:
        """Listen for user input from the CLI."""
        while self._running:
            try:
                # Use async input if available
                content = await asyncio.to_thread(input, "You: ")
                if content.lower() == "exit":
                    self._running = False
                    break
                # Create and enqueue inbound message
                msg = InboundMessage(
                    channel=self.name,
                    sender_id="user",
                    chat_id="direct",
                    content=content,
                    media=[],
                    metadata={},
                )
                if self.bus:
                    await self.bus.enqueue_inbound(msg)
            except EOFError:
                self._running = False
                break
            except Exception:
                pass
