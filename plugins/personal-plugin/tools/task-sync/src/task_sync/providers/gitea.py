"""Gitea `Provider` adapter, implemented over the REST API via stdlib `urllib`.

This exists (rather than shelling out to the `tea` CLI, mirroring the GitHub
adapter's use of `gh`) because `tea`'s JSON output omits `updated_at` and
`body` — fields the reconcile engine (Phase 3) needs for 3-way sync. The
REST API returns both, so this module talks to it directly.

Deliberately stdlib-only: `urllib.request` for HTTP, and a narrow hand-rolled
parser for the one shape of YAML `tea login` writes (a top-level `logins:`
list of flat string-keyed mappings) — not a general YAML parser, and no
`pyyaml` dependency. Never makes a live network call in tests; every test
mocks `urllib.request.urlopen` with recorded responses.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from task_sync.providers.base import VALID_ISSUE_STATES, Issue, parse_aware_datetime

_DEFAULT_TEA_CONFIG_PATH = Path.home() / ".config" / "tea" / "config.yml"
_PAGE_SIZE = 50


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _parse_tea_logins(path: Path) -> list[dict[str, str]]:
    """Parse the `logins:` list out of a `tea` `config.yml`.

    Handles exactly the structure `tea login add` produces: a top-level
    `logins:` key holding a YAML list of flat string-keyed mappings, e.g.::

        logins:
        - name: mygitea
          url: https://git.example.com
          token: abc123
          default: true

    Anything outside that shape (nested structures, multi-line scalars) is
    out of scope — this is intentionally not a general YAML parser.
    """
    logins: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_logins = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        if raw_line.startswith("logins:"):
            in_logins = True
            continue

        if not in_logins:
            continue

        if not raw_line.startswith((" ", "-")):
            # Dedented back to a new top-level key: the logins block ended.
            break

        stripped = raw_line.strip()
        if stripped.startswith("- "):
            if current is not None:
                logins.append(current)
            current = {}
            stripped = stripped[2:]

        if current is None:
            continue

        if ":" in stripped:
            key, _, value = stripped.partition(":")
            current[key.strip()] = _unquote(value)

    if current is not None:
        logins.append(current)

    return logins


def load_gitea_credentials(config_path: Path | None = None) -> tuple[str, str]:
    """Return `(base_url, token)` from the `tea` config, or raise a clear error.

    Raises:
        RuntimeError: if the config file, its `logins:` list, or the
            selected login's `url`/`token` are missing — always pointing
            at `tea login add` as the fix.
    """
    path = config_path or _DEFAULT_TEA_CONFIG_PATH

    if not path.exists():
        raise RuntimeError(
            f"no Gitea credentials found at {path}; run `tea login add` to "
            "configure a server URL and token first"
        )

    logins = _parse_tea_logins(path)
    if not logins:
        raise RuntimeError(
            f"{path} has no `logins:` entries; run `tea login add` to "
            "configure a server URL and token first"
        )

    login = next((entry for entry in logins if entry.get("default") == "true"), logins[0])
    base_url = login.get("url")
    token = login.get("token")

    if not base_url or not token:
        raise RuntimeError(
            f"{path} is missing a url/token for its Gitea login; run `tea login add` to reconfigure"
        )

    return base_url.rstrip("/"), token


class GiteaProvider:
    """Implements `task_sync.providers.base.Provider` over the Gitea REST API.

    `repo` is an `owner/repo` slug (the same shape `detect.detect_provider`
    returns); `base_url` and `token` come from `load_gitea_credentials` (or
    are passed explicitly for testing).
    """

    def __init__(self, repo: str, base_url: str, token: str) -> None:
        owner, _, name = repo.partition("/")
        if not owner or not name:
            raise ValueError(f"'repo' must be 'owner/repo', got {repo!r}")
        self._owner = owner
        self._name = name
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._label_cache: dict[str, int] = {}
        self._milestone_cache: dict[str, int] = {}

    @classmethod
    def from_tea_config(cls, repo: str, config_path: Path | None = None) -> "GiteaProvider":
        """Build a `GiteaProvider` from `~/.config/tea/config.yml` (or `config_path`)."""
        base_url, token = load_gitea_credentials(config_path)
        return cls(repo, base_url, token)

    # -- low-level HTTP ---------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
    ) -> Any:
        url = f"{self._base_url}/api/v1{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Authorization", f"token {self._token}")
        request.add_header("Accept", "application/json")
        if data is not None:
            request.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gitea API error {exc.code} for {method} {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Gitea API request failed for {method} {path}: {exc.reason}"
            ) from exc

        if not raw:
            return None
        return json.loads(raw)

    def _repo_path(self, suffix: str = "") -> str:
        return f"/repos/{self._owner}/{self._name}{suffix}"

    # -- normalization ------------------------------------------------

    @staticmethod
    def _normalize(data: dict[str, Any]) -> Issue:
        labels = [label["name"] for label in data.get("labels") or []]
        milestone = data.get("milestone")
        milestone_title = milestone["title"] if milestone else None

        updated_at = parse_aware_datetime(data.get("updated_at"))
        if updated_at is None:
            raise ValueError(f"Gitea issue #{data.get('number')} is missing updated_at")

        return Issue(
            number=data["number"],
            title=data["title"],
            body=data.get("body") or "",
            state=str(data["state"]).lower(),
            labels=labels,
            milestone=milestone_title,
            updated_at=updated_at,
            closed_at=parse_aware_datetime(data.get("closed_at")),
        )

    # -- label/milestone name<->id resolution ------------------------

    def _fetch_labels(self) -> dict[str, int]:
        data = self._request("GET", self._repo_path("/labels"), params={"limit": _PAGE_SIZE})
        mapping = {item["name"]: item["id"] for item in data or []}
        self._label_cache.update(mapping)
        return mapping

    def _fetch_milestones(self) -> dict[str, int]:
        data = self._request(
            "GET", self._repo_path("/milestones"), params={"state": "all", "limit": _PAGE_SIZE}
        )
        mapping = {item["title"]: item["id"] for item in data or []}
        self._milestone_cache.update(mapping)
        return mapping

    # -- Provider interface --------------------------------------------

    def list_issues(self, state: str = "all") -> list[Issue]:
        issues: list[Issue] = []
        page = 1
        while True:
            data = self._request(
                "GET",
                self._repo_path("/issues"),
                params={"state": state, "type": "issues", "limit": _PAGE_SIZE, "page": page},
            )
            if not data:
                break
            issues.extend(self._normalize(item) for item in data)
            if len(data) < _PAGE_SIZE:
                break
            page += 1
        return issues

    def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
        milestone: str | None = None,
    ) -> Issue:
        labels = list(labels or [])
        payload: dict[str, Any] = {"title": title, "body": body}

        if labels:
            self.ensure_labels(labels)
            payload["labels"] = [self._label_cache[name] for name in labels]

        if milestone:
            self.ensure_milestone(milestone)
            payload["milestone"] = self._milestone_cache[milestone]

        data = self._request("POST", self._repo_path("/issues"), json_body=payload)
        return self._normalize(data)

    def update_issue(self, number: int, **fields: Any) -> Issue:
        payload: dict[str, Any] = {}

        if "title" in fields:
            payload["title"] = fields["title"]

        if "body" in fields:
            payload["body"] = fields["body"]

        if "state" in fields:
            payload["state"] = fields["state"]

        if "labels" in fields:
            names = list(fields["labels"] or [])
            self.ensure_labels(names)
            payload["labels"] = [self._label_cache[name] for name in names]

        if "milestone" in fields:
            milestone = fields["milestone"]
            if milestone is None:
                payload["milestone"] = 0
            else:
                self.ensure_milestone(milestone)
                payload["milestone"] = self._milestone_cache[milestone]

        data = self._request("PATCH", self._repo_path(f"/issues/{number}"), json_body=payload)
        return self._normalize(data)

    def set_state(self, number: int, state: str) -> None:
        if state not in VALID_ISSUE_STATES:
            raise ValueError(f"invalid state {state!r}; must be one of {VALID_ISSUE_STATES}")
        self._request("PATCH", self._repo_path(f"/issues/{number}"), json_body={"state": state})

    def ensure_labels(self, names: list[str]) -> None:
        if not names:
            return
        existing = self._fetch_labels()
        for name in names:
            if name not in existing:
                created = self._request(
                    "POST",
                    self._repo_path("/labels"),
                    json_body={"name": name, "color": "#ededed"},
                )
                existing[name] = created["id"]
                self._label_cache[name] = created["id"]

    def ensure_milestone(self, name: str) -> None:
        existing = self._fetch_milestones()
        if name not in existing:
            created = self._request(
                "POST", self._repo_path("/milestones"), json_body={"title": name}
            )
            existing[name] = created["id"]
            self._milestone_cache[name] = created["id"]

    def visibility(self) -> str:
        data = self._request("GET", self._repo_path())
        return "private" if data.get("private") else "public"
