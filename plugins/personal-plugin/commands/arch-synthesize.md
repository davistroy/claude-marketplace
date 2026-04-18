---
description: Re-synthesize the executive summary from existing domain findings — use after editing findings, re-running a single agent, or resolving conflicts
argument-hint: <path-to-target>
effort: low
allowed-tools: Read, Glob, Grep, Bash
---

# Architecture Review — Synthesize

Re-run synthesis from existing findings. Use after manually editing domain findings, re-running a single agent with `/arch-review-single`, or resolving cross-domain conflicts offline.

**Usage:** `/arch-synthesize <path-to-target>`

---

Parse target path from: **$ARGUMENTS**

1. Validate `<target-path>/arch-review/findings/` exists — if not, stop and suggest running `/arch-review` first

2. Read coverage meta:
```bash
cat <target-path>/arch-review/findings/.meta.json 2>/dev/null || echo "No .meta.json — agent meta unavailable"
```

3. List all findings files present:
```bash
ls <target-path>/arch-review/findings/*.md 2>/dev/null
```

4. Note any agents from the standard 9 whose findings file is missing — flag in report header as "Domain not reviewed"

5. Read all present findings files

6. Run cross-domain conflict detection:
   - Identify any finding in one domain that contradicts or creates tension with a finding in another
   - Resolve using business impact as tiebreaker
   - Document any unresolved conflicts in the executive summary

7. Produce fresh `<target-path>/arch-review/reports/executive-summary.md` — overwrite existing
   - Begin with the **Review Coverage** table rendered from `.meta.json`
   - Follow the full report structure from `/arch-review`

8. Print terminal summary:
   - Total findings by severity across all available domains
   - Any domains with Low/Medium confidence flagged for follow-up
   - Path to executive summary

Do not re-run any domain agents. Synthesize from what exists.
