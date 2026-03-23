---
command: unlock
type: skill
fixtures: []
---

# Eval: /unlock (skill)

## Purpose

Loads secrets from Bitwarden Secrets Manager into the environment using the `bws` CLI. Good behavior: secrets are available as environment variables after invocation, and no secrets are printed to the terminal or written to files.

## Fixtures

None — requires Bitwarden BWS_ACCESS_TOKEN to be set in the environment.

## Test Scenarios

### S1: Load secrets for a project

**Invocation:** `/unlock` or `/unlock <project-name>`

**Must:**
- [ ] Invokes `bws secret list` (or equivalent)
- [ ] Exports secrets as environment variables
- [ ] Reports which variable names were loaded (not their values)
- [ ] Does not print secret values to terminal

**Should:**
- [ ] Reports the count of secrets loaded
- [ ] Notes if any expected secrets are missing

**Must NOT:**
- [ ] Print actual secret values anywhere in output
- [ ] Write secrets to a file
- [ ] Fail silently if BWS_ACCESS_TOKEN is not set

---

### S2: Missing BWS_ACCESS_TOKEN

**Setup:** Unset BWS_ACCESS_TOKEN (`unset BWS_ACCESS_TOKEN`).

**Invocation:** `/unlock`

**Must:**
- [ ] Detects missing access token
- [ ] Displays a clear error with instructions for setting BWS_ACCESS_TOKEN
- [ ] Does not error cryptically (no raw Python tracebacks or bws errors)

---

### S3: Secret values not exposed

**After S1:** Review the conversation output.

**Must NOT:**
- [ ] Any API key values visible in conversation
- [ ] Secrets written to `.env` file or any file

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Secrets loaded into environment | Required |
| Variable names reported (not values) | Required |
| Missing token handled with clear error | Required |
| No secrets written to files or printed to terminal | Required |
