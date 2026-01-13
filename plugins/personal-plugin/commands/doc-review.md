---
description: Comprehensive documentation review and cleanup across the entire project
---

# Documentation Review and Cleanup

You are performing a thorough documentation audit and update for this project. Execute the following systematic process:

## Phase 1: Discovery
1. Map the entire project structure to understand the codebase architecture
2. Identify ALL documentation touchpoints:
   - README files (root and subdirectories)
   - Inline code comments
   - Docstrings/JSDoc/type annotations
   - API documentation
   - Configuration file comments
   - CHANGELOG, CONTRIBUTING, LICENSE files
   - Doc folders (/docs, /documentation, etc.)
   - Package.json descriptions, setup.py metadata, etc.

## Phase 2: Analysis
For each file in the project, evaluate:
- Does the code behavior match its documentation?
- Are there undocumented functions, classes, modules, or exports?
- Are examples/usage snippets still accurate and runnable?
- Are dependencies and version requirements current?
- Is terminology consistent across all docs?
- Are there dead links or references to removed code?

## Phase 3: Remediation
Apply these updates:
1. **Accuracy**: Fix any documentation that contradicts actual code behavior
2. **Completeness**: Add missing docstrings, parameter descriptions, return types, and usage examples
3. **Clarity**: Rewrite confusing explanations; break up walls of text
4. **Consistency**: Standardize formatting, heading styles, and terminology
5. **Currency**: Update version numbers, deprecation notices, and outdated patterns
6. **Cleanup**: Remove commented-out code, stale TODOs, and redundant documentation

## Execution Rules
- Work file-by-file, showing me what you're changing and why
- Preserve the project's existing documentation style and voice
- Prioritize high-impact files (main README, public APIs) first
- For large projects, batch by directory and confirm before proceeding to the next
- Create missing documentation files if the project lacks them (README, CONTRIBUTING, etc.)
- If you find significant architectural decisions that should be documented, note them

## Phase 4: CLAUDE.md Optimization

After completing the general documentation review, perform a detailed evaluation and refactor of the project's CLAUDE.md file:

### Evaluation Criteria
1. **Structure**: Does it follow best practices? (project overview → key commands → architecture → conventions)
2. **Conciseness**: Is every line earning its place? Remove filler words and redundant explanations
3. **Actionability**: Are instructions specific and useful for Claude Code, or generic boilerplate?
4. **Duplication**: Identify and eliminate repeated information across sections
5. **Coherence**: Does information flow logically? Are related topics grouped together?
6. **Relevance**: Remove outdated info, dead links, or references to non-existent files/features

### Refactoring Guidelines
- **Merge overlapping sections** - Combine related guidance into single coherent blocks
- **Use terse, imperative language** - "Use X for Y" not "When you need to do Y, you should consider using X"
- **Prefer lists over prose** - Bullets and tables scan faster than paragraphs
- **Cut meta-commentary** - Remove "This section describes..." type filler
- **Consolidate commands** - Group related shell commands, don't scatter them
- **Eliminate obvious instructions** - Don't tell Claude to "read files" or "understand code"
- **Keep domain knowledge** - Preserve project-specific terminology, stakeholders, and context that Claude wouldn't know otherwise

### Output
Present a before/after comparison showing:
1. Issues identified (with line references)
2. Proposed refactored CLAUDE.md
3. Summary of changes made and bytes/lines reduced

Begin by scanning the project structure and presenting your documentation audit plan before making changes.
