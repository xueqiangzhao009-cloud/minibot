# Skills

Skills extend minibot's capabilities through external tools and APIs. Each skill is defined in a directory with a `SKILL.md` file that describes its functionality, usage, and requirements.

## Available Skills

- **weather**: Get current weather and forecasts (no API key required)
- **cron**: Schedule tasks and reminders
- **memory**: Store and retrieve information
- **summarize**: Summarize text and documents
- **github**: Interact with GitHub repositories
- **calculator**: Perform mathematical calculations

## Adding New Skills

To add a new skill, create a new directory under `skills/` with a `SKILL.md` file that follows the standard format:

```yaml
---
name: skill-name
description: Brief description of the skill
homepage: Optional homepage URL
metadata: {"nanobot":{"emoji":"🎯","requires":{"bins":["tool1","tool2"]}}}
---

# Skill Name

Detailed description and usage instructions...
```
