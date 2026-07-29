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

# Fields requested from `gh issue view` (re-used by `create_issue`/
# `update_issue`, which re-fetch through `_view` after writing so they can
# reuse the same normalizer). `list_issues` no longer uses `gh issue list
# --json` (4.6) -- it fetches the REST `/issues` endpoint directly, whose
# snake_case shape is routed through `_alias_rest_fields` before hitting the
# same `_normalize` both paths share.
_JSON_FIELDS = "number,title,body,state,updatedAt,closedAt,labels,milestone"

_ISSUE_URL_NUMBER_RE = re.compile(r"/issues/(\d+)\s*$")

# Still guards `ensure_labels`'s bounded `gh label list --limit` fetch (4.5);
# unchanged by 4.6.
_LABEL_LIST_LIMIT = 1000

# Guarded the old bounded `gh issue list --limit 1000` fetch (4.5). 4.6
# replaced that fetch with unbounded REST pagination (`list_issues` now
# walks every page via `gh api ... --paginate`), so the single-fetch-
# saturates-at-N truncation this constant detected can no longer happen
# there -- wiring it to the *paginated* total would be a regression (it
# would block a correctly-fetched >=1000-issue repo, which is exactly what
# unbounded pagination exists to support). Kept, not deleted, as
# `_raise_if_issue_fetch_saturated` below: see that method's docstring.
_ISSUE_LIST_LIMIT = 1000


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

    @staticmethod
    def _raise_if_issue_fetch_saturated(data: list[Any]) -> None:
        """4.5's saturation guard for a single bounded `gh issue list` fetch.

        No longer called by `list_issues` -- 4.6 replaced that call with
        unbounded REST pagination, which has no fixed cap to saturate.
        Retained (not deleted) per 4.6's instruction to keep 4.5's guards as
        a backstop, in case a single `--limit`-bounded fetch is ever
        reintroduced. Exercised directly by
        `test_raise_if_issue_fetch_saturated_still_raises` so it stays
        covered and mutation-testable even while unreachable from
        `list_issues`.
        """
        if len(data) >= _ISSUE_LIST_LIMIT:
            raise RuntimeError(
                f"GitHub issue list fetch returned exactly the limit ({_ISSUE_LIST_LIMIT}); "
                "the query may have more results that were not fetched. "
                "This repository needs pagination support (phase 4.6)."
            )

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
    def _alias_rest_fields(data: dict[str, Any]) -> dict[str, Any]:
        """Map REST `/issues` snake_case keys onto `_normalize`'s camelCase.

        `gh issue view --json` (and the old `gh issue list --json`) return
        `updatedAt`/`closedAt`. The REST `/repos/{repo}/issues` endpoint
        `list_issues` now paginates over returns `updated_at`/`closed_at`
        instead -- everything else `_normalize` reads (`number`, `title`,
        `body`, `state`, `labels[].name`, `milestone.title`) is spelled
        identically in both shapes. This is the one alias layer both shapes
        route through before `_normalize`; a second normalizer duplicating
        `_normalize`'s validation for the REST shape would be exactly the
        kind of two-sources-of-truth drift that produced #208/#212.
        """
        if "updatedAt" in data or "closedAt" in data:
            return data  # already gh-CLI-shaped (or already aliased)
        aliased = dict(data)
        aliased["updatedAt"] = data.get("updated_at")
        aliased["closedAt"] = data.get("closed_at")
        return aliased

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

    @staticmethod
    def _parse_paginated_json_arrays(text: str) -> list[Any]:
        """Flatten one or more top-level JSON array values from `gh api --paginate`.

        `--slurp` does not exist on the gh 2.45.0 baseline this tool
        targets, so a plain `json.loads` is not safe here in general: older
        gh behavior (and #212's actual failure mode) is to write each
        page's response to stdout back-to-back with no separator --
        `[...][...]` -- which `json.loads` rejects outright. Parse
        defensively with `raw_decode` instead, walking however many
        top-level JSON array values precede EOF. Verified 2026-07-29
        against the live API on this exact gh version: `gh api
        "repos/{repo}/issues?...&per_page=N" --paginate` actually returns
        pages *already merged* into one array (`json.loads` happens to
        succeed on it) -- but nothing in `gh api --help` guarantees that,
        so this still parses the harder, non-merged shape. The test suite's
        fixtures use two concatenated blobs with no separator specifically
        to prove that case, not the pre-merged one.
        """
        decoder = json.JSONDecoder()
        items: list[Any] = []
        pos = 0
        length = len(text)
        while pos < length:
            while pos < length and text[pos].isspace():
                pos += 1
            if pos >= length:
                break
            value, end = decoder.raw_decode(text, pos)
            if not isinstance(value, list):
                raise ValueError(
                    "expected a JSON array from paginated `gh api` output, "
                    f"got {type(value).__name__} at offset {pos}"
                )
            items.extend(value)
            pos = end
        return items

    # -- Provider interface --------------------------------------------

    def list_issues(self, state: str = "all") -> list[Issue]:
        # REST `/issues` (unlike `gh issue list`) has no `--limit`-style
        # cap to saturate -- `--paginate` walks every page via the
        # response's `Link` header until there isn't a next one. It also
        # includes pull requests, which must never be adopted as tasks
        # (they carry a `pull_request` key issues never do), and returns
        # snake_case timestamp keys that `_alias_rest_fields` maps onto the
        # camelCase `_normalize` expects -- one alias layer, not a second
        # normalizer.
        output = self._run(
            [
                "api",
                f"repos/{self._repo}/issues?state={state}&per_page=100",
                "--paginate",
            ]
        )
        items = self._parse_paginated_json_arrays(output)
        return [
            self._normalize(self._alias_rest_fields(item))
            for item in items
            if "pull_request" not in item
        ]

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
