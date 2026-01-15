"""Common pytest fixtures for Claude Marketplace tests."""

import json
import pytest
from pathlib import Path


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def schema_dir(project_root: Path) -> Path:
    """Return the schemas directory."""
    return project_root / "schemas"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def questions_schema(schema_dir: Path) -> dict:
    """Load the questions JSON schema."""
    schema_path = schema_dir / "questions.json"
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def answers_schema(schema_dir: Path) -> dict:
    """Load the answers JSON schema."""
    schema_path = schema_dir / "answers.json"
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_prd(fixtures_dir: Path) -> str:
    """Load the sample PRD document."""
    prd_path = fixtures_dir / "sample-prd.md"
    with open(prd_path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def expected_questions(fixtures_dir: Path) -> dict:
    """Load the expected questions output."""
    questions_path = fixtures_dir / "expected-questions.json"
    with open(questions_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_answers(fixtures_dir: Path) -> dict:
    """Load the sample answers file."""
    answers_path = fixtures_dir / "sample-answers.json"
    with open(answers_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def expected_updated_prd(fixtures_dir: Path) -> str:
    """Load the expected updated PRD document."""
    prd_path = fixtures_dir / "expected-updated-prd.md"
    with open(prd_path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def sample_prd_path(fixtures_dir: Path) -> Path:
    """Return the path to the sample PRD document."""
    return fixtures_dir / "sample-prd.md"


@pytest.fixture
def expected_questions_path(fixtures_dir: Path) -> Path:
    """Return the path to the expected questions file."""
    return fixtures_dir / "expected-questions.json"


@pytest.fixture
def sample_answers_path(fixtures_dir: Path) -> Path:
    """Return the path to the sample answers file."""
    return fixtures_dir / "sample-answers.json"


@pytest.fixture
def expected_updated_prd_path(fixtures_dir: Path) -> Path:
    """Return the path to the expected updated PRD."""
    return fixtures_dir / "expected-updated-prd.md"


@pytest.fixture
def valid_plugin_dir(fixtures_dir: Path) -> Path:
    """Return the path to the valid plugin fixture."""
    return fixtures_dir / "valid-plugin"


@pytest.fixture
def invalid_plugin_dir(fixtures_dir: Path) -> Path:
    """Return the path to the invalid plugin fixture."""
    return fixtures_dir / "invalid-plugin"


@pytest.fixture
def plugins_dir(project_root: Path) -> Path:
    """Return the plugins directory."""
    return project_root / "plugins"
