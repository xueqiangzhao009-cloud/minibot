"""Built-in commands for minibot."""

from minibot.bus.events import OutboundMessage
from minibot.command.router import CommandContext, CommandRouter


def register_builtin_commands(router: CommandRouter) -> None:
    """Register built-in commands."""
    router.exact("/help", help_command)
    router.exact("/clear", clear_command)
    router.exact("/version", version_command)


async def help_command(ctx: CommandContext) -> OutboundMessage:
    """Show help message."""
    help_text = """Available commands:

/help - Show this help message
/clear - Clear the conversation history
/version - Show minibot version

For more information, visit: https://github.com/minibot-ai/minibot
"""
    return OutboundMessage(
        channel=ctx.msg.channel,
        chat_id=ctx.msg.chat_id,
        content=help_text,
        metadata={}
    )


async def clear_command(ctx: CommandContext) -> OutboundMessage:
    """Clear the conversation history."""
    if ctx.session:
        ctx.session.clear()
    return OutboundMessage(
        channel=ctx.msg.channel,
        chat_id=ctx.msg.chat_id,
        content="Conversation history cleared.",
        metadata={}
    )


async def version_command(ctx: CommandContext) -> OutboundMessage:
    """Show minibot version."""
    from minibot import __version__
    return OutboundMessage(
        channel=ctx.msg.channel,
        chat_id=ctx.msg.chat_id,
        content=f"minibot v{__version__}",
        metadata={}
    )
