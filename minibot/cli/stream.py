"""Stream rendering for minibot CLI."""

import asyncio
from typing import Optional
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

console = Console()


class ThinkingSpinner:
    """Spinner for thinking states."""

    def __init__(self):
        self.spinner = Spinner("dots", text="Thinking...")
        self.live: Optional[Live] = None

    def start(self):
        """Start the spinner."""
        if not self.live:
            self.live = Live(self.spinner, refresh_per_second=20)
            self.live.start()

    def stop(self):
        """Stop the spinner."""
        if self.live:
            self.live.stop()
            self.live = None

    def pause(self):
        """Pause the spinner."""
        return self.live


class StreamRenderer:
    """Renderer for streaming responses."""

    def __init__(self, render_markdown: bool = True):
        self.render_markdown = render_markdown
        self.streamed = False
        self.buffer = []

    async def on_delta(self, content: str):
        """Handle a streaming delta."""
        if not content:
            return
        self.streamed = True
        self.buffer.append(content)
        console.print(content, end="")

    async def on_end(self, resuming: bool = False):
        """Handle the end of a stream."""
        if self.buffer:
            console.print()
            self.buffer = []

    async def close(self):
        """Close the renderer."""
        pass
