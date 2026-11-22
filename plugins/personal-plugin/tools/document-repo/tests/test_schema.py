import copy
import json
from pathlib import Path

import pytest

from document_repo.schema import MAX_SNIPPET_LINES, SCHEMA_VERSION, SPEC, validate

FIXTURE = Path(__file__).parent / "fixtures" / "sample_model.json"


@pytest.fixture
def model() -> dict:
    return json.loads(FIXTURE.read_text())


def test_fixture_is_valid(model) -> None:
    assert validate(model) == []


@pytest.mark.parametrize("key", sorted(SPEC))
def test_every_top_level_key_is_required(model, key: str) -> None:
    del model[key]
    assert f"{key}: missing" in validate(model)


def test_nested_missing_and_types(model) -> None:
    del model["project"]["name"]
    model["modules"][0]["status"] = "done"
    model["modules"][1]["interface"][0]["line"] = True
    model["meta"]["repo_url"] = 5
    errors = validate(model)
    assert "project.name: missing" in errors
    assert "modules[0].status: expected one of ['analyzed', 'not_analyzed']" in errors
    assert "modules[1].interface[0].line: expected int" in errors
    assert "meta.repo_url: expected str or null" in errors


def test_repo_url_may_be_null(model) -> None:
    model["meta"]["repo_url"] = None
    assert validate(model) == []


def test_snippet_optional_but_capped(model) -> None:
    step = model["flows"][0]["steps"][0]
    del step["snippet"]
    assert validate(model) == []
    step["snippet"] = "\n".join(["x"] * (MAX_SNIPPET_LINES + 1))
    assert any("snippet" in e and "30" in e for e in validate(model))


def test_schema_version(model) -> None:
    model["meta"]["schema_version"] = SCHEMA_VERSION + 1
    assert any("schema_version" in e for e in validate(model))


@pytest.mark.parametrize(
    "mutate,needle",
    [
        (
            lambda m: m["architecture"]["components"][0]["module_ids"].append("nope"),
            "unknown module 'nope'",
        ),
        (
            lambda m: m["architecture"]["connections"].append(
                {"from": "api", "to": "ghost", "label": "x"}
            ),
            "unknown component 'ghost'",
        ),
        (
            lambda m: m["modules"][1]["dependencies"]["internal"].append("ghost"),
            "unknown module 'ghost'",
        ),
        (lambda m: m["glossary"][0]["module_ids"].append("ghost"), "unknown module 'ghost'"),
        (
            lambda m: m["paths"][0]["steps"].append(
                {"ref_type": "flow", "ref_id": "ghost", "note": ""}
            ),
            "unknown flow 'ghost'",
        ),
        (
            lambda m: m["paths"][0]["steps"].append(
                {"ref_type": "glossary", "ref_id": "Ghost", "note": ""}
            ),
            "unknown glossary term 'Ghost'",
        ),
        (lambda m: m["modules"].append(copy.deepcopy(m["modules"][0])), "duplicate module id 'db'"),
        (lambda m: m["flows"][0]["steps"][0].update(line_end=1), "line_end before line_start"),
    ],
)
def test_cross_references(model, mutate, needle: str) -> None:
    mutate(model)
    errors = validate(model)
    assert any(needle in e for e in errors), errors


def test_not_an_object() -> None:
    assert validate([]) == ["(root): expected object"]  # type: ignore[arg-type]
