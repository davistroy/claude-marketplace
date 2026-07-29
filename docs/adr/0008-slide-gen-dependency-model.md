# ADR-0008: slide-gen Dependency Model — External Engine, Not Vendored

**Date:** 2026-07-16
**Status:** Accepted
**Deciders:** Troy Davis (proposed via arch-review synthesis, finding SA-001)

## Context

The `slide-gen` plugin ships nine skills (`sg-research`, `sg-outline`, `sg-draft`, `sg-optimize`, `sg-validate-graphics`, `sg-generate-images`, `sg-build`, `sg-full-workflow`, `build-cfa-deck`) that are thin wrappers around an `sg` CLI. Eight of these skills invoke `sg <subcommand>` directly (`sg research`, `sg outline`, `sg build`, ...); `build-cfa-deck` is an exception — it contains ~110 lines of PowerPoint assembly logic written in python-pptx, making it a thin wrapper around the CFA template assets rather than the `sg` engine. None of the actual research, drafting, optimization, or PowerPoint-assembly logic lives inside `plugins/slide-gen/`. The `sg` engine itself is a separate project at `github.com/davistroy/slide-generator`, installed independently via `pip install -e ".[all]"`.

The architecture review (solutions-architect domain, finding SA-001) flagged this as an undeclared dependency: `plugin.json`'s `homepage` field pointed at `slide-generator`, not the marketplace repo, and no README or skill made the external requirement prominent before usage steps. A user installing `slide-gen@troys-plugins` via the documented `/plugin install` flow gets nine skills that all fail at the first `sg` invocation unless they separately know to clone and install a second repo.

Resolving Unknown U1 (`gh repo view davistroy/slide-generator --json isPrivate`) confirmed the repo is **private** (`"isPrivate": true`). This changes the honesty requirement from "document the install step" to "document that installation is currently owner-only" — there is no public path today for a non-owner to obtain `sg` at all, regardless of how well the dependency is documented.

ADR-0002 established that Python tools bundled with this marketplace run from source inside `plugins/<name>/tools/<tool>/` specifically to keep plugins self-contained and avoid PyPI publishing or cross-repo version sync. `slide-generator` was not built under that pattern — it is a pre-existing, independently versioned project with its own CLI, its own dependency surface (`ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, Gemini image generation), and its own release cadence, none of which were designed for in-tree bundling.

## Decision

Treat `slide-gen` as a formally declared **external-dependency plugin**:

1. **Do not vendor the `sg` engine.** `plugins/slide-gen/` continues to ship only the pipeline skills (prompts, argument handling, error-handling tables) — never the `slide-generator` source. This reverses nothing from ADR-0002 for tools that *were* built to be bundled; it recognizes that `slide-generator` was never one of those tools.
2. **State the dependency honestly, and state it first.** The slide-gen README carries a prominent "External Dependency (REQUIRED)" section stating: the plugin requires the `sg` CLI from `davistroy/slide-generator`; that repo is currently **private**; and the plugin is therefore **owner-only** until `slide-generator` is made public or published to a package index. No wording implies public installability that does not exist today.
3. **Fail fast, not mid-pipeline.** Every pipeline entry skill (`sg-full-workflow`, and the individual step skills `sg-research`, `sg-outline`, etc.) runs an `sg --version` preflight check before doing any work. If `sg` is missing, the skill stops immediately with an explicit message naming the private repo and the owner-only constraint, instead of letting the pipeline advance several steps and die on an opaque `sg: command not found`.
4. **Revisit if `slide-generator` changes visibility.** If the engine repo is made public or published, this ADR's Consequences and the README wording get updated in the same change — the owner-only framing is a statement about current reality, not a permanent design constraint.

## Consequences

### Positive
- Closes SA-001 without a large import: no `slide-generator` source, dependency tree, or release cadence enters this marketplace's repo
- Honest by default: a prospective user (including future-Troy on a new machine) learns *before* running anything that this plugin does nothing useful without a private repo they may not have access to
- Preflight failure is immediate and named — no more silent multi-step pipeline death on a missing binary
- Keeps `slide-generator`'s independent versioning, dependency surface, and release process fully decoupled from the marketplace's plugin/version scheme

### Negative
- `slide-gen` is genuinely non-functional for any installer other than the owner today — this is a real limitation being surfaced, not invented by the documentation
- Two repos must now be kept loosely in sync by convention (skill argument shapes vs. `sg` CLI flags) with no automated contract test between them
- The preflight check only verifies `sg` is *present*, not that its version matches what the skills assume — a stale `sg` install can still misbehave past the preflight gate

### Neutral
- No change to the actual pipeline behavior once `sg` is installed and on `PATH`
- If `slide-generator` is later published (PyPI or public GitHub), the fix is a README/ADR wording update, not a code migration

## Alternatives Considered

### Vendor the engine into `plugins/slide-gen/tools/` (per ADR-0002)
- **Description:** Import `slide-generator`'s source into the plugin tree, following the same `tools/<tool>/src/` + `PYTHONPATH` pattern used for other bundled Python tools.
- **Pros:** Fully self-contained plugin; works immediately after `/plugin install` with no second repo; consistent with the marketplace's existing tool-bundling convention.
- **Cons:** `slide-generator` is a substantially larger, independently-evolving codebase (multi-stage LLM pipeline, Gemini image integration, its own CLI and test suite) than the marketplace's existing bundled tools; a one-time import would require an ongoing cross-repo sync process to avoid the two copies drifting, for a tool built for personal deck generation rather than public distribution.
- **Why rejected:** Cost (large initial import + permanent sync burden) is disproportionate to the benefit for a personal-use pipeline plugin. Revisit only if `slide-generator` stabilizes enough to be frozen and folded in deliberately, or if multi-consumer demand justifies the maintenance cost.

### Deprecate/remove slide-gen
- **Description:** Since the plugin is non-functional for non-owners, pull it from the marketplace rather than document around the gap.
- **Pros:** Removes the "misleading install" surface entirely; no honesty burden to maintain.
- **Cons:** slide-gen is actively used by the owner for real presentation work; removing it destroys a working personal tool to solve a documentation problem that has a much cheaper fix.
- **Why rejected:** The finding is about undisclosed dependency, not about the plugin being broken or unwanted. Declaring and preflight-checking the dependency fixes the actual problem at a fraction of the cost.

### Status quo (silent external dependency)
- **Description:** Leave `homepage` pointing at `slide-generator`, keep the dependency documented only inside individual skill "Prerequisites" sections, and let missing-`sg` failures surface wherever the pipeline happens to call it.
- **Pros:** No change needed.
- **Cons:** This is the exact configuration SA-001 flagged — a user has no prominent warning before running a skill, and failures surface mid-pipeline as an opaque `sg: command not found` rather than an immediate, actionable message.
- **Why rejected:** It is the finding being remediated, not an alternative to it.
