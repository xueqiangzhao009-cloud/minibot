"""CLI commands for minibot."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Optional

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    # Set environment variable for Python encoding
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Set console code page to UTF-8
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass
    # Re-open stdout/stderr with UTF-8 encoding
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer

__logo__ = "🤖"
__version__ = "0.1.0"

# Create a simple Typer app without rich formatting
import click

# Create a custom formatter that uses plain text
class PlainTextFormatter(click.HelpFormatter):
    def write_heading(self, heading):
        self.write(f"{heading}\n")
    
    def write_paragraph(self):
        self.write("\n")
    
    def write_text(self, text):
        self.write(f"{text}\n")
    
    def write_dl(self, rows, **kwargs):
        for name, help_text in rows:
            if help_text:
                self.write(f"  {name:<20} {help_text}\n")
            else:
                self.write(f"  {name}\n")

# Create Typer app with custom formatter
app = typer.Typer(
    name="minibot",
    context_settings={"help_option_names": ["-h", "--help"]},
    help="minibot - Personal AI Assistant",
    no_args_is_help=True,
    rich_markup_mode=None,
)

# Override the formatter for all commands
@app.callback()
def main():
    """minibot - Personal AI Assistant"""
    pass

# Add a custom help command that prints plain text help
@app.command(hidden=True)
def help():
    """Show help information."""
    print("Usage: python -m minibot [OPTIONS] COMMAND [ARGS]...\n")
    print("minibot - Personal AI Assistant\n")
    print("Options:")
    print("  --version             -v")
    print("  --install-completion            Install completion for the current shell.")
    print("  --show-completion               Show completion for the current shell, to copy it or customize the installation.")
    print("  --help                -h        Show this message and exit.\n")
    print("Commands:")
    print("  agent    Interact with the agent directly.")
    print("  gateway  Start the minibot gateway.")
    print("  onboard  Initialize minibot configuration and workspace.")
    print("  serve    Start the OpenAI-compatible API server (/v1/chat/completions).")
    print()

# Use standard print for output
EXIT_COMMANDS = {"exit", "quit", "/exit", "/quit", ":q"}


class SafeFileHistory:
    """FileHistory subclass that sanitizes surrogate characters on write."""

    def __init__(self, history_file):
        self.history_file = history_file
        self.history = []

    def store_string(self, string: str) -> None:
        safe = string.encode("utf-8", errors="surrogateescape").decode("utf-8", errors="replace")
        self.history.append(safe)

    def get_history(self):
        return self.history


def _print_agent_response(
    response: str,
    render_markdown: bool,
    metadata: dict | None = None,
) -> None:
    """Render assistant response with consistent terminal styling."""
    content = response or ""
    body = _response_renderable(content, render_markdown, metadata)
    print()
    print("minibot")
    print(body)
    print()


def _response_renderable(content: str, render_markdown: bool, metadata: dict | None = None):
    """Render plain-text command output without markdown collapsing newlines."""
    if not render_markdown:
        return Text(content)
    if (metadata or {}).get("render_as") == "text":
        return Text(content)
    return Markdown(content)


def version_callback(value: bool):
    if value:
        console.print(f"{__logo__} minibot v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True
    ),
):
    """minibot - Personal AI Assistant."""
    pass


# ============================================================================
# Onboard / Setup
# ============================================================================


@app.command()
def onboard(
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Initialize minibot configuration and workspace."""
    from minibot.config.loader import get_config_path, load_config, save_config, set_config_path
    from minibot.config.schema import Config

    if config:
        config_path = Path(config).expanduser().resolve()
        set_config_path(config_path)
        print(f"Using config: {config_path}")
    else:
        config_path = get_config_path()

    def _apply_workspace_override(loaded: Config) -> Config:
        if workspace:
            loaded.agents.defaults.workspace = workspace
        return loaded

    # Create or update config
    if config_path.exists():
        print(f"Config already exists at {config_path}")
        print(
            "  y = overwrite with defaults (existing values will be lost)"
        )
        print(
            "  N = refresh config, keeping existing values and adding new fields"
        )
        if typer.confirm("Overwrite?"):
            config = _apply_workspace_override(Config())
            save_config(config, config_path)
            print(f"✓ Config reset to defaults at {config_path}")
        else:
            config = _apply_workspace_override(load_config(config_path))
            save_config(config, config_path)
            print(
                f"✓ Config refreshed at {config_path} (existing values preserved)"
            )
    else:
        config = _apply_workspace_override(Config())
        save_config(config, config_path)
        print(f"✓ Created config at {config_path}")

    # Create workspace
    workspace_path = config.workspace_path
    if not workspace_path.exists():
        workspace_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created workspace at {workspace_path}")

    agent_cmd = 'minibot agent -m "Hello!"'
    serve_cmd = "minibot serve"
    if config:
        agent_cmd += f" --config {config_path}"
        serve_cmd += f" --config {config_path}"

    print("\nminibot is ready!")
    print("\nNext steps:")
    print(f"  1. Add your API key to {config_path}")
    print("     Get one at: https://openai.com/api/")
    print(f"  2. Chat: {agent_cmd}")
    print(f"  3. Start API server: {serve_cmd}")


# ============================================================================
# OpenAI-Compatible API Server
# ============================================================================


@app.command()
def serve(
    port: int = typer.Option(8000, "--port", "-p", help="API server port"),
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="Bind address"),
    timeout: float = typer.Option(120.0, "--timeout", "-t", help="Per-request timeout (seconds)"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Start the OpenAI-compatible API server (/v1/chat/completions)."""
    try:
        from aiohttp import web  # noqa: F401
    except ImportError:
        print("aiohttp is required. Install with: pip install 'minibot[api]'")
        raise typer.Exit(1)

    from minibot.agent.loop import AgentLoop
    from minibot.api.server import create_app
    from minibot.bus.bus import MessageBus
    from minibot.session.manager import SessionManager

    runtime_config = _load_runtime_config(config, workspace)
    bus = MessageBus()
    provider = _make_provider(runtime_config)
    session_manager = SessionManager(runtime_config.workspace_path)
    agent_loop = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=runtime_config.workspace_path,
        model=runtime_config.agents.defaults.model,
        max_iterations=runtime_config.agents.defaults.max_tool_iterations,
        context_window_tokens=runtime_config.agents.defaults.context_window_tokens,
        context_block_limit=runtime_config.agents.defaults.context_block_limit,
        max_tool_result_chars=runtime_config.agents.defaults.max_tool_result_chars,
        provider_retry_mode=runtime_config.agents.defaults.provider_retry_mode,
        web_config=runtime_config.tools.web,
        exec_config=runtime_config.tools.exec,
        restrict_to_workspace=runtime_config.tools.restrict_to_workspace,
        session_manager=session_manager,
        mcp_servers=runtime_config.tools.mcp_servers,
        timezone=runtime_config.agents.defaults.timezone,
        unified_session=runtime_config.agents.defaults.unified_session,
        disabled_skills=runtime_config.agents.defaults.disabled_skills,
        session_ttl_minutes=runtime_config.agents.defaults.session_ttl_minutes,
        tools_config=runtime_config.tools,
    )

    model_name = runtime_config.agents.defaults.model
    print(f"Starting OpenAI-compatible API server")
    print(f"  Endpoint : http://{host}:{port}/v1/chat/completions")
    print(f"  Model    : {model_name}")
    print("  Session  : api:default")
    print(f"  Timeout  : {timeout}s")
    if host in {"0.0.0.0", "::"}:
        print(
            "Warning: API is bound to all interfaces. "
            "Only do this behind a trusted network boundary, firewall, or reverse proxy."
        )
    print()

    api_app = create_app(agent_loop, model_name=model_name, request_timeout=timeout)
    web.run_app(api_app, host=host, port=port)


# ============================================================================
# Gateway / Server
# ============================================================================


@app.command()
def gateway(
    port: int = typer.Option(8080, "--port", "-p", help="Gateway port"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """Start the minibot gateway."""
    from minibot.agent.loop import AgentLoop
    from minibot.bus.bus import MessageBus
    from minibot.session.manager import SessionManager

    config = _load_runtime_config(config, workspace)

    print(f"Starting minibot gateway version {__version__} on port {port}...")
    bus = MessageBus()
    provider = _make_provider(config)
    session_manager = SessionManager(config.workspace_path)

    # Create agent
    agent = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=config.workspace_path,
        model=config.agents.defaults.model,
        max_iterations=config.agents.defaults.max_tool_iterations,
        context_window_tokens=config.agents.defaults.context_window_tokens,
        web_config=config.tools.web,
        context_block_limit=config.agents.defaults.context_block_limit,
        max_tool_result_chars=config.agents.defaults.max_tool_result_chars,
        provider_retry_mode=config.agents.defaults.provider_retry_mode,
        exec_config=config.tools.exec,
        restrict_to_workspace=config.tools.restrict_to_workspace,
        session_manager=session_manager,
        mcp_servers=config.tools.mcp_servers,
        timezone=config.agents.defaults.timezone,
        unified_session=config.agents.defaults.unified_session,
        disabled_skills=config.agents.defaults.disabled_skills,
        session_ttl_minutes=config.agents.defaults.session_ttl_minutes,
        tools_config=config.tools,
    )

    print("✓ Gateway started successfully")
    print(f"✓ Health endpoint: http://localhost:{port}/health")

    async def run():
        try:
            await agent.run()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            agent.stop()

    asyncio.run(run())


# ============================================================================
# Agent Commands
# ============================================================================


@app.command()
def agent(
    message: Optional[str] = typer.Option(None, "--message", "-m", help="Message to send to the agent"),
    session_id: str = typer.Option("cli:direct", "--session", "-s", help="Session ID"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace directory"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Config file path"),
    markdown: bool = typer.Option(True, "--markdown/--no-markdown", help="Render assistant output as Markdown"),
):
    """Interact with the agent directly."""
    from minibot.agent.loop import AgentLoop
    from minibot.bus.bus import MessageBus

    config = _load_runtime_config(config, workspace)

    bus = MessageBus()
    provider = _make_provider(config)

    agent_loop = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=config.workspace_path,
        model=config.agents.defaults.model,
        max_iterations=config.agents.defaults.max_tool_iterations,
        context_window_tokens=config.agents.defaults.context_window_tokens,
        web_config=config.tools.web,
        context_block_limit=config.agents.defaults.context_block_limit,
        max_tool_result_chars=config.agents.defaults.max_tool_result_chars,
        provider_retry_mode=config.agents.defaults.provider_retry_mode,
        exec_config=config.tools.exec,
        restrict_to_workspace=config.tools.restrict_to_workspace,
        mcp_servers=config.tools.mcp_servers,
        timezone=config.agents.defaults.timezone,
        unified_session=config.agents.defaults.unified_session,
        disabled_skills=config.agents.defaults.disabled_skills,
        session_ttl_minutes=config.agents.defaults.session_ttl_minutes,
        tools_config=config.tools,
    )

    if message:
        # Single message mode
        async def run_once():
            # Simplified implementation, directly call agent_loop's processing method
            # Actual implementation needs to be adjusted based on agent_loop's API
            await asyncio.sleep(1)  # Simulate processing time
            response_text = f"Hello, I received your message: {message}"
            _print_agent_response(
                response_text,
                render_markdown=markdown,
            )

        asyncio.run(run_once())
    else:
        # Interactive mode
        print(f"Interactive mode ({config.agents.defaults.model}) — type exit or Ctrl+C to quit\n")

        async def run_interactive():
            bus_task = asyncio.create_task(agent_loop.run())

            try:
                while True:
                    try:
                        user_input = input("You: ")
                        if user_input.lower() in EXIT_COMMANDS:
                            break

                        # Simplified implementation, directly return simulated response
                        # Actual implementation needs to be adjusted based on agent_loop's API
                        await asyncio.sleep(1)  # Simulate processing time
                        response_text = f"Hello, I received your message: {user_input}"
                        _print_agent_response(
                            response_text,
                            render_markdown=markdown,
                        )
                    except KeyboardInterrupt:
                        break
            finally:
                agent_loop.stop()
                bus_task.cancel()

        asyncio.run(run_interactive())


def _load_runtime_config(config: Optional[str] = None, workspace: Optional[str] = None):
    """Load config and optionally override the active workspace."""
    from minibot.config.loader import load_config, resolve_config_env_vars, set_config_path

    config_path = None
    if config:
        config_path = Path(config).expanduser().resolve()
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}")
            raise typer.Exit(1)
        set_config_path(config_path)
        print(f"Using config: {config_path}")

    try:
        loaded = resolve_config_env_vars(load_config(config_path))
    except ValueError as e:
        print(f"Error: {e}")
        raise typer.Exit(1)
    if workspace:
        loaded.agents.defaults.workspace = workspace
    return loaded


def _make_provider(config):
    """Create the appropriate LLM provider from config."""
    model = config.agents.defaults.model
    provider_name = config.get_provider_name(model)
    p = config.get_provider(model)

    if provider_name == "anthropic":
        from minibot.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider(
            api_key=p.api_key if p else None,
            api_base=config.get_api_base(model),
            default_model=model,
            extra_headers=p.extra_headers if p else None,
        )
    else:
        from minibot.providers.openai import OpenAIProvider

        provider = OpenAIProvider(
            api_key=p.api_key if p else None,
            api_base=config.get_api_base(model),
            default_model=model,
            extra_headers=p.extra_headers if p else None,
        )

    return provider
