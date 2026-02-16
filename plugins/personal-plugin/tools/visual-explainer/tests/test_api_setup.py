"""Tests for api_setup module.

Tests the API key setup wizard including:
- Key presence checking
- Key format validation
- Google key validation (async)
- Anthropic key validation
- .env file creation
- .gitignore update
- Interactive detection
- Display functions (with mocked console)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from visual_explainer.api_setup import (
    _update_gitignore,
    check_api_keys,
    create_env_file,
    is_interactive,
    supports_unicode,
    validate_anthropic_key,
    validate_google_key,
)

# ---------------------------------------------------------------------------
# is_interactive Tests
# ---------------------------------------------------------------------------


class TestIsInteractive:
    """Tests for is_interactive function."""

    def test_returns_bool(self):
        """Test is_interactive returns a boolean."""
        result = is_interactive()
        assert isinstance(result, bool)

    def test_non_tty_not_interactive(self, monkeypatch):
        """Test that non-TTY stdin is not interactive."""
        import sys

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = False
        monkeypatch.setattr(sys, "stdin", mock_stdin)

        assert not is_interactive()


# ---------------------------------------------------------------------------
# supports_unicode Tests
# ---------------------------------------------------------------------------


class TestSupportsUnicode:
    """Tests for supports_unicode function."""

    def test_returns_bool(self):
        """Test supports_unicode returns a boolean."""
        result = supports_unicode()
        assert isinstance(result, bool)

    def test_with_wt_session(self, monkeypatch):
        """Test Windows Terminal detection via WT_SESSION."""
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("WT_SESSION", "some-session-id")
        assert supports_unicode()

    def test_with_vscode(self, monkeypatch):
        """Test VS Code terminal detection."""
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.delenv("WT_SESSION", raising=False)
        monkeypatch.delenv("ConEmuANSI", raising=False)
        monkeypatch.setenv("TERM_PROGRAM", "vscode")
        assert supports_unicode()


# ---------------------------------------------------------------------------
# check_api_keys Tests
# ---------------------------------------------------------------------------


class TestCheckApiKeys:
    """Tests for check_api_keys function."""

    def test_both_keys_present(self, monkeypatch):
        """Test both keys present and valid format."""
        monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy" + "x" * 30)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-" + "x" * 30)

        result = check_api_keys()

        assert result["google"]["present"] is True
        assert result["anthropic"]["present"] is True

    def test_no_keys_present(self, mock_env_without_api_keys):
        """Test no keys in environment."""
        result = check_api_keys()

        assert result["google"]["present"] is False
        assert result["anthropic"]["present"] is False

    def test_google_key_too_short(self, monkeypatch):
        """Test Google key that's too short."""
        monkeypatch.setenv("GOOGLE_API_KEY", "short")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = check_api_keys()

        assert result["google"]["present"] is True
        assert result["google"]["valid"] is False
        assert "too short" in result["google"]["error"].lower()

    def test_anthropic_key_wrong_prefix(self, monkeypatch):
        """Test Anthropic key with wrong prefix."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "wrong-prefix-key-value")

        result = check_api_keys()

        assert result["anthropic"]["present"] is True
        assert result["anthropic"]["valid"] is False
        assert "sk-ant-" in result["anthropic"]["error"]

    def test_google_key_empty(self, monkeypatch):
        """Test empty Google API key."""
        monkeypatch.setenv("GOOGLE_API_KEY", "")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = check_api_keys()
        assert result["google"]["present"] is False

    def test_anthropic_key_valid_format(self, monkeypatch):
        """Test Anthropic key with valid sk-ant- prefix."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-value")

        result = check_api_keys()
        assert result["anthropic"]["present"] is True
        assert result["anthropic"]["valid"] is None  # Not validated yet
        assert result["anthropic"]["error"] is None

    def test_keys_stripped(self, monkeypatch):
        """Test that keys are stripped of whitespace."""
        monkeypatch.setenv("GOOGLE_API_KEY", "  AIzaSy" + "x" * 30 + "  ")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = check_api_keys()
        assert result["google"]["present"] is True


# ---------------------------------------------------------------------------
# validate_google_key Tests
# ---------------------------------------------------------------------------


class TestValidateGoogleKey:
    """Tests for validate_google_key function."""

    async def test_empty_key_invalid(self):
        """Test empty key returns invalid."""
        valid, error = await validate_google_key("")
        assert not valid
        assert "too short" in error.lower()

    async def test_short_key_invalid(self):
        """Test short key returns invalid."""
        valid, error = await validate_google_key("short")
        assert not valid

    async def test_valid_key_success(self):
        """Test valid key returns success via API check."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("visual_explainer.api_setup.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            valid, error = await validate_google_key("AIzaSy" + "x" * 30)
            assert valid
            assert error is None

    async def test_forbidden_key(self):
        """Test 403 response returns invalid."""
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("visual_explainer.api_setup.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            valid, error = await validate_google_key("AIzaSy" + "x" * 30)
            assert not valid
            assert "invalid" in error.lower() or "not enabled" in error.lower()

    async def test_bad_request_key(self):
        """Test 400 response returns invalid format."""
        mock_response = MagicMock()
        mock_response.status_code = 400

        with patch("visual_explainer.api_setup.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            valid, error = await validate_google_key("AIzaSy" + "x" * 30)
            assert not valid

    async def test_timeout_error(self):
        """Test timeout returns invalid with message."""
        import httpx

        with patch("visual_explainer.api_setup.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("timed out")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            valid, error = await validate_google_key("AIzaSy" + "x" * 30)
            assert not valid
            assert "timed out" in error.lower()

    async def test_connection_error(self):
        """Test connection error returns invalid."""
        import httpx

        with patch("visual_explainer.api_setup.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("cannot connect")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            valid, error = await validate_google_key("AIzaSy" + "x" * 30)
            assert not valid
            assert "connect" in error.lower()

    async def test_unexpected_status_code(self):
        """Test unexpected status code returns invalid."""
        mock_response = MagicMock()
        mock_response.status_code = 503

        with patch("visual_explainer.api_setup.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            valid, error = await validate_google_key("AIzaSy" + "x" * 30)
            assert not valid
            assert "503" in error


# ---------------------------------------------------------------------------
# validate_anthropic_key Tests
# ---------------------------------------------------------------------------


class TestValidateAnthropicKey:
    """Tests for validate_anthropic_key function."""

    def test_empty_key_invalid(self):
        """Test empty key returns invalid."""
        valid, error = validate_anthropic_key("")
        assert not valid
        assert "format" in error.lower()

    def test_wrong_prefix_invalid(self):
        """Test wrong prefix returns invalid."""
        valid, error = validate_anthropic_key("wrong-prefix-key")
        assert not valid
        assert "sk-ant-" in error

    def test_valid_key_success(self):
        """Test valid key with successful API call."""
        with patch("visual_explainer.api_setup.anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.Anthropic.return_value = mock_client

            valid, error = validate_anthropic_key("sk-ant-api03-testkey123")
            assert valid
            assert error is None

    def test_auth_error(self):
        """Test authentication error."""
        import anthropic as anthropic_real

        with patch("visual_explainer.api_setup.anthropic") as mock_anthropic_mod:
            mock_client = MagicMock()
            mock_anthropic_mod.Anthropic.return_value = mock_client
            # Map all exception classes so except blocks work
            mock_anthropic_mod.AuthenticationError = anthropic_real.AuthenticationError
            mock_anthropic_mod.PermissionDeniedError = anthropic_real.PermissionDeniedError
            mock_anthropic_mod.RateLimitError = anthropic_real.RateLimitError
            mock_anthropic_mod.APIConnectionError = anthropic_real.APIConnectionError
            mock_client.messages.create.side_effect = anthropic_real.AuthenticationError(
                message="Invalid API key",
                response=MagicMock(status_code=401),
                body=None,
            )

            valid, error = validate_anthropic_key("sk-ant-api03-invalid")
            assert not valid
            assert "authentication" in error.lower()

    def test_rate_limit_means_valid(self):
        """Test rate limit response means key is valid."""
        import anthropic as anthropic_real

        with patch("visual_explainer.api_setup.anthropic") as mock_anthropic_mod:
            mock_client = MagicMock()
            mock_anthropic_mod.Anthropic.return_value = mock_client
            # Map ALL exception classes to real exceptions so except blocks work
            mock_anthropic_mod.AuthenticationError = anthropic_real.AuthenticationError
            mock_anthropic_mod.PermissionDeniedError = anthropic_real.PermissionDeniedError
            mock_anthropic_mod.RateLimitError = anthropic_real.RateLimitError
            mock_anthropic_mod.APIConnectionError = anthropic_real.APIConnectionError
            mock_client.messages.create.side_effect = anthropic_real.RateLimitError(
                message="Rate limited",
                response=MagicMock(status_code=429),
                body=None,
            )

            valid, error = validate_anthropic_key("sk-ant-api03-testkey")
            assert valid


# ---------------------------------------------------------------------------
# create_env_file Tests
# ---------------------------------------------------------------------------


class TestCreateEnvFile:
    """Tests for create_env_file function."""

    def test_create_with_both_keys(self, tmp_path):
        """Test creating .env with both keys."""
        path = create_env_file("google-key-123", "sk-ant-key-456", tmp_path / ".env")
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "GOOGLE_API_KEY=google-key-123" in content
        assert "ANTHROPIC_API_KEY=sk-ant-key-456" in content

    def test_create_with_google_only(self, tmp_path):
        """Test creating .env with only Google key."""
        path = create_env_file("google-key", None, tmp_path / ".env")
        content = path.read_text(encoding="utf-8")
        assert "GOOGLE_API_KEY=google-key" in content
        assert "# ANTHROPIC_API_KEY=" in content

    def test_create_with_anthropic_only(self, tmp_path):
        """Test creating .env with only Anthropic key."""
        path = create_env_file(None, "sk-ant-key", tmp_path / ".env")
        content = path.read_text(encoding="utf-8")
        assert "# GOOGLE_API_KEY=" in content
        assert "ANTHROPIC_API_KEY=sk-ant-key" in content

    def test_creates_gitignore(self, tmp_path):
        """Test .env file creation also creates/updates .gitignore."""
        create_env_file("key", "key2", tmp_path / ".env")
        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert ".env" in gitignore.read_text(encoding="utf-8")

    def test_includes_header(self, tmp_path):
        """Test .env file includes header comment."""
        path = create_env_file("key", "key2", tmp_path / ".env")
        content = path.read_text(encoding="utf-8")
        assert "Visual Explainer" in content
        assert "Generated" in content


# ---------------------------------------------------------------------------
# _update_gitignore Tests
# ---------------------------------------------------------------------------


class TestUpdateGitignore:
    """Tests for _update_gitignore function."""

    def test_creates_gitignore_if_missing(self, tmp_path):
        """Test creates .gitignore if it doesn't exist."""
        _update_gitignore(tmp_path)
        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        assert ".env" in gitignore.read_text(encoding="utf-8")

    def test_adds_env_to_existing(self, tmp_path):
        """Test adds .env to existing .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n", encoding="utf-8")

        _update_gitignore(tmp_path)

        content = gitignore.read_text(encoding="utf-8")
        assert ".env" in content
        assert "*.pyc" in content

    def test_no_duplicate_if_already_present(self, tmp_path):
        """Test doesn't add .env if already in .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n.env\n", encoding="utf-8")

        _update_gitignore(tmp_path)

        content = gitignore.read_text(encoding="utf-8")
        assert content.count(".env") == 1

    def test_detects_star_env_pattern(self, tmp_path):
        """Test detects *.env pattern as covering .env."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.env\n", encoding="utf-8")

        _update_gitignore(tmp_path)

        content = gitignore.read_text(encoding="utf-8")
        # Should not add another .env since *.env covers it
        lines = [line.strip() for line in content.strip().split("\n")]
        assert "*.env" in lines


# ---------------------------------------------------------------------------
# handle_setup_keys_flag Tests
# ---------------------------------------------------------------------------


class TestHandleSetupKeysFlag:
    """Tests for handle_setup_keys_flag function."""

    def test_non_interactive_returns_1(self):
        """Test non-interactive mode returns exit code 1."""
        from visual_explainer.api_setup import handle_setup_keys_flag

        with patch("visual_explainer.api_setup.is_interactive", return_value=False):
            result = handle_setup_keys_flag()
        assert result == 1


# ---------------------------------------------------------------------------
# check_keys_and_prompt_if_missing Tests
# ---------------------------------------------------------------------------


class TestCheckKeysAndPrompt:
    """Tests for check_keys_and_prompt_if_missing function."""

    def test_keys_present_returns_true(self, monkeypatch):
        """Test returns True when both keys present."""
        monkeypatch.setenv("GOOGLE_API_KEY", "g" * 30)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-" + "x" * 30)

        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        result = check_keys_and_prompt_if_missing()
        assert result is True

    def test_keys_missing_non_interactive(self, monkeypatch):
        """Test returns False when keys missing in non-interactive mode."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        # Patch dotenv.load_dotenv so it doesn't reload keys from .env files
        with patch("dotenv.load_dotenv"):
            with patch("visual_explainer.api_setup.is_interactive", return_value=False):
                result = check_keys_and_prompt_if_missing()
        assert result is False
