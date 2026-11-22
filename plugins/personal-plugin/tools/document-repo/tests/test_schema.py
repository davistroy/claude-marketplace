import copy
import json
from pathlib import Path

import pytest

from document_repo import schema
from document_repo.modules import slug
from document_repo.schema import MAX_SNIPPET_LINES, SCHEMA_VERSION, SPEC, OneOf, validate

FIXTURE = Path(__file__).parent / "fixtures" / "sample_model.json"

ID_HINT = "lowercase letters, digits and single hyphens"
DOC_HINT = "expected a relative POSIX path: no leading '/', no '..' segment, no backslash, no NUL"


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


def test_not_an_object() -> None:
    assert validate([]) == ["(root): expected object"]  # type: ignore[arg-type]


def test_nested_object_expected(model) -> None:
    model["project"] = []
    assert validate(model) == ["project: expected object"]


def test_plain_type_mismatch(model) -> None:
    model["project"]["name"] = 5
    assert validate(model) == ["project.name: expected str"]


def test_bool_is_not_an_int(model) -> None:
    model["meta"]["schema_version"] = True  # True == 1, so only the shape pass can catch it
    assert validate(model) == ["meta.schema_version: expected int"]


def test_array_expected(model) -> None:
    model["project"]["users"] = "Note takers"
    assert validate(model) == ["project.users: expected array"]


def test_oneof_has_docstring_and_repr() -> None:
    assert OneOf.__doc__
    assert repr(OneOf("a", "b")) == "OneOf('a', 'b')"


# --- unknown keys ---------------------------------------------------------------------------


def test_snippet_typo_is_rejected_not_silently_dropped(model) -> None:
    step = model["flows"][0]["steps"][0]
    step["snipet"] = step.pop("snippet")
    assert validate(model) == ["flows[0].steps[0].snipet: unknown field"]


def test_unknown_root_key(model) -> None:
    model["extra"] = 1
    assert validate(model) == ["extra: unknown field"]


def test_optional_marker_is_not_part_of_the_key(model) -> None:
    model["flows"][0]["steps"][0]["snippet?"] = "x"
    assert validate(model) == ["flows[0].steps[0].snippet?: unknown field"]


# --- ids ------------------------------------------------------------------------------------

BAD_IDS = ["", "../../evil", "a/b", "A", "a--b", "-a", "a-", "a_b", "a b", "a\n"]
ID_OWNERS = {
    "modules[0]": lambda m: m["modules"][0],
    "architecture.components[0]": lambda m: m["architecture"]["components"][0],
    "architecture.diagrams[0]": lambda m: m["architecture"]["diagrams"][0],
    "flows[0]": lambda m: m["flows"][0],
    "paths[0]": lambda m: m["paths"][0],
}


@pytest.mark.parametrize("bad", BAD_IDS)
@pytest.mark.parametrize("where", sorted(ID_OWNERS))
def test_id_must_be_a_slug(model, where: str, bad: str) -> None:
    ID_OWNERS[where](model)["id"] = bad
    assert validate(model) == [f"{where}.id: invalid id '{bad}' ({ID_HINT})"]


def test_id_must_be_a_string(model) -> None:
    model["modules"][0]["id"] = 5
    assert validate(model) == ["modules[0].id: expected str"]


@pytest.mark.parametrize("good", ["a", "0", "a1-b2-c3", "root", "src-api-2"])
def test_good_ids(model, good: str) -> None:
    model["architecture"]["diagrams"][0]["id"] = good
    assert validate(model) == []


@pytest.mark.parametrize("key", [".config", "config", "lib/foo", "Lib Foo", "_", "src/api/v2", "ü"])
def test_modules_slug_output_is_a_valid_id(model, key: str) -> None:
    model["architecture"]["diagrams"][0]["id"] = slug(key)
    assert validate(model) == []
    model["architecture"]["diagrams"][0]["id"] = f"{slug(key)}-2"
    assert validate(model) == []


# --- uniqueness -----------------------------------------------------------------------------


def _dup_glossary(m: dict) -> None:
    m["glossary"].append({**m["glossary"][0], "term": "note"})


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (
            lambda m: m["modules"].append(copy.deepcopy(m["modules"][0])),
            "duplicate module id 'db'",
        ),
        (
            lambda m: m["architecture"]["components"].append(
                copy.deepcopy(m["architecture"]["components"][0])
            ),
            "duplicate component id 'api'",
        ),
        (
            lambda m: m["flows"].append(copy.deepcopy(m["flows"][0])),
            "duplicate flow id 'save-note'",
        ),
        (_dup_glossary, "duplicate glossary term 'note'"),
        (
            lambda m: m["paths"].append(copy.deepcopy(m["paths"][0])),
            "duplicate path id 'new-dev'",
        ),
        (
            lambda m: m["architecture"]["diagrams"].append(
                copy.deepcopy(m["architecture"]["diagrams"][0])
            ),
            "duplicate diagram id 'overview'",
        ),
    ],
    ids=["module", "component", "flow", "glossary-case-folded", "path", "diagram"],
)
def test_duplicates(model, mutate, expected: str) -> None:
    mutate(model)
    assert validate(model) == [expected]


def test_glossary_terms_differing_only_in_case_collide_but_references_stay_exact(model) -> None:
    _dup_glossary(model)
    model["glossary"].pop(0)  # keep only 'note'; the fixture path refers to 'Note'
    assert validate(model) == ["paths[0].steps[3]: unknown glossary term 'Note'"]


# --- every cross-reference, pinned to its own location --------------------------------------


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (
            lambda m: m["architecture"]["components"][0]["module_ids"].append("nope"),
            "architecture.components[0].module_ids: unknown module 'nope'",
        ),
        (
            lambda m: m["architecture"]["connections"].append(
                {"from": "ghost", "to": "db", "label": "x"}
            ),
            "architecture.connections[1].from: unknown component 'ghost'",
        ),
        (
            lambda m: m["architecture"]["connections"].append(
                {"from": "api", "to": "ghost", "label": "x"}
            ),
            "architecture.connections[1].to: unknown component 'ghost'",
        ),
        (
            lambda m: m["modules"][1]["dependencies"]["internal"].append("ghost"),
            "modules[1].dependencies.internal: unknown module 'ghost'",
        ),
        (
            lambda m: m["glossary"][0]["module_ids"].append("ghost"),
            "glossary[0].module_ids: unknown module 'ghost'",
        ),
        (
            lambda m: m["paths"][0]["steps"].append(
                {"ref_type": "module", "ref_id": "ghost", "note": ""}
            ),
            "paths[0].steps[4]: unknown module 'ghost'",
        ),
        (
            lambda m: m["paths"][0]["steps"].append(
                {"ref_type": "flow", "ref_id": "ghost", "note": ""}
            ),
            "paths[0].steps[4]: unknown flow 'ghost'",
        ),
        (
            lambda m: m["paths"][0]["steps"].append(
                {"ref_type": "glossary", "ref_id": "Ghost", "note": ""}
            ),
            "paths[0].steps[4]: unknown glossary term 'Ghost'",
        ),
    ],
    ids=[
        "component-module",
        "connection-from",
        "connection-to",
        "dependency-internal",
        "glossary-module",
        "path-module",
        "path-flow",
        "path-glossary",
    ],
)
def test_each_reference_is_checked_at_its_own_location(model, mutate, expected: str) -> None:
    mutate(model)
    assert validate(model) == [expected]


def test_module_may_not_depend_on_itself(model) -> None:
    model["modules"][1]["dependencies"]["internal"].append("src-api")
    assert validate(model) == ["modules[1].dependencies.internal: module depends on itself"]


# --- snippet --------------------------------------------------------------------------------


def test_snippet_is_optional(model) -> None:
    del model["flows"][0]["steps"][0]["snippet"]
    assert validate(model) == []


def test_snippet_at_the_cap_passes(model) -> None:
    model["flows"][0]["steps"][0]["snippet"] = "\n".join(["x"] * MAX_SNIPPET_LINES)
    assert validate(model) == []


def test_snippet_one_over_the_cap_fails(model) -> None:
    model["flows"][0]["steps"][0]["snippet"] = "\n".join(["x"] * (MAX_SNIPPET_LINES + 1))
    assert validate(model) == [f"flows[0].steps[0].snippet: more than {MAX_SNIPPET_LINES} lines"]


def test_snippet_message_follows_the_constant(model, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(schema, "MAX_SNIPPET_LINES", 3)
    model["flows"][0]["steps"][0]["snippet"] = "a\nb\nc\nd"
    assert validate(model) == ["flows[0].steps[0].snippet: more than 3 lines"]


# --- schema version -------------------------------------------------------------------------


def test_schema_version(model) -> None:
    model["meta"]["schema_version"] = SCHEMA_VERSION + 1
    assert validate(model) == [f"meta.schema_version: expected {SCHEMA_VERSION}"]


def test_wrong_version_is_reported_alongside_shape_errors(model) -> None:
    model["meta"]["schema_version"] = SCHEMA_VERSION + 1
    del model["project"]["tagline"]
    errors = validate(model)
    assert f"meta.schema_version: expected {SCHEMA_VERSION}" in errors
    assert "project.tagline: missing" in errors


def test_version_check_needs_a_meta_object_with_the_key(model) -> None:
    del model["meta"]["schema_version"]
    assert validate(model) == ["meta.schema_version: missing"]
    model["meta"] = "oops"
    assert validate(model) == ["meta: expected object"]


# --- line numbers ---------------------------------------------------------------------------

LINE_OWNERS = {
    "modules[1].interface[0].line": lambda m: (m["modules"][1]["interface"][0], "line"),
    "flows[0].steps[0].line_start": lambda m: (m["flows"][0]["steps"][0], "line_start"),
    "flows[0].steps[0].line_end": lambda m: (m["flows"][0]["steps"][0], "line_end"),
}


@pytest.mark.parametrize("bad", [0, -5])
@pytest.mark.parametrize("where", sorted(LINE_OWNERS))
def test_line_numbers_start_at_one(model, where: str, bad: int) -> None:
    owner, key = LINE_OWNERS[where](model)
    owner[key] = bad
    assert validate(model) == [f"{where}: expected line number >= 1"]


def test_line_one_is_valid(model) -> None:
    step = model["flows"][0]["steps"][0]
    step["line_start"] = step["line_end"] = 1
    model["modules"][1]["interface"][0]["line"] = 1
    assert validate(model) == []


def test_line_end_before_line_start(model) -> None:
    model["flows"][0]["steps"][0]["line_end"] = 1
    assert validate(model) == ["flows[0].steps[0]: line_end before line_start"]


# --- doc references -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad", ["../../etc/passwd", "/etc/x", "a\\b", "", "a/../b", "..", "a\0b", "docs/.."]
)
def test_doc_ref_must_be_a_safe_relative_path(model, bad: str) -> None:
    model["paths"][0]["steps"][0]["ref_id"] = bad
    assert validate(model) == [f"paths[0].steps[0].ref_id: invalid doc path {bad!r} ({DOC_HINT})"]


@pytest.mark.parametrize("good", ["README.md", "docs/ARCHITECTURE.md", "docs/a..b.md", "..hidden"])
def test_doc_ref_good(model, good: str) -> None:
    model["paths"][0]["steps"][0]["ref_id"] = good
    assert validate(model) == []


def test_doc_ref_is_not_looked_up_as_a_module(model) -> None:
    model["paths"][0]["steps"][0]["ref_id"] = "nonexistent.md"
    assert validate(model) == []
