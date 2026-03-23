---
command: visual-explainer
type: skill
fixtures: [docs/sample-prd.md]
---

# Eval: /visual-explainer (skill)

## Purpose

Transforms text or documents into AI-generated infographic pages using Gemini Pro 3 for image generation and Claude Vision for evaluation. Good output: one or more image files that visually explain the content, plus a quality evaluation of each image.

## Fixtures

| Fixture | Purpose |
|---------|---------|
| `docs/sample-prd.md` | Source document for visual explanation |

## Setup

Before testing: run `/unlock` to load GOOGLE_API_KEY (required for Gemini image generation).

## Test Scenarios

### S1: Generate visual explainer from PRD

**Invocation:** `/visual-explainer fixtures/docs/sample-prd.md`

**Must:**
- [ ] Generates at least one image file
- [ ] Image is saved to disk (not just shown inline)
- [ ] Output path is reported to user
- [ ] Claude Vision evaluates the image quality after generation

**Should:**
- [ ] Image visually represents the standup bot concept (not a random image)
- [ ] Quality evaluation report notes relevance to source document

**Must NOT:**
- [ ] Fail silently if Gemini API call fails
- [ ] Produce an empty or corrupted image file

---

### S2: Missing API key

**Setup:** Run without GOOGLE_API_KEY set.

**Invocation:** `/visual-explainer fixtures/docs/sample-prd.md`

**Must:**
- [ ] Detects missing GOOGLE_API_KEY
- [ ] Tells user to run `/unlock` first
- [ ] Does not produce a confusing Gemini API error

---

### S3: Multiple pages

**Invocation:** `/visual-explainer fixtures/docs/sample-prd.md --pages 3`

**Must:**
- [ ] Generates 3 images (or fewer if content doesn't warrant it, with explanation)
- [ ] Each image covers a different aspect of the source document

## Rubric

| Criterion | Pass Threshold |
|-----------|---------------|
| Image file(s) generated | Required |
| Output path reported | Required |
| Vision quality evaluation performed | Should |
| Missing API key handled clearly | Required |
| Image is contextually relevant to source | Should |
