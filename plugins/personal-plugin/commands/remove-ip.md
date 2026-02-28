---
description: Sanitize documents by removing company identifiers and non-public intellectual property while preserving meaning and usefulness
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Company De-Identification and IP Sanitization

Remove company-identifying information and intellectual property from documents to prevent re-identification while preserving maximum meaning, structure, and usefulness.

## Input Validation

**Required Arguments:**
- `<document-path>` - Path to the document to sanitize

**Optional Arguments:**
- `--company <name>` - Company name to redact (auto-detected if not provided)
- `--mode [standard|strict]` - Sanitization mode (default: standard)
  - `standard`: Preserve maximum context while removing identifiers and likely non-public IP
  - `strict`: Assume adversarial re-identification attempts; default to redacting anything specific
- `--industry <industry>` - Industry context (helps with generalization)
- `--audience <audience>` - Intended audience of sanitized version
- `--web-research [yes|no]` - Allow web research for public info verification (default: yes in standard, no in strict)
- `--no-prompt` - Skip interactive prompts and ambiguity questions. Apply safe defaults for all decisions (default to more redaction when uncertain).

**Validation:**
If the document path is missing:

1. **If `--no-prompt` is specified**, display the error and exit:
```text
Error: Missing required argument

Usage: /remove-ip <document-path> [options]
Example: /remove-ip internal-process.md
Example: /remove-ip strategy-doc.md --mode strict
```

2. **Otherwise (default)**, display the full usage help:
```text
Usage: /remove-ip <document-path> [options]

Options:
  --company <name>         Company name to redact (auto-detected if omitted)
  --mode [standard|strict] Sanitization mode (default: standard)
  --industry <industry>    Industry context for generalization
  --audience <audience>    Intended audience of sanitized version
  --web-research [yes|no]  Allow web research (default: yes for standard, no for strict)
  --no-prompt              Skip interactive prompts, apply safe defaults

Examples:
  /remove-ip internal-process.md
  /remove-ip strategy-doc.md --mode strict
  /remove-ip playbook.md --company "Acme Corp" --industry "Finance"
```

## Mission

Sanitize the document by removing:

1. **Company identifiers** - Company name, known aliases, and anything that could link the text to the company
2. **Linkable information** - Product names, internal programs, project codenames, employee names, unique role titles, org charts, vendor/client/partner names, locations, facility details, internal systems, URLs, domains, email formats, internal acronyms, proprietary terminology, unique metrics/KPIs, unique policies
3. **Non-public IP** - Proprietary strategies, playbooks, methods, processes, SOPs, workflows, implementation details, system architecture, configurations, pricing, contracts, negotiation positions, operational constraints, incident details, security details, internal performance data
4. **Trade-secret-like content** - Any content that is not clearly public

**Primary objective:** Prevent re-identification and remove non-public IP.
**Secondary objective:** Preserve meaning and usefulness.

## Mode Behavior

### STANDARD Mode

- Preserve maximum context while removing identifiers and likely non-public IP
- Ask questions for genuinely ambiguous areas
- Keep common industry tools and generic practices when not identifying
- Treat something as "publicly available" only if it appears in official company sources, reputable media, SEC filings, published case studies, or public conference talks

### STRICT Mode

Assume an adversary will try to re-identify the company using "mosaic" clues:

- Default to redacting/generalizing anything specific, even if it *might* be public
- No web research unless explicitly allowed AND trusted sources provided
- Replace ALL names (people, vendors, clients, partners) with placeholders
- Generalize ALL quantities (money, headcount, timelines, volumes, SLA times) to ranges or relative terms
- Remove or abstract ALL detailed process steps, tooling architecture, configuration details, and "how we did it" playbooks - keep only intent, high-level phases, and outcomes
- Generalize industry/geography if it narrows identity
- If uncertain, choose the safer option (more redaction), then ask the user
- Even if something is public, keep it generalized unless it is both (a) widely known AND (b) non-identifying in combination with other details

## Instructions

### Step 1: Read and Analyze the Document

Thoroughly read the document to understand:
- Document purpose and structure
- Company name (if not provided, infer from content)
- Industry and domain context
- Types of sensitive information present

### Step 2: Research (Standard Mode Only)

If `--web-research` is enabled:
- Verify whether named strategies/processes/tools are publicly described by the company
- Check official company sources, reputable media, SEC filings, published case studies, public conference talks
- Document findings for the redaction log

### Step 3: Apply Redaction Strategy

Replace sensitive content using the **least-lossy** substitute that meets the mode's safety bar.

#### Replacement Patterns

| Original | Standard Mode Replacement | Strict Mode Replacement |
|----------|---------------------------|-------------------------|
| Company name | Generic name or `[Company]` | `[Company]` |
| Business unit/program names | `[Business Unit]`, `[Internal Program]` | `[Business Unit]`, `[Internal Program]` |
| Product names | `[Product]` or `[Customer-Facing Product]` | `[Product]` |
| Proprietary process | `[Internal Process]` + generic description | `[Internal Process]` (no details) |
| Proprietary strategy | `[Internal Strategy]` + generalized intent | `[Internal Strategy]` (no details) |
| Common tools (ServiceNow, etc.) | Keep if non-identifying | `[ITSM Platform]`, `[CRM]`, `[Data Warehouse]` |
| Numbers/metrics | Keep non-sensitive; redact unique ones | Generalize ALL to ranges/relative terms |
| People names | Replace with roles; generalize unique roles | `[Role]` or `[Team]` |
| Dates | Keep if non-identifying; generalize if needed | Broad periods ("recent quarter", "over several months") |
| Locations | Generalize to region | `[Location]` or `[Region]` |
| Vendor/partner names | `[Partner]`, `[Vendor]` | `[Partner]`, `[Vendor]` |
| Client names | `[Client]`, `[Customer]` | `[Client]`, `[Customer]` |
| Internal URLs/domains | `[Internal System]` | `[Internal System]` |
| Email formats | `[Email Address]` | `[Email Address]` |

#### Generalization Ladder (in order of preference)

1. **Keep detail** - Only if allowed by mode and non-identifying
2. **Generalize** - Retain purpose + mechanism but remove specificity
3. **Abstract** - Retain intent only
4. **Remove** - Only if nothing can be preserved safely

### Step 4: Mosaic Test (Strict Mode)

If multiple small details together could identify the company, further generalize. Check for:
- Unique combinations of industry + geography + company size
- Distinctive process names or terminology
- Rare tool combinations
- Specific incident dates + impact + industry

### Step 5: Generate Output

Produce a markdown file with **three sections**:

#### Section 1: Sanitized Document

The fully sanitized version with all replacements applied. Maintain original structure and formatting.

#### Section 2: Redaction Log

A table documenting all changes:

| Original Snippet (short) | Risk Type | Action | Replacement | Reasoning |
|--------------------------|-----------|--------|-------------|-----------|
| "Acme Corp" | Company Identifier | Replaced | `[Company]` | Direct company name |
| "$5.2M revenue" | Sensitive Ops | Generalized | "significant revenue" | Financial details |
| ... | ... | ... | ... | ... |

**Risk Types:**
- Company Identifier
- Non-Public IP
- Sensitive Ops
- Security
- Legal
- Other

**Actions:**
- Kept
- Generalized
- Replaced
- Removed

Keep "Original Snippet" short and non-reconstructive.

#### Section 3: Questions for User (if needed)

Only ask high-leverage questions. Categorize each:
- **(A) Linkability risk** - Could this identify the company?
- **(B) IP risk** - Is this proprietary information?
- **(C) Sensitivity risk** - Could this cause harm if disclosed?

For each question, include:
- What you're unsure about
- What decision you need from the user
- The safe default you will apply if they don't answer

### Step 6: Save Output

**Output Location:** Save to the same directory as the source document.

**Filename Format:** `[document-name]-sanitized-YYYYMMDD-HHMMSS.md`

Example: `playbook-sanitized-20260115-143052.md`

## Safety and Quality Checks

Before finalizing, verify:

- [ ] Sanitized text cannot be attributed via unique phrasing, named programs, metrics, or rare combinations
- [ ] Replacements are consistent across the document (same entity always gets same placeholder)
- [ ] Document still makes sense and is useful after sanitization
- [ ] No identifying information leaked in examples, code snippets, or metadata
- [ ] In STRICT mode: mosaic test passed

## Example Usage

### Standard Mode

```yaml
User: /remove-ip internal-playbook.md

Claude: I've read internal-playbook.md and identified it as belonging to Acme Corp in the
financial services industry.

I'll sanitize this document in STANDARD mode, preserving maximum context while removing
identifying information and non-public IP.

[Performs sanitization]

Sanitization complete!

**Summary:**
- Mode: STANDARD
- Replacements made: 47
- Company identifiers removed: 12
- Non-public IP redacted: 23
- Sensitive operations generalized: 8
- Items preserved (verified public): 4

**Questions for you:**

1. **(A) Linkability risk:** The document mentions "Project Phoenix" - this appears in a 2024
   press release. Should I:
   - Keep as-is (verified public)
   - Replace with `[Internal Project]` anyway?

   *Safe default: Replace with `[Internal Project]`*

Output saved to: internal-playbook-sanitized-20260115-143052.md
```

### Strict Mode

```yaml
User: /remove-ip strategy-doc.md --mode strict --company "Contoso"

Claude: I've read strategy-doc.md. Running in STRICT mode with maximum redaction.

[Performs strict sanitization]

Sanitization complete!

**Summary:**
- Mode: STRICT
- Replacements made: 89
- All quantities generalized to ranges
- All tool names replaced with categories
- All dates generalized to periods
- Mosaic test: PASSED

No questions - all ambiguous items defaulted to safer redaction.

Output saved to: strategy-doc-sanitized-20260115-143052.md
```

## Error Handling

Handle these error conditions before proceeding with sanitization:

| Error Condition | Detection | Recovery Action |
|----------------|-----------|-----------------|
| **File not found** | Read tool returns file-not-found error | Display: "File not found: [path]. Verify the path is correct and the file exists." |
| **Binary file** | File contains non-text content (images, PDFs, executables) | Display: "Cannot sanitize binary file: [path]. This command works with text-based documents only (markdown, text, docx via conversion)." |
| **Empty file** | File exists but has no content | Display: "File is empty: [path]. Nothing to sanitize." |
| **Permission error** | Read or Write tool returns access denied | Display: "Permission denied for [path]. Check file permissions and try again." |
| **File already de-identified** | No company identifiers or IP found during analysis | Display: "No identifiable company information or IP found in [path]. The document appears to already be de-identified. No changes made." |
| **Very large file** | File exceeds 5,000 lines | Warn: "Large file detected ([N] lines). Sanitization may take longer and may need to be processed in sections. Proceed? (yes/no)" |
| **Write failure** | Cannot save output file to target directory | Display: "Cannot write to [output-path]. Check directory permissions and disk space." |

## What Gets Removed vs Preserved

**Examples of content that gets REMOVED or REPLACED:**

| Original Content | What Happens | Replacement Example |
|-----------------|-------------|---------------------|
| "Acme Corp deployed..." | Company name replaced | "[Company] deployed..." |
| "Project Phoenix roadmap" | Internal program name replaced | "[Internal Program] roadmap" |
| "John Smith, VP of Engineering" | Person name replaced with role | "[VP of Engineering]" |
| "$5.2M annual savings" | Specific financial figure generalized | "significant cost savings" |
| "ServiceNow ITSM instance at acme.service-now.com" | Internal URL removed, tool kept (standard) or replaced (strict) | "ITSM platform" (strict) or "ServiceNow instance at [Internal URL]" (standard) |
| "Building 7, Atlanta campus" | Location generalized | "[Company Location]" |

**Examples of content that gets PRESERVED:**

| Content | Why Preserved |
|---------|--------------|
| Generic industry practices ("agile methodology") | Not company-specific |
| Common tool names in standard mode ("ServiceNow", "Salesforce") | Widely used, non-identifying on their own |
| Document structure and formatting | Preserves readability |
| General business concepts ("cost reduction strategy") | Not proprietary |
| Publicly verifiable facts (in standard mode only) | Confirmed via web research |

## Web Research Guidance

If the user asks to verify that company information has been removed, use WebSearch to check if remaining terms are generic (not company-specific). Do not use web research tools by default -- only when verification is explicitly requested by the user or when `--web-research yes` is specified.

## Related Commands

- `/assess-document` - Evaluate document quality before sanitization
- `/consolidate-documents` - Merge multiple document versions after sanitization
