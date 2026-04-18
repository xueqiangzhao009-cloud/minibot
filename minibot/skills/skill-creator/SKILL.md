---
name: skill-creator
description: Create or update AgentSkills. Use when designing, structuring, or packaging skills with scripts, references, and assets.
---

# Skill Creator

This skill provides guidance for creating effective skills.

## About Skills

Skills are modular, self-contained packages that extend the agent's capabilities by providing specialized knowledge, workflows, and tools. Think of them as "onboarding guides" for specific domains or tasks.

### What Skills Provide

1. Specialized workflows - Multi-step procedures for specific domains
2. Tool integrations - Instructions for working with specific file formats or APIs
3. Domain expertise - Company-specific knowledge, schemas, business logic
4. Bundled resources - Scripts, references, and assets for complex and repetitive tasks

## Core Principles

### Concise is Key

The context window is a public good. Skills share the context window with everything else the agent needs.

**Default assumption: the agent is already very smart.** Only add context the agent doesn't already have.

### Degrees of Freedom

Match the level of specificity to the task's fragility and variability:

- **High freedom**: Text-based instructions for when multiple approaches are valid
- **Medium freedom**: Pseudocode or scripts with parameters
- **Low freedom**: Specific scripts when operations are fragile and consistency is critical

### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation loaded as needed
    └── assets/           - Files used in output (templates, icons)
```

#### SKILL.md Structure

Every SKILL.md consists of:

- **Frontmatter** (YAML): Contains `name` and `description` fields
- **Body** (Markdown): Instructions and guidance

#### Bundled Resources

**scripts/**: Executable code for deterministic reliability
**references/**: Documentation loaded into context as needed
**assets/**: Files used in output (templates, images, boilerplate)

## Skill Creation Process

1. Understand the skill with concrete examples
2. Plan reusable skill contents (scripts, references, assets)
3. Initialize the skill (run init_skill.py)
4. Edit the skill (implement resources and write SKILL.md)
5. Package the skill (run package_skill.py)
6. Iterate based on real usage

### Skill Naming

- Use lowercase letters, digits, and hyphens only
- Keep names under 64 characters
- Prefer short, verb-led phrases

### Initialization

```bash
python scripts/init_skill.py <skill-name> --path <output-directory> [--resources scripts,references,assets] [--examples]
```

### Packaging

```bash
python scripts/package_skill.py <path/to/skill-folder>
```

The packaging script validates and creates a .skill file.

## Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (~100 words): Always in context
2. **SKILL.md body** (<5k words): When skill triggers
3. **Bundled resources**: As needed

Keep SKILL.md body under 500 lines. Split content into separate files when approaching this limit.
