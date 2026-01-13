---
description: Convert a markdown file to a nicely formatted Microsoft Word document
---

# Markdown to Word Conversion

Convert a markdown file into a professionally formatted Microsoft Word document (.docx).

## Process

### Step 1: Identify Source File

If the user hasn't provided a markdown file path, ask them to specify:
- The path to the markdown file to convert
- Optional: desired output filename (defaults to same name with .docx extension)

### Step 2: Validate Prerequisites

Check that pandoc is installed:
```bash
pandoc --version
```

If pandoc is not installed, inform the user:
- **Windows**: `winget install pandoc` or download from https://pandoc.org/installing.html
- **macOS**: `brew install pandoc`
- **Linux**: `sudo apt install pandoc` or equivalent

### Step 3: Analyze Document Structure

Read the markdown file and identify:
- Heading hierarchy (H1, H2, H3, etc.)
- Code blocks and their languages
- Tables
- Lists (ordered/unordered)
- Images and links
- Frontmatter (if present)

### Step 4: Convert to Word

Execute the conversion with professional formatting options:

```bash
pandoc "{input_file}" -o "{output_file}" \
  --from=markdown \
  --to=docx \
  --highlight-style=tango \
  --toc \
  --toc-depth=3 \
  --standalone
```

#### Pandoc Options Explained:
- `--highlight-style=tango`: Syntax highlighting for code blocks
- `--toc`: Generate table of contents from headings
- `--toc-depth=3`: Include H1-H3 in TOC
- `--standalone`: Complete document with headers/footers

#### Optional Enhancements:

If the user wants custom styling, create a reference doc:
```bash
pandoc -o custom-reference.docx --print-default-data-file reference.docx
```

Then use it:
```bash
pandoc "{input_file}" -o "{output_file}" --reference-doc=custom-reference.docx
```

### Step 5: Post-Conversion

After successful conversion:
1. Confirm the output file was created
2. Report the file size
3. Summarize what was converted (heading count, code blocks, tables, etc.)

## Formatting Features

The generated Word document will include:
- **Headings**: Properly styled heading hierarchy
- **Code blocks**: Syntax-highlighted with monospace font
- **Tables**: Formatted with borders and header row styling
- **Lists**: Proper indentation and numbering
- **Links**: Clickable hyperlinks
- **Images**: Embedded (if local) or linked (if remote)
- **Table of Contents**: Auto-generated from headings

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Images not appearing | Ensure image paths are relative to the markdown file |
| Code not highlighted | Specify language after opening ``` |
| TOC missing | Document needs at least one heading |
| Encoding issues | Save markdown as UTF-8 |

## Example Usage

```
User: /wordify docs/api-guide.md
Claude: Converting docs/api-guide.md to docs/api-guide.docx...
        ✓ Created docs/api-guide.docx (45 KB)
        - 12 headings, 5 code blocks, 2 tables
```
