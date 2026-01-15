# Troubleshooting Guide

This guide covers common issues and their solutions when using Claude Marketplace plugins.

---

## Table of Contents

1. [Installation Issues](#1-installation-issues)
2. [Dependency Issues](#2-dependency-issues)
3. [Command Failures](#3-command-failures)
4. [Output Problems](#4-output-problems)
5. [Workflow Issues](#5-workflow-issues)

---

## 1. Installation Issues

### 1.1 Plugin Not Found After Installation

**Symptom:** Commands like `/help` don't work after installing the marketplace.

**Cause:** The marketplace was not properly added to Claude Code configuration.

**Solution:**
1. Verify installation:
   ```bash
   claude mcp list
   ```
2. If not listed, reinstall:
   ```bash
   claude mcp add-plugin https://github.com/davistroy/claude-marketplace
   ```
3. Restart Claude Code to refresh plugin registry.

---

### 1.2 Permission Denied During Installation

**Symptom:** Installation fails with "Permission denied" or "Access denied" errors.

**Cause:** Insufficient permissions to write to the plugin directory.

**Solution:**

**Windows:**
1. Run PowerShell as Administrator
2. Retry installation
3. Or change plugin directory permissions:
   ```powershell
   icacls "$env:USERPROFILE\.claude-code\plugins" /grant "$env:USERNAME:(OI)(CI)F"
   ```

**macOS/Linux:**
1. Check directory ownership:
   ```bash
   ls -la ~/.claude-code/plugins
   ```
2. Fix permissions:
   ```bash
   sudo chown -R $USER:$USER ~/.claude-code/plugins
   ```

---

### 1.3 Python Dependency Installation Fails

**Symptom:** `pip install` fails when setting up plugin tools.

**Cause:** Missing Python, wrong Python version, or pip not in PATH.

**Solution:**

1. Verify Python is installed (3.8+ required):
   ```bash
   python --version
   # or
   python3 --version
   ```

2. If Python missing, install:
   - **Windows:** `winget install Python.Python.3.11`
   - **macOS:** `brew install python@3.11`
   - **Linux:** `sudo apt install python3.11 python3.11-venv`

3. Ensure pip is available:
   ```bash
   python -m pip --version
   ```

4. Upgrade pip if needed:
   ```bash
   python -m pip install --upgrade pip
   ```

---

## 2. Dependency Issues

### 2.1 Pandoc Not Found

**Symptom:** `/convert-markdown` fails with "pandoc: command not found" or "pandoc is not recognized".

**Cause:** Pandoc is not installed or not in PATH.

**Solution:**

Install pandoc:

| Platform | Command |
|----------|---------|
| Windows | `winget install pandoc` |
| macOS | `brew install pandoc` |
| Ubuntu/Debian | `sudo apt install pandoc` |
| Fedora | `sudo dnf install pandoc` |
| Arch | `sudo pacman -S pandoc` |

Verify installation:
```bash
pandoc --version
```

If installed but not found, add to PATH:
- **Windows:** Add `C:\Users\<user>\AppData\Local\Pandoc` to system PATH
- **macOS/Linux:** Usually automatic; check `/usr/local/bin/pandoc`

---

### 2.2 Graphviz Not Found

**Symptom:** `/bpmn-to-drawio` fails with "dot: command not found" or "Graphviz not installed".

**Cause:** Graphviz is required for automatic diagram layout but is not installed.

**Solution:**

Install Graphviz:

| Platform | Command |
|----------|---------|
| Windows | `choco install graphviz` or download from https://graphviz.org/download/ |
| macOS | `brew install graphviz` |
| Ubuntu/Debian | `sudo apt install graphviz libgraphviz-dev` |
| Fedora | `sudo dnf install graphviz graphviz-devel` |

Then install Python bindings:
```bash
pip install pygraphviz
```

**Windows-specific:** After installing Graphviz, add to PATH:
1. Find installation directory (usually `C:\Program Files\Graphviz\bin`)
2. Add to system PATH
3. Restart terminal

**Alternative:** If you cannot install Graphviz and your BPMN file already has layout coordinates:
```bash
/bpmn-to-drawio input.bpmn output.drawio --layout=preserve
```

---

### 2.3 Missing Python Packages

**Symptom:** `ModuleNotFoundError: No module named 'lxml'` (or similar).

**Cause:** Required Python packages for BPMN tools are not installed.

**Solution:**

Install required packages:
```bash
pip install lxml networkx pyyaml pygraphviz
```

If `pygraphviz` fails, install Graphviz first (see 2.2 above).

---

## 3. Command Failures

### 3.1 Missing Required Argument

**Symptom:** Error message showing "Missing required argument" or usage instructions.

**Cause:** Command requires arguments that were not provided.

**Solution:**

Check command usage:
```
/help
```

Most commands show usage format:
```
Usage: /command-name <required-arg> [optional-arg]
```

- `<arg>` = required
- `[arg]` = optional

Example:
```
/convert-markdown docs/readme.md
```

---

### 3.2 File Not Found

**Symptom:** "File not found" or "No such file or directory" error.

**Cause:** The specified file path does not exist or is misspelled.

**Solution:**

1. Verify the file exists:
   ```bash
   ls -la path/to/file.md
   ```

2. Use the correct path format:
   - Relative paths start from repository root
   - Use forward slashes even on Windows: `docs/spec.md` not `docs\spec.md`

3. Check for typos in filename/extension.

4. Ensure you're in the correct directory:
   ```bash
   pwd
   ```

---

### 3.3 Invalid JSON Input

**Symptom:** "JSON decode error" or "Invalid JSON" when running `/ask-questions` or `/finish-document`.

**Cause:** The input JSON file is malformed or corrupted.

**Solution:**

1. Validate the JSON file:
   ```bash
   python -m json.tool reference/questions-*.json
   ```

2. Common JSON issues:
   - Trailing commas: `["item1", "item2",]` (remove trailing comma)
   - Single quotes: `{'key': 'value'}` (use double quotes)
   - Unescaped characters in strings

3. If file is corrupted, regenerate:
   ```
   /define-questions docs/source-document.md
   ```

---

### 3.4 GitHub CLI Authentication Error

**Symptom:** `/ship` or `/review-pr` fails with "authentication required" or "gh: not logged in".

**Cause:** GitHub CLI is not installed or not authenticated.

**Solution:**

1. Install GitHub CLI:
   - **Windows:** `winget install GitHub.cli`
   - **macOS:** `brew install gh`
   - **Linux:** See https://github.com/cli/cli/blob/trunk/docs/install_linux.md

2. Authenticate:
   ```bash
   gh auth login
   ```
   Follow the prompts to authenticate via browser.

3. Verify authentication:
   ```bash
   gh auth status
   ```

---

## 4. Output Problems

### 4.1 Output Written to Wrong Directory

**Symptom:** Cannot find output file after command completes.

**Cause:** Output may be in a different directory than expected.

**Solution:**

Check standard output locations:

| Output Type | Directory |
|-------------|-----------|
| Analysis reports | `reports/` |
| JSON reference data | `reference/` |
| Converted documents | Same directory as source |
| Temporary files | `.tmp/` |

Commands create directories automatically, but check:
```bash
ls -la reports/ reference/
```

---

### 4.2 Malformed Output File

**Symptom:** Output file contains invalid JSON, XML, or malformed content.

**Cause:** Command was interrupted, or there was a processing error.

**Solution:**

1. Check for error messages during command execution
2. Delete the malformed file:
   ```bash
   rm reports/malformed-file.json
   ```
3. Re-run the command
4. If issue persists, check input file for unusual characters or encoding issues

---

### 4.3 Word Document Not Formatted Correctly

**Symptom:** `/convert-markdown` produces a .docx file without proper formatting.

**Cause:** Input markdown may have formatting issues, or pandoc options need adjustment.

**Solution:**

1. Check markdown file for:
   - Proper heading hierarchy (H1, H2, H3)
   - Code blocks with language specified: ` ```python ` not just ` ``` `
   - Tables with proper alignment

2. Verify images use relative paths from the markdown file location

3. Check pandoc version (newer versions have better formatting):
   ```bash
   pandoc --version
   ```

4. For complex documents, consider using a reference template:
   ```bash
   pandoc -o custom-reference.docx --print-default-data-file reference.docx
   # Edit custom-reference.docx in Word to set styles
   # Then convert with:
   /convert-markdown doc.md --reference-doc=custom-reference.docx
   ```

---

### 4.4 BPMN Conversion Produces Empty Diagram

**Symptom:** Draw.io file opens but shows no elements or blank canvas.

**Cause:** BPMN file may be invalid or missing required elements.

**Solution:**

1. Verify BPMN file is valid:
   ```bash
   head -50 process.bpmn
   ```
   Should contain `<bpmn:definitions>` and `<bpmn:process>` tags.

2. Check for DI (diagram interchange) data:
   ```bash
   grep "bpmndi:BPMNDiagram" process.bpmn
   ```
   If missing, ensure you use `--layout=graphviz` (requires Graphviz).

3. Run conversion with verbose output:
   ```bash
   /bpmn-to-drawio process.bpmn output.drawio --verbose
   ```

4. Check for validation warnings and fix source BPMN file.

---

## 5. Workflow Issues

### 5.1 Interactive Session Interrupted

**Symptom:** `/ask-questions` or similar command was interrupted mid-session.

**Cause:** Terminal closed, network issue, or manual interrupt.

**Solution:**

1. Check for partial answer file:
   ```bash
   ls -la reference/answers-*.json
   ```

2. Re-run the same command:
   ```
   /ask-questions reference/questions-doc-20260114.json
   ```
   Commands with session support will prompt to resume.

3. If resume doesn't work, check the answer file for `"status": "in_progress"` field.

---

### 5.2 Cannot Resume Previous Session

**Symptom:** Command starts fresh instead of resuming incomplete session.

**Cause:** Answer file may be corrupted or missing status metadata.

**Solution:**

1. Check answer file format:
   ```bash
   python -m json.tool reference/answers-*.json | head -20
   ```

2. Look for metadata section with status:
   ```json
   "metadata": {
     "status": "in_progress",
     "last_question_answered": 15
   }
   ```

3. If metadata is missing, you may need to start over or manually edit the file to add it.

4. Backup and restart if needed:
   ```bash
   cp reference/answers-doc.json reference/answers-doc.backup.json
   # Then start fresh
   /ask-questions reference/questions-doc.json
   ```

---

### 5.3 Ship Command Creates Duplicate PRs

**Symptom:** Multiple PRs created for same changes.

**Cause:** Running `/ship` multiple times without pushing or merging.

**Solution:**

1. Check existing PRs:
   ```bash
   gh pr list
   ```

2. If duplicate exists, close it:
   ```bash
   gh pr close <PR-number>
   ```

3. Push to existing PR branch instead of creating new:
   ```bash
   git push origin <branch-name>
   ```

4. `/ship` will detect existing PR and update it instead of creating new.

---

### 5.4 Git Conflicts During Ship

**Symptom:** `/ship` fails with merge conflict errors.

**Cause:** Changes on remote conflict with local changes.

**Solution:**

1. Fetch latest changes:
   ```bash
   git fetch origin main
   ```

2. Rebase or merge:
   ```bash
   git rebase origin/main
   # or
   git merge origin/main
   ```

3. Resolve conflicts manually:
   - Edit conflicting files
   - `git add <resolved-files>`
   - `git rebase --continue` (if rebasing)

4. Then retry `/ship`

---

### 5.5 Plan Improvements Taking Too Long

**Symptom:** `/plan-improvements` runs for extended time without output.

**Cause:** Large codebase requires extensive analysis.

**Solution:**

1. Check if command is still running (look for activity indicators)

2. For large codebases, expect longer runtimes:
   - Small projects: 1-2 minutes
   - Medium projects: 3-5 minutes
   - Large projects: 5-15 minutes

3. If stuck, interrupt and try `/review-arch` for quick analysis instead.

4. Consider running on a subset of the codebase first.

---

## Getting Help

If your issue is not covered here:

1. Check the [SECURITY.md](SECURITY.md) for security-related issues
2. Check the [WORKFLOWS.md](WORKFLOWS.md) for workflow guidance
3. Open an issue at https://github.com/davistroy/claude-marketplace/issues

When reporting issues, include:
- Command that failed
- Full error message
- Operating system and version
- Relevant file contents (sanitized of sensitive data)
