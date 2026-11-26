"""Command-line front end for the document-repo tool.

Each subcommand is a thin wrapper: parse arguments, call one library
function, print JSON. Exit codes: 0 success, 1 a check failed (for example a
file changed in more than its comments), 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import __version__


def emit(obj: Any, out: Path | None = None) -> None:
    """Write ``obj`` as pretty JSON to ``out``, or to stdout when ``out`` is None.

    A path that is not valid UTF-8 reaches here as a surrogate escape (git output is decoded
    with ``surrogateescape``). It is written back as its original bytes rather than crashing the
    writer after the work is done.
    """
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    if out is None:
        # Write UTF-8 bytes directly: a Windows console may use a legacy code page that cannot
        # encode the text.
        buffer = getattr(sys.stdout, "buffer", None)
        if buffer is not None:
            # Flush text already buffered on the text layer so output stays in order.
            sys.stdout.flush()
            buffer.write(text.encode("utf-8", "surrogateescape"))
            buffer.flush()
        else:
            sys.stdout.write(text)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", errors="surrogateescape")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _cmd_inventory(args: argparse.Namespace) -> int:
    from .inventory import build_inventory

    try:
        inventory = build_inventory(args.repo)
    except NotADirectoryError as exc:
        print(f"inventory: {exc}", file=sys.stderr)
        return 2
    emit(inventory, args.out)
    return 0


def _register_inventory(sub: Any) -> None:
    p = sub.add_parser("inventory", help="list files, languages, skip reasons, entry points")
    p.add_argument("repo", type=Path)
    p.add_argument("--out", type=Path)
    p.set_defaults(func=_cmd_inventory)


def _cmd_modules(args: argparse.Namespace) -> int:
    from .modules import propose_modules

    emit(propose_modules(load_json(args.inventory)), args.out)
    return 0


def _register_modules(sub: Any) -> None:
    p = sub.add_parser("modules", help="propose module boundaries from an inventory")
    p.add_argument("inventory", type=Path)
    p.add_argument("--out", type=Path)
    p.set_defaults(func=_cmd_modules)


def _cmd_verify(args: argparse.Namespace) -> int:
    import subprocess

    from .verify import changed_files, verify_file

    if args.changed:
        if not args.before.strip():
            sys.stderr.write("verify: --before is empty (an unset variable?)\n")
            return 2
        try:
            files = changed_files(args.repo, args.before)
        except NotADirectoryError as exc:
            sys.stderr.write(f"verify: {exc}\n")
            return 2
        except subprocess.CalledProcessError as exc:
            err = (exc.stderr or b"").decode("utf-8", "replace").strip()
            sys.stderr.write(f"verify: cannot list changes against {args.before!r}: {err}\n")
            return 2
    elif args.files:
        files = list(args.files)
    else:
        sys.stderr.write("verify: give FILE paths or --changed\n")
        return 2
    results = [verify_file(args.repo, f, args.before).to_dict() for f in files]
    emit(results)
    return 0 if all(r["ok"] for r in results) else 1


def _register_verify(sub: Any) -> None:
    p = sub.add_parser("verify", help="prove files changed only in comments")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--before", default="HEAD", help="base git ref (default HEAD)")
    p.add_argument(
        "--changed", action="store_true", help="verify every changed or untracked file but docs"
    )
    p.add_argument("files", nargs="*")
    p.set_defaults(func=_cmd_verify)


def _cmd_assemble(args: argparse.Namespace) -> int:
    from .build import assemble_model, read_object
    from .schema import validate

    if not args.repo.is_dir():
        sys.stderr.write(f"assemble: {args.repo} is not a directory\n")
        return 2
    try:
        base = read_object(args.base_model) if args.base_model else None
        model, notes = assemble_model(args.run_dir, args.repo, base_model=base)
        emit(model, args.run_dir / "model.json")
        emit(notes, args.run_dir / "file-notes.json")
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"assemble: {exc}\n")
        return 2
    errors = validate(model)
    for err in errors:
        sys.stderr.write(err + "\n")
    return 1 if errors else 0


def _register_assemble(sub: Any) -> None:
    p = sub.add_parser("assemble", help="join module records + system sections into model.json")
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--base-model", type=Path)
    p.set_defaults(func=_cmd_assemble)


def _cmd_build(args: argparse.Namespace) -> int:
    from .build import (
        TEMPLATE_DIR,
        ensure_installable,
        install_template,
        read_json,
        write_explorer_data,
    )
    from .schema import validate

    try:
        model = read_json(args.model)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"build: {exc}\n")
        return 2
    errors = validate(model)
    if errors:
        for err in errors:
            sys.stderr.write(err + "\n")
        return 1
    if args.validate_only:
        return 0
    try:
        # Before any write, with or without --template: data written into a directory the
        # skill did not make would turn its marker valid (see build.ensure_installable).
        ensure_installable(args.template or TEMPLATE_DIR, args.explorer_dir)
        if args.template:
            install_template(args.template, args.explorer_dir)
        state = write_explorer_data(model, args.explorer_dir / "data")
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"build: {exc}\n")
        return 2
    emit(state)
    return 0


def _register_build(sub: Any) -> None:
    p = sub.add_parser("build", help="validate a model and write explorer data")
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--explorer-dir", type=Path, required=True)
    p.add_argument("--template", type=Path)
    p.add_argument("--validate-only", action="store_true")
    p.set_defaults(func=_cmd_build)


def _cmd_remap(args: argparse.Namespace) -> int:
    from .remap import RemapError, remap_model, write_model

    try:
        model = json.loads(args.model.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"remap: {args.model}: {exc}\n")
        return 2
    try:
        remapped, warnings = remap_model(model, args.repo, args.to)
        write_model(args.model, remapped)
    except (OSError, RemapError) as exc:
        sys.stderr.write(f"remap: {exc}\n")
        return 2
    emit({"warnings": warnings})
    return 0


def _register_remap(sub: Any) -> None:
    p = sub.add_parser("remap", help="move model line numbers to a newer commit")
    p.add_argument("--model", type=Path, required=True, help="model.json, rewritten in place")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--to", default="HEAD", help="commit the line numbers should refer to")
    p.set_defaults(func=_cmd_remap)


def _cmd_upsert_section(args: argparse.Namespace) -> int:
    from .docs import upsert_file

    try:
        body = args.content_file.read_text(encoding="utf-8")
        upsert_file(args.file, args.section, body, args.repo)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"upsert-section: {exc}\n")
        return 2
    return 0


def _register_upsert_section(sub: Any) -> None:
    p = sub.add_parser("upsert-section", help="write a generated section between markers")
    p.add_argument("--file", type=Path, required=True)
    p.add_argument("--section", required=True)
    p.add_argument("--content-file", type=Path, required=True)
    p.add_argument(
        "--repo",
        type=Path,
        help="top level of the git work tree the file must resolve into "
        "(default: the work tree that holds --file)",
    )
    p.set_defaults(func=_cmd_upsert_section)


def _load_input(path: Path) -> Any:
    """``load_json`` with the file named in the error: a parse error does not say which file."""
    try:
        return load_json(path)
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc


def _cmd_changes(args: argparse.Namespace) -> int:
    from .changes import compute_changes, work_tree
    from .inventory import OUTPUT_DIR

    data = (args.explorer_dir or args.repo / OUTPUT_DIR) / "data"
    try:
        # First: a --repo that is not the top level has no explorer/data of its own, and "no such
        # file" would hide the real mistake.
        work_tree(args.repo)
        state = _load_input(data / "state.json")
        model = _load_input(data / "model.json")
        result = compute_changes(args.repo, state, model)
    except (ValueError, OSError) as exc:
        sys.stderr.write(f"changes: {exc}\n")
        return 2
    emit(result)
    return 0


def _register_changes(sub: Any) -> None:
    p = sub.add_parser("changes", help="modules affected since the docs were built")
    p.add_argument("--repo", type=Path, required=True, help="top level of the git work tree")
    p.add_argument(
        "--explorer-dir",
        type=Path,
        help="holds data/state.json and data/model.json (REPO/explorer)",
    )
    p.set_defaults(func=_cmd_changes)


def _repo_arg(value: str) -> Path:
    """``--repo`` for commands that write: an empty value (an unset variable) is an error."""
    if not value.strip():
        raise argparse.ArgumentTypeError("--repo is empty (an unset variable?)")
    return Path(value)


def _cmd_commit(args: argparse.Namespace) -> int:
    from .commit import InputError, commit_paths

    try:
        outcome = commit_paths(
            args.repo,
            list(args.files),
            list(args.message),
            None if args.no_content_check else args.verify_against,
            skip_hooks=args.skip_hooks,
        )
    except InputError as exc:
        sys.stderr.write(f"commit: {exc}\n")
        return 2
    except Exception as exc:
        # ``commit_paths`` turns every failure after ``git commit`` ran into a ``stop`` outcome,
        # so an exception that reaches here was raised before the commit: nothing was committed.
        detail = f"{type(exc).__name__}: {exc}; nothing was committed"
        sys.stderr.write(f"commit: error: {detail}\n")
        emit({"status": "error", "detail": detail})
        return 2
    emit(outcome.to_dict())
    if outcome.exit_code:
        sys.stderr.write(f"commit: {outcome.status}: {outcome.detail}\n")
    return outcome.exit_code


def _register_commit(sub: Any) -> None:
    p = sub.add_parser("commit", help="commit exactly the listed paths and prove the commit")
    p.add_argument("--repo", type=_repo_arg, required=True, help="top level of the git work tree")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--verify-against", metavar="REF", help="every changed path must be comment-only vs REF"
    )
    mode.add_argument(
        "--no-content-check", action="store_true", help="skip the comment-only check (docs)"
    )
    p.add_argument(
        "--message",
        "-m",
        action="append",
        required=True,
        help="commit message; repeat for more paragraphs (subject first)",
    )
    p.add_argument(
        "--skip-hooks", action="store_true", help="pass --no-verify to git commit (user's choice)"
    )
    p.add_argument("files", nargs="*", metavar="FILE", help="paths relative to --repo")
    p.set_defaults(func=_cmd_commit)


def _cmd_backstop(args: argparse.Namespace) -> int:
    from .commit import GitError, InputError, backstop

    try:
        result = backstop(args.repo, args.base)
    except (InputError, GitError, OSError) as exc:
        sys.stderr.write(f"backstop: {exc}\n")
        return 2
    emit(result)
    return 0 if result["ok"] else 1


def _register_backstop(sub: Any) -> None:
    p = sub.add_parser("backstop", help="verify the whole branch against its base, tree clean")
    p.add_argument("--repo", type=_repo_arg, required=True, help="top level of the git work tree")
    p.add_argument("--base", required=True, help="the commit the branch started from")
    p.set_defaults(func=_cmd_backstop)


def _cmd_explorer_status(args: argparse.Namespace) -> int:
    from .build import (
        DATA_DIR,
        RUN_REPORT_FILE,
        TEMPLATE_DIR,
        explorer_output,
        foreign_files,
        is_our_explorer,
        read_marker,
    )
    from .commit import GitError, left_out, rule_in_place, tracked_paths
    from .inventory import OUTPUT_DIR
    from .verify import toplevel

    top = toplevel(args.repo)
    if top is None or top.resolve() != args.repo.resolve():
        sys.stderr.write(f"explorer-status: not the top level of a git work tree: {args.repo}\n")
        return 2
    explorer = top / OUTPUT_DIR
    foreign = foreign_files(TEMPLATE_DIR, explorer)
    # "absent" covers a directory build would accept but that is not (yet) ours: an empty one,
    # what moving files aside leaves, or an install that stopped before data/ was written.
    if foreign:
        status = "foreign"
    elif os.path.lexists(explorer) and is_our_explorer(explorer):
        status = "ours"
    else:
        status = "absent"
    # Ask git before the gate: a rule such as ``data/`` would keep the build's own files out of
    # the commit, and ``git add`` would not say so. Exists or not, git answers for the path.
    outputs = explorer_output(TEMPLATE_DIR)
    try:
        ignored = left_out(top, outputs)
        tracked = sorted(tracked_paths(top, outputs))
    except GitError as exc:
        sys.stderr.write(f"explorer-status: {exc}\n")
        return 2
    # What HEAD holds of the build's output. Holding some but not all (the app without its data,
    # because a rule skipped it) is an explorer that opens empty on a fresh clone. The run report
    # is written last and nothing needs it, so it does not count.
    required = set(outputs) - {f"{OUTPUT_DIR}/{DATA_DIR}/{RUN_REPORT_FILE}"}
    incomplete = sorted(required - set(tracked)) if required & set(tracked) else []
    recorded = read_marker(explorer)
    emit(
        {
            "explorer": status,
            "foreign_files": foreign,
            "ignored": sorted(ignored),
            "ignored_by": sorted(set(ignored.values())),
            "tracked": tracked,
            "incomplete": incomplete,
            "kept_local": None
            if recorded is None
            else {"rules": recorded, "gone": [r for r in recorded if not rule_in_place(top, r)]},
        }
    )
    return 0


def _register_explorer_status(sub: Any) -> None:
    p = sub.add_parser(
        "explorer-status",
        help="is REPO/explorer ours (a build made it), foreign, or absent (build may write it)",
    )
    p.add_argument("--repo", type=_repo_arg, required=True, help="top level of the git work tree")
    p.set_defaults(func=_cmd_explorer_status)


def _cmd_keep_local(args: argparse.Namespace) -> int:
    from .build import (
        LOCAL_MARKER,
        TEMPLATE_DIR,
        explorer_output,
        foreign_files,
        read_marker,
        write_marker,
    )
    from .commit import GitError, left_out
    from .inventory import OUTPUT_DIR
    from .verify import toplevel

    top = toplevel(args.repo)
    if top is None or top.resolve() != args.repo.resolve():
        sys.stderr.write(f"keep-local: not the top level of a git work tree: {args.repo}\n")
        return 2
    explorer = top / OUTPUT_DIR
    if explorer.is_symlink() or not explorer.is_dir():
        sys.stderr.write(f"keep-local: no explorer to keep local: {explorer} is not a directory\n")
        return 2
    kept = read_marker(explorer)
    if kept is not None:
        # Looking again would only see the marker's own ``*``, so the rules it recorded stand.
        emit({"written": False, "rules": kept})
        return 0
    if os.path.lexists(explorer / LOCAL_MARKER):
        sys.stderr.write(
            f"keep-local: {explorer / LOCAL_MARKER} exists and is not the file keep-local writes: "
            "move it aside, then run again\n"
        )
        return 2
    foreign = foreign_files(TEMPLATE_DIR, explorer)
    if foreign:
        sys.stderr.write(
            f"keep-local: {explorer} holds what a build does not write: {', '.join(foreign)}\n"
        )
        return 2
    try:
        rules = sorted(set(left_out(top, explorer_output(TEMPLATE_DIR)).values()))
        if not rules:
            sys.stderr.write(
                "keep-local: nothing to keep local: no ignore rule keeps the explorer out of git\n"
            )
            return 2
        write_marker(explorer, rules)
    except (GitError, OSError) as exc:
        sys.stderr.write(f"keep-local: {exc}\n")
        return 2
    emit({"written": True, "rules": rules})
    return 0


def _register_keep_local(sub: Any) -> None:
    p = sub.add_parser(
        "keep-local",
        help="write explorer/.gitignore so a kept-local explorer leaves the tree clean",
    )
    p.add_argument("--repo", type=_repo_arg, required=True, help="top level of the git work tree")
    p.set_defaults(func=_cmd_keep_local)


def _cmd_traps(args: argparse.Namespace) -> int:
    from .commit import GitError, InputError
    from .traps import Skipped, harvest_traps

    skipped: list[Skipped] = []
    try:
        found = harvest_traps(args.repo, args.before, skipped)
    except (InputError, GitError, OSError) as exc:
        sys.stderr.write(f"traps: {exc}\n")
        return 2
    # stdout stays a plain list of traps, so a skipped file is said on stderr only.
    for item in skipped:
        sys.stderr.write(
            f"traps: skipped {item.path}: {item.size} bytes is over the {item.limit}-byte limit, "
            "not read\n"
        )
    emit([trap.to_dict() for trap in found], args.out)
    return 0


def _register_traps(sub: Any) -> None:
    p = sub.add_parser(
        "traps",
        help="list the Traps: labels in comments (those the branch added, or all of them)",
        description=(
            "List the Traps: labels in comments, as a JSON list of {path, line, text}. "
            "With --before, only the labels on lines added since that commit. "
            "Without --before, every Traps: comment in the tracked, non-exempt files of the work "
            "tree, the owner's included. "
            "A trap's text is cut at 2000 characters and ends in ' ...'. "
            "A file over the size limit is not read: its path and size are written to stderr, "
            "one line per file, and stdout stays the JSON list."
        ),
    )
    p.add_argument("--repo", type=_repo_arg, required=True, help="top level of the git work tree")
    p.add_argument(
        "--before",
        help="the commit the branch started from; an empty value is an error, not 'no base'",
    )
    p.add_argument("--out", type=Path, help="write the JSON list here instead of stdout")
    p.set_defaults(func=_cmd_traps)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="document_repo", description="Helpers for the document-repo skill."
    )
    parser.add_argument("--version", action="version", version=f"document_repo {__version__}")
    sub = parser.add_subparsers(dest="cmd", metavar="<command>")
    # SUBCOMMANDS — each later task adds one `_register_<name>(sub)` call here, in task order.
    _register_inventory(sub)
    _register_modules(sub)
    _register_verify(sub)
    _register_assemble(sub)
    _register_build(sub)
    _register_remap(sub)
    _register_upsert_section(sub)
    _register_changes(sub)
    _register_commit(sub)
    _register_backstop(sub)
    _register_explorer_status(sub)
    _register_keep_local(sub)
    _register_traps(sub)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help(sys.stderr)
        return 2
    return int(args.func(args))
