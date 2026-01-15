# Security Documentation

This document describes the security model, data handling practices, and vulnerability reporting process for Claude Marketplace plugins.

---

## Table of Contents

1. [Data Handling](#1-data-handling)
2. [Secret Detection](#2-secret-detection)
3. [Input Safety](#3-input-safety)
4. [Output Safety](#4-output-safety)
5. [Current Limitations](#5-current-limitations)
6. [Vulnerability Reporting](#6-vulnerability-reporting)

---

## 1. Data Handling

### What Data Commands Process

| Command Category | Data Processed |
|------------------|----------------|
| Document analysis | File contents (markdown, text, JSON) |
| Code review | Source code files, git diffs |
| BPMN generation | Process descriptions, XML |
| Architecture review | Full codebase structure and contents |

### Where Data is Stored

**Local Storage Only:**
- All input files remain on your local filesystem
- Output files are written to your local filesystem
- No data is uploaded to external servers (except Claude API)

**Output Locations:**

| Type | Location | Cleanup |
|------|----------|---------|
| Analysis reports | `reports/` | Manual deletion |
| JSON reference data | `reference/` | Manual deletion |
| Temporary files | `.tmp/` | Auto-cleaned by commands |
| Converted documents | Same as source | Manual deletion |

### What Gets Sent to Claude API

When you run plugin commands:

1. **Sent to Claude API:**
   - Command instructions (from .md files)
   - File contents you explicitly provide as input
   - Context needed to complete the task

2. **NOT sent to Claude API:**
   - Files not referenced in your command
   - Environment variables
   - System credentials
   - Other browser tabs or applications

**Important:** Claude API has its own data handling policies. See [Anthropic's Privacy Policy](https://www.anthropic.com/privacy) for details on how your data is handled by the API.

---

## 2. Secret Detection

### Built-in Secret Scanning

The `/ship` command includes automatic secret detection as part of its auto-review feature:

**Patterns Detected:**
- API keys (AWS, GCP, Azure, GitHub, etc.)
- Private keys (SSH, PGP, certificates)
- Passwords in configuration files
- Database connection strings with credentials
- OAuth tokens and secrets
- Webhook URLs with embedded tokens

**When Detected:**
- The auto-review will flag secrets as CRITICAL issues
- You will be prompted to remove them before proceeding
- The PR will not be created until secrets are removed

### Commands WITHOUT Built-in Secret Scanning

Most commands do **not** automatically scan for secrets:
- `/define-questions`
- `/analyze-transcript`
- `/convert-markdown`
- `/review-arch`
- `/bpmn-generator`

**Recommendation:** If processing sensitive documents, manually review output files before committing.

### Best Practices for Sensitive Documents

1. **Before processing:**
   - Remove or redact sensitive data from input files
   - Use placeholder values for secrets

2. **After processing:**
   - Review output files for accidentally included secrets
   - Check JSON output for sensitive field values
   - Verify no secrets in generated documentation

3. **Environment variables:**
   - Use environment variables for secrets in code
   - Never hardcode credentials in documents being processed

---

## 3. Input Safety

### Trust Model

**Commands trust their input files completely.**

There is no:
- Input sanitization
- Sandboxing
- File permission restrictions
- Content validation beyond format requirements

**Implications:**
- Malicious input files could potentially cause unexpected behavior
- Commands execute in your user context with your permissions
- File paths are used as provided without additional validation

### User Responsibility

You are responsible for:
- Ensuring input files come from trusted sources
- Validating content before processing sensitive documents
- Not providing system files or credentials as input

### Safe Input Practices

1. **Known sources only:** Only process files you created or trust
2. **Review before processing:** Check file contents if source is uncertain
3. **Limit scope:** Don't process entire filesystems; specify exact files

---

## 4. Output Safety

### Output May Contain Sensitive Data

Generated output files may inadvertently contain:
- Extracted questions that reference confidential information
- Code snippets from your codebase
- File paths revealing directory structure
- Metadata about your development environment

### Recommended .gitignore Additions

Add these to your `.gitignore` to prevent accidental commits:

```gitignore
# Claude Marketplace outputs
reports/
reference/
.tmp/

# Specific sensitive patterns
**/secrets-*
**/credentials-*
**/*-confidential.*

# BPMN working files (may contain process details)
*.bpmn.backup
*.drawio.backup
```

### Backup File Handling

Some commands create backup files:
- Automatically cleaned up on success
- May remain if command is interrupted
- Located in `.tmp/` or alongside source files

**Regular cleanup:**
```bash
rm -rf .tmp/
find . -name "*.backup" -delete
```

### Sharing Output Files

Before sharing output files (reports, JSON, etc.):

1. **Review contents** for sensitive data
2. **Redact** confidential information
3. **Check** for hardcoded paths or usernames
4. **Verify** no embedded credentials or tokens

---

## 5. Current Limitations

### No Sandboxing

Commands run with your full user permissions. They can:
- Read any file you can read
- Write to any location you can write
- Execute system commands (for tools like pandoc, graphviz)

### No Encryption

- Output files are not encrypted
- Data at rest uses filesystem permissions only
- No additional access controls beyond OS-level

### Limited Input Validation

- Commands validate format (JSON structure, markdown syntax)
- Commands do NOT validate content safety
- No protection against path traversal in user-provided paths

### No Audit Trail

By default:
- No logging of command execution
- No history of processed files
- No record of data access

(Note: Audit logging is planned for future versions)

### Third-Party Dependencies

Some commands rely on external tools:
- **pandoc** - Document conversion
- **graphviz** - Diagram layout
- **GitHub CLI (gh)** - Git operations

These tools have their own security considerations. Keep them updated.

---

## 6. Vulnerability Reporting

### Reporting Process

If you discover a security vulnerability:

1. **Do NOT** open a public GitHub issue
2. **Use GitHub's private vulnerability reporting:** Go to the repository's Security tab and click "Report a vulnerability"
3. **Or email:** troy.e.davis@gmail.com with subject line "[SECURITY] claude-marketplace"

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Any suggested fixes (optional)

### Response Timeline

| Stage | Expected Timeframe |
|-------|-------------------|
| Acknowledgment | 48 hours |
| Initial assessment | 1 week |
| Fix development | 2-4 weeks (depending on severity) |
| Public disclosure | After fix is released |

### Severity Classification

| Severity | Description | Response Priority |
|----------|-------------|-------------------|
| Critical | Remote code execution, data exfiltration | Immediate |
| High | Privilege escalation, sensitive data exposure | 1 week |
| Medium | Information disclosure, denial of service | 2 weeks |
| Low | Minor issues, hardening opportunities | Next release |

### Safe Harbor

We will not pursue legal action against security researchers who:
- Make good faith efforts to avoid privacy violations
- Avoid destruction of data
- Give us reasonable time to fix issues before disclosure
- Do not exploit vulnerabilities for personal gain

---

## Security Checklist for Users

Before using these plugins on sensitive projects:

- [ ] Review what data will be processed
- [ ] Update `.gitignore` with recommended patterns
- [ ] Keep external dependencies (pandoc, graphviz, gh) updated
- [ ] Review output files before committing or sharing
- [ ] Use `/ship` auto-review to catch secrets before PRs
- [ ] Remove or redact sensitive data from input files
- [ ] Regularly clean up temporary and backup files

---

## Questions?

For security-related questions that don't involve vulnerabilities:
- Open a GitHub Discussion (non-sensitive questions only)
- Contact the maintainers through the security email above

For general support, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
