#!/usr/bin/env python3
"""
Generate help.md files for Claude Code plugins.

This script scans commands/*.md and skills/*.md files in a plugin directory,
extracts metadata from frontmatter and content, and generates a help.md file
that matches the existing help.md structure.

Usage:
    python scripts/generate-help.py <plugin-path>
    python scripts/generate-help.py plugins/personal-plugin
    python scripts/generate-help.py --all    # Process all plugins
    python scripts/generate-help.py --check  # Validate only, no output

The script extracts:
    - description from frontmatter
    - arguments from "Input Validation" section
    - output from "Output" or "File Naming" sections
    - example from "Example" sections

Exit codes:
    0 - Success
    1 - No changes needed (with --check)
    2 - Changes detected (with --check)
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CommandInfo:
    """Information extracted from a command/skill markdown file."""
    name: str
    description: str
    arguments: str
    output: str
    example: str
    is_skill: bool


def parse_frontmatter(content: str) -> Dict[str, str]:
    """Extract YAML frontmatter from markdown content."""
    frontmatter = {}

    if not content.startswith('---'):
        return frontmatter

    # Find the closing ---
    end_idx = content.find('---', 3)
    if end_idx == -1:
        return frontmatter

    fm_content = content[3:end_idx].strip()

    # Parse simple YAML (key: value pairs)
    current_key = None
    current_value_lines = []

    for line in fm_content.split('\n'):
        # Check for multiline value continuation (starts with whitespace or is '>','|')
        if current_key and (line.startswith('  ') or line.startswith('\t')):
            current_value_lines.append(line.strip())
            continue

        # Check for new key
        if ':' in line:
            # Save previous key if exists
            if current_key:
                frontmatter[current_key] = ' '.join(current_value_lines).strip()

            key, _, value = line.partition(':')
            current_key = key.strip()
            value = value.strip()

            # Handle multiline indicators
            if value in ('>', '|', '>-', '|-'):
                current_value_lines = []
            else:
                current_value_lines = [value] if value else []

    # Save last key
    if current_key:
        frontmatter[current_key] = ' '.join(current_value_lines).strip()

    return frontmatter


def extract_section(content: str, section_names: List[str]) -> Optional[str]:
    """Extract content from a specific section by heading name."""
    lines = content.split('\n')
    in_section = False
    section_lines = []
    section_level = 0

    for line in lines:
        # Check for section header
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)

        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()

            # Check if this is our target section
            title_lower = title.lower()
            is_target = any(name.lower() in title_lower for name in section_names)

            if is_target and not in_section:
                in_section = True
                section_level = level
                continue
            elif in_section and level <= section_level:
                # We've hit a same-level or higher-level heading, stop
                break

        if in_section:
            section_lines.append(line)

    if section_lines:
        return '\n'.join(section_lines).strip()
    return None


def extract_arguments(content: str) -> str:
    """Extract arguments from Input Validation or similar section."""
    section = extract_section(content, ['Input Validation', 'Arguments', 'Usage'])

    if not section:
        return "None required"

    # Look for argument patterns
    args = []

    # Pattern: **Required Arguments:** or **Optional Arguments:**
    req_match = re.search(r'\*\*Required Arguments?:\*\*\s*\n((?:[-*]\s+.+\n?)+)', section)
    if req_match:
        arg_lines = req_match.group(1).strip().split('\n')
        for line in arg_lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('*'):
                arg = line.lstrip('-* ').strip()
                # Extract just the argument name/pattern
                if '`' in arg:
                    # Extract content between backticks
                    backtick_match = re.search(r'`([^`]+)`', arg)
                    if backtick_match:
                        args.append(backtick_match.group(1))
                elif ' - ' in arg:
                    args.append(arg.split(' - ')[0].strip())
                else:
                    args.append(arg)

    # Pattern: Optional Arguments
    opt_match = re.search(r'\*\*Optional Arguments?:\*\*\s*\n((?:[-*]\s+.+\n?)+)', section)
    if opt_match:
        arg_lines = opt_match.group(1).strip().split('\n')
        for line in arg_lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('*'):
                arg = line.lstrip('-* ').strip()
                if '`' in arg:
                    backtick_match = re.search(r'`([^`]+)`', arg)
                    if backtick_match:
                        args.append(f"[{backtick_match.group(1)}]")
                elif ' - ' in arg:
                    args.append(f"[{arg.split(' - ')[0].strip()}]")

    if args:
        return ' '.join(args)

    # Fallback: look for usage patterns in code blocks
    usage_match = re.search(r'Usage:\s*\/\w+\s*(.+?)(?:\n|$)', section)
    if usage_match:
        return usage_match.group(1).strip()

    return "None required"


def extract_output(content: str) -> str:
    """Extract output information from the markdown content."""
    # Try multiple section names
    section = extract_section(content, ['Output', 'File Naming', 'Output Format', 'Output Location'])

    if not section:
        return "In-conversation output"

    # Look for filename patterns
    filename_match = re.search(r'`([^`]+\[.+\][^`]*\.(json|md|docx|txt))`', section)
    if filename_match:
        return filename_match.group(1)

    # Look for Save as patterns
    save_match = re.search(r'[Ss]ave.*?[`"]([^`"]+)[`"]', section)
    if save_match:
        return save_match.group(1)

    # Look for directory mentions
    dir_match = re.search(r'to (?:the )?`([^`]+/)`', section)
    if dir_match:
        return f"Files in {dir_match.group(1)}"

    # Fallback
    return "Generated output file"


def extract_example(content: str, command_name: str) -> str:
    """Extract example usage from the markdown content."""
    # First, look for Example section
    section = extract_section(content, ['Example', 'Usage'])

    # Also search the entire content for code blocks with commands
    all_examples = []

    # Search both section and entire content for better coverage
    search_content = section if section else content

    # Look for code blocks with command examples
    code_blocks = re.findall(r'```(?:bash|sh)?\s*\n(.*?)```', search_content, re.DOTALL)
    for block in code_blocks:
        for line in block.strip().split('\n'):
            line = line.strip()
            if line.startswith(f'/{command_name}'):
                all_examples.append(line)

    if all_examples:
        return '\n'.join(all_examples[:3])  # Return up to 3 examples

    # Look in entire content for examples
    code_blocks = re.findall(r'```(?:bash|sh)?\s*\n(.*?)```', content, re.DOTALL)
    for block in code_blocks:
        for line in block.strip().split('\n'):
            line = line.strip()
            if line.startswith(f'/{command_name}'):
                all_examples.append(line)

    if all_examples:
        return '\n'.join(all_examples[:3])

    # Look for inline command examples with backticks
    inline_matches = re.findall(rf'`(/{command_name}[^`]*)`', content)
    if inline_matches:
        return '\n'.join(inline_matches[:3])

    # Look for Example: pattern
    example_matches = re.findall(rf'Example:\s*`?(/{command_name}[^`\n]+)`?', content)
    if example_matches:
        return '\n'.join(example_matches[:3])

    return f"/{command_name}"


def parse_command_file(filepath: Path, is_skill: bool = False) -> Optional[CommandInfo]:
    """Parse a command or skill markdown file and extract metadata."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
        return None

    # Get command name from filename
    name = filepath.stem

    # Parse frontmatter
    frontmatter = parse_frontmatter(content)
    description = frontmatter.get('description', '')

    # Clean up multiline descriptions
    description = ' '.join(description.split())

    if not description:
        # Try to extract from first paragraph after title
        title_match = re.search(r'^#[^#].+?\n\n(.+?)(?:\n\n|$)', content, re.MULTILINE | re.DOTALL)
        if title_match:
            description = title_match.group(1).strip().replace('\n', ' ')

    # Truncate long descriptions
    if len(description) > 80:
        # Find a good break point
        description = description[:77].rsplit(' ', 1)[0] + '...'

    arguments = extract_arguments(content)
    output = extract_output(content)
    example = extract_example(content, name)

    return CommandInfo(
        name=name,
        description=description,
        arguments=arguments,
        output=output,
        example=example,
        is_skill=is_skill
    )


def scan_plugin_directory(plugin_path: Path) -> Tuple[List[CommandInfo], List[CommandInfo]]:
    """Scan a plugin directory for commands and skills."""
    commands = []
    skills = []

    # Scan commands directory
    commands_dir = plugin_path / 'commands'
    if commands_dir.exists():
        for md_file in sorted(commands_dir.glob('*.md')):
            info = parse_command_file(md_file, is_skill=False)
            if info:
                commands.append(info)

    # Scan skills directory
    skills_dir = plugin_path / 'skills'
    if skills_dir.exists():
        for md_file in sorted(skills_dir.glob('*.md')):
            info = parse_command_file(md_file, is_skill=True)
            if info:
                skills.append(info)

    return commands, skills


def generate_help_content(plugin_name: str, commands: List[CommandInfo], skills: List[CommandInfo]) -> str:
    """Generate the help.md content matching the existing format."""
    lines = [
        "---",
        "description: Show available commands and skills in this plugin with usage information",
        "---",
        "",
        "# Help Skill",
        "",
        f"Display help information for the {plugin_name} commands and skills.",
        "",
        "**IMPORTANT:** This skill must be updated whenever commands or skills are added, changed, or removed from this plugin.",
        "",
        "## Usage",
        "",
        "```",
        "/help                          # Show all commands and skills",
        "/help <command-name>           # Show detailed help for a specific command",
        "```",
        "",
        "## Mode 1: List All (no arguments)",
        "",
        "When invoked without arguments, display this table:",
        "",
        "```",
        f"{plugin_name} Commands and Skills",
        "=" * len(f"{plugin_name} Commands and Skills"),
        "",
    ]

    # Commands section
    if commands:
        lines.extend([
            "COMMANDS",
            "--------",
            "| Command | Description |",
            "|---------|-------------|",
        ])
        for cmd in commands:
            lines.append(f"| /{cmd.name} | {cmd.description} |")
        lines.append("")

    # Skills section
    if skills:
        lines.extend([
            "SKILLS",
            "------",
            "| Skill | Description |",
            "|-------|-------------|",
        ])
        for skill in skills:
            lines.append(f"| /{skill.name} | {skill.description} |")
        lines.append("")

    lines.extend([
        "---",
        "Use '/help <name>' for detailed help on a specific command or skill.",
        "```",
        "",
        "## Mode 2: Detailed Help (with argument)",
        "",
        "When invoked with a command or skill name, read the corresponding file and display:",
        "",
        "1. **Description** - From frontmatter",
        "2. **Arguments** - From \"Input Validation\" section if present",
        "3. **Output** - What the command produces",
        "4. **Example** - Usage example",
        "",
        "### Command Reference",
        "",
        "Use this reference to provide detailed help. Read the actual command file to get the most accurate information.",
        "",
    ])

    # Detailed command reference
    for cmd in commands + skills:
        lines.extend([
            "---",
            "",
            f"#### /{cmd.name}",
            f"**Description:** {cmd.description}",
            f"**Arguments:** {cmd.arguments}",
            f"**Output:** {cmd.output}",
            "**Example:**",
            "```",
            cmd.example if cmd.example else f"/{cmd.name}",
            "```",
            "",
        ])

    # Error handling section
    cmd_names = ', '.join(f'/{c.name}' for c in commands)
    skill_names = ', '.join(f'/{s.name}' for s in skills)

    lines.extend([
        "---",
        "",
        "## Error Handling",
        "",
        "If the requested command is not found:",
        "```",
        f"Command '[name]' not found in {plugin_name}.",
        "",
        "Available commands:",
    ])

    if commands:
        lines.append(f"  {cmd_names}")

    if skills:
        lines.extend([
            "",
            "Available skills:",
            f"  {skill_names}",
        ])

    lines.extend([
        "```",
        "",
    ])

    return '\n'.join(lines)


def generate_bpmn_help_content(plugin_name: str, skills: List[CommandInfo]) -> str:
    """Generate help.md content for BPMN plugin (skills only, simpler format)."""
    lines = [
        "---",
        "description: Show available skills in this plugin with usage information",
        "---",
        "",
        "# Help Skill",
        "",
        f"Display help information for the {plugin_name} skills.",
        "",
        "**IMPORTANT:** This skill must be updated whenever skills are added, changed, or removed from this plugin.",
        "",
        "## Usage",
        "",
        "```",
        "/help                          # Show all skills",
        "/help <skill-name>             # Show detailed help for a specific skill",
        "```",
        "",
        "## Mode 1: List All (no arguments)",
        "",
        "When invoked without arguments, display this table:",
        "",
        "```",
        f"{plugin_name} Skills",
        "=" * len(f"{plugin_name} Skills"),
        "",
        "| Skill | Description |",
        "|-------|-------------|",
    ]

    for skill in skills:
        lines.append(f"| /{skill.name} | {skill.description} |")

    lines.extend([
        "",
        "---",
        "Use '/help <name>' for detailed help on a specific skill.",
        "```",
        "",
        "## Mode 2: Detailed Help (with argument)",
        "",
        "When invoked with a skill name, display detailed information.",
        "",
        "### Skill Reference",
        "",
    ])

    # Detailed skill reference
    for skill in skills:
        lines.extend([
            "---",
            "",
            f"#### /{skill.name}",
            f"**Description:** {skill.description}",
            f"**Arguments:** {skill.arguments}",
            f"**Output:** {skill.output}",
            "",
            "**Example:**",
            "```",
            skill.example if skill.example else f"/{skill.name}",
            "```",
            "",
        ])

    # Error handling section
    skill_names = ', '.join(f'/{s.name}' for s in skills)

    lines.extend([
        "---",
        "",
        "## Error Handling",
        "",
        "If the requested skill is not found:",
        "```",
        f"Skill '[name]' not found in {plugin_name}.",
        "",
        "Available skills:",
        f"  {skill_names}",
        "```",
        "",
    ])

    return '\n'.join(lines)


def process_plugin(plugin_path: Path, check_only: bool = False) -> bool:
    """Process a single plugin directory."""
    plugin_name = plugin_path.name
    print(f"Processing {plugin_name}...")

    commands, skills = scan_plugin_directory(plugin_path)

    if not commands and not skills:
        print(f"  Warning: No commands or skills found in {plugin_name}")
        return True

    print(f"  Found {len(commands)} commands, {len(skills)} skills")

    # Generate content based on plugin type
    if commands:
        content = generate_help_content(plugin_name, commands, skills)
    else:
        content = generate_bpmn_help_content(plugin_name, skills)

    # Output path
    help_path = plugin_path / 'skills' / 'help.md'

    if check_only:
        # Compare with existing
        if help_path.exists():
            existing = help_path.read_text(encoding='utf-8')
            if existing.strip() == content.strip():
                print(f"  help.md is up to date")
                return True
            else:
                print(f"  help.md needs updating")
                return False
        else:
            print(f"  help.md does not exist")
            return False

    # Write the file
    help_path.parent.mkdir(parents=True, exist_ok=True)
    help_path.write_text(content, encoding='utf-8')
    print(f"  Generated: {help_path}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Generate help.md files for Claude Code plugins',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        'plugin_path',
        nargs='?',
        help='Path to plugin directory (e.g., plugins/personal-plugin)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all plugins in the plugins/ directory'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if help.md is up to date without writing'
    )

    args = parser.parse_args()

    # Find repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    plugins_dir = repo_root / 'plugins'

    if args.all:
        # Process all plugins
        if not plugins_dir.exists():
            print(f"Error: plugins directory not found at {plugins_dir}", file=sys.stderr)
            sys.exit(1)

        all_ok = True
        for plugin_dir in sorted(plugins_dir.iterdir()):
            if plugin_dir.is_dir() and (plugin_dir / '.claude-plugin').exists():
                ok = process_plugin(plugin_dir, check_only=args.check)
                all_ok = all_ok and ok

        if args.check:
            sys.exit(0 if all_ok else 2)
        sys.exit(0)

    if not args.plugin_path:
        parser.print_help()
        sys.exit(1)

    plugin_path = Path(args.plugin_path)
    if not plugin_path.is_absolute():
        plugin_path = repo_root / plugin_path

    if not plugin_path.exists():
        print(f"Error: Plugin directory not found: {plugin_path}", file=sys.stderr)
        sys.exit(1)

    ok = process_plugin(plugin_path, check_only=args.check)

    if args.check:
        sys.exit(0 if ok else 2)
    sys.exit(0)


if __name__ == '__main__':
    main()
