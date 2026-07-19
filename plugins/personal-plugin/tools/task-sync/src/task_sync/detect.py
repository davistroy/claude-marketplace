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

# Same shape as `_URL_RE` restricted to http(s) (never ssh), with the scheme
# captured — used by `detect_gitea_base_url` to derive an API base. ssh
# origins are excluded on purpose: there is no reliable way to infer the
# http(s) scheme/port a Gitea instance's API listens on from its ssh
# endpoint.
_HTTP_URL_RE = re.compile(
    r"^(?P<scheme>https?)://(?:[^@/]+@)?(?P<host>[^/]+)/(?P<path>.+?)(?:\.git)?/?$"
)


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


def _get_origin_url(repo_root: str | Path) -> str | None:
    """Return the raw, stripped `origin` remote URL at `repo_root`, or `None`.

    `None` covers every reason there is nothing to parse: `git` is not
    installed, there is no `origin` remote, or the command otherwise failed.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None

    return result.stdout.strip()


def detect_provider(repo_root: str | Path) -> tuple[str, str | None]:
    """Return `(provider, repo)` for the `origin` remote at `repo_root`.

    `provider` is one of `'github'`, `'gitea'`, `'none'`. `repo` is the
    `owner/repo`-shaped path from the remote URL, or `None` when `provider`
    is `'none'`.
    """
    url = _get_origin_url(repo_root)
    if url is None:
        return ("none", None)

    parsed = _parse_remote(url)
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


def detect_gitea_base_url(repo_root: str | Path) -> str:
    """Derive a Gitea API base URL (`scheme://host[:port]`, no path/user).

    Only trusts http(s) `origin` remotes — an ssh remote (`git@host:owner/
    repo.git` or `ssh://...`) cannot reliably yield an http(s) API base
    (the scheme and port are ambiguous), so this returns `""` for those and
    for anything else that isn't a parseable http(s) URL (no remote, an
    unparseable URL, etc.). Callers should treat `""` as "unknown" and fall
    back to `$GITEA_URL` or the `tea` config (see `providers/gitea.py`).
    """
    url = _get_origin_url(repo_root)
    if url is None:
        return ""

    match = _HTTP_URL_RE.match(url)
    if match is None:
        return ""

    return f"{match.group('scheme')}://{match.group('host')}"
