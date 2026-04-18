"""Channel manager for minibot."""

import asyncio
from typing import Dict, List, Type

from minibot.bus.bus import MessageBus
from minibot.bus.events import OutboundMessage
from minibot.channels.base import BaseChannel
from minibot.channels.registry import discover_all


class ChannelManager:
    """
    Manages chat channels and routes outbound messages.
    """

    def __init__(self, config: Dict, bus: MessageBus):
        """
        Initialize the channel manager.

        Args:
            config: Channel configuration.
            bus: The message bus for communication.
        """
        self.config = config
        self.bus = bus
        self.channels: Dict[str, BaseChannel] = {}
        self._tasks: List[asyncio.Task] = []

    @property
    def enabled_channels(self) -> List[str]:
        """List of enabled channel names."""
        channels = []
        for name, channel_config in self.config.items():
            if isinstance(channel_config, dict):
                if channel_config.get("enabled", False):
                    channels.append(name)
            else:
                if getattr(channel_config, "enabled", False):
                    channels.append(name)
        return channels

    async def start_all(self) -> None:
        """Start all enabled channels."""
        all_channels = discover_all()
        for name, cls in all_channels.items():
            if name not in self.enabled_channels:
                continue
            try:
                channel_config = self.config.get(name, {})
                channel = cls(channel_config, self.bus)
                self.channels[name] = channel
                task = asyncio.create_task(channel.start())
                self._tasks.append(task)
            except Exception as e:
                print(f"Error starting channel {name}: {e}")

        # Start message handler for outbound messages
        self._tasks.append(asyncio.create_task(self._handle_outbound()))

    async def stop_all(self) -> None:
        """Stop all channels."""
        for channel in self.channels.values():
            try:
                await channel.stop()
            except Exception as e:
                print(f"Error stopping channel {channel.name}: {e}")

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _handle_outbound(self) -> None:
        """Handle outbound messages from the bus."""
        while True:
            try:
                msg = await self.bus.consume_outbound()
                await self._route_message(msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error handling outbound message: {e}")

    async def _route_message(self, msg: OutboundMessage) -> None:
        """Route an outbound message to the appropriate channel."""
        if msg.channel not in self.channels:
            return
        try:
            channel = self.channels[msg.channel]
            await channel.send(msg)
        except Exception as e:
            print(f"Error sending message via channel {msg.channel}: {e}")
