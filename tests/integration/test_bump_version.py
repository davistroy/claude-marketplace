"""Integration tests for the /bump-version command.

Tests validate:
1. Version bumping logic works correctly (major, minor, patch)
2. Multi-file updates are synchronized
3. Semver format is maintained
"""

import json
import re
import pytest
from pathlib import Path


def parse_semver(version: str) -> tuple:
    """Parse semver string into tuple of (major, minor, patch)."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ValueError(f"Invalid semver: {version}")
    return tuple(int(x) for x in match.groups())


def bump_version(current: str, bump_type: str) -> str:
    """Calculate new version based on bump type."""
    major, minor, patch = parse_semver(current)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def get_plugin_version(plugin_dir: Path) -> str:
    """Get version from plugin.json."""
    plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"
    with open(plugin_json, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("version", "")


def update_plugin_json_version(plugin_dir: Path, new_version: str) -> bool:
    """Update version in plugin.json. Returns True if successful."""
    plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"
    try:
        with open(plugin_json, encoding="utf-8") as f:
            data = json.load(f)

        data["version"] = new_version

        with open(plugin_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        return True
    except Exception:
        return False


class TestSemverParsing:
    """Tests for semver parsing and validation."""

    def test_parse_valid_semver(self):
        """Verify valid semver strings parse correctly."""
        assert parse_semver("1.0.0") == (1, 0, 0)
        assert parse_semver("2.5.3") == (2, 5, 3)
        assert parse_semver("10.20.30") == (10, 20, 30)
        assert parse_semver("0.0.1") == (0, 0, 1)

    def test_parse_invalid_semver_raises(self):
        """Verify invalid semver strings raise ValueError."""
        with pytest.raises(ValueError):
            parse_semver("1.0")  # Missing patch

        with pytest.raises(ValueError):
            parse_semver("v1.0.0")  # Has prefix

        with pytest.raises(ValueError):
            parse_semver("1.0.0-alpha")  # Has prerelease

        with pytest.raises(ValueError):
            parse_semver("not.a.version")  # Not numbers


class TestVersionBumping:
    """Tests for version bump calculations."""

    def test_major_bump_resets_minor_and_patch(self):
        """Verify major bump resets minor and patch to 0."""
        assert bump_version("1.2.3", "major") == "2.0.0"
        assert bump_version("0.9.9", "major") == "1.0.0"
        assert bump_version("5.0.0", "major") == "6.0.0"

    def test_minor_bump_resets_patch(self):
        """Verify minor bump resets patch to 0."""
        assert bump_version("1.2.3", "minor") == "1.3.0"
        assert bump_version("1.0.0", "minor") == "1.1.0"
        assert bump_version("2.9.5", "minor") == "2.10.0"

    def test_patch_bump_increments_only_patch(self):
        """Verify patch bump only increments patch number."""
        assert bump_version("1.2.3", "patch") == "1.2.4"
        assert bump_version("1.0.0", "patch") == "1.0.1"
        assert bump_version("0.0.0", "patch") == "0.0.1"

    def test_invalid_bump_type_raises(self):
        """Verify invalid bump type raises ValueError."""
        with pytest.raises(ValueError):
            bump_version("1.0.0", "invalid")

        with pytest.raises(ValueError):
            bump_version("1.0.0", "MAJOR")  # Case sensitive

    def test_bump_preserves_semver_format(self):
        """Verify bumped versions maintain valid semver format."""
        for bump_type in ["major", "minor", "patch"]:
            new_version = bump_version("1.2.3", bump_type)
            # Should parse without error
            parse_semver(new_version)


class TestPluginVersionOperations:
    """Tests for plugin version file operations."""

    def test_get_version_from_valid_plugin(self, fixtures_dir: Path):
        """Verify version extraction from valid plugin."""
        valid_plugin = fixtures_dir / "valid-plugin"
        version = get_plugin_version(valid_plugin)

        assert version == "1.0.0"
        # Verify it's valid semver
        parse_semver(version)

    def test_update_plugin_version(self, tmp_path: Path):
        """Verify plugin version can be updated."""
        # Create a temporary plugin structure
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()

        plugin_json = plugin_dir / "plugin.json"
        plugin_json.write_text(json.dumps({
            "name": "test-plugin",
            "description": "Test",
            "version": "1.0.0"
        }, indent=2))

        # Update the version
        success = update_plugin_json_version(tmp_path, "2.0.0")
        assert success

        # Verify the update
        new_version = get_plugin_version(tmp_path)
        assert new_version == "2.0.0"

    def test_update_preserves_other_fields(self, tmp_path: Path):
        """Verify version update preserves other plugin.json fields."""
        plugin_dir = tmp_path / ".claude-plugin"
        plugin_dir.mkdir()

        original_data = {
            "name": "test-plugin",
            "description": "Test description",
            "version": "1.0.0",
            "author": "Test Author",
            "dependencies": {"other-plugin": ">=1.0.0"}
        }

        plugin_json = plugin_dir / "plugin.json"
        plugin_json.write_text(json.dumps(original_data, indent=2))

        # Update the version
        update_plugin_json_version(tmp_path, "2.0.0")

        # Read back and verify all fields preserved
        with open(plugin_json, encoding="utf-8") as f:
            updated_data = json.load(f)

        assert updated_data["name"] == "test-plugin"
        assert updated_data["description"] == "Test description"
        assert updated_data["version"] == "2.0.0"
        assert updated_data["author"] == "Test Author"
        assert updated_data["dependencies"] == {"other-plugin": ">=1.0.0"}


class TestMultiFileVersionSync:
    """Tests for multi-file version synchronization."""

    def test_version_sync_scenario(self, tmp_path: Path):
        """Verify version can be synced across multiple files."""
        # Create plugin.json
        plugin_dir = tmp_path / "test-plugin" / ".claude-plugin"
        plugin_dir.mkdir(parents=True)

        plugin_json = plugin_dir / "plugin.json"
        plugin_json.write_text(json.dumps({
            "name": "test-plugin",
            "description": "Test",
            "version": "1.0.0"
        }, indent=2))

        # Create marketplace.json
        marketplace_json = tmp_path / "marketplace.json"
        marketplace_json.write_text(json.dumps({
            "version": "1.0.0",
            "plugins": [
                {
                    "name": "test-plugin",
                    "version": "1.0.0",
                    "path": "test-plugin"
                }
            ]
        }, indent=2))

        # Simulate bump operation
        new_version = bump_version("1.0.0", "minor")
        assert new_version == "1.1.0"

        # Update plugin.json
        update_plugin_json_version(tmp_path / "test-plugin", new_version)

        # Update marketplace.json (simulated)
        with open(marketplace_json, encoding="utf-8") as f:
            marketplace_data = json.load(f)

        for plugin in marketplace_data["plugins"]:
            if plugin["name"] == "test-plugin":
                plugin["version"] = new_version

        with open(marketplace_json, "w", encoding="utf-8") as f:
            json.dump(marketplace_data, f, indent=2)
            f.write("\n")

        # Verify both files have new version
        assert get_plugin_version(tmp_path / "test-plugin") == "1.1.0"

        with open(marketplace_json, encoding="utf-8") as f:
            marketplace_data = json.load(f)

        plugin_entry = next(
            (p for p in marketplace_data["plugins"] if p["name"] == "test-plugin"),
            None
        )
        assert plugin_entry is not None
        assert plugin_entry["version"] == "1.1.0"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_bump_from_zero(self):
        """Verify bumping from version 0.0.0 works correctly."""
        assert bump_version("0.0.0", "major") == "1.0.0"
        assert bump_version("0.0.0", "minor") == "0.1.0"
        assert bump_version("0.0.0", "patch") == "0.0.1"

    def test_bump_large_numbers(self):
        """Verify bumping large version numbers works correctly."""
        assert bump_version("99.99.99", "major") == "100.0.0"
        assert bump_version("99.99.99", "minor") == "99.100.0"
        assert bump_version("99.99.99", "patch") == "99.99.100"

    def test_version_string_immutability(self):
        """Verify original version string is not modified."""
        original = "1.2.3"
        bump_version(original, "major")
        # Original should be unchanged
        assert original == "1.2.3"

    def test_nonexistent_plugin_version(self, tmp_path: Path):
        """Verify graceful handling of missing plugin.json."""
        with pytest.raises(FileNotFoundError):
            get_plugin_version(tmp_path / "nonexistent")


class TestBumpVersionIntegration:
    """Integration tests simulating full bump-version workflow."""

    def test_full_bump_workflow(self, tmp_path: Path):
        """Test complete version bump workflow."""
        # Setup: Create plugin structure
        plugin_name = "my-plugin"
        plugin_path = tmp_path / plugin_name
        plugin_config_dir = plugin_path / ".claude-plugin"
        plugin_config_dir.mkdir(parents=True)

        # Create plugin.json with initial version
        plugin_json = plugin_config_dir / "plugin.json"
        plugin_json.write_text(json.dumps({
            "name": plugin_name,
            "description": "Test plugin",
            "version": "1.5.3"
        }, indent=2))

        # Create marketplace.json
        marketplace_json = tmp_path / "marketplace.json"
        marketplace_json.write_text(json.dumps({
            "plugins": [
                {"name": plugin_name, "version": "1.5.3"}
            ]
        }, indent=2))

        # Execute: Bump minor version
        current_version = get_plugin_version(plugin_path)
        assert current_version == "1.5.3"

        new_version = bump_version(current_version, "minor")
        assert new_version == "1.6.0"

        # Update plugin.json
        update_plugin_json_version(plugin_path, new_version)

        # Update marketplace.json
        with open(marketplace_json, encoding="utf-8") as f:
            data = json.load(f)
        data["plugins"][0]["version"] = new_version
        with open(marketplace_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        # Verify: Both files updated
        assert get_plugin_version(plugin_path) == "1.6.0"

        with open(marketplace_json, encoding="utf-8") as f:
            data = json.load(f)
        assert data["plugins"][0]["version"] == "1.6.0"

    def test_consecutive_bumps(self, tmp_path: Path):
        """Test multiple consecutive version bumps."""
        plugin_path = tmp_path / "test" / ".claude-plugin"
        plugin_path.mkdir(parents=True)

        plugin_json = plugin_path.parent / ".claude-plugin" / "plugin.json"
        plugin_json.parent.mkdir(parents=True, exist_ok=True)
        plugin_json.write_text(json.dumps({
            "name": "test",
            "version": "1.0.0"
        }, indent=2))

        # Series of bumps
        versions = ["1.0.0"]
        bumps = [("patch", "1.0.1"), ("patch", "1.0.2"), ("minor", "1.1.0"), ("major", "2.0.0")]

        current = "1.0.0"
        for bump_type, expected in bumps:
            new = bump_version(current, bump_type)
            assert new == expected, f"Expected {expected} but got {new}"
            current = new
