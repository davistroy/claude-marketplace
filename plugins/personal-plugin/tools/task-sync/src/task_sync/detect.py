"""Detect which tracker a repo's `origin` remote points at.

Only two backends are supported (`github.py`, `gitea.py`), so the heuristic
is deliberately simple: `github.com` maps to `'github'`, and *any other*
parseable remote host is treated as a self-hosted Gitea instance (Gitea
hostnames are arbitrary — there's no fixed domain to match on). No remote,
an unparseable URL, or no git repo at all all resolve to `('none', None)`
(local-only mode).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# `git@host:owner/repo.git` (the "scp-like" SSH syntax).
_SSH_RE = re.compile(r"^git@(?P<host>[^:/]+):(?P<path>.+?)(?:\.git)?/?$")

# `ssh://git@host[:port]/owner/repo.git`, `https://[user@]host[:port]/owner/repo.git`,
# and the unauthenticated `http://` variant.
_URL_RE = re.compile(r"^(?:ssh|https?)://(?:[^@/]+@)?(?P<host>[^/]+)/(?P<path>.+?)(?:\.git)?/?$")


def _parse_remote(url: str) -> tuple[str, str] | None:
    url = url.strip()
    match = _SSH_RE.match(url) or _URL_RE.match(url)
    if match is None:
        return None
    host = match.group("host")
    path = match.group("path").strip("/")
    if not host or not path:
        return None
    return host, path


def detect_provider(repo_root: str | Path) -> tuple[str, str | None]:
    """Return `(provider, repo)` for the `origin` remote at `repo_root`.

    `provider` is one of `'github'`, `'gitea'`, `'none'`. `repo` is the
    `owner/repo`-shaped path from the remote URL, or `None` when `provider`
    is `'none'`.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ("none", None)

    if result.returncode != 0 or not result.stdout.strip():
        return ("none", None)

    parsed = _parse_remote(result.stdout)
    if parsed is None:
        return ("none", None)

    host, repo_path = parsed
    # Strip a trailing :port so "gitea.example.com:3000" and
    # "gitea.example.com" are recognized consistently; github.com is never
    # served on a nonstandard port so this only affects the gitea branch.
    bare_host = host.rsplit(":", 1)[0] if not host.startswith("[") else host

    if bare_host == "github.com":
        return ("github", repo_path)

    return ("gitea", repo_path)
