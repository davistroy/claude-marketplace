# Security Documentation

This document describes the security model, data handling practices, and vulnerability reporting process for Claude Marketplace plugins.

---

## Table of Contents

1. [Data Handling](#1-data-handling)
2. [Data Egress & Confidentiality Policy](#2-data-egress--confidentiality-policy)
3. [Secret Detection](#3-secret-detection)
4. [Input Safety](#4-input-safety)
5. [Output Safety](#5-output-safety)
6. [Current Limitations](#6-current-limitations)
7. [Supply-Chain Controls](#7-supply-chain-controls)
8. [Vulnerability Reporting](#8-vulnerability-reporting)

---

## 1. Data Handling

### What Data Commands Process

| Command Category | Data Processed |
|------------------|----------------|
| Document analysis | File contents (markdown, text, JSON) |
| Code review | Source code files, git diffs |
| BPMN generation | Process descriptions, XML |
| Architecture review | Full codebase structure and contents |
| Security analysis | Source code, dependencies, configurations |
| Document sanitization | Documents with company/proprietary information |
| Multi-provider research | Research queries sent to Anthropic, OpenAI, and Google APIs |
| Visual generation | Text/document content sent to image generation APIs |
| Secrets management | Bitwarden vault access (reads secrets, never writes to disk) |
| Feedback synthesis | Notion page content, feedback data |

### Where Data is Stored

**Local Storage Only:**
- All input files remain on your local filesystem
- Output files are written to your local filesystem
- No data is uploaded to external servers except through LLM APIs (Claude, OpenAI, Google Gemini -- see "What Gets Sent to Claude API" below)

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

**Multi-Provider Note:** The `/research-topic` skill sends data to **Anthropic, OpenAI, and Google APIs in parallel** as part of its multi-provider research workflow. Data sent to each provider is subject to that provider's respective privacy and data handling policies.

**Important:** Claude API has its own data handling policies. See [Anthropic's Privacy Policy](https://www.anthropic.com/privacy) for details on how your data is handled by the API.

**Before sending any document to a command or skill that egresses to a third-party AI API** (see Section 2 immediately below), classify the data first. Section 2 defines what must never leave your machine this way and which tools are the actual egress points.

---

## 2. Data Egress & Confidentiality Policy

This section exists because the soft caution in Section 1 ("data sent to each provider is subject to that provider's policies") is not sufficient on its own -- a user can point `/visual-explainer` or `/research-topic` at a confidential client document with nothing stronger than a note in this file standing between the document and a third-party API call. This is the highest genuine compliance exposure in this repository (arch-review RISK-04 / DA-04 / SEC-09) and this section is the explicit policy, not just a description of behavior.

### Data Classification

Classify input **before** running any command or skill against it:

| Tier | Examples | Third-party AI API OK? |
|------|----------|------------------------|
| **Public** | Published docs, open-source code, marketing content, this repository itself | Yes |
| **Internal / business-confidential** | Internal process docs, non-regulated internal notes, draft content not yet public | Generally yes, but treat provider egress as a business decision -- see retention/training note below |
| **Regulated / confidential** | Anything in the "NEVER send" list below | **No.** Do not run `/visual-explainer`, `/research-topic`, `/analyze-transcript`, `/summarize-feedback`, or any other command against this tier without first stripping/redacting the regulated content, or without a verified data-processing agreement with the specific provider covering this use case |

When in doubt, treat the input as the more restrictive tier. `/remove-ip` (Section 3) can help sanitize a document down to a lower tier, but review its output -- automated redaction is not a substitute for classification judgment.

### NEVER Send to Third-Party AI APIs

Do not provide the following as input to any command or skill, regardless of provider:

- **Secrets and credentials** -- API keys, passwords, private keys, OAuth tokens, database connection strings, `.env` file contents (see Section 3, Secret Detection, for scanning coverage and gaps)
- **Regulated client deliverables or work product** -- anything covered by an NDA, MSA confidentiality clause, or client contract restricting redistribution or third-party processing
- **Personally Identifiable Information (PII) / Protected Health Information (PHI) / financial account data** belonging to clients, employees, or any third party
- **Anything marked confidential, attorney-client privileged, export-controlled, or CUI (Controlled Unclassified Information)**
- **Data subject to a residency or sovereignty requirement** inconsistent with processing by a public cloud AI API in an unknown jurisdiction

### Which Tools/Skills Egress Data, and to Which Providers

| Command / Skill | What Leaves Your Machine | Destination Provider(s) | Notes |
|------------------|---------------------------|--------------------------|-------|
| `/visual-explainer` | Text/content describing the image to generate (may be derived from a source document) | **Google Gemini** (image generation API) | Requires `GEMINI_API_KEY`; see `google-genai` SDK reference in Section 6 |
| `/research-topic` | The research query and surrounding context | **Anthropic, OpenAI, and Google in parallel** (multi-provider fan-out) | The same query is sent to all three vendors simultaneously -- see the Multi-Provider Note in Section 1 |
| `/analyze-transcript` | The full meeting transcript, verbatim | **Anthropic** (Claude API) | Purpose-built to ingest raw transcripts, which frequently contain internal/confidential discussion -- classify before running |
| `/summarize-feedback` | Notion Voice Capture feedback content, often personnel-review material | **Anthropic** (Claude API) | Ingests potentially sensitive personnel feedback verbatim -- classify before running |
| All other commands/skills (default case) | File contents you explicitly provide as input | **Anthropic** (Claude API) | Baseline behavior described in Section 1 |

Egress is not limited to these five rows -- any command that reads a file and passes its content to an LLM sends that content to that provider. The five above are called out because they are the highest-likelihood entry points for regulated data reaching a third party: two call out to non-Anthropic providers, two are purpose-built to ingest raw, often-sensitive source documents.

### Provider Data-Processing and Retention Terms

Retention windows, training-data usage, and human-review policies **differ by provider, by product tier (API vs. consumer app), and by account agreement (individual vs. enterprise/commercial terms), and change over time.** The links below are pointers for locating the current terms -- they are not a substitute for reading the terms that apply to the specific account and tier in use, and they must be verified before sending anything above the "Internal" classification tier:

- **Anthropic:** [Privacy Policy](https://www.anthropic.com/privacy) / [Commercial Terms & Data Processing Addendum](https://www.anthropic.com/legal/data-processing-addendum)
- **OpenAI:** [Data Processing Addendum](https://openai.com/policies/data-processing-addendum/) / [Enterprise Privacy](https://openai.com/enterprise-privacy/)
- **Google (Gemini API):** [Gemini API Additional Terms of Service](https://ai.google.dev/gemini-api/terms) / [Cloud Data Processing Addendum](https://cloud.google.com/terms/data-processing-addendum) (for Vertex AI / enterprise Gemini usage, which carries different retention terms than the free Gemini API tier)

**Do not assume zero-retention or no-training-use by default.** Free/individual API tiers for some providers historically differ from paid/enterprise tiers on exactly these points. Verify the current terms for the account actually configured (see `.env` / Bitwarden item naming per the root `CLAUDE.md`) before sending regulated data through any of the tools in the table above.

### Issue-Tracker Egress (task-sync)

`/task-sync` introduces a **different egress class** from everything else in this section: authenticated calls to an **issue tracker** (GitHub via the `gh` CLI, Gitea via its REST API), not an LLM provider. Nothing in the table above covers it, so it is called out on its own.

- **What leaves the machine:** task titles, bodies, labels, milestones, and status for any task the plan-decide-apply sync creates or pushes as an issue. Reads (pulling issue state to reconcile locally) are lower-risk but still authenticated calls to the same API.
- **Destination:** the tracker configured for the current repo's `origin` remote -- GitHub (via the already-authenticated `gh` CLI) or Gitea (via REST, using the token in `~/.config/tea/config.yml`). Never an LLM API; the bundled `task_sync` tool has zero third-party AI dependencies.
- **Confidentiality scan gates outbound content.** Before any create/push, `sync --plan` scans the affected task's title/body for secret/token shapes (`ghp_`, `sk-`, AWS keys, PEM blocks, bearer tokens) and generic structural identifiers (emails, internal hostnames, ticket/asset IDs), plus any per-repo `sensitive_terms` configured in `tasks.json`. `CRITICAL` findings (recognizable secret shapes) block that item until the user explicitly dispositions it (`keep`/`redact`/`remove`/`anonymize`) -- the skill never lets a flagged push proceed silently, and the scan output itself never prints the full secret, only a redacted preview.
- **Public-repo visibility guardrail.** Before the first push/create of a sync session, the skill checks the target repo's visibility (`gh repo view --json visibility`, or the Gitea REST equivalent) and requires an explicit "yes" if the repo is public -- pushing task content to a public tracker is a materially different exposure than a private one, and this guardrail exists so that is never assumed silently.
- **What this does NOT cover:** the confidentiality scan is a content-shape detector, not a classification engine -- it catches known secret patterns and configured terms, not every form of regulated data. Classify task content the same way you would classify input to any other command (Data Classification, above) before syncing it to a tracker, especially a public one.

---

## 3. Secret Detection

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

Most commands do **not** automatically scan for secrets. This includes (non-exhaustive):
- `/define-questions`
- `/analyze-transcript`
- `/convert-markdown`
- `/review-arch`
- `/bpmn-generator`
- `/research-topic`
- `/visual-explainer`
- `/summarize-feedback`
- `/security-analysis`
- `/unlock`
- `/prime`
- `/review-intent`
- `/plan-improvements`
- `/assess-document`

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

### Security-Relevant Skills and Commands

Several commands and skills are directly relevant to security workflows:

- **`/security-analysis`** - Comprehensive security analysis with automatic tech stack detection. This is the most security-focused skill in the plugin. It scans codebases for vulnerabilities, insecure patterns, dependency risks, and configuration issues across multiple languages and frameworks. Use it as a first-pass security audit on any project.

- **`/remove-ip`** - Document sanitization and de-identification. Strips company names, proprietary information, and intellectual property from documents. Use this before sharing documents externally or when creating anonymized case studies. Review output carefully -- automated redaction may miss context-dependent references.

- **`/unlock`** - Bitwarden Secrets Manager integration. Loads secrets from Bitwarden vault into the current environment using the `bws` CLI. This avoids storing API keys and credentials in `.env` files or configuration. Requires the `bws` CLI to be installed and a valid machine access token. Secrets are loaded into environment variables for the current session only -- they are not written to disk.

---

## 4. Input Safety

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

## 5. Output Safety

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

## 6. Current Limitations

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

### Audit Trail

By default, commands do not log their execution. However, audit logging **is available** via the `--audit` flag on `/clean-repo` and `/ship`. When enabled:
- Command execution is logged with timestamps
- Processed files are recorded
- Data access is tracked for review

If you require a full audit trail, use the `--audit` flag on supported commands.

### Third-Party Dependencies

Some commands rely on external tools:
- **pandoc** - Document conversion
- **graphviz** - Diagram layout
- **GitHub CLI (gh)** - Git operations (`/ship`)
- **tea** - Gitea CLI (`/ship` for Gitea remotes)
- **bws** - Bitwarden Secrets Manager CLI (`/unlock`)
- **google-genai** - Google Gemini SDK (`/research-topic`)
- **openai** - OpenAI SDK (`/research-topic`, `/visual-explainer`)

These tools have their own security considerations. Keep them updated.

### Fleet recon/audit trust boundary

Four skills interact with the personal fleet (DGX Spark, Jetson Orin Nano): `spark-audit`, `jetson-audit`, `spark-recon`, `jetson-recon`. This is the arch-review SEC-01 boundary made explicit -- documented here, not closed.

**What SSHes where, with what privilege:**
- `spark-audit` SSHes to `claude@spark.k4jda.net`; `jetson-audit` SSHes to `claude@jetson.k4jda.net`. Both hold unscoped `Bash` and issue `sudo`-prefixed commands directly (`spark-audit`: `sudo dmesg`; `jetson-audit`: `sudo tegrastats`, `sudo nvpmodel`, `sudo jetson_clocks`).
- The `claude` SSH user has passwordless sudo on fleet hosts for `docker`, `systemctl`, `modprobe`, `reboot`, `dpkg`, `apt`, `depmod`, `dkms`, `cp`, `mv`, `rm`, `ln`, `mkdir`, `chmod`, `chown`, `mount`, `umount`, `nvidia-smi`, `sysctl`. Several of these (`rm`, `chmod`, `chown`, `mount`, `apt`, `reboot`) are root-equivalent for that host, not read-only conveniences -- reaching a shell on that account is effectively reaching fleet root.
- `jetson-recon` combines both halves of the injection trifecta in one skill: Checks 1-4 ingest untrusted third-party content (NVIDIA/JetPack notes, llama.cpp GitHub, HuggingFace, the NVIDIA developer forum) via `WebFetch`/`WebSearch`, then Check 5 SSHes into `claude@jetson.k4jda.net` for a live health read, all under the same unscoped `Bash` grant.
- `spark-recon` ingests the same class of untrusted content but declares no SSH target in its machine config and states it "never touches the Spark system" -- its `Bash` grant is for local file/notebook operations only.

**Blast radius if injected:** content smuggled into `jetson-recon`'s fetched forum/GitHub/HuggingFace results, or into anything `spark-audit`/`jetson-audit` reads back from the live host (container logs, baseline files, command output), rides an unscoped shell that can reach a passwordless-sudo account -- i.e., fleet root, not just the invoking user's local privileges.

**Mitigations in place:**
- **3.1 (Bash scoping):** unscoped `Bash` on content-ingesting skills is replaced with `Bash(<cmd>:*)` scopes matching each skill's actual needs, shrinking what an injected instruction can execute even if it rides along.
- **3.2 (fetch/act separation):** the untrusted-fetch step in recon skills is separated from the local/remote-action step so no shell/SSH tool is active while third-party content is being read; the highest-blast-radius recon skills are evaluated for `disable-model-invocation` so injected content cannot auto-trigger them.

**Residual risk:** audit skills still hold legitimate, scoped SSH+sudo grants for their designed function (`docker`/`nvidia-smi`/`systemctl`/`tegrastats`/`nvpmodel`/`jetson_clocks`). Scoping reduces the blast radius of an injected command but does not eliminate the underlying fact -- the shell these skills reach is a passwordless-sudo shell. Users who consider this unacceptable should run audit/recon skills only under explicit human review, or narrow the `claude` SSH user's sudo grant below the current fleet-wide policy.

---

## 7. Supply-Chain Controls

This section documents the automated controls that actually run against this repository's own dependencies and code (arch-review RISK-03). These are distinct from the "Third-Party Dependencies" list above, which covers external tools the *commands* shell out to at runtime -- this section covers what protects the repository's build/CI pipeline itself.

| Control | What It Does | Cadence | Enforcement Point |
|---------|---------------|---------|--------------------|
| **Dependabot** | Scans for outdated/vulnerable pip packages in each bundled tool directory (`bpmn2drawio`, `visual-explainer`, `feedback-docx-generator`) and for outdated GitHub Actions at the repo root; opens PRs with the update. Minor/patch bumps are grouped per ecosystem to avoid one-PR-per-package pileup; major bumps always surface individually for review. | Weekly (Monday 06:00 America/New_York) | Opened PRs must pass the same required CI checks as any other PR before merge (branch protection, below) -- Dependabot gets no bypass |
| **pip-audit** (`Dependency Security Audit` CI job) | Audits each tool's *declared, pinned* dependencies (`requirements-lock.txt`) against the NVD and PyPI advisory databases for known CVEs | Every push and PR (via CI) | **Required status check** under branch protection -- a PR cannot merge to `main` while this job is red |
| **CodeQL** | Static analysis / code scanning for common vulnerability patterns, run via GitHub's default-setup configuration (no workflow file in this repo -- managed through repo Security settings) | Every push and PR | Advisory (Security tab) -- **not** a required status check (see rationale below) |
| **GitGuardian** | Automated secret-scanning GitHub App; scans every push/PR for exposed credentials, keys, and tokens | Every push and PR | Advisory (Security tab) -- **not** a required status check (see rationale below) |
| **Branch protection on `main`** | Requires a PR (no direct pushes) with all authored-workflow status checks green: `Run Tests` + the 3 per-tool test jobs (×2 OS), `Validate Plugins` (×2), `Schema Validation`, `Lint Markdown`, `Python Lint & Format`, and `Dependency Security Audit` -- 14 required checks total. `required_approving_review_count=0` (solo-maintained repo -- a required review would deadlock every merge). `enforce_admins=false` is an explicit maintainer escape hatch, not an oversight. | Always-on (repo config, not a schedule) | This *is* the enforcement point for every other control above -- it converts what used to be an advisory CI suite into a merge gate (ADR-0007) |

**Why CodeQL and GitGuardian are advisory, not required:** both run as app/default-setup checks whose context names are less stable than this repo's own authored workflow jobs; making them required risked deadlocking merges on a check that fails to report a status at all. They are monitored via the Security tab instead of gating merges. This trade-off, and the branch-protection design as a whole, is recorded in [`docs/adr/0007-distribution-safety-model.md`](docs/adr/0007-distribution-safety-model.md).

**Evidence trail (LAB_NOTEBOOK.md):** Entry 012 (regenerated 5 tool lockfiles to clear all 38 open pip CVE alerts), Entry 013 (added `.github/dependabot.yml`, verified CI green including the GitGuardian check on both OSes), Entry 016 (a live example of `Dependency Security Audit` acting as a real gate -- a newly-disclosed setuptools CVE broke an unrelated PR's audit job, fixed by patching the build tool in CI; Entries 012/013/016 are archived -- see `docs/archive/LAB_NOTEBOOK-E001-E016.md`), and Entry 017/Entry 020 (branch protection enabled with the 14 required checks above via ADR-0007, and `Dependency Security Audit` subsequently re-scoped to each tool's lockfile only -- removing the whole-runner-environment scan that caused the Entry 016 false-positive class of failure -- alongside SHA-pinning the GitHub Actions Dependabot itself tracks; Entries 017/020 are archived -- see `docs/archive/LAB_NOTEBOOK-E017-E050.md`).

---

## 8. Vulnerability Reporting

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

### Response Timeline (Best-Effort)

**This is a solo-maintained project.** The timeframes below are best-effort targets, not guaranteed SLAs -- there is no team to cover for the maintainer during travel, illness, or other unavailability. If you need a guaranteed response time, this project's support model does not provide one.

| Stage | Best-Effort Target |
|-------|--------------------|
| Acknowledgment | ~48 hours |
| Initial assessment | ~1 week |
| Fix development | ~2-4 weeks (depending on severity) |
| Public disclosure | After fix is released |

### Severity Classification

Severity guides prioritization of the maintainer's available time, not a committed response deadline.

| Severity | Description | Response Priority |
|----------|-------------|-------------------|
| Critical | Remote code execution, data exfiltration | Highest priority |
| High | Privilege escalation, sensitive data exposure | High priority (~1 week target) |
| Medium | Information disclosure, denial of service | Medium priority (~2 week target) |
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
- [ ] Keep external dependencies (pandoc, graphviz, gh, tea, bws) updated
- [ ] Review output files before committing or sharing
- [ ] Use `/ship` auto-review to catch secrets before PRs
- [ ] Use `/security-analysis` for first-pass security audits
- [ ] Use `/remove-ip` to sanitize documents before external sharing
- [ ] Use `/unlock` for secrets management instead of `.env` files
- [ ] Remove or redact sensitive data from input files
- [ ] Regularly clean up temporary and backup files

---

## Questions?

For security-related questions that don't involve vulnerabilities:
- Open a GitHub Discussion (non-sensitive questions only)
- Contact the maintainers through the security email above

For general support, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md). For the maintainer's incident response and rollback procedure, see [docs/RUNBOOK.md](docs/RUNBOOK.md).
