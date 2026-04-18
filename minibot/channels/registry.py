"""Channel registry for minibot."""

import importlib
import os
from pathlib import Path
from typing import Dict, Type

from minibot.channels.base import BaseChannel


_channel_registry: Dict[str, Type[BaseChannel]] = {}


def discover_all() -> Dict[str, Type[BaseChannel]]:
    """Discover all available channels."""
    global _channel_registry
    if _channel_registry:
        return _channel_registry

    # Discover built-in channels
    channels_dir = Path(__file__).parent
    for file in channels_dir.iterdir():
        if file.is_file() and file.suffix == ".py" and file.name != "__init__.py" and file.name != "base.py" and file.name != "manager.py" and file.name != "registry.py":
            module_name = f"minibot.channels.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                for name, obj in module.__dict__.items():
                    if isinstance(obj, type) and issubclass(obj, BaseChannel) and obj != BaseChannel:
                        _channel_registry[obj.name] = obj
            except Exception:
                pass

    return _channel_registry


def find_by_name(name: str) -> Type[BaseChannel] | None:
    """Find a channel by name."""
    return discover_all().get(name)
