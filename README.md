# minibot

minibot is an ultra-lightweight personal AI assistant framework inspired by nanobot.
Delivers core agent functionality with 99% fewer lines of code.

## Features

- **Ultra-Lightweight**: Minimal footprint means faster startup, lower resource usage, and quicker iterations.
- **Research-Ready**: Clean, readable code that's easy to understand, modify, and extend for research.
- **Easy-to-Use**: One-click to deploy and you're ready to go.
- **Multi-Provider Support**: Integrates with OpenAI, Anthropic, and Ollama (local LLM) APIs.
- **Multi-Channel Support**: Includes CLI and Feishu (飞书) channels for easy interaction.
- **Voice Interaction**: Voice input/output, speech recognition (Whisper), and text-to-speech (TTS).
- **Image Processing**: Image analysis, OCR, face recognition, object detection, and image generation.
- **Multilingual Support**: Real-time translation, language detection, and localization.
- **Knowledge Management**: Knowledge graphs, document management, knowledge base, and information extraction.
- **System Integration**: Smart home control, calendar management, email, messaging apps, and database integration.
- **Development Tools**: Code generation, code analysis, testing, and deployment automation.
- **Personalization**: User profiling, recommendations, continuous learning, and adaptive dialogue.
- **Multimodal Interaction**: Video understanding, 3D model interaction, VR/AR support.
- **Collaboration**: Multi-user collaboration, shared sessions, team tasks, and collaborative editing.
- **Deployment Options**: Docker support, cloud deployment, edge deployment, and mobile app support.
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
pip install speechrecognition pyaudio gtts pyttsx3 # For voice tools
pip install opencv-python pillow pytesseract # For image tools
pip install googletrans langdetect transformers # For language tools
pip install networkx py2neo langchain openai # For knowledge tools
pip install pyjokes pyowm requests pymysql # For integration tools
pip install pycodestyle pylint radon # For development tools
pip install numpy scikit-learn # For personalization tools
pip install open3d # For 3D model tools
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

## Tools

minibot includes a comprehensive set of tools:

### Voice Tools
- **voice_input**: Voice input with microphone, converts speech to text
- **voice_output**: Text-to-speech output
- **whisper_recognition**: High-quality speech recognition using Whisper
- **tts**: Text-to-speech with multiple TTS engines

### Image Tools
- **image_analysis**: Analyze images and generate descriptions
- **ocr**: Extract text from images
- **face_recognition**: Detect and analyze faces
- **object_detection**: Detect objects in images
- **image_generation**: Generate images from text descriptions

### Language Tools
- **translation**: Real-time translation between languages
- **language_detection**: Automatically detect input language
- **multilingual_model**: Process text with multilingual models
- **localization**: Support for different regional cultures

### Knowledge Tools
- **knowledge_graph**: Build and query knowledge graphs
- **document_management**: Upload, index, and search documents
- **knowledge_base**: Create and manage knowledge bases
- **information_extraction**: Extract structured information from text

### Integration Tools
- **smart_home**: Control smart home devices
- **calendar**: Manage calendars and schedules
- **email**: Read and send emails
- **messaging**: Integrate with messaging apps
- **database**: Connect to various databases

### Development Tools
- **code_generation**: Generate code from requirements
- **code_analysis**: Analyze code quality
- **testing**: Auto-generate and run tests
- **deployment**: Automate deployment workflows

### Personalization Tools
- **user_profile**: Build user interest profiles
- **recommendation**: Personalized content recommendations
- **continuous_learning**: Learn from user interactions
- **adaptive_dialogue**: Adjust dialogue style based on user

### Multimodal Tools
- **video_understanding**: Analyze video content
- **3d_model**: View and manipulate 3D models
- **vr**: Virtual reality interactions
- **ar**: Augmented reality information overlay

### Collaboration Tools
- **multi_user_collaboration**: Support multiple users
- **shared_session**: Share conversation history
- **team_task**: Assign and track team tasks
- **collaborative_editing**: Multiple users editing documents

### Deployment Tools
- **docker**: Docker containerization support
- **cloud_deployment**: Deploy to AWS, Azure, GCP
- **edge_deployment**: Deploy to edge devices
- **mobile_app**: iOS and Android app support

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
│   ├── tools/      # Tool implementations
│   │   ├── voice.py      # Voice interaction tools
│   │   ├── image.py      # Image processing tools
│   │   ├── language.py   # Multilingual support tools
│   │   ├── knowledge.py  # Knowledge management tools
│   │   ├── integration.py # System integration tools
│   │   ├── development.py # Development tools
│   │   ├── personalization.py # Personalization tools
│   │   ├── multimodal.py # Multimodal interaction tools
│   │   ├── collaboration.py # Collaboration tools
│   │   ├── deployment.py  # Deployment tools
│   │   ├── sandbox.py     # Sandbox tool
│   │   └── notebook.py    # Notebook tool
│   ├── autocompact.py # Auto-compaction for sessions
│   ├── hook.py     # Agent lifecycle hooks
│   └── subagent.py # Subagent support
├── api/            # OpenAI-compatible API server
├── bus/            # Message bus for communication
├── channels/       # Channel implementations
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
