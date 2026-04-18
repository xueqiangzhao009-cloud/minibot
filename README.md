# minibot

minibot is an ultra-lightweight personal AI assistant framework inspired by nanobot.
Delivers core agent functionality with 99% fewer lines of code.

## Features

- **Ultra-Lightweight**: Minimal footprint means faster startup, lower resource usage, and quicker iterations.
- **Research-Ready**: Clean, readable code that's easy to understand, modify, and extend for research.
- **Easy-to-Use**: One-click to deploy and you're ready to go.
- **Multi-Provider Support**: Integrates with OpenAI, Anthropic, and Ollama (local LLM) APIs.
- **Tool Integration**: Supports custom tools and function calling, including filesystem, shell, web, sandbox, and notebook tools.
- **Multi-Channel Support**: Includes CLI and Feishu (飞书) channels for easy interaction.
- **Session Management**: Maintains conversation history with persistent session storage.
- **Auto-Compaction**: Proactive compression of idle sessions to reduce token cost and latency.
- **Skills System**: Extensible skill framework for adding new capabilities.
- **Skill-Creator**: Dedicated skill for creating and managing skills with scripts, references, and assets.
- **API Server**: OpenAI-compatible API server for integration with other applications.
- **Gateway Service**: Gateway service for running minibot as a background service.
- **Cron Jobs**: Built-in scheduling support for automated tasks.
- **Heartbeat Service**: Regular health checks and task monitoring.
- **Subagent Support**: Background task execution with real-time status tracking.

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/xueqiangzhao009-cloud/minibot.git
cd minibot

# Install with pip
pip install -e .

# Optional: Install additional dependencies for new features
pip install lark-oapi # For Feishu channel
pip install jupyter # For notebook tool
pip install bubblewrap # For sandbox tool
```

## Configuration

Create a config file or use environment variables:

```bash
# Run onboard command to initialize configuration
python -m minibot onboard
```

### Environment Variables

```env
# OpenAI API Key
OPENAI_API_KEY=your-openai-api-key

# Anthropic API Key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Ollama Settings (local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Feishu (飞书) Settings
FEISHU_APP_ID=your-feishu-app-id
FEISHU_APP_SECRET=your-feishu-app-secret
FEISHU_ENCRYPT_KEY=your-feishu-encrypt-key (optional)
FEISHU_VERIFICATION_TOKEN=your-feishu-verification-token (optional)
```

## Usage

### Initialize Configuration

```bash
python -m minibot onboard
```

### Interact with Agent

```bash
# Interactive mode
python -m minibot agent

# Single message mode
python -m minibot agent -m "Hello, how are you?"
```

### Start API Server

```bash
python -m minibot serve --port 8000
```

The API server provides an OpenAI-compatible endpoint at `/v1/chat/completions`.

### Start Gateway

```bash
python -m minibot gateway --port 8080
```

## Skills

minibot includes several built-in skills:

- **weather**: Get current weather and forecasts
- **cron**: Schedule tasks and reminders
- **memory**: Store and retrieve information
- **summarize**: Summarize text and documents
- **github**: Interact with GitHub repositories
- **calculator**: Perform mathematical calculations
- **skill-creator**: Create and manage skills with scripts, references, and assets

## Architecture

```
minibot/
├── agent/          # Core agent logic
│   ├── tools/      # Tool implementations (sandbox, notebook)
│   ├── autocompact.py # Auto-compaction for sessions
│   ├── hook.py     # Agent lifecycle hooks
│   └── subagent.py # Subagent support
├── api/            # OpenAI-compatible API server
├── bus/            # Message bus for communication
├── channels/       # Channel implementations (CLI, Feishu)
│   └── feishu.py   # Feishu (飞书) channel
├── cli/            # CLI commands
├── config/         # Configuration management
├── cron/           # Cron job scheduling
├── heartbeat/      # Heartbeat service
├── providers/      # LLM provider integrations
│   └── ollama.py   # Ollama (local LLM) provider
├── security/       # Security utilities
├── session/        # Session management
├── skills/         # Built-in skills
│   └── skill-creator/ # Skill creation and management
├── templates/      # Templates for agents
└── utils/         # Utility functions
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License