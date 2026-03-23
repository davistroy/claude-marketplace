---
command: research-topic
type: skill
fixtures: []
---

# Eval: /research-topic (skill)

## Purpose

Orchestrates parallel deep research across multiple LLM providers and synthesizes results into a comprehensive report. Good output: a synthesized research document that draws from multiple sources, identifies consensus and disagreements, and is more thorough than a single-provider answer.

## Fixtures

None — this skill queries external LLM APIs. Requires API keys loaded via `/unlock`.

## Setup

Before testing: run `/unlock` to load API keys. Verify keys for at least 2 providers are available.

## Test Scenarios

### S1: Research a well-defined technical topic

**Invocation:** `/research-topic "best practices for retry logic in distributed systems"`

**Must:**
- [ ] Queries at least 2 LLM providers in parallel
- [ ] Produces a synthesized report that is longer and more detailed than a single-provider answer
- [ ] Report identifies where providers agreed and disagreed
- [ ] Report is saved to a file (timestamped)

**Should:**
- [ ] Uses the research-models.md configuration for provider selection
- [ ] Includes citations or source attribution per provider
- [ ] Report follows the practitioner depth style (technical, specific)

**Must NOT:**
- [ ] Return identical content from each provider (must actually synthesize)
- [ ] Fail silently if one provider is unavailable (should gracefully degrade)

---

### S2: Research with provider failure

**Setup:** Intentionally use an invalid API key for one provider.

**Must:**
- [ ] Continues with remaining providers
- [ ] Notes which provider failed in the report
- [ ] Does not produce an empty report if at least one provider succeeds

---

### S3: Short topic

**Invocation:** `/research-topic "git rebase vs merge"`

**Must:**
- [ ] Still queries multiple providers
- [ ] Synthesis adds value over a single response
- [ ] Completes in a reasonable time

---

### S4: No API keys available

**Setup:** Run without calling `/unlock` first.

**Must:**
- [ ] Detects missing API keys
- [ ] Tells user to run `/unlock` first
- [ ] Does not crash with an obscure error

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Parallel provider queries | Required |
| Synthesis identifies agreement/disagreement | Required |
| Report saved to timestamped file | Required |
| Graceful degradation on provider failure | Required |
| Missing API keys produce clear error | Required |
