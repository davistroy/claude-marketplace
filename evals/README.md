# personal-plugin Eval Suite

Structured test specifications for every command and skill in `personal-plugin`. Each eval defines concrete scenarios, pass/fail criteria, and a quality rubric — so you can verify that commands behave as specified after edits, refactors, or model upgrades.

## Structure

```
evals/
  README.md                    # This file
  fixtures/
    docs/                      # Sample input documents
      sample-prd.md            # Well-formed PRD (~3.5-4.5 quality score)
      draft-prd.md             # Incomplete PRD with TBDs and gaps (~2-3 score)
      meeting-transcript.md    # Team meeting with action items and decisions
      ip-document.md           # Doc containing company identifiers (for remove-ip)
      multi-variant-a.md       # API design doc — REST perspective (for consolidate)
      multi-variant-b.md       # API design doc — GraphQL perspective (for consolidate)
    json/
      questions-sample.json    # Pre-extracted questions (for ask-questions)
    plans/
      implementation-plan.md   # Sample IMPLEMENTATION_PLAN.md (for implement-plan)
  commands/
    *.eval.md                  # One eval file per command
  skills/
    *.eval.md                  # One eval file per skill
```

## Eval File Format

Each eval file contains:

```markdown
---
command: <name>
type: command|skill
fixtures: [list of required fixtures]
---

# Eval: /<name>

## Purpose
What this command does and what "good" output looks like.

## Fixtures
Table of required fixture files and their purpose.

## Test Scenarios

### S1: <scenario name>
**Invocation:** `/command-name <args>`
**Setup:** <any preconditions>

**Must** (fail eval if any are missing):
- [ ] criterion 1

**Should** (warn if missing, don't fail):
- [ ] criterion 1

**Must NOT** (fail eval if present):
- [ ] criterion 1

## Rubric
Scoring table with weights.
```

## Running Evals

Evals are designed to be executed in a live Claude Code session. They are not automated unit tests — they test LLM behavior against a behavioral contract.

### Manual Execution

1. Open a Claude Code session in a scratch directory (not the marketplace repo)
2. Install the plugin: `/plugin marketplace add davistroy/claude-marketplace && /plugin install personal-plugin@troys-plugins`
3. Copy the relevant fixture file(s) into the scratch directory
4. Follow the invocation and setup steps in each scenario
5. Check each Must/Should/Must NOT criterion

### Batch Evaluation

To evaluate all commands systematically:

```bash
# Create a temp eval workspace
mkdir -p /tmp/eval-workspace && cd /tmp/eval-workspace
cp -r <marketplace>/evals/fixtures/* .

# Open Claude Code and run each scenario
# Track results in a spreadsheet or eval-results.md
```

### Scoring

For each scenario:
- All **Must** criteria met = PASS
- Any **Must NOT** criterion present = FAIL regardless of Must
- **Should** criteria tracked separately as quality notes

For each command overall, score the Rubric criteria and record:
- PASS (all Must met, no Must NOT triggered)
- PARTIAL (some Must missing, no Must NOT)
- FAIL (Must NOT triggered, or critical Must missing)

## Fixture Descriptions

| Fixture | Description | Commands That Use It |
|---------|-------------|----------------------|
| `docs/sample-prd.md` | Well-formed PRD for "Daily Standup Bot" | assess-document, define-questions, create-plan, review-intent |
| `docs/draft-prd.md` | Incomplete PRD with TBDs, questions, vague requirements | assess-document, define-questions, finish-document, create-plan |
| `docs/meeting-transcript.md` | 20-min kickoff meeting with action items and decisions | analyze-transcript |
| `docs/ip-document.md` | Internal process doc with company identifiers | remove-ip |
| `docs/multi-variant-a.md` | API design doc, REST-centric | consolidate-documents |
| `docs/multi-variant-b.md` | API design doc, GraphQL-centric | consolidate-documents |
| `json/questions-sample.json` | 5 pre-extracted questions from draft-prd.md | ask-questions |
| `plans/implementation-plan.md` | 2-phase IMPLEMENTATION_PLAN.md for the standup bot | implement-plan |

## Maintenance

- When a command's behavior changes, update the corresponding eval file
- When adding a new command or skill, add a new eval file and register the fixture if needed
- Run the full eval suite before releasing a new plugin version (`/bump-version`)
- The `/validate-plugin` command checks structure; evals check behavior
