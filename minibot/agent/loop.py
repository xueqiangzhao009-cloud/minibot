import asyncio
import logging
from contextlib import nullcontext
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Awaitable
from minibot.agent.context import ContextBuilder
from minibot.agent.tools.registry import ToolRegistry
from minibot.agent.tools.filesystem import ReadFileTool, WriteFileTool, EditFileTool, ListDirTool
from minibot.agent.tools.shell import ExecTool
from minibot.agent.tools.web import WebSearchTool, WebFetchTool
from minibot.agent.tools.message import MessageTool
from minibot.bus.message import InboundMessage, OutboundMessage
from minibot.bus.bus import MessageBus
from minibot.config.schema import AgentDefaults, WebToolsConfig, ExecToolConfig, ToolsConfig
from minibot.providers.base import BaseProvider
from minibot.session.manager import Session, SessionManager

logger = logging.getLogger(__name__)

UNIFIED_SESSION_KEY = "unified:default"

class AgentLoop:
    """
    The agent loop is the core processing engine.

    It:
    1. Receives messages from the bus
    2. Builds context with history, memory, skills
    3. Calls the LLM
    4. Executes tool calls
    5. Sends responses back
    """

    def __init__(
        self,
        bus: MessageBus,
        provider: BaseProvider,
        workspace: Path,
        model: str | None = None,
        max_iterations: int | None = None,
        context_window_tokens: int | None = None,
        context_block_limit: int | None = None,
        max_tool_result_chars: int | None = None,
        provider_retry_mode: str = "standard",
        web_config: WebToolsConfig | None = None,
        exec_config: ExecToolConfig | None = None,
        restrict_to_workspace: bool = False,
        session_manager: SessionManager | None = None,
        mcp_servers: dict | None = None,
        timezone: str | None = None,
        session_ttl_minutes: int = 0,
        unified_session: bool = False,
        disabled_skills: list[str] | None = None,
        tools_config: ToolsConfig | None = None,
    ):
        _tc = tools_config or ToolsConfig()
        defaults = AgentDefaults()
        self.bus = bus
        self.provider = provider
        self.workspace = workspace
        self.model = model or provider.get_default_model()
        self.max_iterations = (
            max_iterations if max_iterations is not None else defaults.max_tool_iterations
        )
        self.context_window_tokens = (
            context_window_tokens
            if context_window_tokens is not None
            else defaults.context_window_tokens
        )
        self.context_block_limit = context_block_limit
        self.max_tool_result_chars = (
            max_tool_result_chars
            if max_tool_result_chars is not None
            else defaults.max_tool_result_chars
        )
        self.provider_retry_mode = provider_retry_mode
        self.web_config = web_config or WebToolsConfig()
        self.exec_config = exec_config or ExecToolConfig()
        self.restrict_to_workspace = restrict_to_workspace

        self.context = ContextBuilder(workspace, timezone=timezone, disabled_skills=disabled_skills)
        self.sessions = session_manager or SessionManager(workspace)
        self.tools = ToolRegistry()
        self._unified_session = unified_session
        self._running = False
        self._mcp_servers = mcp_servers or {}
        self._active_tasks: dict[str, list[asyncio.Task]] = {}  # session_key -> tasks
        self._background_tasks: list[asyncio.Task] = []
        self._session_locks: dict[str, asyncio.Lock] = {}
        # Per-session pending queues for mid-turn message injection
        self._pending_queues: dict[str, asyncio.Queue] = {}
        # NANOBOT_MAX_CONCURRENT_REQUESTS: <=0 means unlimited; default 3
        _max = 3
        self._concurrency_gate: asyncio.Semaphore | None = (
            asyncio.Semaphore(_max) if _max > 0 else None
        )

        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the default set of tools."""
        allowed_dir = (
            self.workspace if (self.restrict_to_workspace or self.exec_config.sandbox) else None
        )
        self.tools.register(
            ReadFileTool(
                workspace=self.workspace, allowed_dir=allowed_dir
            )
        )
        for cls in (WriteFileTool, EditFileTool, ListDirTool):
            self.tools.register(cls(workspace=self.workspace, allowed_dir=allowed_dir))
        if self.exec_config.enable:
            self.tools.register(
                ExecTool(
                    working_dir=str(self.workspace),
                    timeout=self.exec_config.timeout,
                    restrict_to_workspace=self.restrict_to_workspace,
                    sandbox=self.exec_config.sandbox,
                    path_append=self.exec_config.path_append,
                    allowed_env_keys=self.exec_config.allowed_env_keys,
                )
            )
        if self.web_config.enable:
            self.tools.register(
                WebSearchTool(config=self.web_config.search, proxy=self.web_config.proxy)
            )
            self.tools.register(WebFetchTool(proxy=self.web_config.proxy))
        self.tools.register(MessageTool(send_callback=self.bus.publish_outbound))

    def _effective_session_key(self, msg: InboundMessage) -> str:
        """Return the session key used for task routing and mid-turn injections."""
        if self._unified_session and not msg.session_id_override:
            return UNIFIED_SESSION_KEY
        return msg.session_key

    async def run(self) -> None:
        """Run the agent loop, dispatching messages as tasks to stay responsive."""
        self._running = True
        logger.info("Agent loop started")

        while self._running:
            try:
                msg = await asyncio.wait_for(self.bus.consume_inbound(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                if not self._running or asyncio.current_task().cancelling():
                    raise
                continue
            except Exception as e:
                logger.warning("Error consuming inbound message: {}, continuing...", e)
                continue

            effective_key = self._effective_session_key(msg)
            # If this session already has an active pending queue, route the message there
            if effective_key in self._pending_queues:
                pending_msg = msg
                if effective_key != msg.session_key:
                    pending_msg = msg
                try:
                    self._pending_queues[effective_key].put_nowait(pending_msg)
                except asyncio.QueueFull:
                    logger.warning(
                        "Pending queue full for session {}, falling back to queued task",
                        effective_key,
                    )
                else:
                    logger.info(
                        "Routed follow-up message to pending queue for session {}",
                        effective_key,
                    )
                    continue
            # Compute the effective session key before dispatching
            task = asyncio.create_task(self._dispatch(msg))
            self._active_tasks.setdefault(effective_key, []).append(task)
            task.add_done_callback(
                lambda t, k=effective_key: self._active_tasks.get(k, [])
                and self._active_tasks[k].remove(t)
                if t in self._active_tasks.get(k, [])
                else None
            )

    async def _dispatch(self, msg: InboundMessage) -> None:
        """Process a message: per-session serial, cross-session concurrent."""
        session_key = self._effective_session_key(msg)
        lock = self._session_locks.setdefault(session_key, asyncio.Lock())
        gate = self._concurrency_gate or nullcontext()

        # Register a pending queue so follow-up messages for this session are
        # routed here (mid-turn injection) instead of spawning a new task
        pending = asyncio.Queue(maxsize=20)
        self._pending_queues[session_key] = pending

        try:
            async with lock, gate:
                try:
                    response = await self._process_message(
                        msg, pending_queue=pending,
                    )
                    if response is not None:
                        await self.bus.publish_outbound(response)
                    elif msg.channel == "cli":
                        await self.bus.publish_outbound(OutboundMessage(
                            channel=msg.channel, chat_id=msg.chat_id,
                            content="", metadata=msg.metadata or {},
                        ))
                except asyncio.CancelledError:
                    logger.info("Task cancelled for session {}", session_key)
                    raise
                except Exception:
                    logger.exception("Error processing message for session {}", session_key)
                    await self.bus.publish_outbound(OutboundMessage(
                        channel=msg.channel, chat_id=msg.chat_id,
                        content="Sorry, I encountered an error.",
                    ))
        finally:
            # Drain any messages still in the pending queue and re-publish
            # them to the bus so they are processed as fresh inbound messages
            queue = self._pending_queues.pop(session_key, None)
            if queue is not None:
                leftover = 0
                while True:
                    try:
                        item = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    await self.bus.publish_inbound(item)
                    leftover += 1
                if leftover:
                    logger.info(
                        "Re-published {} leftover message(s) to bus for session {}",
                        leftover, session_key,
                    )

    async def _process_message(
        self,
        msg: InboundMessage,
        session_key: str | None = None,
        pending_queue: asyncio.Queue | None = None,
    ) -> OutboundMessage | None:
        """Process a single inbound message and return the response."""
        key = session_key or msg.session_key
        session = self.sessions.get_or_create(key)

        # Extract document text from media at the processing boundary
        if msg.media:
            # Simplified: just use the content as-is
            pass

        preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        logger.info("Processing message from {}:{}: {}", msg.channel, msg.sender_id, preview)

        # Save the triggering user message immediately
        if isinstance(msg.content, str) and msg.content.strip():
            session.add_message("user", msg.content)
            self.sessions.save(session)

        # Build context and generate response
        history = session.get_history()
        initial_messages = self.context.build_messages(
            history=history,
            current_message=msg.content,
            channel=msg.channel,
            chat_id=msg.chat_id,
        )

        # Generate response
        response = await self.provider.generate(initial_messages)

        # Handle tool calls
        while response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["name"]
                arguments = tool_call.get("arguments", {})

                # Execute tool
                try:
                    tool = self.tools.get(tool_name)
                    if tool:
                        result = await tool.run(**arguments)
                        # Add tool response to session
                        session.add_message("tool", str(result))
                    else:
                        # Add error response
                        session.add_message("tool", f"Error: Tool {tool_name} not found")
                except Exception as e:
                    # Add error response
                    session.add_message("tool", f"Error: {str(e)}")

            # Generate follow-up response
            history = session.get_history()
            follow_up_messages = self.context.build_messages(
                history=history,
                current_message="",
                channel=msg.channel,
                chat_id=msg.chat_id,
            )
            response = await self.provider.generate(follow_up_messages)

        # Add assistant response to session
        final_content = response.get("content", "")
        session.add_message("assistant", final_content)
        self.sessions.save(session)

        preview = final_content[:120] + "..." if len(final_content) > 120 else final_content
        logger.info("Response to {}:{}: {}", msg.channel, msg.sender_id, preview)

        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=final_content,
            metadata=msg.metadata or {},
        )

    def stop(self) -> None:
        """Stop the agent loop."""
        self._running = False
        logger.info("Agent loop stopping")
