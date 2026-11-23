"""Command-line front end for the document-repo tool.

Each subcommand is a thin wrapper: parse arguments, call one library
function, print JSON. Exit codes: 0 success, 1 a check failed (for example a
file changed in more than its comments), 2 bad input.
"""

from __future__ import annotations

import argparse
import json
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
    from .build import install_template, read_json, write_explorer_data
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
        upsert_file(args.file, args.section, body)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"upsert-section: {exc}\n")
        return 2
    return 0


def _register_upsert_section(sub: Any) -> None:
    p = sub.add_parser("upsert-section", help="write a generated section between markers")
    p.add_argument("--file", type=Path, required=True)
    p.add_argument("--section", required=True)
    p.add_argument("--content-file", type=Path, required=True)
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help(sys.stderr)
        return 2
    return int(args.func(args))
