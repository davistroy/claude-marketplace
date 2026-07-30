#!/usr/bin/env python3
"""
Regenerate the plugin inventory in README.md and CLAUDE.md from plugin metadata.

This script scans commands/*.md, skills/*/SKILL.md and agents/*.md files in
plugin directories and rewrites the derived inventory in every registered
target, preserving all hand-written content around it.

Targets:
    README.md   - the per-plugin Command/Skill description tables and the
                  prose/header counts that accompany them.
    CLAUDE.md   - the name lists inside the "Repository Structure" tree, which
                  is delimited by BEGIN:inventory / END:inventory HTML comments.
                  Only `commands/`, `skills/` and `agents/` lines nested under
                  `plugins/<name>/` are regenerated; every other line in the
                  tree (`deprecated/`, `references/`, `tools/`, `hooks/`, and
                  the top-level `.claude/agents/` block) is hand-written and is
                  left byte-for-byte alone. Nothing outside the two markers is
                  ever touched -- notably the curated "Command Patterns" table.

Usage:
    python scripts/update-readme.py              # Update all targets
    python scripts/update-readme.py --check      # Check if an update is needed
    python scripts/update-readme.py --verbose    # Show detailed output

Exit codes:
    0 - Success (or no changes needed with --check)
    1 - Error occurred
    2 - Changes detected (with --check)
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


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


def scan_plugin(plugin_path: Path,
                repo_root: Path) -> Tuple[List[CommandEntry], List[CommandEntry]]:
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

    # Scan skills (nested layout: skills/<name>/SKILL.md — NOT a flat glob).
    # Deliberately `glob('*/SKILL.md')` rather than `rglob('*.md')`: rglob would
    # also pick up the ~15 frontmatter-less reference .md files living under
    # skills/*/ (e.g. references/, templates/) and choke on them.
    skills_dir = plugin_path / 'skills'
    if skills_dir.exists():
        for md_file in sorted(skills_dir.glob('*/SKILL.md')):
            try:
                content = md_file.read_text(encoding='utf-8')
                fm = parse_frontmatter(content)
                description = fm.get('description', '')
                description = ' '.join(description.split())
                if description:
                    # Get relative path from repo root for linking
                    rel_path = md_file.relative_to(repo_root).as_posix()
                    skills.append(CommandEntry(
                        name=md_file.parent.name,
                        description=description,
                        is_skill=True,
                        file_path=rel_path
                    ))
            except Exception as e:
                print(f"Warning: Could not read {md_file}: {e}", file=sys.stderr)

    return commands, skills


def scan_agent_names(plugin_path: Path) -> List[str]:
    """Return the sorted agent names shipped by a plugin (agents/*.md stems).

    Agents are a flat directory of markdown files, unlike the nested skill
    layout. They carry no README table of their own -- this exists purely so
    the CLAUDE.md tree can name them instead of omitting the directory.
    """
    agents_dir = plugin_path / 'agents'
    if not agents_dir.exists():
        return []
    return sorted(md_file.stem for md_file in agents_dir.glob('*.md')
                  if md_file.stem != 'README')


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


def rewrite_prose_counts(section_content: str,
                          commands: List[CommandEntry],
                          skills: List[CommandEntry]) -> str:
    """Surgically rewrite the count tokens in a plugin section's prose.

    Touches exactly two things, and nothing else in the surrounding text:
      1. The "N commands and M skills" summary sentence, if present.
      2. The "**N Commands:**" / "**M Skills:**" table header counts, if present.

    Both substitutions are no-ops when the corresponding text isn't present
    (e.g. a plugin with zero commands has no "Commands:" header to rewrite),
    so this never fabricates a section that wasn't there before.
    """
    n_commands = len(commands)
    n_skills = len(skills)

    # "N commands and M skills" prose sentence (personal-plugin style intro).
    section_content = re.sub(
        r'\d+ commands and \d+ skills',
        f'{n_commands} commands and {n_skills} skills',
        section_content,
        count=1,
    )

    # "**N Commands:**" table header (optional existing count prefix).
    section_content = re.sub(
        r'\*\*(?:\d+ )?Commands:\*\*',
        f'**{n_commands} Commands:**',
        section_content,
        count=1,
    )

    # "**M Skills:**" table header (optional existing count prefix).
    section_content = re.sub(
        r'\*\*(?:\d+ )?Skills:\*\*',
        f'**{n_skills} Skills:**',
        section_content,
        count=1,
    )

    return section_content


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

    # Rewrite prose/header counts before touching the tables themselves —
    # the table-anchor regexes below tolerate either the old or new header
    # text, so ordering relative to the table rewrite doesn't matter.
    section_content = rewrite_prose_counts(section_content, commands, skills)

    # Update Commands table if commands exist
    if commands:
        commands_table = generate_table(commands, 'Command')

        # Pattern to match existing commands table (header + separator + rows).
        # Tolerates an optional "N " count prefix on the header, e.g.
        # "**23 Commands:**", since rewrite_prose_counts() may have just
        # written one (or the README may already carry one).
        commands_pattern = r'(\*\*(?:\d+ )?Commands:\*\*\n)((?:\|[^\n]+\n)+)'
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

        # Pattern to match existing skills table (header + separator + rows).
        # Tolerates an optional "N " count prefix on the header, same as above.
        skills_pattern = r'(\*\*(?:\d+ )?Skills:\*\*\n)((?:\|[^\n]+\n)+)'
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


# --- CLAUDE.md "Repository Structure" inventory -----------------------------
#
# The tree is a plain code fence, so there is no in-band way to mark generated
# spans. The region is therefore delimited by explicit HTML comment anchors,
# and *within* that region only three directory keys are considered derived.
# Everything else -- including all four hand-written annotations (`# Archived
# commands`, the hedged personal-plugin `references/` list, `# BPMN element
# docs and guides`, and the ADR-0005 note on `.claude/agents/`) -- is preserved
# verbatim, exactly the way rewrite_prose_counts() leaves README prose alone.

INVENTORY_BEGIN = '<!-- BEGIN:inventory -->'
INVENTORY_END = '<!-- END:inventory -->'


class InventoryError(Exception):
    """The CLAUDE.md inventory region is unusable (missing anchor, missing plugin).

    Raised rather than warned-and-skipped on purpose. Every one of these
    conditions makes the regeneration a no-op, and a no-op that exits 0 is a
    guard that cannot fail -- the exact defect this script shipped once before.
    """

# Directory keys under `plugins/<name>/` whose comment name-list is derived.
GENERATED_DIRS = ('commands', 'skills', 'agents')

# Column at which the `#` of a tree comment starts, and the wrap width. Both
# match the hand-written style already in the file.
COMMENT_COLUMN = 23
MAX_LINE_WIDTH = 100

# `    skills/ (29)      # name, name, ...` -- the count and the comment are
# both optional so a bare `    agents/` line is still recognised and filled in.
_ENTRY_RE = re.compile(
    r'^ {4}(?P<dir>' + '|'.join(GENERATED_DIRS) + r')/'
    r'(?P<count> \(\d+\))?'
    r'(?: +#.*)?$'
)
# A wrapped continuation of the comment above: whitespace, then `#`.
_CONT_RE = re.compile(r'^ +#')
# `  plugin-name/` nested directly under a top-level `plugins/`.
_PLUGIN_RE = re.compile(r'^ {2}(?P<name>[A-Za-z0-9._-]+)/$')


def render_tree_entry(dir_key: str, has_count: bool, names: List[str]) -> List[str]:
    """Render one `<dir>/ (N)   # a, b, c` tree entry, wrapped at MAX_LINE_WIDTH.

    Continuation lines are indented to COMMENT_COLUMN so the comment block
    stays aligned. The trailing comma is kept on the wrapped line, matching the
    existing hand-written style.
    """
    prefix = f'    {dir_key}/'
    if has_count:
        prefix += f' ({len(names)})'
    prefix = prefix.ljust(COMMENT_COLUMN)

    body_width = MAX_LINE_WIDTH - COMMENT_COLUMN - len('# ')

    chunks: List[str] = []
    current = ''
    for i, name in enumerate(names):
        token = name if i == len(names) - 1 else name + ','
        candidate = f'{current} {token}' if current else token
        if current and len(candidate) > body_width:
            chunks.append(current)
            current = token
        else:
            current = candidate
    if current:
        chunks.append(current)
    if not chunks:
        chunks = ['']

    lines = [f'{prefix}# {chunks[0]}'.rstrip()]
    pad = ' ' * COMMENT_COLUMN
    lines.extend(f'{pad}# {chunk}'.rstrip() for chunk in chunks[1:])
    return lines


def rewrite_inventory_block(block: str, inventory: Dict[str, Dict[str, List[str]]],
                            verbose: bool = False) -> str:
    """Rewrite the derived name lists inside the CLAUDE.md inventory block.

    Walks the block line by line tracking which `plugins/<name>/` subtree the
    cursor is in. A line matching _ENTRY_RE at indent 4 inside a known plugin
    is replaced (together with its wrapped continuation lines) by a freshly
    rendered list. Every other line is copied through untouched -- including
    the `.claude/agents/` entry at the end, which sits at indent 2 outside any
    plugin subtree and so can never match.
    """
    out: List[str] = []
    lines = block.split('\n')
    in_plugins = False
    plugin: str = ''
    seen_plugins: set = set()

    i = 0
    while i < len(lines):
        line = lines[i]

        if line and not line.startswith(' ') and not line.startswith('#'):
            in_plugins = line.strip() == 'plugins/'
            plugin = ''
            out.append(line)
            i += 1
            continue

        plugin_match = _PLUGIN_RE.match(line)
        if plugin_match:
            plugin = plugin_match.group('name') if in_plugins else ''
            if plugin:
                seen_plugins.add(plugin)
            out.append(line)
            i += 1
            continue

        entry_match = _ENTRY_RE.match(line) if plugin in inventory else None
        if entry_match:
            dir_key = entry_match.group('dir')
            names = inventory[plugin].get(dir_key, [])
            # Never fabricate: an entry for a directory the plugin does not
            # ship is left exactly as the author wrote it.
            if names:
                out.extend(render_tree_entry(
                    dir_key,
                    has_count=entry_match.group('count') is not None,
                    names=names,
                ))
                if verbose:
                    print(f"  Rendered {plugin}/{dir_key}/ ({len(names)} entries)")
                # Swallow the old wrapped continuation lines.
                i += 1
                while i < len(lines) and _CONT_RE.match(lines[i]):
                    i += 1
                continue

        out.append(line)
        i += 1

    # A plugin absent from the tree would silently regenerate nothing.
    missing = sorted(set(inventory) - seen_plugins)
    if missing:
        raise InventoryError(
            f"plugin(s) {', '.join(missing)} exist on disk but have no "
            f"`  <name>/` node under `plugins/` in the CLAUDE.md inventory block"
        )

    return '\n'.join(out)


def update_claude_md(content: str, inventory: Dict[str, Dict[str, List[str]]],
                     verbose: bool = False) -> str:
    """Regenerate the anchored inventory region of CLAUDE.md.

    Raises InventoryError if the anchors are missing or inverted. It must not
    fall back to rewriting the whole file (destructive) *or* to returning the
    content unchanged (which would make --check pass on an unchecked file).
    """
    begin = content.find(INVENTORY_BEGIN)
    end = content.find(INVENTORY_END)

    if begin == -1 or end == -1 or end < begin:
        raise InventoryError(
            f"{INVENTORY_BEGIN} / {INVENTORY_END} anchors missing or inverted "
            f"in CLAUDE.md -- the inventory region cannot be located"
        )

    inner_start = begin + len(INVENTORY_BEGIN)
    rewritten = rewrite_inventory_block(content[inner_start:end], inventory, verbose)
    return content[:inner_start] + rewritten + content[end:]


def main():
    parser = argparse.ArgumentParser(
        description='Regenerate README.md and CLAUDE.md inventory from plugin metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if any target needs updating without writing'
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
    target_paths = [repo_root / 'README.md', repo_root / 'CLAUDE.md']

    if not plugins_dir.exists():
        print(f"Error: plugins directory not found at {plugins_dir}", file=sys.stderr)
        sys.exit(1)

    for target_path in target_paths:
        if not target_path.exists():
            print(f"Error: {target_path.name} not found at {target_path}", file=sys.stderr)
            sys.exit(1)

    print("Scanning plugins...")

    # One scan, many targets: every renderer below reads from this.
    entries: Dict[str, Tuple[List[CommandEntry], List[CommandEntry]]] = {}
    inventory: Dict[str, Dict[str, List[str]]] = {}

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        if not (plugin_dir / '.claude-plugin').exists():
            continue

        plugin_name = plugin_dir.name
        print(f"  Processing {plugin_name}...")

        commands, skills = scan_plugin(plugin_dir, repo_root)
        agents = scan_agent_names(plugin_dir)

        entries[plugin_name] = (commands, skills)
        inventory[plugin_name] = {
            'commands': [c.name for c in commands],
            'skills': [s.name for s in skills],
            'agents': agents,
        }

        if args.verbose:
            print(f"    Found {len(commands)} commands, {len(skills)} skills, "
                  f"{len(agents)} agents")

    readme_path, claude_md_path = target_paths

    readme_original = readme_path.read_text(encoding='utf-8')
    readme_content = readme_original
    for plugin_name, (commands, skills) in entries.items():
        readme_content = update_readme_section(
            readme_content,
            plugin_name,
            commands,
            skills,
            verbose=args.verbose
        )

    claude_md_original = claude_md_path.read_text(encoding='utf-8')
    try:
        claude_md_content = update_claude_md(claude_md_original, inventory,
                                             verbose=args.verbose)
    except InventoryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    results = [
        (readme_path, readme_original, readme_content),
        (claude_md_path, claude_md_original, claude_md_content),
    ]
    drifted = [(path, updated) for path, original, updated in results
               if original != updated]

    if not drifted:
        print("\n" + ", ".join(p.name for p in target_paths) + " are up to date.")
        sys.exit(0)

    if args.check:
        print()
        for path, _ in drifted:
            print(f"{path.name} needs updating.")
        print("Run without --check to apply updates.")
        sys.exit(2)

    print()
    for path, updated in drifted:
        path.write_text(updated, encoding='utf-8')
        print(f"Updated: {path}")
    sys.exit(0)


if __name__ == '__main__':
    main()
