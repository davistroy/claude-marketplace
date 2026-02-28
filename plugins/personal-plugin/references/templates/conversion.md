<!-- ============================================================
     CONVERSION COMMAND TEMPLATE

     Canonical Section Order:
     1. Frontmatter (description, allowed-tools)
     2. Title (# Command Name)
     3. Brief description paragraph
     4. Input Validation
     5. Instructions (organized as phases)
     6. Output Format (required for conversion)
     7. Examples
     8. Performance (if applicable)

     Pattern References:
     - Naming: references/patterns/naming.md
     - Validation: references/patterns/validation.md
     - Output: references/patterns/output.md
     - Testing: references/patterns/testing.md (prerequisite checks)

     Note: Conversion commands TRANSFORM files between formats
     ============================================================ -->

<!-- SECTION 1: FRONTMATTER -->
---
description: {{DESCRIPTION}}
---

<!-- SECTION 2: TITLE -->
# {{TITLE}}

<!-- SECTION 3: BRIEF DESCRIPTION -->
{{INTRO_PARAGRAPH}}

<!-- SECTION 4: INPUT VALIDATION -->
## Input Validation

**Required Arguments:**
- `<input-file>` - Path to the source file to convert

**Optional Arguments:**
- `<output-file>` - Desired output filename (defaults to input name with new extension)
- `--format <format>` - Target format (if multiple supported)

**Supported Formats:**

| Input Format | Output Format | Extension |
|--------------|---------------|-----------|
| {{INPUT_FORMAT}} | {{OUTPUT_FORMAT}} | .{{OUTPUT_EXT}} |

**Validation:**
If the input file path is missing, display:
```
Error: Missing required argument

Usage: /{{COMMAND_NAME}} <input-file> [output-file]

Arguments:
  <input-file>    Path to the source file to convert (required)
  [output-file]   Desired output filename (optional)
                  Defaults to same name with .{{OUTPUT_EXT}} extension

Examples:
  /{{COMMAND_NAME}} document.{{INPUT_EXT}}
  /{{COMMAND_NAME}} docs/guide.{{INPUT_EXT}}
  /{{COMMAND_NAME}} input.{{INPUT_EXT}} custom-output.{{OUTPUT_EXT}}
```

See `references/patterns/validation.md` for error message format.

<!-- SECTION 5: INSTRUCTIONS -->
## Instructions

### Phase 1: Identify Source File

If the user hasn't provided a file path, ask them to specify:
- The path to the file to convert
- Optional: desired output filename

### Phase 2: Validate Prerequisites

**CRITICAL:** Check that required dependencies are installed BEFORE any processing:

```bash
# Check for required tool
{{PREREQUISITE_CHECK}}
```

If the prerequisite check fails, display this error and stop:

```
Error: Required dependency '{{PREREQUISITE_NAME}}' not found

/{{COMMAND_NAME}} requires {{PREREQUISITE_NAME}} for conversion.

Installation instructions:
  Windows: {{INSTALL_WINDOWS}}
  macOS:   {{INSTALL_MACOS}}
  Linux:   {{INSTALL_LINUX}}

After installing, run the command again.
```

**Do NOT proceed** with any file processing if prerequisites are missing.

See `references/patterns/testing.md` for prerequisite validation pattern.

### Phase 3: Analyze Source Structure

Read the input file and identify:
- [Structure element 1]
- [Structure element 2]
- [Structure element 3]
- [Structure element 4]
- [Structure element 5]

Note any elements that require special handling during conversion.

### Phase 4: Execute Conversion

Execute the conversion with appropriate options:

```bash
{{CONVERSION_COMMAND}}
```

#### Conversion Options Explained:
- [Option 1]: [Description]
- [Option 2]: [Description]
- [Option 3]: [Description]
- [Option 4]: [Description]

#### Optional Enhancements:

[Describe optional enhancements or custom configurations]

### Phase 5: Post-Conversion Verification

After conversion:
1. Confirm the output file was created
2. Report the file size
3. Summarize what was converted (element counts, special handling, etc.)

<!-- SECTION 6: OUTPUT FORMAT -->
## Output Format

**File Naming:**
- Default: Same as input with `.{{OUTPUT_EXT}}` extension
- Custom: User-specified output filename

**Location:** Same directory as input file (unless specified otherwise)

See `references/patterns/naming.md` for naming conventions.

### Conversion Features

The generated output will include:
- [Feature 1]: [Description]
- [Feature 2]: [Description]
- [Feature 3]: [Description]
- [Feature 4]: [Description]
- [Feature 5]: [Description]

### Completion Message

```
Conversion complete.

Input:  {{INPUT_FORMAT}} (X KB)
Output: {{OUTPUT_FORMAT}} (Y KB)

Converted:
- [Element type 1]: X items
- [Element type 2]: Y items
- [Element type 3]: Z items

Saved to: [output-path]
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| [Common issue 1] | [Solution] |
| [Common issue 2] | [Solution] |
| [Common issue 3] | [Solution] |
| [Common issue 4] | [Solution] |

<!-- SECTION 7: EXAMPLES -->
## Examples

### Basic Usage

```
User: /{{COMMAND_NAME}} document.{{INPUT_EXT}}

Claude: Converting document.{{INPUT_EXT}} to document.{{OUTPUT_EXT}}...

Analyzing source structure:
- [X] [element type 1]
- [Y] [element type 2]
- [Z] [element type 3]

Executing conversion...

Conversion complete.

Input:  {{INPUT_FORMAT}} (12 KB)
Output: {{OUTPUT_FORMAT}} (45 KB)

Converted:
- [Element type 1]: 12 items
- [Element type 2]: 5 items
- [Element type 3]: 2 items

Saved to: document.{{OUTPUT_EXT}}
```

### With Custom Output Name

```
User: /{{COMMAND_NAME}} input.{{INPUT_EXT}} custom-output.{{OUTPUT_EXT}}

Claude: Converting input.{{INPUT_EXT}} to custom-output.{{OUTPUT_EXT}}...

[Conversion process]

Saved to: custom-output.{{OUTPUT_EXT}}
```

### Handling Missing Prerequisites

```
User: /{{COMMAND_NAME}} document.{{INPUT_EXT}}

Claude: Error: Required dependency '{{PREREQUISITE_NAME}}' not found

/{{COMMAND_NAME}} requires {{PREREQUISITE_NAME}} for conversion.

Installation instructions:
  Windows: {{INSTALL_WINDOWS}}
  macOS:   {{INSTALL_MACOS}}
  Linux:   {{INSTALL_LINUX}}

After installing, run the command again.
```

<!-- SECTION 8: PERFORMANCE -->
## Performance

**Typical Duration:**

| File Size | Expected Time |
|-----------|---------------|
| < 50 KB | < 30 seconds |
| 50-500 KB | 30-60 seconds |
| 500 KB - 5 MB | 1-3 minutes |
| > 5 MB | 3+ minutes |

**Factors Affecting Performance:**
- **File size**: Larger files take longer
- **Element complexity**: Complex structures require more processing
- **System resources**: Available memory and CPU affect speed
- **Prerequisite tool version**: Older versions may be slower

**If the command seems stuck:**
1. Check for output activity
2. Wait at least 2 minutes for large files
3. If no activity, interrupt and check for errors
4. Try with a smaller test file first

See `references/patterns/logging.md` for performance documentation pattern.

## Execution Instructions

- **Validate prerequisites first** - Never attempt conversion without required tools
- **Preserve source file** - Never modify or delete the input file
- **Verify output** - Confirm successful conversion before reporting
- **Report issues clearly** - If conversion fails, explain why and how to fix

Begin by validating prerequisites, then analyze the source before converting.
