#!/usr/bin/env python3
"""Skill Packager - Validates and packages skills into .skill files."""

import argparse
import sys
import zipfile
from pathlib import Path


def validate_skill(skill_dir: Path) -> tuple[bool, list]:
    """Validate skill structure and frontmatter."""
    errors = []

    if not skill_dir.is_dir():
        errors.append(f"Skill directory does not exist: {skill_dir}")
        return False, errors

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append("SKILL.md is required but not found")
        return False, errors

    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"Failed to read SKILL.md: {e}")
        return False, errors

    if not content.startswith("---"):
        errors.append("SKILL.md must have YAML frontmatter starting with '---'")
        return False, errors

    frontmatter_end = content.find("---\n", 3)
    if frontmatter_end == -1:
        errors.append("SKILL.md must have YAML frontmatter ending with '---'")
        return False, errors

    import yaml
    try:
        frontmatter = yaml.safe_load(content[3:frontmatter_end])
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML frontmatter: {e}")
        return False, errors

    if not isinstance(frontmatter, dict):
        errors.append("Frontmatter must be a YAML dictionary")
        return False, errors

    if "name" not in frontmatter:
        errors.append("Frontmatter must have 'name' field")
    if "description" not in frontmatter:
        errors.append("Frontmatter must have 'description' field")

    name = frontmatter.get("name", "")
    if name and name != skill_dir.name:
        errors.append(f"Skill name in frontmatter ('{name}') must match directory name ('{skill_dir.name}')")

    if not errors:
        valid_resources = {"scripts", "references", "assets"}
        for resource in skill_dir.iterdir():
            if resource.is_dir() and resource.name not in valid_resources:
                errors.append(f"Unknown resource directory '{resource.name}'. Expected one of: {', '.join(sorted(valid_resources))}")

    return len(errors) == 0, errors


def package_skill(skill_dir: Path, output_dir: Path | None = None) -> Path | None:
    """Package skill into a .skill file."""
    is_valid, errors = validate_skill(skill_dir)
    if not is_valid:
        for error in errors:
            print(f"[ERROR] {error}")
        return None

    if output_dir is None:
        output_dir = skill_dir.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    skill_name = skill_dir.name
    output_file = output_dir / f"{skill_name}.skill"

    try:
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in skill_dir.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(skill_dir)
                    zf.write(file, arcname)

        print(f"[OK] Packaged skill to: {output_file}")
        return output_file
    except Exception as e:
        print(f"[ERROR] Failed to create skill package: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Package a skill into a .skill file")
    parser.add_argument("skill_path", help="Path to the skill directory")
    parser.add_argument("output_dir", nargs="?", help="Output directory for the .skill file")
    args = parser.parse_args()

    skill_dir = Path(args.skill_path).resolve()

    if not skill_dir.exists() or not skill_dir.is_dir():
        print(f"[ERROR] Skill directory not found: {skill_dir}")
        sys.exit(1)

    output_dir = Path(args.output_dir).resolve() if args.output_dir else None

    result = package_skill(skill_dir, output_dir)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
