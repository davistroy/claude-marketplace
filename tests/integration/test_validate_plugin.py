"""Integration tests for the /validate-plugin command.

Tests validate:
1. Valid plugins pass all validation checks
2. Invalid plugins fail with appropriate error messages
3. Specific violations are detected (forbidden fields, missing sections, etc.)
"""

import json
import re
import pytest
import yaml
from pathlib import Path


@pytest.fixture
def valid_plugin_dir(fixtures_dir: Path) -> Path:
    """Return the path to the valid plugin fixture."""
    return fixtures_dir / "valid-plugin"


@pytest.fixture
def invalid_plugin_dir(fixtures_dir: Path) -> Path:
    """Return the path to the invalid plugin fixture."""
    return fixtures_dir / "invalid-plugin"


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}

    # Find the closing ---
    end_marker = content.find("---", 3)
    if end_marker == -1:
        return {}

    frontmatter_text = content[3:end_marker].strip()
    try:
        return yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        return {}


def validate_plugin_json(plugin_dir: Path) -> list:
    """Validate plugin.json structure and return list of errors."""
    errors = []
    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"

    if not plugin_json_path.exists():
        errors.append("plugin.json not found")
        return errors

    try:
        with open(plugin_json_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return errors

    # Check required fields
    required_fields = ["name", "description", "version"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Validate version format (semver)
    if "version" in data:
        version_pattern = r"^\d+\.\d+\.\d+$"
        if not re.match(version_pattern, data["version"]):
            errors.append(f"Invalid version format: {data['version']}")

    return errors


def validate_frontmatter(file_path: Path) -> list:
    """Validate frontmatter of a markdown file and return list of errors."""
    errors = []

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    frontmatter = parse_frontmatter(content)

    # Check for required description field
    if "description" not in frontmatter:
        errors.append(f"{file_path.name}: Missing required field 'description'")

    # Check for forbidden name field
    if "name" in frontmatter:
        errors.append(f"{file_path.name}: Forbidden field 'name' found")

    return errors


def validate_required_sections(file_path: Path) -> list:
    """Validate that command has required sections."""
    errors = []

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Check for Input Validation section
    if "## Input Validation" not in content:
        errors.append(f"{file_path.name}: Missing section 'Input Validation'")

    # Check for Instructions section
    if "## Instructions" not in content:
        errors.append(f"{file_path.name}: Missing section 'Instructions'")

    return errors


class TestValidPluginValidation:
    """Tests for valid plugin fixture."""

    def test_plugin_json_exists(self, valid_plugin_dir: Path):
        """Verify valid plugin has plugin.json."""
        plugin_json = valid_plugin_dir / ".claude-plugin" / "plugin.json"
        assert plugin_json.exists(), "plugin.json should exist"

    def test_plugin_json_is_valid(self, valid_plugin_dir: Path):
        """Verify valid plugin's plugin.json passes validation."""
        errors = validate_plugin_json(valid_plugin_dir)
        assert errors == [], f"Validation errors: {errors}"

    def test_plugin_json_has_required_fields(self, valid_plugin_dir: Path):
        """Verify plugin.json has all required fields."""
        plugin_json_path = valid_plugin_dir / ".claude-plugin" / "plugin.json"
        with open(plugin_json_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "name" in data
        assert "description" in data
        assert "version" in data

    def test_plugin_json_version_is_semver(self, valid_plugin_dir: Path):
        """Verify plugin version follows semver format."""
        plugin_json_path = valid_plugin_dir / ".claude-plugin" / "plugin.json"
        with open(plugin_json_path, encoding="utf-8") as f:
            data = json.load(f)

        version = data.get("version", "")
        assert re.match(r"^\d+\.\d+\.\d+$", version), f"Version {version} is not semver"

    def test_commands_directory_exists(self, valid_plugin_dir: Path):
        """Verify valid plugin has commands directory."""
        commands_dir = valid_plugin_dir / "commands"
        assert commands_dir.exists(), "commands directory should exist"
        assert commands_dir.is_dir(), "commands should be a directory"

    def test_commands_have_valid_frontmatter(self, valid_plugin_dir: Path):
        """Verify all commands have valid frontmatter."""
        commands_dir = valid_plugin_dir / "commands"
        all_errors = []

        for md_file in commands_dir.glob("*.md"):
            errors = validate_frontmatter(md_file)
            all_errors.extend(errors)

        assert all_errors == [], f"Frontmatter errors: {all_errors}"

    def test_commands_have_required_sections(self, valid_plugin_dir: Path):
        """Verify all commands have required sections."""
        commands_dir = valid_plugin_dir / "commands"
        all_errors = []

        for md_file in commands_dir.glob("*.md"):
            errors = validate_required_sections(md_file)
            all_errors.extend(errors)

        assert all_errors == [], f"Section errors: {all_errors}"

    def test_skills_directory_exists(self, valid_plugin_dir: Path):
        """Verify valid plugin has skills directory."""
        skills_dir = valid_plugin_dir / "skills"
        assert skills_dir.exists(), "skills directory should exist"

    def test_help_skill_exists(self, valid_plugin_dir: Path):
        """Verify valid plugin has help.md skill."""
        help_file = valid_plugin_dir / "skills" / "help.md"
        assert help_file.exists(), "help.md skill should exist"

    def test_help_skill_has_valid_frontmatter(self, valid_plugin_dir: Path):
        """Verify help.md has valid frontmatter."""
        help_file = valid_plugin_dir / "skills" / "help.md"
        errors = validate_frontmatter(help_file)
        assert errors == [], f"Help frontmatter errors: {errors}"


class TestInvalidPluginValidation:
    """Tests for invalid plugin fixture."""

    def test_plugin_json_missing_version(self, invalid_plugin_dir: Path):
        """Verify invalid plugin is detected for missing version."""
        errors = validate_plugin_json(invalid_plugin_dir)
        assert any("version" in e.lower() for e in errors), (
            f"Should detect missing version field. Errors: {errors}"
        )

    def test_forbidden_name_field_detected(self, invalid_plugin_dir: Path):
        """Verify forbidden name field in frontmatter is detected."""
        file_path = invalid_plugin_dir / "commands" / "forbidden-name-field.md"
        errors = validate_frontmatter(file_path)

        assert any("name" in e.lower() and "forbidden" in e.lower() for e in errors), (
            f"Should detect forbidden name field. Errors: {errors}"
        )

    def test_missing_description_detected(self, invalid_plugin_dir: Path):
        """Verify missing description field is detected."""
        file_path = invalid_plugin_dir / "commands" / "missing-description.md"
        errors = validate_frontmatter(file_path)

        assert any("description" in e.lower() for e in errors), (
            f"Should detect missing description. Errors: {errors}"
        )

    def test_missing_sections_detected(self, invalid_plugin_dir: Path):
        """Verify missing required sections are detected."""
        file_path = invalid_plugin_dir / "commands" / "missing-sections.md"
        errors = validate_required_sections(file_path)

        assert any("input validation" in e.lower() for e in errors), (
            f"Should detect missing Input Validation section. Errors: {errors}"
        )
        assert any("instructions" in e.lower() for e in errors), (
            f"Should detect missing Instructions section. Errors: {errors}"
        )


class TestValidationHelpers:
    """Tests for validation helper functions."""

    def test_parse_frontmatter_with_valid_yaml(self):
        """Verify frontmatter parsing works with valid YAML."""
        content = """---
description: Test description
allowed-tools: Bash
---

# Content
"""
        result = parse_frontmatter(content)
        assert result["description"] == "Test description"
        assert result["allowed-tools"] == "Bash"

    def test_parse_frontmatter_without_markers(self):
        """Verify frontmatter parsing returns empty dict without markers."""
        content = """# No Frontmatter

Just content here.
"""
        result = parse_frontmatter(content)
        assert result == {}

    def test_parse_frontmatter_with_empty_yaml(self):
        """Verify frontmatter parsing handles empty YAML."""
        content = """---
---

# Content
"""
        result = parse_frontmatter(content)
        assert result == {}

    def test_validate_plugin_json_nonexistent(self, tmp_path: Path):
        """Verify validation handles non-existent plugin.json."""
        errors = validate_plugin_json(tmp_path)
        assert any("not found" in e.lower() for e in errors)


class TestStrictModeValidation:
    """Tests for strict mode validation behavior."""

    def test_valid_plugin_passes_strict_mode(self, valid_plugin_dir: Path):
        """Verify valid plugin would pass strict mode validation."""
        # Collect all validation errors
        all_errors = []

        # Plugin.json validation
        all_errors.extend(validate_plugin_json(valid_plugin_dir))

        # Frontmatter validation for all commands
        commands_dir = valid_plugin_dir / "commands"
        for md_file in commands_dir.glob("*.md"):
            all_errors.extend(validate_frontmatter(md_file))
            all_errors.extend(validate_required_sections(md_file))

        # Skills validation
        skills_dir = valid_plugin_dir / "skills"
        for md_file in skills_dir.glob("*.md"):
            all_errors.extend(validate_frontmatter(md_file))

        assert all_errors == [], f"Valid plugin should have no errors: {all_errors}"

    def test_invalid_plugin_fails_strict_mode(self, invalid_plugin_dir: Path):
        """Verify invalid plugin would fail strict mode validation."""
        all_errors = []

        # Plugin.json validation
        all_errors.extend(validate_plugin_json(invalid_plugin_dir))

        # Frontmatter validation for all commands
        commands_dir = invalid_plugin_dir / "commands"
        for md_file in commands_dir.glob("*.md"):
            all_errors.extend(validate_frontmatter(md_file))

        assert len(all_errors) > 0, "Invalid plugin should have errors"
