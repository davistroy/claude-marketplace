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
    """Write ``obj`` as pretty JSON to ``out``, or to stdout when ``out`` is None."""
    text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    if out is None:
        # Write UTF-8 bytes directly: a Windows console may use a legacy code page that cannot
        # encode the text.
        buffer = getattr(sys.stdout, "buffer", None)
        if buffer is not None:
            # Flush text already buffered on the text layer so output stays in order.
            sys.stdout.flush()
            buffer.write(text.encode("utf-8"))
            buffer.flush()
        else:
            sys.stdout.write(text)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


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
    from .verify import changed_files, verify_file

    if args.changed:
        try:
            files = changed_files(args.repo, args.before)
        except NotADirectoryError as exc:
            sys.stderr.write(f"verify: {exc}\n")
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help(sys.stderr)
        return 2
    return int(args.func(args))
