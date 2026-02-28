---
description: Convert a markdown file to a nicely formatted Microsoft Word document
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Markdown to Word Conversion

Convert a markdown file into a professionally formatted Microsoft Word document (.docx).

## Input Validation

**Required Arguments:**
- `<markdown-file>` - Path to the markdown file to convert

**Optional Arguments:**
- `<output-file>` - Desired output filename (defaults to same name with .docx extension)
- `--no-toc` - Skip table of contents generation
- `--style <path>` - Use a custom reference document (.docx) for Word styling
- `--dry-run` - Show the pandoc command that would be run without executing it
- `--highlight <style>` - Syntax highlighting style for code blocks (default: `tango`). Options: `pygments`, `tango`, `espresso`, `zenburn`, `kate`, `monochrome`, `breezedark`, `haddock`

**Validation:**
If the markdown file path is missing, display:
```text
Usage: /convert-markdown <markdown-file> [output-file] [--no-toc] [--style <path>] [--dry-run] [--highlight <style>]

Examples:
  /convert-markdown docs/api-guide.md
  /convert-markdown README.md documentation.docx
  /convert-markdown report.md --no-toc
  /convert-markdown report.md --style company-template.docx
  /convert-markdown report.md --dry-run
```

## Instructions

### Step 1: Identify Source File

If the user hasn't provided a markdown file path, ask them to specify:
- The path to the markdown file to convert
- Optional: desired output filename (defaults to same name with .docx extension)

Verify the source file exists. If not:
```text
Error: Source file not found: [path]

Please check the file path and try again.
```

### Step 2: Validate Prerequisites

**CRITICAL:** Check that pandoc is installed BEFORE any processing:

```bash
# Check for pandoc
pandoc --version
```

If the pandoc check fails (command not found), display this error and stop:

```text
Error: Required dependency 'pandoc' not found

/convert-markdown requires pandoc for document conversion.

Installation instructions:
  Windows:  winget install pandoc
            choco install pandoc
  macOS:    brew install pandoc
  Linux:    sudo apt install pandoc       (Debian/Ubuntu)
            sudo dnf install pandoc       (Fedora)
            sudo pacman -S pandoc         (Arch)

After installing, run the command again.
```

**Do NOT proceed** with any file processing if pandoc is missing. The user must install pandoc first.

### Step 3: Analyze Document Structure

Read the markdown file and perform a structural analysis. This analysis drives the pandoc flags used in Step 4.

**Detect these features and their impact on conversion:**

| Feature Detected | Pandoc Flag Added | Reason |
|-----------------|-------------------|--------|
| 3+ headings | `--toc --toc-depth=3` | Enough structure to warrant a table of contents |
| Code blocks with language tags | `--highlight-style=tango` | Enable syntax highlighting for code |
| Code blocks without language tags | (none, but warn) | Unhighlighted code blocks will render as plain monospace |
| Tables | (none, but verify) | Pandoc handles pipe tables natively; warn if complex grid tables detected |
| Images with local paths | (none, but verify paths) | Check that referenced image files exist; warn if missing |
| Images with remote URLs | (warn) | Remote images require network access during conversion; may fail offline |
| LaTeX math expressions | `--mathjax` or `--webtex` | Enable math rendering |
| YAML frontmatter | `--strip-comments` consideration | Frontmatter may render as visible text if not handled |
| Fewer than 3 headings | skip `--toc` | TOC not useful for short documents |

**Display analysis results:**
```text
Document Analysis: [filename]
-----------------------------
Headings:     [count] (H1: [n], H2: [n], H3: [n])
Code blocks:  [count] ([n] with language tags, [n] without)
Tables:       [count]
Images:       [count] ([n] local, [n] remote)
Lists:        [count] ([n] ordered, [n] unordered)
Math:         [yes/no]
Frontmatter:  [yes/no]
Word count:   ~[count]

Pandoc flags selected based on analysis:
  [list of flags and why each was chosen]
```

### Step 4: Check for Output File Conflict

If the output file already exists, prompt the user:
```text
Output file already exists: [path] ([size])
Overwrite? (y/n):
```

Proceed only if the user confirms.

### Step 5: Build and Execute Pandoc Command

Build the pandoc command based on the analysis from Step 3 and any user-specified flags:

**Base command:**
```bash
pandoc "{input_file}" -o "{output_file}" \
  --from=markdown \
  --to=docx \
  --standalone
```

**Add flags based on analysis and user options:**
- If headings >= 3 AND `--no-toc` not specified: add `--toc --toc-depth=3`
- If code blocks with language tags found: add `--highlight-style=[style]` (default: tango, or user-specified via `--highlight`)
- If `--style <path>` specified: add `--reference-doc=[path]` (verify the reference doc exists first)
- If math detected: add `--webtex`

**Dry-run mode (`--dry-run`):**
Display the full pandoc command that would be executed, then stop without running it:
```text
Dry run -- the following command would be executed:

  pandoc "docs/api-guide.md" -o "docs/api-guide.docx" \
    --from=markdown \
    --to=docx \
    --standalone \
    --toc --toc-depth=3 \
    --highlight-style=tango

No files were created or modified.
```

**Execute conversion:**
```bash
pandoc "{input_file}" -o "{output_file}" \
  --from=markdown \
  --to=docx \
  --highlight-style=tango \
  --toc \
  --toc-depth=3 \
  --standalone
```

**If using a custom style reference:**
```bash
pandoc "{input_file}" -o "{output_file}" \
  --from=markdown \
  --to=docx \
  --reference-doc="{style_path}" \
  --toc \
  --toc-depth=3 \
  --standalone
```

### Step 6: Validate Output and Report

After conversion, verify the output:

1. **Confirm the output file was created** (check file exists)
2. **Report the file size** (if file is 0 bytes, warn about possible conversion failure)
3. **Summarize what was converted:**

```text
Conversion Complete
-------------------
Source:     [input_file] ([size])
Output:     [output_file] ([size])
Features:   [heading count] headings, [code block count] code blocks, [table count] tables
Flags used: [list of pandoc flags applied]

Warnings:
  - [any warnings from analysis, e.g., missing images, untagged code blocks]
```

## Formatting Features

The generated Word document will include:
- **Headings**: Properly styled heading hierarchy
- **Code blocks**: Syntax-highlighted with monospace font (when language specified)
- **Tables**: Formatted with borders and header row styling
- **Lists**: Proper indentation and numbering
- **Links**: Clickable hyperlinks
- **Images**: Embedded (if local) or linked (if remote)
- **Table of Contents**: Auto-generated from headings (unless `--no-toc`)

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| pandoc not installed | Binary not on PATH | Display platform-specific installation instructions (see Step 2) |
| Source file not found | Invalid path or typo | Report the path checked and suggest verifying it |
| pandoc conversion failure | Non-zero exit code from pandoc | Display pandoc's stderr output; common causes: invalid markdown syntax, missing image files |
| Output file already exists | Previous conversion output present | Prompt for overwrite confirmation |
| Custom style reference not found | `--style` path is invalid | Report the path and suggest verifying it exists |
| Images not appearing | Image paths relative to wrong directory | Suggest using paths relative to the markdown file location |
| Code not highlighted | Missing language tag on fenced code blocks | Suggest adding language identifiers (e.g., fenced blocks tagged with `python`, `bash`, etc.) |
| TOC missing | Document has fewer than 3 headings | Inform user that TOC was skipped; use explicit `--toc` to force |
| Encoding issues | File not saved as UTF-8 | Suggest re-saving the markdown file as UTF-8 |
| Zero-byte output | pandoc ran but produced empty file | Check pandoc stderr; likely a malformed input file |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Images not appearing | Ensure image paths are relative to the markdown file |
| Code not highlighted | Specify language after opening triple-backtick fence |
| TOC missing | Document needs at least 3 headings (or use explicit `--toc`) |
| Encoding issues | Save markdown as UTF-8 |

## Example Usage

```yaml
User: /convert-markdown docs/api-guide.md

Claude:
Document Analysis: docs/api-guide.md
-----------------------------
Headings:     12 (H1: 1, H2: 5, H3: 6)
Code blocks:  5 (4 with language tags, 1 without)
Tables:       2
Images:       0
Lists:        8 (3 ordered, 5 unordered)
Math:         no
Frontmatter:  no
Word count:   ~2,400

Pandoc flags selected based on analysis:
  --toc --toc-depth=3    (12 headings detected)
  --highlight-style=tango (code blocks with language tags)

Converting docs/api-guide.md to docs/api-guide.docx...

Conversion Complete
-------------------
Source:     docs/api-guide.md (8.2 KB)
Output:     docs/api-guide.docx (45 KB)
Features:   12 headings, 5 code blocks, 2 tables
Flags used: --toc --toc-depth=3 --highlight-style=tango --standalone

Warnings:
  - 1 code block has no language tag (will render as plain monospace)
```

```yaml
User: /convert-markdown report.md --dry-run --no-toc

Claude:
Document Analysis: report.md
-----------------------------
Headings:     2 (H1: 1, H2: 1)
...

Dry run -- the following command would be executed:

  pandoc "report.md" -o "report.docx" \
    --from=markdown \
    --to=docx \
    --standalone \
    --highlight-style=tango

No files were created or modified.
```

## Related Commands

- `/convert-hooks` -- Convert bash hook scripts to PowerShell (another conversion command)
- `/analyze-transcript` -- Generate markdown reports that can then be converted to Word
- `/consolidate-documents` -- Merge documents before converting to Word
- `/assess-document` -- Evaluate document quality before conversion
