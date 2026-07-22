"""Plan/apply split: `--plan`/`--dry-run` write nothing; `--apply` executes.

The centerpiece is `test_dry_run_writes_nothing`, which asserts that after a
`sync --dry-run` the tasks.json bytes are unchanged AND the git working tree
is clean — the reconcile engine's core safety property. Every provider
interaction goes through the in-memory `MockProvider`; nothing touches a
live `gh`/Gitea backend.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from conftest import MockProvider
from task_sync import store
from task_sync.__main__ import (
    _apply_summary,
    _build_provider,
    _load_decisions,
    _scan_confidentiality,
    build_parser,
    main,
    run_sync,
)
from task_sync.models import Task, TaskList
from task_sync.providers.base import Issue, Provider, parse_aware_datetime
from task_sync.reconcile.apply import apply
from task_sync.reconcile.classify import classify, content_hash
from task_sync.reconcile.plan import SyncPlan, build_plan, summarize_plan

BASE_AT = "2026-07-10T00:00:00Z"
LATER = "2026-07-15T00:00:00Z"
NOW = "2026-07-20T00:00:00Z"


def _issue(number: int = 1, *, title: str = "T", updated: str = BASE_AT, **kw: object) -> Issue:
    base: dict[str, object] = {
        "number": number,
        "title": title,
        "body": "b",
        "state": "open",
        "labels": [],
        "milestone": None,
        "updated_at": parse_aware_datetime(updated),
        "closed_at": None,
    }
    base.update(kw)
    return Issue(**base)  # type: ignore[arg-type]


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def _git_status(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        capture_output=True,
        text=True,
    ).stdout


def _committed_repo(root: Path, tasklist: TaskList) -> Path:
    _git(root, "init")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "Test")
    tasks_path = root / "tasks.json"
    store.save(tasklist, tasks_path)
    _git(root, "add", "tasks.json")
    _git(root, "commit", "-m", "init")
    return tasks_path


def _parse(tasks_path: Path, root: Path, *flags: str) -> object:
    return build_parser().parse_args(
        ["sync", *flags, "--tasks", str(tasks_path), "--repo-root", str(root)]
    )


def _by_id(tasklist: TaskList, task_id: str) -> Task:
    return next(t for t in tasklist.tasks if t.id == task_id)


# -- MockProvider is a real Provider ---------------------------------------


def test_mock_provider_satisfies_protocol() -> None:
    assert isinstance(MockProvider(), Provider)


# -- --dry-run / --plan write nothing --------------------------------------


def test_dry_run_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    tl = TaskList(
        provider="github",
        repo="o/r",
        tasks=[Task(id="t-1", title="local task", issue_number=None)],
    )
    tasks_path = _committed_repo(tmp_path, tl)
    before = tasks_path.read_bytes()

    # A NEW_REMOTE issue guarantees a non-empty plan, so "nothing written"
    # is a real assertion, not vacuously true on an empty plan.
    provider = MockProvider(issues=[_issue(number=9)])
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--dry-run"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    assert tasks_path.read_bytes() == before  # byte-identical
    assert _git_status(tmp_path) == ""  # git tree clean
    # not a single mutating provider call happened
    assert provider.method_calls("create_issue") == []
    assert provider.method_calls("update_issue") == []
    assert provider.method_calls("set_state") == []
    out = capsys.readouterr().out
    assert "dry run" in out.lower()


def test_plan_json_writes_nothing_and_emits_valid_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    tl = TaskList(
        provider="github",
        repo="o/r",
        tasks=[Task(id="t-1", title="local task", issue_number=None)],
    )
    tasks_path = _committed_repo(tmp_path, tl)
    before = tasks_path.read_bytes()

    provider = MockProvider(issues=[_issue(number=9)])
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--plan", "--json"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    assert tasks_path.read_bytes() == before
    assert _git_status(tmp_path) == ""
    payload = json.loads(capsys.readouterr().out)
    # `skipped_adopts` is part of the documented --plan --json shape: without
    # it a consumer cannot tell "nothing to pull" from "N issues were left
    # unadopted by the window".
    assert set(payload) == {
        "creates",
        "pushes",
        "pulls",
        "conflicts",
        "skipped_adopts",
        "confidentiality_findings",
    }
    assert len(payload["creates"]) == 1  # the local task
    assert len(payload["pulls"]) == 1  # the NEW_REMOTE issue
    assert payload["skipped_adopts"] == []  # the issue is open -> adopted
    assert payload["confidentiality_findings"] == []


# -- --adopt-all vs. the default adopt window (issue #167) ------------------


SKIPPED_LINE = "skipped (closed outside adopt window): 1 — use --adopt-all to mirror them"


def test_plan_long_closed_new_remote_issue_is_not_adopted_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A NEW_REMOTE issue past the adopt window is skipped, not adopted-then-pruned.

    And the skip is *reported*: a silent `continue` let the plan print
    "already in sync — nothing to do" while the issue sat unmirrored.
    """
    tl = TaskList(provider="github", repo="o/r", tasks=[])
    tasks_path = _committed_repo(tmp_path, tl)

    long_closed = datetime.now(timezone.utc) - timedelta(days=400)
    issue = _issue(number=9, state="closed", closed_at=long_closed)
    provider = MockProvider(issues=[issue])
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--plan"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    out = capsys.readouterr().out
    assert "pull   (remote -> local): 0" in out
    assert SKIPPED_LINE in out
    assert "already in sync" not in out


def test_plan_recently_closed_new_remote_issue_is_not_adopted_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The adopt window's own default is 0 (open issues only) — unlike the old
    30-day prune-window-sourced default, even a 3-day-old close is skipped."""
    tl = TaskList(provider="github", repo="o/r", tasks=[])
    tasks_path = _committed_repo(tmp_path, tl)

    recently_closed = datetime.now(timezone.utc) - timedelta(days=3)
    issue = _issue(number=9, state="closed", closed_at=recently_closed)
    provider = MockProvider(issues=[issue])
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--plan"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    out = capsys.readouterr().out
    assert "pull   (remote -> local): 0" in out
    assert SKIPPED_LINE in out
    assert "already in sync" not in out


def test_plan_json_reports_skipped_adopt_issue_numbers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The machine-readable plan names the skipped issues, not just a count."""
    tl = TaskList(provider="github", repo="o/r", tasks=[])
    tasks_path = _committed_repo(tmp_path, tl)

    closed = datetime.now(timezone.utc) - timedelta(days=3)
    provider = MockProvider(
        issues=[
            _issue(number=9, state="closed", closed_at=closed),
            _issue(number=11, state="closed", closed_at=closed),
        ]
    )
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--plan", "--json"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pulls"] == []
    assert payload["skipped_adopts"] == [9, 11]


def test_plan_adopt_all_flag_adopts_a_long_closed_issue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--adopt-all` is the full-mirror escape hatch: it ignores the window entirely."""
    tl = TaskList(provider="github", repo="o/r", tasks=[])
    tasks_path = _committed_repo(tmp_path, tl)

    long_closed = datetime.now(timezone.utc) - timedelta(days=400)
    issue = _issue(number=9, state="closed", closed_at=long_closed)
    provider = MockProvider(issues=[issue])
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--plan", "--adopt-all"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    out = capsys.readouterr().out
    assert "pull   (remote -> local): 1" in out
    assert "skipped (closed outside adopt window)" not in out


def test_apply_adopt_all_mirrors_a_closed_issue_into_tasks_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`sync --apply --adopt-all` — the documented mutating combination.

    The issue is closed 3 days ago: outside the default adopt window (0, open
    issues only) but well inside the 30-day prune window, so `--adopt-all`
    must both adopt it AND leave it in the store rather than adopting-then-
    pruning it in the same run.
    """
    tl = TaskList(provider="github", repo="o/r", tasks=[])
    tasks_path = _committed_repo(tmp_path, tl)

    closed = datetime.now(timezone.utc) - timedelta(days=3)
    issue = _issue(number=9, title="closed issue", state="closed", closed_at=closed)
    provider = MockProvider(issues=[issue], now=NOW)
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--apply", "--adopt-all"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    saved = store.load(tasks_path)
    assert [t.issue_number for t in saved.tasks] == [9]
    assert saved.tasks[0].title == "closed issue"
    assert saved.tasks[0].status == "done"
    # A pull is purely local: no issue was created or mutated on the tracker.
    assert provider.method_calls("create_issue") == []
    assert provider.method_calls("update_issue") == []
    assert "1 pull(s)" in capsys.readouterr().out


def test_apply_without_adopt_all_leaves_a_closed_issue_unadopted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The counterpart: the same `--apply` run without `--adopt-all` adopts nothing."""
    tl = TaskList(provider="github", repo="o/r", tasks=[])
    tasks_path = _committed_repo(tmp_path, tl)

    closed = datetime.now(timezone.utc) - timedelta(days=3)
    issue = _issue(number=9, title="closed issue", state="closed", closed_at=closed)
    provider = MockProvider(issues=[issue], now=NOW)
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--apply"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    assert store.load(tasks_path).tasks == []
    out = capsys.readouterr().out
    assert "0 pull(s)" in out
    # ...and --apply says WHY it pulled nothing, rather than reporting a bare 0.
    assert "1 issue(s) closed outside the adopt window were not adopted" in out
    assert "--adopt-all" in out


# -- confidentiality scan is wired into --plan/--dry-run --------------------


def test_plan_populates_confidentiality_findings_for_secret_bearing_create(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A create/push whose body carries a live-looking secret is flagged in the plan."""
    ghp_token = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
    tl = TaskList(
        provider="github",
        repo="o/r",
        tasks=[
            Task(
                id="t-secret",
                title="local task",
                body=f"connect using token {ghp_token}",
                issue_number=None,
            )
        ],
    )
    tasks_path = _committed_repo(tmp_path, tl)
    before = tasks_path.read_bytes()

    provider = MockProvider(issues=[])
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--plan", "--json"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    # Provably side-effect-free even though findings were produced.
    assert tasks_path.read_bytes() == before
    assert _git_status(tmp_path) == ""

    payload = json.loads(capsys.readouterr().out)
    findings = payload["confidentiality_findings"]
    assert len(findings) == 1
    assert findings[0]["task_id"] == "t-secret"
    categories = {f["category"] for f in findings[0]["findings"]}
    assert "secret.github" in categories


def test_dry_run_with_secret_still_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--dry-run` surfaces the same findings but remains provably write-nothing."""
    ghp_token = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
    tl = TaskList(
        provider="github",
        repo="o/r",
        tasks=[
            Task(
                id="t-secret",
                title="local task",
                body=f"connect using token {ghp_token}",
                issue_number=None,
            )
        ],
    )
    tasks_path = _committed_repo(tmp_path, tl)
    before = tasks_path.read_bytes()

    provider = MockProvider(issues=[])
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--dry-run"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    assert tasks_path.read_bytes() == before
    assert _git_status(tmp_path) == ""
    assert provider.method_calls("create_issue") == []
    assert provider.method_calls("update_issue") == []
    out = capsys.readouterr().out
    assert "confidentiality findings:  1" in out


def test_plan_flags_sensitive_term_on_push() -> None:
    """A push whose body contains a configured sensitive term is flagged."""
    task = Task(id="t-push", title="push me", body="the Zephyrix rollout continues", status="todo")
    task.last_synced = {"hash": "stale-hash", "at": BASE_AT}  # local diverged from base
    task.issue_number = 5
    tl = TaskList(
        provider="github",
        repo="o/r",
        config={"sensitive_terms": ["Zephyrix"]},
        tasks=[task],
    )
    issue = _issue(number=5, updated=BASE_AT)  # remote unchanged -> CHANGED_LOCAL -> push
    plan = build_plan(classify(tl, [issue]))
    assert len(plan.pushes) == 1

    findings = _scan_confidentiality(plan, tl)
    assert len(findings) == 1
    assert findings[0]["task_id"] == "t-push"
    assert findings[0]["findings"][0]["category"] == "sensitive-term"


def test_clean_outbound_task_yields_no_confidentiality_findings() -> None:
    """A create with no secrets/terms produces zero findings."""
    tl = TaskList(tasks=[Task(id="t-1", title="tidy task", body="nothing sensitive here")])
    plan = build_plan(classify(tl, []))
    assert len(plan.creates) == 1
    assert _scan_confidentiality(plan, tl) == []


def test_already_reviewed_unchanged_task_is_not_reflagged() -> None:
    """A task whose confidentiality review still covers its content is skipped."""
    from task_sync.confidential.apply import apply_review
    from task_sync.confidential.scan import scan_task as _scan

    task = Task(id="t-1", title="task", body="the Zephyrix rollout continues")
    findings = _scan(task, ["Zephyrix"])
    assert findings  # sanity: the term is actually detected pre-review
    apply_review(task, findings, "keep", at=BASE_AT)  # stamps confidentiality.reviewed_hash

    tl = TaskList(config={"sensitive_terms": ["Zephyrix"]}, tasks=[task])
    plan = build_plan(classify(tl, []))
    assert len(plan.creates) == 1  # still a NEW_LOCAL create

    assert _scan_confidentiality(plan, tl) == []


# -- build_plan is pure -----------------------------------------------------


def test_build_plan_calls_no_provider_and_returns_shape() -> None:
    tl = TaskList(tasks=[Task(id="t-1", title="x", issue_number=None)])
    provider = MockProvider(issues=[_issue(number=3)])
    plan = build_plan(classify(tl, provider.list_issues()))
    # list_issues is the only call so far; build_plan itself calls nothing.
    provider.calls.clear()
    _ = build_plan(classify(tl, [_issue(number=3)]))
    assert provider.calls == []
    assert not plan.is_empty()


# -- --apply executes exactly the planned actions --------------------------


def test_apply_executes_exactly_the_planned_actions() -> None:
    t_create = Task(id="t-create", title="brand new", issue_number=None)
    t_push = Task(id="t-push", title="push me", status="todo", issue_number=2)
    t_push.last_synced = {"hash": "stale-hash", "at": BASE_AT}  # local diverged

    tl = TaskList(provider="github", repo="o/r", tasks=[t_create, t_push])
    issue2 = _issue(number=2, updated=BASE_AT)  # matches t_push, remote unchanged
    issue3 = _issue(number=3, title="adopt me", updated=BASE_AT)  # NEW_REMOTE
    provider = MockProvider(issues=[issue2, issue3], now=NOW)

    plan = build_plan(classify(tl, [issue2, issue3]))
    assert len(plan.creates) == 1 and len(plan.pushes) == 1 and len(plan.pulls) == 1

    updated = apply(plan, {}, tl, provider, now=parse_aware_datetime(NOW))

    # Exactly one create + one push hit the provider — no extras, no pulls-as-calls.
    assert len(provider.method_calls("create_issue")) == 1
    assert len(provider.method_calls("update_issue")) == 1

    created = _by_id(updated, "t-create")
    assert created.issue_number == 4  # provider minted the next number
    assert created.last_synced["hash"] == content_hash(created)
    assert created.last_synced["at"] == parse_aware_datetime(NOW).isoformat()

    pushed = _by_id(updated, "t-push")
    assert pushed.last_synced["hash"] == content_hash(pushed)
    assert pushed.last_synced["at"] == parse_aware_datetime(NOW).isoformat()

    # NEW_REMOTE issue #3 was adopted as a fresh task.
    adopted = [t for t in updated.tasks if t.issue_number == 3]
    assert len(adopted) == 1 and adopted[0].title == "adopt me"

    # The input TaskList was NOT mutated (apply works on a copy).
    assert tl.tasks[0].issue_number is None
    assert t_push.last_synced == {"hash": "stale-hash", "at": BASE_AT}


def test_changed_remote_pull_updates_task_content() -> None:
    task = Task(id="t-1", title="old", body="old body", status="todo", issue_number=7)
    task.last_synced = {"hash": content_hash(task), "at": BASE_AT}
    tl = TaskList(tasks=[task])
    issue = _issue(number=7, title="new title", updated=LATER, labels=["status/in-progress"])
    provider = MockProvider(issues=[issue], now=NOW)

    plan = build_plan(classify(tl, [issue]))
    assert len(plan.pulls) == 1 and plan.pulls[0].task_id == "t-1"

    updated = apply(plan, {}, tl, provider, now=parse_aware_datetime(NOW))
    pulled = _by_id(updated, "t-1")
    assert pulled.title == "new title"
    assert pulled.status == "in-progress"
    assert pulled.updated_at == parse_aware_datetime(LATER).isoformat()
    # no remote mutation for a pure pull
    assert provider.method_calls("update_issue") == []
    assert provider.method_calls("create_issue") == []


def test_closed_remote_issue_pulls_task_to_done() -> None:
    task = Task(id="t-1", title="task", status="in-progress", issue_number=7)
    task.last_synced = {"hash": content_hash(task), "at": BASE_AT}
    tl = TaskList(tasks=[task])
    issue = _issue(number=7, state="closed", updated=LATER, closed_at=parse_aware_datetime(LATER))
    provider = MockProvider(issues=[issue], now=NOW)

    updated = apply(
        build_plan(classify(tl, [issue])), {}, tl, provider, now=parse_aware_datetime(NOW)
    )
    pulled = _by_id(updated, "t-1")
    assert pulled.status == "done"
    assert pulled.closed_at == parse_aware_datetime(LATER).isoformat()


# -- conflict decisions -----------------------------------------------------


def _conflict_setup() -> tuple[TaskList, MockProvider, object]:
    task = Task(id="t-c", title="local title", body="local", status="todo", issue_number=5)
    task.last_synced = {"hash": "stale", "at": BASE_AT}  # local changed
    tl = TaskList(tasks=[task])
    issue = _issue(number=5, title="remote title", updated=LATER)  # remote changed
    provider = MockProvider(issues=[issue], now=NOW)
    plan = build_plan(classify(tl, [issue]))
    assert len(plan.conflicts) == 1
    return tl, provider, plan


def test_conflict_decision_local_pushes() -> None:
    tl, provider, plan = _conflict_setup()
    updated = apply(plan, {"t-c": "local"}, tl, provider, now=parse_aware_datetime(NOW))  # type: ignore[arg-type]
    assert len(provider.method_calls("update_issue")) == 1
    task = _by_id(updated, "t-c")
    assert task.title == "local title"  # local won
    assert task.last_synced["at"] == parse_aware_datetime(NOW).isoformat()


def test_conflict_decision_remote_pulls() -> None:
    tl, provider, plan = _conflict_setup()
    updated = apply(plan, {"t-c": "remote"}, tl, provider, now=parse_aware_datetime(NOW))  # type: ignore[arg-type]
    assert provider.method_calls("update_issue") == []  # pull, no remote write
    task = _by_id(updated, "t-c")
    assert task.title == "remote title"  # remote won


def test_conflict_without_decision_is_left_untouched() -> None:
    tl, provider, plan = _conflict_setup()
    updated = apply(plan, {}, tl, provider, now=parse_aware_datetime(NOW))  # type: ignore[arg-type]
    assert provider.method_calls("update_issue") == []
    assert provider.method_calls("create_issue") == []
    task = _by_id(updated, "t-c")
    assert task.title == "local title"  # unchanged; base NOT refreshed
    assert task.last_synced == {"hash": "stale", "at": BASE_AT}


def test_conflict_unknown_decision_is_treated_as_skip() -> None:
    tl, provider, plan = _conflict_setup()
    updated = apply(plan, {"t-c": "banana"}, tl, provider, now=parse_aware_datetime(NOW))  # type: ignore[arg-type]
    assert provider.method_calls("update_issue") == []
    assert _by_id(updated, "t-c").last_synced == {"hash": "stale", "at": BASE_AT}


# -- --apply via the CLI writes the file + dirties git ---------------------


def test_apply_via_cli_writes_file_and_dirties_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    tl = TaskList(
        provider="github",
        repo="o/r",
        tasks=[Task(id="t-1", title="local task", issue_number=None)],
    )
    tasks_path = _committed_repo(tmp_path, tl)
    provider = MockProvider(issues=[], now=NOW)
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    rc = run_sync(_parse(tasks_path, tmp_path, "--apply"), provider=provider)  # type: ignore[arg-type]

    assert rc == 0
    assert len(provider.method_calls("create_issue")) == 1
    assert _git_status(tmp_path) != ""  # tasks.json changed
    saved = store.load(tasks_path)
    assert saved.tasks[0].issue_number is not None  # linked after create
    assert "applied" in capsys.readouterr().out


def test_main_dispatches_sync_and_builds_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    tl = TaskList(provider="github", repo="o/r", tasks=[Task(id="t-1", title="x")])
    tasks_path = tmp_path / "tasks.json"
    store.save(tl, tasks_path)
    provider = MockProvider(issues=[_issue(number=1)])
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))
    monkeypatch.setattr("task_sync.__main__._build_provider", lambda *a: provider)

    rc = main(["sync", "--dry-run", "--tasks", str(tasks_path), "--repo-root", str(tmp_path)])
    assert rc == 0
    assert "dry run" in capsys.readouterr().out.lower()


# -- local-only + error paths ----------------------------------------------


def test_local_only_mode_is_a_noop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    tl = TaskList(provider="none", tasks=[Task(id="t-1", title="x")])
    tasks_path = tmp_path / "tasks.json"
    store.save(tl, tasks_path)
    before = tasks_path.read_bytes()
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("none", None))

    rc = run_sync(_parse(tasks_path, tmp_path, "--dry-run"))  # type: ignore[arg-type]
    assert rc == 0
    assert tasks_path.read_bytes() == before
    assert "local-only" in capsys.readouterr().out


def test_missing_tasks_file_returns_error(tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    rc = run_sync(_parse(missing, tmp_path, "--dry-run"))  # type: ignore[arg-type]
    assert rc == 1


# -- helper units -----------------------------------------------------------


def test_load_decisions_variants(tmp_path: Path) -> None:
    assert _load_decisions(None) == {}
    flat = tmp_path / "flat.json"
    flat.write_text(json.dumps({"t-1": "local"}))
    assert _load_decisions(str(flat)) == {"t-1": "local"}
    wrapped = tmp_path / "wrapped.json"
    wrapped.write_text(json.dumps({"decisions": {"t-2": "remote"}}))
    assert _load_decisions(str(wrapped)) == {"t-2": "remote"}


def test_load_decisions_rejects_non_object(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(["not", "a", "map"]))
    with pytest.raises(ValueError, match="must be a JSON object"):
        _load_decisions(str(bad))
    # the offending path is named, so the user knows *which* file to fix.
    # Substring, not `match=` — `match` is a regex and a Windows tmp path
    # (`C:\Users\...`) is full of backslash escapes.
    with pytest.raises(ValueError) as excinfo:
        _load_decisions(str(bad))
    assert str(bad) in str(excinfo.value)


def test_load_decisions_missing_file_raises_value_error_naming_the_path(tmp_path: Path) -> None:
    """A missing `--decisions` path is an OSError underneath; it must surface
    as a ValueError carrying the path, not escape as a raw traceback."""
    missing = tmp_path / "gone.json"
    with pytest.raises(ValueError, match="cannot read decisions file"):
        _load_decisions(str(missing))
    with pytest.raises(ValueError) as excinfo:
        _load_decisions(str(missing))
    assert str(missing) in str(excinfo.value)


def test_load_decisions_malformed_json_names_the_path(tmp_path: Path) -> None:
    bad = tmp_path / "broken.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed JSON in decisions file"):
        _load_decisions(str(bad))
    with pytest.raises(ValueError) as excinfo:
        _load_decisions(str(bad))
    assert str(bad) in str(excinfo.value)


def test_sync_apply_with_missing_decisions_file_errors_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`sync --apply --decisions missing.json` exits 1 with a message, and —
    critically — writes nothing, since the load happens before `apply`."""
    tl = TaskList(
        provider="github",
        repo="o/r",
        tasks=[Task(id="t-1", title="local task", issue_number=None)],
    )
    tasks_path = _committed_repo(tmp_path, tl)
    before = tasks_path.read_bytes()
    missing = tmp_path / "gone.json"

    provider = MockProvider(issues=[], now=NOW)
    monkeypatch.setattr("task_sync.__main__.detect_provider", lambda r: ("github", "o/r"))

    args = build_parser().parse_args(
        [
            "sync",
            "--apply",
            "--decisions",
            str(missing),
            "--tasks",
            str(tasks_path),
            "--repo-root",
            str(tmp_path),
        ]
    )
    rc = run_sync(args, provider=provider)

    assert rc == 1
    err = capsys.readouterr().err
    assert "task-sync sync:" in err
    assert str(missing) in err
    assert tasks_path.read_bytes() == before
    assert provider.method_calls("create_issue") == []


def test_build_provider_github() -> None:
    from task_sync.providers.github import GithubProvider

    assert isinstance(_build_provider("github", "o/r", {}), GithubProvider)


def test_build_provider_gitea_from_config(monkeypatch: pytest.MonkeyPatch) -> None:
    from task_sync.providers.gitea import GiteaProvider

    monkeypatch.delenv("GITEA_URL", raising=False)
    monkeypatch.setenv("GITEA_TOKEN", "tok")
    provider = _build_provider("gitea", "o/r", {"gitea_url": "https://git.example.com"})
    assert isinstance(provider, GiteaProvider)
    assert provider._base_url == "https://git.example.com"
    assert provider._token == "tok"


def test_build_provider_gitea_falls_back_to_tea_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """No env vars, no `config['gitea_url']` — falls back to the tea config."""
    from task_sync.providers.gitea import GiteaProvider

    monkeypatch.delenv("GITEA_URL", raising=False)
    monkeypatch.delenv("GITEA_TOKEN", raising=False)
    monkeypatch.setattr(
        "task_sync.providers.gitea.load_gitea_credentials",
        lambda: ("https://tea.example.com", "tea-tok"),
    )

    provider = _build_provider("gitea", "o/r", {})

    assert isinstance(provider, GiteaProvider)
    assert provider._base_url == "https://tea.example.com"
    assert provider._token == "tea-tok"


def test_build_provider_gitea_env_overrides_tea_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """`$GITEA_URL`/`$GITEA_TOKEN` win over both config and tea config, and the
    tea config is never even consulted once env fully supplies both."""
    from task_sync.providers.gitea import GiteaProvider

    monkeypatch.setenv("GITEA_URL", "https://env.example.com")
    monkeypatch.setenv("GITEA_TOKEN", "env-tok")

    def _unexpected() -> tuple[str, str]:
        raise AssertionError("tea config should not be read when env supplies both")

    monkeypatch.setattr("task_sync.providers.gitea.load_gitea_credentials", _unexpected)

    provider = _build_provider("gitea", "o/r", {"gitea_url": "https://config.example.com"})

    assert isinstance(provider, GiteaProvider)
    assert provider._base_url == "https://env.example.com"
    assert provider._token == "env-tok"


def test_build_provider_gitea_needs_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """No env, no `config['gitea_url']`, and no usable tea config: a clear error."""
    monkeypatch.delenv("GITEA_URL", raising=False)
    monkeypatch.delenv("GITEA_TOKEN", raising=False)

    def _no_config() -> tuple[str, str]:
        raise RuntimeError("no Gitea credentials found at ...; run `tea login add` ...")

    monkeypatch.setattr("task_sync.providers.gitea.load_gitea_credentials", _no_config)

    with pytest.raises(ValueError, match="gitea provider needs credentials"):
        _build_provider("gitea", "o/r", {})


def test_build_provider_rejects_missing_repo_and_unknown() -> None:
    with pytest.raises(ValueError, match="without a repo"):
        _build_provider("github", None, {})
    with pytest.raises(ValueError, match="unknown provider"):
        _build_provider("svn", "o/r", {})


def test_apply_summary_text() -> None:
    tl = TaskList(tasks=[Task(id="t-1", title="x", issue_number=None)])
    plan = build_plan(classify(tl, []))
    text = _apply_summary(plan)
    assert "1 create" in text
    # no skipped adoptions -> no trailing sentence about them
    assert "adopt window" not in text


def test_summarize_empty_plan_says_in_sync() -> None:
    text = summarize_plan(SyncPlan())
    assert "already in sync" in text
    assert "skipped (closed outside adopt window)" not in text


def test_plan_with_only_skipped_adopts_is_not_empty_and_says_so() -> None:
    """No actions, but 20 issues left unadopted is NOT "already in sync"."""
    plan = SyncPlan(skipped_adopts=list(range(1, 21)))
    assert not plan.is_empty()
    text = summarize_plan(plan)
    assert "skipped (closed outside adopt window): 20 — use --adopt-all to mirror them" in text
    assert "already in sync" not in text


def test_summarize_plan_lists_conflicts() -> None:
    task = Task(id="t-c", title="local", body="l", status="todo", issue_number=5)
    task.last_synced = {"hash": "stale", "at": BASE_AT}
    issue = _issue(number=5, title="remote", updated=LATER)
    plan = build_plan(classify(TaskList(tasks=[task]), [issue]))
    text = summarize_plan(plan)
    assert "! conflict: task t-c <-> issue #5" in text
    assert "conflicts (need decision): 1" in text


def test_apply_ensures_milestone_and_labels_on_create() -> None:
    task = Task(
        id="t-1",
        title="x",
        status="in-progress",
        priority="P1",
        milestone="v2.0",
        issue_number=None,
    )
    tl = TaskList(tasks=[task])
    provider = MockProvider(issues=[], now=NOW)
    apply(build_plan(classify(tl, [])), {}, tl, provider, now=parse_aware_datetime(NOW))
    assert "v2.0" in provider.ensured_milestones
    assert "status/in-progress" in provider.ensured_labels
    assert "priority/P1" in provider.ensured_labels
