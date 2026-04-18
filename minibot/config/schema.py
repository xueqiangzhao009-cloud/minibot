"""Configuration schema using Pydantic."""

from pathlib import Path
from typing import Literal, Optional, Dict, List
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_settings import BaseSettings


class Base(BaseModel):
    """Base model with common configuration."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="ignore",
    )


class ProviderConfig(Base):
    """Configuration for a specific LLM provider."""
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None


class WebSearchConfig(Base):
    """Configuration for web search tool."""
    engine: str = "google"
    api_key: Optional[str] = None
    cse_id: Optional[str] = None


class WebToolsConfig(Base):
    """Configuration for web-related tools."""
    enable: bool = True
    search: WebSearchConfig = WebSearchConfig()
    proxy: Optional[str] = None


class ExecToolConfig(Base):
    """Configuration for exec tool."""
    enable: bool = True
    timeout: int = 60
    sandbox: bool = False
    path_append: Optional[str] = None
    allowed_env_keys: Optional[List[str]] = None


class MyToolConfig(Base):
    """Configuration for my tool."""
    enable: bool = True
    allow_set: bool = False


class ToolsConfig(Base):
    """Configuration for tools."""
    web: WebToolsConfig = WebToolsConfig()
    exec: ExecToolConfig = ExecToolConfig()
    my: MyToolConfig = MyToolConfig()
    ssrf_whitelist: List[str] = Field(default_factory=list)
    restrict_to_workspace: bool = False
    mcp_servers: Dict[str, Dict[str, str]] = Field(default_factory=dict)


class AgentDefaults(Base):
    """Default settings for agents."""
    model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 2048
    max_tool_iterations: int = 10
    context_window_tokens: int = 128000
    context_block_limit: Optional[int] = None
    max_tool_result_chars: int = 4000
    provider_retry_mode: str = "standard"
    reasoning_effort: Literal["low", "medium", "high"] = "medium"
    timezone: Optional[str] = None
    unified_session: bool = False
    disabled_skills: List[str] = Field(default_factory=list)
    session_ttl_minutes: int = 0


class AgentsConfig(Base):
    """Configuration for agents."""
    defaults: AgentDefaults = AgentDefaults()


class ChannelConfig(Base):
    """Configuration for a single channel."""
    enable: bool = False


class ChannelsConfig(Base):
    """Configuration for channels."""
    cli: ChannelConfig = ChannelConfig(enable=True)
    telegram: ChannelConfig = ChannelConfig()
    discord: ChannelConfig = ChannelConfig()
    slack: ChannelConfig = ChannelConfig()
    feishu: ChannelConfig = ChannelConfig()


class HeartbeatConfig(Base):
    """Heartbeat configuration."""
    enabled: bool = True
    interval_s: int = 30 * 60
    keep_recent_messages: int = 10


class GatewayConfig(Base):
    """Gateway configuration."""
    host: str = "127.0.0.1"
    port: int = 8080
    heartbeat: HeartbeatConfig = HeartbeatConfig()


class APIConfig(Base):
    """API server configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    timeout: float = 120.0


class Config(Base):
    """Root configuration model."""
    agents: AgentsConfig = AgentsConfig()
    tools: ToolsConfig = ToolsConfig()
    channels: ChannelsConfig = ChannelsConfig()
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    gateway: GatewayConfig = GatewayConfig()
    api: APIConfig = APIConfig()

    @property
    def workspace_path(self) -> Path:
        """Get the workspace path."""
        return Path.home() / ".minibot"

    def get_provider_name(self, model: str) -> Optional[str]:
        """Get the provider name for a given model."""
        if model.startswith("claude-"):
            return "anthropic"
        elif model.startswith("gpt-"):
            return "openai"
        return None

    def get_provider(self, model: str) -> Optional[ProviderConfig]:
        """Get the provider configuration for a given model."""
        provider_name = self.get_provider_name(model)
        if provider_name:
            return self.providers.get(provider_name)
        return None

    def get_api_base(self, model: str) -> Optional[str]:
        """Get the API base URL for a given model."""
        provider = self.get_provider(model)
        if provider:
            return provider.api_base
        return None
