#!/usr/bin/env python3
"""
Update README.md command/skill tables from plugin metadata.

This script scans commands/*.md and skills/*.md files in plugin directories,
extracts descriptions from frontmatter, and updates the corresponding tables
in README.md while preserving all non-table content.

Usage:
    python scripts/update-readme.py              # Update README.md
    python scripts/update-readme.py --check      # Check if update needed
    python scripts/update-readme.py --verbose    # Show detailed output

The script:
    - Scans all plugins in the plugins/ directory
    - Extracts command/skill descriptions from frontmatter
    - Updates only the command/skill tables in README.md
    - Preserves all other README content

Exit codes:
    0 - Success (or no changes needed with --check)
    1 - Error occurred
    2 - Changes detected (with --check)
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CommandEntry:
    """A command or skill entry for the table."""
    name: str
    description: str
    is_skill: bool
    file_path: str = ""  # Relative path from repo root


def parse_frontmatter(content: str) -> Dict[str, str]:
    """Extract YAML frontmatter from markdown content."""
    frontmatter = {}

    if not content.startswith('---'):
        return frontmatter

    end_idx = content.find('---', 3)
    if end_idx == -1:
        return frontmatter

    fm_content = content[3:end_idx].strip()

    current_key = None
    current_value_lines = []

    for line in fm_content.split('\n'):
        if current_key and (line.startswith('  ') or line.startswith('\t')):
            current_value_lines.append(line.strip())
            continue

        if ':' in line:
            if current_key:
                frontmatter[current_key] = ' '.join(current_value_lines).strip()

            key, _, value = line.partition(':')
            current_key = key.strip()
            value = value.strip()

            if value in ('>', '|', '>-', '|-'):
                current_value_lines = []
            else:
                current_value_lines = [value] if value else []

    if current_key:
        frontmatter[current_key] = ' '.join(current_value_lines).strip()

    return frontmatter


def truncate_to_sentence(text: str, max_length: int = 120) -> str:
    """Truncate text to first complete sentence, or at max_length if no period found.

    Tries to find a natural truncation point at a sentence boundary (period followed
    by space or end of string). If the full first sentence is shorter than max_length,
    returns it. Otherwise, truncates at max_length with ellipsis.
    """
    if len(text) <= max_length:
        return text

    # Look for first sentence end (period followed by space or end)
    # Search within max_length + some buffer to find a sentence end
    search_limit = min(len(text), max_length + 50)

    for i, char in enumerate(text[:search_limit]):
        if char == '.':
            # Check if this is end of sentence (followed by space, newline, or end)
            if i + 1 >= len(text) or text[i + 1] in ' \n\t':
                sentence = text[:i + 1]
                if len(sentence) <= max_length:
                    return sentence
                break  # First sentence is too long, need to truncate

    # No suitable sentence boundary found within limit, truncate with ellipsis
    return text[:max_length - 3].rstrip() + '...'


def scan_plugin(plugin_path: Path, repo_root: Path) -> Tuple[List[CommandEntry], List[CommandEntry]]:
    """Scan a plugin directory and return commands and skills."""
    commands = []
    skills = []

    # Scan commands
    commands_dir = plugin_path / 'commands'
    if commands_dir.exists():
        for md_file in sorted(commands_dir.glob('*.md')):
            try:
                content = md_file.read_text(encoding='utf-8')
                fm = parse_frontmatter(content)
                description = fm.get('description', '')
                # Clean up description
                description = ' '.join(description.split())
                if description:
                    # Get relative path from repo root for linking
                    rel_path = md_file.relative_to(repo_root).as_posix()
                    commands.append(CommandEntry(
                        name=md_file.stem,
                        description=description,
                        is_skill=False,
                        file_path=rel_path
                    ))
            except Exception as e:
                print(f"Warning: Could not read {md_file}: {e}", file=sys.stderr)

    # Scan skills
    skills_dir = plugin_path / 'skills'
    if skills_dir.exists():
        for md_file in sorted(skills_dir.glob('*.md')):
            try:
                content = md_file.read_text(encoding='utf-8')
                fm = parse_frontmatter(content)
                description = fm.get('description', '')
                description = ' '.join(description.split())
                if description:
                    # Get relative path from repo root for linking
                    rel_path = md_file.relative_to(repo_root).as_posix()
                    skills.append(CommandEntry(
                        name=md_file.stem,
                        description=description,
                        is_skill=True,
                        file_path=rel_path
                    ))
            except Exception as e:
                print(f"Warning: Could not read {md_file}: {e}", file=sys.stderr)

    return commands, skills


def generate_table(entries: List[CommandEntry], entry_type: str) -> str:
    """Generate a markdown table for commands or skills.

    Uses natural sentence truncation to avoid mid-word ellipsis,
    and adds hyperlinks to the source files.
    """
    if entry_type == 'Command':
        header = "| Command | Description |\n|---------|-------------|"
    else:
        header = "| Skill | Description |\n|-------|-------------|"

    rows = []
    for entry in entries:
        # Use natural sentence truncation instead of hard character cutoff
        desc = truncate_to_sentence(entry.description, max_length=100)

        # Create hyperlink to source file
        if entry.file_path:
            name_link = f"[`/{entry.name}`]({entry.file_path})"
        else:
            name_link = f"`/{entry.name}`"

        rows.append(f"| {name_link} | {desc} |")

    return header + "\n" + "\n".join(rows)


def update_readme_section(readme_content: str, plugin_name: str,
                          commands: List[CommandEntry],
                          skills: List[CommandEntry],
                          verbose: bool = False) -> str:
    """Update the tables for a specific plugin in README content."""

    # Find the plugin section
    plugin_section_pattern = rf'(### {re.escape(plugin_name)}.*?)(?=### |\Z)'
    plugin_match = re.search(plugin_section_pattern, readme_content, re.DOTALL)

    if not plugin_match:
        if verbose:
            print(f"  Warning: Plugin section '{plugin_name}' not found in README")
        return readme_content

    section_content = plugin_match.group(1)
    section_start = plugin_match.start()
    section_end = plugin_match.end()

    # Update Commands table if commands exist
    if commands:
        commands_table = generate_table(commands, 'Command')

        # Pattern to match existing commands table (header + separator + rows)
        commands_pattern = r'(\*\*Commands:\*\*\n)((?:\|[^\n]+\n)+)'
        commands_match = re.search(commands_pattern, section_content)

        if commands_match:
            # Replace entire table including header
            new_section = section_content[:commands_match.start(2)] + \
                          commands_table + '\n' + \
                          section_content[commands_match.end(2):]
            section_content = new_section
            if verbose:
                print(f"  Updated Commands table ({len(commands)} entries)")
        else:
            if verbose:
                print(f"  Warning: Commands table not found for {plugin_name}")

    # Update Skills table if skills exist
    if skills:
        skills_table = generate_table(skills, 'Skill')

        # Pattern to match existing skills table (header + separator + rows)
        skills_pattern = r'(\*\*Skills:\*\*\n)((?:\|[^\n]+\n)+)'
        skills_match = re.search(skills_pattern, section_content)

        if skills_match:
            # Replace entire table including header
            new_section = section_content[:skills_match.start(2)] + \
                          skills_table + '\n' + \
                          section_content[skills_match.end(2):]
            section_content = new_section
            if verbose:
                print(f"  Updated Skills table ({len(skills)} entries)")
        else:
            if verbose:
                print(f"  Warning: Skills table not found for {plugin_name}")

    # Reconstruct README with updated section
    return readme_content[:section_start] + section_content + readme_content[section_end:]


def main():
    parser = argparse.ArgumentParser(
        description='Update README.md command/skill tables from plugin metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if README needs updating without writing'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    args = parser.parse_args()

    # Find repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    plugins_dir = repo_root / 'plugins'
    readme_path = repo_root / 'README.md'

    if not plugins_dir.exists():
        print(f"Error: plugins directory not found at {plugins_dir}", file=sys.stderr)
        sys.exit(1)

    if not readme_path.exists():
        print(f"Error: README.md not found at {readme_path}", file=sys.stderr)
        sys.exit(1)

    # Read current README
    readme_content = readme_path.read_text(encoding='utf-8')
    original_content = readme_content

    print("Scanning plugins...")

    # Process each plugin
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        if not (plugin_dir / '.claude-plugin').exists():
            continue

        plugin_name = plugin_dir.name
        print(f"  Processing {plugin_name}...")

        commands, skills = scan_plugin(plugin_dir, repo_root)

        if args.verbose:
            print(f"    Found {len(commands)} commands, {len(skills)} skills")

        readme_content = update_readme_section(
            readme_content,
            plugin_name,
            commands,
            skills,
            verbose=args.verbose
        )

    # Check for changes
    if readme_content == original_content:
        print("\nREADME.md is up to date.")
        sys.exit(0)

    if args.check:
        print("\nREADME.md needs updating.")
        print("Run without --check to apply updates.")
        sys.exit(2)

    # Write updated README
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"\nUpdated: {readme_path}")
    sys.exit(0)


if __name__ == '__main__':
    main()
