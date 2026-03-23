---
command: develop-image-prompt
type: command
fixtures: [docs/sample-prd.md, docs/meeting-transcript.md]
---

# Eval: /develop-image-prompt

## Purpose

Generates a detailed image generation prompt from a document or content description. Good output: a prompt that is specific, visual, non-abstract, includes style/composition/lighting guidance, and is calibrated to the specified dimensions and style options.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/sample-prd.md` | Source document for a product feature illustration |
| `docs/meeting-transcript.md` | Source for a team collaboration visual |

## Test Scenarios

### S1: Happy path — prompt from PRD

**Invocation:** `/develop-image-prompt fixtures/docs/sample-prd.md`

**Must:**
- [ ] Generates at least one image prompt
- [ ] Prompt is specific and visual (mentions concrete visual elements — not abstract concepts like "productivity")
- [ ] Prompt includes style guidance (e.g., illustration style, color palette, mood)
- [ ] Prompt is a single coherent paragraph or structured block, not a list of bullet points

**Should:**
- [ ] Prompt references Slack-like interface elements given the PRD's subject matter
- [ ] Includes composition guidance (foreground/background, perspective)
- [ ] Suggests aspect ratio or dimensions appropriate for the content

**Must NOT:**
- [ ] Generate a prompt that is purely text-based (e.g., "an image showing productivity")
- [ ] Include real company names, trademarks, or real people's faces

---

### S2: Custom dimensions

**Invocation:** `/develop-image-prompt fixtures/docs/sample-prd.md --dimensions 16:9`

**Must:**
- [ ] Prompt specifies 16:9 landscape orientation
- [ ] Composition guidance suits widescreen format

---

### S3: Custom style

**Invocation:** `/develop-image-prompt fixtures/docs/sample-prd.md --style photorealistic`

**Must:**
- [ ] Prompt is calibrated for photorealistic output (not cartoon/illustration)
- [ ] Style guidance in prompt matches the requested style

---

### S4: Multiple prompt variants

**Invocation:** `/develop-image-prompt fixtures/docs/sample-prd.md --variants 3`

**Must:**
- [ ] Generates 3 distinct prompts (if `--variants` flag is supported)
- [ ] Each variant takes a meaningfully different visual approach

---

### S5: Error — file not found

**Invocation:** `/develop-image-prompt fixtures/docs/nonexistent.md`

**Must:**
- [ ] Displays error for missing file

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Prompt contains concrete visual elements | Required |
| Style/composition guidance included | Required |
| No abstract vague language as the entire prompt | Required |
| Dimensions respected when specified | Required |
