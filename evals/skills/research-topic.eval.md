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

---

### S5: Claude leg — safety refusal discards the report, does not fail the run

**Setup:** The Claude leg's `research-sse` accumulator terminates with a safety
refusal (`$ACC_EXIT=4`) — the terminal reason arrived inside a streamed
`message_delta` event, not a top-level `stop_reason` field.

**Must:**
- [ ] Discards any partial text — no `reports/research-claude-[TIMESTAMP].md`
      file is written for this leg
- [ ] Branches on `$ACC_EXIT` (the exit-status contract), never re-derives the
      refusal from a top-level field lookup on the response body
- [ ] Notes in the synthesized report that the Claude leg was declined by
      safety classifiers, rather than silently omitting it
- [ ] Continues synthesis with the remaining providers rather than failing
      the whole run

**Must NOT:**
- [ ] Write a partial or empty Claude report file after a refusal
- [ ] Present exit code 4 as a generic transport/network failure

---

### S6: Claude leg — truncation at the depth ceiling is kept, not discarded

**Setup:** The Claude leg's stream reaches `stop_reason: max_tokens` and
`research-sse` exits 0 with `"truncated": true` in its metadata.

**Must:**
- [ ] Treats exit 0 as success even when `truncated` is `true` — truncation is
      not read as a failure
- [ ] Keeps the accumulated findings rather than discarding them
- [ ] Appends a truncation note (e.g. "response truncated at the depth
      ceiling; consider a deeper `--depth`") to the Claude section so
      synthesis does not treat a cut-off section as complete

**Must NOT:**
- [ ] Discard truncated-but-real content
- [ ] Present the truncated Claude section as complete with no note

---

### S7: Claude leg — stream dies mid-flight with no terminal event

**Setup:** The Claude leg's stream opens with HTTP 200 and then dies before
any terminal reason is ever resolved (`research-sse` exits 5, the
completeness sentinel).

**Must:**
- [ ] Fails the Claude leg based on `$ACC_EXIT=5`, never on the header HTTP
      status (a 200 header proves nothing about stream completeness)
- [ ] Continues synthesis with the remaining providers rather than failing
      the whole run
- [ ] Notes that the Claude leg failed rather than silently omitting it

**Must NOT:**
- [ ] Report Claude-leg success because the header status was 200
- [ ] Treat a mid-flight death the same as a clean, complete response

---

### S8: Claude leg — response parse keeps only report text, never reasoning

**Setup:** The Claude leg's stream interleaves `thinking`/`redacted_thinking`
content blocks alongside `text` blocks before terminating normally.

**Must:**
- [ ] The written Claude report contains only the concatenated `text` block
      content, in block-index order
- [ ] Reasoning content is excluded regardless of the `thinking.display`
      request setting

**Must NOT:**
- [ ] Include any `thinking_delta`, `signature_delta`, or
      `redacted_thinking` content in the final written report

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Parallel provider queries | Required |
| Synthesis identifies agreement/disagreement | Required |
| Report saved to timestamped file | Required |
| Graceful degradation on provider failure | Required |
| Missing API keys produce clear error | Required |
| Claude-leg refusal (`$ACC_EXIT=4`) discards partial output and is noted, not silently dropped | Required |
| Claude-leg truncation (`$ACC_EXIT=0`, `truncated=true`) keeps findings and appends a note | Required |
| Claude-leg mid-flight death (`$ACC_EXIT=5`) is never read as success from a 200 header | Required |
| Claude report text excludes all reasoning/thinking block content | Required |
