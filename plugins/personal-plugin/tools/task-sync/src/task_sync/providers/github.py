"""GitHub `Provider` adapter, implemented over the `gh` CLI via `subprocess`.

Never makes a live network call in tests — every test mocks `subprocess.run`
with recorded `gh` JSON output. `gh` is treated as the source of truth for
auth/repo context; this module only builds argv lists and parses stdout.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any

from task_sync.providers.base import Issue, parse_aware_datetime

# Fields requested from `gh issue list`/`gh issue view`. Keep the two calls
# symmetric so `create_issue`/`update_issue` can reuse the same normalizer
# after re-fetching the issue.
_JSON_FIELDS = "number,title,body,state,updatedAt,closedAt,labels,milestone"

_ISSUE_URL_NUMBER_RE = re.compile(r"/issues/(\d+)\s*$")

# Fetch limits for pagination detection
_ISSUE_LIST_LIMIT = 1000
_LABEL_LIST_LIMIT = 1000


class GithubProvider:
    """Implements `task_sync.providers.base.Provider` over the `gh` CLI.

    `repo` is the `owner/repo` slug passed to every `gh ... --repo` call
    (the same shape `detect.detect_provider` returns).
    """

    def __init__(self, repo: str) -> None:
        self._repo = repo

    # -- low-level gh invocation -----------------------------------------

    def _run(self, args: list[str]) -> str:
        try:
            result = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
        except FileNotFoundError as exc:
            raise RuntimeError(
                "the 'gh' CLI was not found on PATH; install and authenticate "
                "GitHub CLI (https://cli.github.com) first"
            ) from exc

        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"gh {' '.join(args)} failed: {detail}")

        return result.stdout

    def _run_json(self, args: list[str]) -> Any:
        return json.loads(self._run(args))

    def _view(self, number: int) -> dict[str, Any]:
        data = self._run_json(
            [
                "issue",
                "view",
                str(number),
                "--repo",
                self._repo,
                "--json",
                _JSON_FIELDS,
            ]
        )
        assert isinstance(data, dict)
        return data

    # -- normalization ------------------------------------------------

    @staticmethod
    def _normalize(data: dict[str, Any]) -> Issue:
        labels = [label["name"] for label in data.get("labels") or []]
        milestone = data.get("milestone")
        milestone_title = milestone["title"] if milestone else None

        updated_at = parse_aware_datetime(data.get("updatedAt"))
        if updated_at is None:
            raise ValueError(f"gh issue #{data.get('number')} is missing updatedAt")

        return Issue(
            number=data["number"],
            title=data["title"],
            body=data.get("body") or "",
            state=str(data["state"]).lower(),
            labels=labels,
            milestone=milestone_title,
            updated_at=updated_at,
            closed_at=parse_aware_datetime(data.get("closedAt")),
        )

    # -- Provider interface --------------------------------------------

    def list_issues(self, state: str = "all") -> list[Issue]:
        data = self._run_json(
            [
                "issue",
                "list",
                "--repo",
                self._repo,
                "--state",
                state,
                "--json",
                _JSON_FIELDS,
                "--limit",
                str(_ISSUE_LIST_LIMIT),
            ]
        )
        assert isinstance(data, list)
        if len(data) >= _ISSUE_LIST_LIMIT:
            raise RuntimeError(
                f"GitHub issue list fetch returned exactly the limit ({_ISSUE_LIST_LIMIT}); "
                "the query may have more results that were not fetched. "
                "This repository needs pagination support (phase 4.6)."
            )
        return [self._normalize(item) for item in data]

    def create_issue(
        self,
        title: str,
        body: str,
        labels: list[str] | None = None,
        milestone: str | None = None,
    ) -> Issue:
        labels = list(labels or [])
        args = ["issue", "create", "--repo", self._repo, "--title", title, "--body", body]

        if labels:
            self.ensure_labels(labels)
            for name in labels:
                args += ["--label", name]

        if milestone:
            self.ensure_milestone(milestone)
            args += ["--milestone", milestone]

        output = self._run(args)
        match = _ISSUE_URL_NUMBER_RE.search(output.strip())
        if match is None:
            raise RuntimeError(
                f"could not parse issue number from `gh issue create` output: {output!r}"
            )

        return self._normalize(self._view(int(match.group(1))))

    def update_issue(self, number: int, **fields: Any) -> Issue:
        args = ["issue", "edit", str(number), "--repo", self._repo]
        changed = False

        if "title" in fields:
            args += ["--title", fields["title"]]
            changed = True

        if "body" in fields:
            args += ["--body", fields["body"]]
            changed = True

        if "labels" in fields:
            desired = set(fields["labels"] or [])
            self.ensure_labels(list(desired))
            current = {label["name"] for label in self._view(number).get("labels") or []}
            for name in sorted(desired - current):
                args += ["--add-label", name]
                changed = True
            for name in sorted(current - desired):
                args += ["--remove-label", name]
                changed = True

        # `gh issue edit` has --remove-assignee/-label/-project but NO
        # --remove-milestone (#212). Clearing therefore goes through the REST
        # API, and only when there is genuinely something to clear: the caller
        # always supplies `milestone`, so a task without one used to ask gh to
        # unset a milestone that was never set — aborting the entire edit.
        clear_milestone = False
        if "milestone" in fields:
            milestone = fields["milestone"]
            if milestone is None:
                clear_milestone = bool(self._view(number).get("milestone"))
            else:
                self.ensure_milestone(milestone)
                args += ["--milestone", milestone]
                changed = True

        if "state" in fields:
            self.set_state(number, fields["state"])

        if changed:
            self._run(args)

        if clear_milestone:
            # `-F` sends a typed JSON null (which clears it); `-f` would send
            # the *string* "null" and set a bogus milestone name instead.
            self._run(
                [
                    "api",
                    f"repos/{self._repo}/issues/{number}",
                    "-X",
                    "PATCH",
                    "-F",
                    "milestone=null",
                ]
            )

        return self._normalize(self._view(number))

    def set_state(self, number: int, state: str) -> None:
        if state == "open":
            self._run(["issue", "reopen", str(number), "--repo", self._repo])
        elif state == "closed":
            self._run(["issue", "close", str(number), "--repo", self._repo])
        else:
            raise ValueError(f"invalid state {state!r}; must be 'open' or 'closed'")

    def ensure_labels(self, names: list[str]) -> None:
        if not names:
            return
        labels_data = self._run_json(
            [
                "label",
                "list",
                "--repo",
                self._repo,
                "--json",
                "name",
                "--limit",
                str(_LABEL_LIST_LIMIT),
            ]
        )
        assert isinstance(labels_data, list)
        if len(labels_data) >= _LABEL_LIST_LIMIT:
            raise RuntimeError(
                f"GitHub label list fetch returned exactly the limit ({_LABEL_LIST_LIMIT}); "
                "the query may have more results that were not fetched. "
                "This repository needs pagination support (phase 4.6)."
            )
        existing = {label["name"] for label in labels_data}
        for name in names:
            if name not in existing:
                self._run(["label", "create", name, "--repo", self._repo, "--color", "ededed"])

    def ensure_milestone(self, name: str) -> None:
        existing = {
            item["title"] for item in self._run_json(["api", f"repos/{self._repo}/milestones"])
        }
        if name not in existing:
            self._run(["api", f"repos/{self._repo}/milestones", "-f", f"title={name}"])

    def visibility(self) -> str:
        data = self._run_json(["repo", "view", self._repo, "--json", "visibility"])
        return "public" if str(data.get("visibility", "")).upper() == "PUBLIC" else "private"
