#!/usr/bin/env python3
"""Skill Initializer - Creates a new skill from template."""

import argparse
import re
import sys
from pathlib import Path

MAX_SKILL_NAME_LENGTH = 64
ALLOWED_RESOURCES = {"scripts", "references", "assets"}

SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: Complete and informative explanation of what the skill does and when to use it. Include WHEN to use this skill - specific scenarios, file types, or tasks that trigger it.]
---

# {skill_title}

## Overview

[TODO: 1-2 sentences explaining what this skill enables]

## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose]

## [TODO: Add content here]

## Resources (optional)

### scripts/
Executable code (Python/Bash/etc.) that can be run directly.

### references/
Documentation loaded into context as needed.

### assets/
Files used within the output (templates, images, boilerplate).
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""Example helper script for {skill_name}."""

def main():
    print("This is an example script for {skill_name}")

if __name__ == "__main__":
    main()
'''


def normalize_skill_name(skill_name: str) -> str:
    """Normalize a skill name to lowercase hyphen-case."""
    normalized = skill_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized


def title_case_skill_name(skill_name: str) -> str:
    """Convert hyphenated skill name to Title Case for display."""
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def parse_resources(raw_resources: str) -> list:
    """Parse comma-separated resource list."""
    if not raw_resources:
        return []
    resources = [item.strip() for item in raw_resources.split(",") if item.strip()]
    invalid = sorted({item for item in resources if item not in ALLOWED_RESOURCES})
    if invalid:
        allowed = ", ".join(sorted(ALLOWED_RESOURCES))
        print(f"[ERROR] Unknown resource type(s): {', '.join(invalid)}")
        print(f"   Allowed: {allowed}")
        sys.exit(1)
    return list(dict.fromkeys(resources))


def init_skill(skill_name: str, path: str, resources: list, include_examples: bool) -> Path | None:
    """Initialize a new skill directory with template SKILL.md."""
    skill_dir = Path(path).resolve() / skill_name

    if skill_dir.exists():
        print(f"[ERROR] Skill directory already exists: {skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"[OK] Created skill directory: {skill_dir}")
    except Exception as e:
        print(f"[ERROR] Error creating directory: {e}")
        return None

    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(skill_name=skill_name, skill_title=skill_title)

    skill_md_path = skill_dir / "SKILL.md"
    try:
        skill_md_path.write_text(skill_content)
        print("[OK] Created SKILL.md")
    except Exception as e:
        print(f"[ERROR] Error creating SKILL.md: {e}")
        return None

    if resources:
        for resource in resources:
            resource_dir = skill_dir / resource
            resource_dir.mkdir(exist_ok=True)
            print(f"[OK] Created {resource}/")

            if include_examples and resource == "scripts":
                example_script = resource_dir / "example.py"
                example_script.write_text(EXAMPLE_SCRIPT.format(skill_name=skill_name))
                print("[OK] Created scripts/example.py")

    print(f"\n[OK] Skill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Edit SKILL.md to complete the TODO items")
    if resources:
        print(f"2. Add resources to {', '.join(resources)}/ as needed")
    print("3. Run the validator when ready")

    return skill_dir


def main():
    parser = argparse.ArgumentParser(description="Create a new skill directory.")
    parser.add_argument("skill_name", help="Skill name (normalized to hyphen-case)")
    parser.add_argument("--path", required=True, help="Output directory for the skill")
    parser.add_argument("--resources", default="", help="Comma-separated: scripts,references,assets")
    parser.add_argument("--examples", action="store_true", help="Create example files")
    args = parser.parse_args()

    raw_skill_name = args.skill_name
    skill_name = normalize_skill_name(raw_skill_name)

    if not skill_name:
        print("[ERROR] Skill name must include at least one letter or digit.")
        sys.exit(1)

    if len(skill_name) > MAX_SKILL_NAME_LENGTH:
        print(f"[ERROR] Skill name '{skill_name}' is too long ({len(skill_name)} chars). Max: {MAX_SKILL_NAME_LENGTH}")
        sys.exit(1)

    if skill_name != raw_skill_name:
        print(f"Note: Normalized skill name from '{raw_skill_name}' to '{skill_name}'.")

    resources = parse_resources(args.resources)

    if args.examples and not resources:
        print("[ERROR] --examples requires --resources to be set.")
        sys.exit(1)

    print(f"Initializing skill: {skill_name}")
    print(f"   Location: {args.path}")
    if resources:
        print(f"   Resources: {', '.join(resources)}")
    print()

    result = init_skill(skill_name, args.path, resources, args.examples)

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
