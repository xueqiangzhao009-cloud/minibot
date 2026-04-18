import asyncio
from typing import List, Optional
from minibot.bus.message import InboundMessage, OutboundMessage

class MessageBus:
    def __init__(self):
        self.inbound_queue = asyncio.Queue()
        self.outbound_queue = asyncio.Queue()

    async def enqueue_inbound(self, message: InboundMessage):
        await self.inbound_queue.put(message)

    async def dequeue_inbound(self) -> InboundMessage:
        return await self.inbound_queue.get()

    async def enqueue_outbound(self, message: OutboundMessage):
        await self.outbound_queue.put(message)

    async def dequeue_outbound(self) -> OutboundMessage:
        return await self.outbound_queue.get()

    async def consume_inbound(self) -> InboundMessage:
        """Consume an inbound message from the queue."""
        return await self.inbound_queue.get()

    async def publish_outbound(self, message: OutboundMessage):
        """Publish an outbound message to the queue."""
        await self.outbound_queue.put(message)

    async def publish_inbound(self, message: InboundMessage):
        """Publish an inbound message to the queue."""
        await self.inbound_queue.put(message)

