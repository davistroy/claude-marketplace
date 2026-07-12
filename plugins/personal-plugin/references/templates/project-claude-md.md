# {{PROJECT_NAME}}

**Org:** {{ORG}}

## Project Overview

[One paragraph: what this project is, who it's for, and why it exists. Fill in before the first real commit — do not ship this stub.]

## Tech Stack

{{TECH_STACK}}

## Secrets

**CRITICAL:** All API keys and tokens live in Bitwarden — never real keys in `.env`.

- Bitwarden item: `{{BITWARDEN_ITEM}}`
- Load secrets into the environment: `source ~/.claude/scripts/get-secrets.sh {{PROJECT_NAME}}`
- Add or update secrets: `~/.claude/scripts/store-secrets.sh {{PROJECT_NAME}}`
- `.env` holds placeholder values only (`your-<x>-key`, `get-from-bitwarden`). A repo-wide secrets-guard hook denies commits/writes of real-looking key patterns (`sk-ant-...`, `AKIA...`, `ghp_...`, etc.) to any `.env` file — this is a backstop, not the primary control. The primary control is: real keys go in Bitwarden, full stop.

## Key References

- `LAB_NOTEBOOK.md` — experiment log with decision tracking and action items (run `/lab-notebook init` if it doesn't exist yet)
- `BRIEF.md` — problem statement, success/kill criteria, and review date

## Problem-Solving Standards

Before any change, fix, or recommendation:

1. **Investigate deeply** — read actual code, trace data flow, verify assumptions. No surface analysis.
2. **Root cause, not symptom** — ask "why" until the structural reason is found.
3. **Map interactions first** — shared state, upstream/downstream dependencies, contracts, config consumers.
4. **Integrated solutions** — cohesive, architecturally sound changes that touch all affected files. No band-aids.
5. **Analysis before code** — for non-trivial changes, summarize findings and trade-offs before implementing. Allow redirect before writing code.

## Lab Notebook Discipline

If `LAB_NOTEBOOK.md` exists in this repo: write all significant findings (recommendations, analysis, decisions, design options) **immediately**, before proceeding to the next step. Never let substantive work live only in conversation context — a crashed session should be recoverable from the notebook alone.
