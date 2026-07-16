# slide-gen

AI-assisted presentation generation pipeline: research, outline, draft, optimize, validate graphics, generate images, and build PowerPoint files.

## External Dependency (REQUIRED)

**This plugin ships pipeline skills only — it does not include the generation engine.** Every skill in `slide-gen` is a thin wrapper around an `sg` CLI that must be installed separately, from a repo that is **not this one**.

- The `sg` engine lives in [`davistroy/slide-generator`](https://github.com/davistroy/slide-generator), a **PRIVATE** GitHub repository.
- As of this writing, that repo has no public release and no published package. There is no install path for anyone without direct access to it.
- **This plugin is functional only for the repo owner** (someone with access to the private `slide-generator` repo, with `sg` installed and on `PATH`, plus `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY` set). If that isn't you, installing `slide-gen@troys-plugins` gets you skill prompts that will fail their preflight check on first use.
- If `slide-generator` is later made public or published, this section and ADR-0008 (`docs/adr/0008-slide-gen-dependency-model.md`) will be updated to reflect a real install path.

See [ADR-0008](../../docs/adr/0008-slide-gen-dependency-model.md) for the full rationale on why the engine is declared external rather than vendored into this plugin.

## Installation

```text
/plugin install slide-gen@troys-plugins
```

See [root README](../../README.md) for marketplace setup instructions.

## What's Included

- **9 Skills** — 7-step pipeline from topic research to finished PowerPoint: `/sg-research`, `/sg-outline`, `/sg-draft`, `/sg-optimize`, `/sg-validate-graphics`, `/sg-generate-images`, `/sg-build`, `/sg-full-workflow` (end-to-end runner), and `/build-cfa-deck` (on-brand Chick-fil-A presentations)
- **Research Integration** — autonomous web research with structured output
- **Image Generation** — Gemini Pro integration for slide visuals from validated graphics descriptions
- **PowerPoint Assembly** — combine markdown slides and generated images into polished .pptx files

Full pipeline documentation available in [root README](../../README.md#slide-gen).

## License

MIT — see [LICENSE](LICENSE)

## Version

1.2.0
