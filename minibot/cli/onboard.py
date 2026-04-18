"""Onboarding wizard for minibot."""

from typing import Dict, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm

from minibot.cli.models import OnboardResult
from minibot.config.schema import Config

console = Console()


def run_onboard(initial_config: Config) -> OnboardResult:
    """Run the interactive onboarding wizard."""
    console.print("[cyan]🤖 minibot Configuration Wizard[/cyan]")
    console.print("Let's set up your minibot configuration.\n")

    # Model selection
    console.print("[bold]Step 1: Choose your AI model[/bold]")
    model = Prompt.ask(
        "Model name",
        default=initial_config.agents.defaults.model,
        show_default=True
    )
    initial_config.agents.defaults.model = model

    # API key setup
    console.print("\n[bold]Step 2: API Configuration[/bold]")
    provider_name = initial_config.get_provider_name(model)
    console.print(f"Detected provider: [cyan]{provider_name}[/cyan]")

    if provider_name == "anthropic":
        api_key = Prompt.ask(
            "Anthropic API key",
            default=initial_config.providers.anthropic.api_key or "",
            show_default=False
        )
        initial_config.providers.anthropic.api_key = api_key
    else:
        api_key = Prompt.ask(
            "OpenAI API key",
            default=initial_config.providers.openai.api_key or "",
            show_default=False
        )
        initial_config.providers.openai.api_key = api_key

    # Workspace setup
    console.print("\n[bold]Step 3: Workspace Setup[/bold]")
    workspace = Prompt.ask(
        "Workspace directory",
        default=str(initial_config.workspace_path),
        show_default=True
    )
    initial_config.agents.defaults.workspace = workspace

    # Tool configuration
    console.print("\n[bold]Step 4: Tool Configuration[/bold]")
    restrict_to_workspace = Confirm.ask(
        "Restrict file operations to workspace",
        default=initial_config.tools.restrict_to_workspace
    )
    initial_config.tools.restrict_to_workspace = restrict_to_workspace

    # Confirmation
    console.print("\n[bold]Configuration Summary[/bold]")
    console.print(f"Model: [cyan]{initial_config.agents.defaults.model}[/cyan]")
    console.print(f"Provider: [cyan]{provider_name}[/cyan]")
    console.print(f"Workspace: [cyan]{initial_config.workspace_path}[/cyan]")
    console.print(f"Restrict to workspace: [cyan]{initial_config.tools.restrict_to_workspace}[/cyan]")

    should_save = Confirm.ask("\nSave this configuration?")

    return OnboardResult(
        config=initial_config.model_dump(),
        should_save=should_save
    )
