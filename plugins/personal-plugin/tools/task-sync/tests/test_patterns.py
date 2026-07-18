"""Tests for the generic structural-identifier detectors.

The load-bearing negative case: a public domain like ``example.com`` must
NOT be mis-flagged as an internal hostname (only the internal TLDs count).
"""

from __future__ import annotations

import pytest

from task_sync.confidential.patterns import find_structural


def _categories(text: str) -> set[str]:
    return {f.category for f in find_structural(text)}


def test_email_flagged() -> None:
    findings = find_structural("Ping alice@example.com about the outage.")
    assert any(f.category == "structural.email" for f in findings)


@pytest.mark.parametrize(
    "hostname",
    ["db.internal", "server01.corp", "host.corp.local", "gw.lan", "svc.intra"],
)
def test_internal_hostname_flagged(hostname: str) -> None:
    findings = find_structural(f"Connect to {hostname} over the VPN.")
    assert any(f.category == "structural.internal_hostname" for f in findings)


@pytest.mark.parametrize(
    "text",
    [
        "Visit example.com for the public docs.",
        "See www.example.com and docs.python.org.",
        "Our site is company.com and blog.company.io.",
    ],
)
def test_public_domain_not_flagged_internal(text: str) -> None:
    assert "structural.internal_hostname" not in _categories(text)


def test_ipv4_flagged() -> None:
    assert "structural.ipv4" in _categories("The gateway is 10.0.0.138 today.")


def test_phone_flagged() -> None:
    assert "structural.phone" in _categories("Call (555) 123-4567 for support.")


def test_ticket_id_flagged() -> None:
    assert "structural.ticket_id" in _categories("Blocked on INC1234567 in the queue.")


def test_asset_id_flagged() -> None:
    assert "structural.asset_id" in _categories("Asset SN123456 was retired.")


def test_ordinary_sentence_not_flagged() -> None:
    assert find_structural("The reconcile engine is finished and tested.") == []


def test_email_hostname_not_double_flagged() -> None:
    """The hostname inside an email must not produce a second finding."""
    findings = find_structural("mail bob@host.corp for details")
    spans = [f.span for f in findings]
    # exactly one finding (the email); its hostname tail is not re-reported.
    assert len(findings) == 1
    assert findings[0].category == "structural.email"
    assert len(spans) == len(set(spans))
