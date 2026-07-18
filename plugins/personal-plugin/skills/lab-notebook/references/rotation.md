# Lab Notebook Rotation Procedure

Detailed steps for `/lab-notebook rotate`. Rotation bounds the size of `LAB_NOTEBOOK.md` — which CLAUDE.md and `/prime` mandate reading in full — by moving the oldest closed experiment entries into a dated archive under `docs/archive/`, while keeping every decision live in the notebook.

**Rotation is a MOVE, not a delete (Rule 4).** No decision, and no entry content, is ever lost — it relocates, with pointers in both directions.

## When to rotate (trigger)

Rotate when the Experiment Log has grown enough that the mandatory first-read is expensive:

- **~40+ entries**, OR
- **`LAB_NOTEBOOK.md` > ~1200 lines** (roughly 50K tokens), OR
- opportunistically at a **release boundary** when the recent arc is closed.

Target end state: the live notebook keeps its living sections plus roughly the **last ~20 entries** (~800–1000 lines). `/lab-notebook status` recommends rotation when the trigger is hit.

## Procedure

### Step 0 (BLOCKING) — Promote body-only decisions

Before choosing anything to archive, guarantee the Decision Log is complete. Scan the entries that would be archived for decisions recorded **only in entry bodies** and never promoted to the Decision Log table:

- `**Decision (Dxx):**` prose lines
- `Dxx:` bullets inside an entry's Actions/Decisions section
- any `Dxx` referenced from outside the notebook (CLAUDE.md, ADRs, SECURITY.md) that is not a table row

For each, add a row to the Decision Log table (verbatim statement + alternatives + source entry). **Skipping this silently deletes live decisions** — it nearly lost D14–D18 (a Rule 7 lapse where five decisions lived only in E005/E006 bodies while an Accepted ADR cited one of them). Commit this promotion separately if it is substantial; it is valuable on its own.

Verify: `grep -oP '^\| D\K[0-9]+' LAB_NOTEBOOK.md | sort -n | uniq` shows a **contiguous** sequence with no gaps.

### Step 1 — Choose the cut point (a session marker)

List the session markers and entry headings:

```bash
grep -n '^--- New session\|^### Entry' LAB_NOTEBOOK.md
```

Pick the `--- New session:` marker that leaves roughly the last ~20 entries (and every entry newer than it) in the live file. **Cut only at a session marker** so no session narrative is split, and never split an individual entry. Everything from the first `### Entry` up to (but not including) that marker is the slice to archive. Note the first and last entry numbers in the slice (e.g. E001–E016).

### Step 2 — Create the archive file

Write `docs/archive/LAB_NOTEBOOK-E{first}-E{last}.md` containing the sliced entries **verbatim**, prefixed with a banner:

```markdown
# Lab Notebook Archive — Entries E{first}–E{last}

**Archived:** {YYYY-MM-DD}
**Source:** `../../LAB_NOTEBOOK.md` (rotated to bound the mandatory first-read size)
**Range:** Entry {first} ({date}) through Entry {last} ({date})
**Note:** Historical. Every decision these entries established remains live in the Decision Log of `../../LAB_NOTEBOOK.md`. Nothing here was deleted.

---
```

### Step 3 — Stage the archive with `-f`

`docs/archive/` is matched by a global `~/.gitignore_global` `archive/` rule, so a plain `git add`/`git add -A` **silently skips** the new file. Force-add it:

```bash
git add -f docs/archive/LAB_NOTEBOOK-E{first}-E{last}.md
git check-ignore docs/archive/LAB_NOTEBOOK-E{first}-E{last}.md   # confirms it WAS ignored (hence -f)
git status --short | grep archive                                # confirms it is now staged (A)
```

### Step 4 — Cut from the live notebook + forward pointer

Remove the archived slice from `LAB_NOTEBOOK.md`. Keep the `## Experiment Log` header and insert a forward pointer directly beneath it:

```markdown
> **Earlier entries archived:** E{first}–E{last} ({date}→{date}) live in
> [`docs/archive/LAB_NOTEBOOK-E{first}-E{last}.md`](docs/archive/LAB_NOTEBOOK-E{first}-E{last}.md).
> Every decision they established remains in the Decision Log above. Entries below start at E{last+1}.
```

Do **not** touch the living sections (Decision Log, Action Items, Prior Work Summary, Current Baseline) or any retained entry.

### Step 5 — Re-point external references

Archived entries are usually referenced as prose (`Entry 0NN` / `E0NN`), not markdown links, so archiving degrades rather than breaks them. Add an archive hint next to external references that point into the archived range:

```text
... (archived — see `docs/archive/LAB_NOTEBOOK-E{first}-E{last}.md`)
```

Check `SECURITY.md`, `docs/adr/*`, `CLAUDE.md`, and `IMPLEMENTATION_PLAN.md`. References whose decision now lives in the Decision Log table need no hint. Never modify already-frozen files under `docs/archive/*`.

### Step 6 — Verify, then commit

```bash
# Decision Log intact and gapless
grep -oP '^\| D\K[0-9]+' LAB_NOTEBOOK.md | sort -n | uniq | tr '\n' ' '
# Archive holds exactly the entries removed
grep -c '^### Entry' docs/archive/LAB_NOTEBOOK-E{first}-E{last}.md
# No entry appears in both files (must print 0)
comm -12 <(grep '^### Entry' LAB_NOTEBOOK.md | sort) \
         <(grep '^### Entry' docs/archive/LAB_NOTEBOOK-E{first}-E{last}.md | sort) | wc -l
# Both files lint clean
npx markdownlint-cli --config .markdownlint.json LAB_NOTEBOOK.md docs/archive/LAB_NOTEBOOK-E{first}-E{last}.md
```

All must pass: Decision Log contiguous, archive count equals the number removed, zero live/archive overlap, lint clean. The commit-gate hook still passes because recent entries carry today's date. Log the rotation as a new entry before committing (Rule 11).

## What must never happen

- A decision disappearing from the notebook (Rule 4) — Step 0 prevents this.
- A split session or entry — Step 1 cuts only at session markers.
- The archive file missing from the commit — Step 3's `git add -f` prevents the silent gitignore skip.
