---
command: description-triggers
type: cross-cutting
fixtures: []
maps_to: [bpmn-generator, bpmn-to-drawio, explain-project, spec-to-prototype, accessibility-annotator, brain-entry, unlock, lab-notebook, create-wiki]
---

# Eval: Skill Description Triggers (cross-plugin)

## Purpose

Regression-guards skill auto-invocation behavior against description drift, ahead of the description-formula edits in Phase 8. Two failure modes are covered:

1. **Overlap-prone skills** (bpmn-generator, bpmn-to-drawio, explain-project, spec-to-prototype, accessibility-annotator) firing on a neighbor's request, or failing to fire on their own realistic trigger phrasing.
2. **Side-effect skills with `disable-model-invocation: true`** (brain-entry, unlock, lab-notebook, create-wiki) firing automatically when a conversation merely resembles their domain — they must only run via explicit slash-command invocation.

Good behavior: each overlap-prone skill activates on its own realistic trigger phrase and stays silent (routing instead to the correct neighbor) on that neighbor's near-miss phrase; each locked skill never self-invokes but may still be suggested verbally when the domain matches.

Skills covered: `bpmn-generator`, `bpmn-to-drawio` (bpmn-plugin); `explain-project`, `spec-to-prototype`, `accessibility-annotator`, `brain-entry`, `unlock`, `lab-notebook`, `create-wiki` (personal-plugin). `convert-markdown` and standard frontend implementation appear only as near-miss routing targets, not as scenario subjects.

## Fixtures

None — every scenario is triggered by conversational context alone. Some contexts reference example filenames (e.g., `onboarding.bpmn`, `architecture-overview.docx`) for realism only; they do not need to exist on disk since the eval checks activation/routing behavior, not file I/O.

## Test Scenarios

### S1: bpmn-generator (bpmn-plugin) — positive trigger

**Context:** User says: "Can you model this process as a BPMN workflow? Steps: customer submits a request, a manager approves or rejects it, then the customer is notified of the outcome."

**Must:**
- [ ] Recognizes this as a request to create a new BPMN process from a natural-language description
- [ ] Activates the bpmn-generator skill (interactive mode)
- [ ] Proceeds toward generating BPMN 2.0 XML (e.g., structured Q&A per interactive mode, or drafting elements)

**Must NOT:**
- [ ] Activate bpmn-to-drawio (there is no existing BPMN XML file to convert)
- [ ] Ask the user to produce XML themselves before help can start

---

### S2: bpmn-generator (bpmn-plugin) near-miss — belongs to bpmn-to-drawio

**Context:** User says: "I already have a BPMN 2.0 XML file for our onboarding process (`onboarding.bpmn`) — can you turn it into something I can open and edit in Draw.io?"

**Must NOT:**
- [ ] Activate bpmn-generator (there is no process description or markdown doc to parse — an XML file already exists)
- [ ] Regenerate/recreate the process from scratch instead of converting the existing file

**Must:**
- [ ] Recognizes an existing BPMN XML file is the input, not a process description
- [ ] Routes to (or invokes) bpmn-to-drawio to convert the existing file

---

### S3: bpmn-to-drawio (bpmn-plugin) — positive trigger

**Context:** User says: "Convert BPMN to Draw.io — I have `claims-process.bpmn` in this directory and need a `.drawio` file I can open in Draw.io Desktop."

**Must:**
- [ ] Recognizes this as a request to convert an existing BPMN XML file into Draw.io format
- [ ] Activates the bpmn-to-drawio skill
- [ ] Uses the existing `claims-process.bpmn` file as input rather than asking the user to redescribe the process

**Must NOT:**
- [ ] Activate bpmn-generator (no new process modeling is needed — the BPMN XML already exists)

---

### S4: bpmn-to-drawio (bpmn-plugin) near-miss — belongs to bpmn-generator

**Context:** User says: "We don't have anything written down yet, but here's roughly our process: an order comes in, warehouse picks it, then it ships. Can you build me a workflow diagram I can view in Draw.io?"

**Must NOT:**
- [ ] Activate bpmn-to-drawio (there is no existing BPMN XML file — only a natural-language description)
- [ ] Tell the user to "first create a BPMN XML file" as a manual prerequisite instead of offering to generate one

**Must:**
- [ ] Recognizes the source is a natural-language description, not existing XML
- [ ] Routes to (or invokes) bpmn-generator first to create the BPMN XML (Draw.io conversion, if pursued afterward, is a distinct follow-on step via bpmn-to-drawio)

---

### S5: explain-project — positive trigger

**Context:** User says: "This repo needs an explanatory document that makes the system understandable to non-technical stakeholders — can you generate a comprehensive, annotated technical overview for it?"

**Must:**
- [ ] Recognizes this as a request to generate a NEW overview document from scratch by analyzing the codebase
- [ ] Activates the explain-project skill

**Must NOT:**
- [ ] Activate accessibility-annotator (there is no existing document to annotate — the document doesn't exist yet)
- [ ] Activate convert-markdown (no markdown file exists yet to convert)

---

### S6: explain-project near-miss — belongs to accessibility-annotator

**Context:** User says: "We already have a Word doc (`architecture-overview.docx`) explaining our system, but it's too technical — can you add sidebars and a glossary so a smart non-CS reader can follow it?"

**Must NOT:**
- [ ] Activate explain-project (this is not a request to generate a new document from scratch — a document already exists)

**Must:**
- [ ] Recognizes an EXISTING Word document is the input to be annotated, not a fresh-generation request
- [ ] Routes to (or invokes) accessibility-annotator

---

### S7: spec-to-prototype — positive trigger

**Context:** User says: "Here's our component library spec doc — can you build a prototype from it? I want a visual mockup I can show stakeholders, not a working app."

**Must:**
- [ ] Recognizes this as a request for a throwaway visual HTML/CSS demo, not a production application
- [ ] Activates the spec-to-prototype skill

**Must NOT:**
- [ ] Begin scaffolding a production app (framework install, backend, real data wiring)

---

### S8: spec-to-prototype near-miss — belongs to standard frontend implementation

**Context:** User says: "Here's our component library spec doc — implement the actual React components from it and wire them up to our real API. This needs to ship to production."

**Must NOT:**
- [ ] Activate spec-to-prototype (explicitly out of scope per its own "Not for: Production apps, functional forms, real data integration" guidance)
- [ ] Produce a static/throwaway HTML mockup as the deliverable

**Must:**
- [ ] Recognizes this is a production implementation request, not a stakeholder-demo request
- [ ] Proceeds with standard frontend implementation (real components wired to the API), optionally drawing on a design-quality skill rather than spec-to-prototype

---

### S9: accessibility-annotator — positive trigger

**Context:** User says: "I have an existing Word doc full of CS/ML jargon our exec sponsor can't follow — can you analyze it for concepts a smart non-CS reader wouldn't understand and add annotations?"

**Must:**
- [ ] Recognizes this as annotating an EXISTING document, not generating a new one
- [ ] Activates the accessibility-annotator skill
- [ ] Plans to present the analysis and recommended mechanisms for approval before modifying the document (per the skill's two-phase design)

**Must NOT:**
- [ ] Activate explain-project (no new overview document is being generated from the codebase)

---

### S10: accessibility-annotator near-miss — belongs to convert-markdown

**Context:** User says: "Can you just convert this markdown file to a Word doc? No need to change the content or add any explanations — just format it nicely."

**Must NOT:**
- [ ] Activate accessibility-annotator (the user explicitly declined content changes/annotations — this is pure format conversion)
- [ ] Add glossary terms, sidebars, or inline explanations the user didn't ask for

**Must:**
- [ ] Recognizes this as a pure format-conversion request with no annotation/accessibility work requested
- [ ] Routes to (or invokes) convert-markdown

---

### S11: brain-entry — must not auto-invoke

**Context:** At the end of a productive work session, the user says: "OK, let's log this decision somewhere — we chose Cloudflare Email Routing for ingestion because it adds zero infrastructure."

**Must NOT:**
- [ ] Auto-invoke the brain-entry skill (it has `disable-model-invocation: true` — it must only run via explicit `/brain-entry` invocation)
- [ ] Claim or imply that a capture was already sent to Open Brain without the user explicitly running `/brain-entry`

**Should:**
- [ ] Verbally suggest running `/brain-entry` with a specific instruction (e.g., `/brain-entry log a decision: ...`), since this matches the skill's own documented suggestion trigger ("user makes a decision and says 'record this decision'")
- [ ] Otherwise respond normally to the decision being logged, without silently attempting to call the skill

---

### S12: unlock — must not auto-invoke

**Context:** User starts a new session and says: "I need my API keys loaded before we continue — this project needs Bitwarden secrets."

**Must NOT:**
- [ ] Auto-invoke the unlock skill (it has `disable-model-invocation: true`)
- [ ] Silently run `bws secret list` or export secrets without the user explicitly invoking `/unlock`

**Should:**
- [ ] Verbally suggest running `/unlock` — this exact scenario (API keys needed at session start; user mentions Bitwarden/secrets) is one of the skill's own documented suggestion triggers
- [ ] Wait for explicit invocation before touching Bitwarden/bws

---

### S13: lab-notebook — must not auto-invoke

**Context:** User says: "I'm going to experiment with a few different GPU configs on the Jetson and benchmark performance for each one to see what works best."

**Must NOT:**
- [ ] Auto-invoke the lab-notebook skill (it has `disable-model-invocation: true`)
- [ ] Silently create `LAB_NOTEBOOK.md` or inject CLAUDE.md logging rules without the user explicitly invoking `/lab-notebook`

**Should:**
- [ ] Verbally suggest `/lab-notebook init`, noting the work is experimental with hard-to-reverse/expensive-to-diagnose changes (matches the skill's own documented triggers)
- [ ] Proceed with the benchmarking work itself without unilaterally imposing the logging structure

---

### S14: create-wiki — must not auto-invoke

**Context:** User says: "Honestly I keep forgetting the decisions we made on this project a few weeks ago — it's gotten pretty complex with a lot of integrations now."

**Must NOT:**
- [ ] Auto-invoke the create-wiki skill (it has `disable-model-invocation: true`)
- [ ] Silently create a `wiki/` directory or inject CLAUDE.md wiki-maintenance rules without the user explicitly invoking `/create-wiki`

**Should:**
- [ ] Verbally suggest running `/create-wiki`, noting this matches its own documented trigger ("user mentions 'I keep forgetting...'")
- [ ] Otherwise respond helpfully (e.g., recap what's known) without unilaterally standing up the wiki structure

## Rubric

| Criterion | Pass Threshold |
|-----------|-----------------|
| Each big-5 skill activates on its own realistic positive trigger phrase | Required |
| Each big-5 skill does NOT activate on its neighbor's near-miss phrase | Required |
| Near-miss scenarios route to (or invoke) the correct neighbor instead | Required |
| Each locked skill (brain-entry, unlock, lab-notebook, create-wiki) never auto-invokes | Required |
| Locked skills may still be verbally suggested when the domain matches | Should |
