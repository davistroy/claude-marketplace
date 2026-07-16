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


# ---------------------------------------------------------------------------
# supports_unicode Extra Branch Tests
# ---------------------------------------------------------------------------


class TestSupportsUnicodeExtra:
    """Additional branch coverage for supports_unicode on Windows."""

    def test_with_conemu(self, monkeypatch):
        """Test ConEmuANSI env var is detected as Unicode-capable."""
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.delenv("WT_SESSION", raising=False)
        monkeypatch.setenv("ConEmuANSI", "ON")

        assert supports_unicode() is True

    def test_ctypes_fallback_returns_false_on_non_windows_ctypes(self, monkeypatch):
        """Test the ctypes.windll fallback path (AttributeError caught) returns False."""
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.delenv("WT_SESSION", raising=False)
        monkeypatch.delenv("ConEmuANSI", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)

        # ctypes.windll does not exist on this (non-Windows) interpreter, so the
        # function's internal try/except AttributeError path is exercised.
        assert supports_unicode() is False

    def test_windows_codepage_65001_detected(self, monkeypatch):
        """Test a fake win32 ctypes.windll reporting code page 65001 is Unicode-capable."""
        import ctypes

        from visual_explainer.api_setup import supports_unicode

        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.delenv("WT_SESSION", raising=False)
        monkeypatch.delenv("ConEmuANSI", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)

        fake_kernel32 = MagicMock()
        fake_kernel32.GetConsoleOutputCP.return_value = 65001
        fake_windll = MagicMock()
        fake_windll.kernel32 = fake_kernel32
        monkeypatch.setattr(ctypes, "windll", fake_windll, raising=False)

        assert supports_unicode() is True

    def test_windows_codepage_not_65001_returns_false(self, monkeypatch):
        """Test a fake win32 ctypes.windll reporting a non-UTF-8 code page is not Unicode-capable."""
        import ctypes

        from visual_explainer.api_setup import supports_unicode

        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.delenv("WT_SESSION", raising=False)
        monkeypatch.delenv("ConEmuANSI", raising=False)
        monkeypatch.delenv("TERM_PROGRAM", raising=False)

        fake_kernel32 = MagicMock()
        fake_kernel32.GetConsoleOutputCP.return_value = 1252  # Windows-1252, not UTF-8
        fake_windll = MagicMock()
        fake_windll.kernel32 = fake_kernel32
        monkeypatch.setattr(ctypes, "windll", fake_windll, raising=False)

        assert supports_unicode() is False


# ---------------------------------------------------------------------------
# get_console Tests
# ---------------------------------------------------------------------------


class TestGetConsole:
    """Tests for get_console (Console singleton creation)."""

    def test_creates_console_when_none_non_windows(self, monkeypatch):
        """Test a new Console is created on non-Windows platforms."""
        from visual_explainer import api_setup

        monkeypatch.setattr(api_setup, "_console", None)
        monkeypatch.setattr(api_setup, "RICH_AVAILABLE", True)
        monkeypatch.setattr(api_setup.sys, "platform", "linux")

        mock_instance = MagicMock()
        mock_console_cls = MagicMock(return_value=mock_instance)
        monkeypatch.setattr(api_setup, "Console", mock_console_cls)

        result = api_setup.get_console()

        assert result is mock_instance
        mock_console_cls.assert_called_once()
        _, kwargs = mock_console_cls.call_args
        assert "legacy_windows" not in kwargs

    def test_creates_console_windows_platform(self, monkeypatch):
        """Test Console is created with legacy_windows kwarg on win32."""
        from visual_explainer import api_setup

        monkeypatch.setattr(api_setup, "_console", None)
        monkeypatch.setattr(api_setup, "RICH_AVAILABLE", True)
        monkeypatch.setattr(api_setup.sys, "platform", "win32")
        monkeypatch.setattr(api_setup, "is_interactive", lambda: True)
        monkeypatch.setattr(api_setup, "supports_unicode", lambda: True)

        mock_instance = MagicMock()
        mock_console_cls = MagicMock(return_value=mock_instance)
        monkeypatch.setattr(api_setup, "Console", mock_console_cls)

        result = api_setup.get_console()

        assert result is mock_instance
        _, kwargs = mock_console_cls.call_args
        assert kwargs["legacy_windows"] is False
        assert kwargs["force_terminal"] is True

    def test_returns_cached_console(self, monkeypatch):
        """Test an already-created console is reused without recreating."""
        from visual_explainer import api_setup

        sentinel = MagicMock()
        monkeypatch.setattr(api_setup, "_console", sentinel)

        result = api_setup.get_console()
        assert result is sentinel

    def test_raises_when_rich_unavailable(self, monkeypatch):
        """Test RuntimeError is raised when Rich is not installed."""
        import pytest

        from visual_explainer import api_setup

        monkeypatch.setattr(api_setup, "_console", None)
        monkeypatch.setattr(api_setup, "RICH_AVAILABLE", False)

        with pytest.raises(RuntimeError, match="Rich library not available"):
            api_setup.get_console()


# ---------------------------------------------------------------------------
# validate_google_key Extra Branch Tests
# ---------------------------------------------------------------------------


class TestValidateGoogleKeyExtra:
    """Additional branch coverage for validate_google_key."""

    async def test_generic_exception_returns_invalid(self):
        """Test a generic (non-httpx) exception is caught and reported."""
        with patch("visual_explainer.api_setup.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = ValueError("boom")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            valid, error = await validate_google_key("AIzaSy" + "x" * 30)
            assert not valid
            assert "validation error" in error.lower()
            assert "boom" in error


# ---------------------------------------------------------------------------
# validate_anthropic_key Extra Branch Tests
# ---------------------------------------------------------------------------


class TestValidateAnthropicKeyExtra:
    """Additional branch coverage for validate_anthropic_key."""

    def test_package_unavailable_valid_prefix(self, monkeypatch):
        """Test format-only check succeeds when anthropic package is not installed."""
        from visual_explainer import api_setup

        monkeypatch.setattr(api_setup, "ANTHROPIC_AVAILABLE", False)

        valid, error = api_setup.validate_anthropic_key("sk-ant-abc123")
        assert valid
        assert error is None

    def test_package_unavailable_invalid_key(self, monkeypatch):
        """Test format-only check fails for a non-matching prefix."""
        from visual_explainer import api_setup

        monkeypatch.setattr(api_setup, "ANTHROPIC_AVAILABLE", False)

        valid, error = api_setup.validate_anthropic_key("no-prefix-key")
        assert not valid
        assert "sk-ant-" in error

    def test_permission_denied_error(self):
        """Test PermissionDeniedError is caught and reported."""
        import anthropic as anthropic_real

        with patch("visual_explainer.api_setup.anthropic") as mock_anthropic_mod:
            mock_client = MagicMock()
            mock_anthropic_mod.Anthropic.return_value = mock_client
            mock_anthropic_mod.AuthenticationError = anthropic_real.AuthenticationError
            mock_anthropic_mod.PermissionDeniedError = anthropic_real.PermissionDeniedError
            mock_anthropic_mod.RateLimitError = anthropic_real.RateLimitError
            mock_anthropic_mod.APIConnectionError = anthropic_real.APIConnectionError
            mock_client.messages.create.side_effect = anthropic_real.PermissionDeniedError(
                "no permission",
                response=MagicMock(status_code=403),
                body=None,
            )

            valid, error = validate_anthropic_key("sk-ant-api03-testkey")
            assert not valid
            assert "permission denied" in error.lower()

    def test_api_connection_error(self):
        """Test APIConnectionError is caught and reported."""
        import anthropic as anthropic_real

        with patch("visual_explainer.api_setup.anthropic") as mock_anthropic_mod:
            mock_client = MagicMock()
            mock_anthropic_mod.Anthropic.return_value = mock_client
            mock_anthropic_mod.AuthenticationError = anthropic_real.AuthenticationError
            mock_anthropic_mod.PermissionDeniedError = anthropic_real.PermissionDeniedError
            mock_anthropic_mod.RateLimitError = anthropic_real.RateLimitError
            mock_anthropic_mod.APIConnectionError = anthropic_real.APIConnectionError
            mock_client.messages.create.side_effect = anthropic_real.APIConnectionError(
                message="no network", request=MagicMock()
            )

            valid, error = validate_anthropic_key("sk-ant-api03-testkey")
            assert not valid
            assert "connect" in error.lower()

    def test_generic_exception_with_authentication_keyword(self):
        """Test a generic exception mentioning 'authentication' is reported invalid."""
        with patch("visual_explainer.api_setup.anthropic") as mock_anthropic_mod:
            mock_client = MagicMock()
            mock_anthropic_mod.Anthropic.return_value = mock_client
            mock_anthropic_mod.AuthenticationError = type("AuthenticationError", (Exception,), {})
            mock_anthropic_mod.PermissionDeniedError = type(
                "PermissionDeniedError", (Exception,), {}
            )
            mock_anthropic_mod.RateLimitError = type("RateLimitError", (Exception,), {})
            mock_anthropic_mod.APIConnectionError = type("APIConnectionError", (Exception,), {})
            mock_client.messages.create.side_effect = RuntimeError("Authentication issue detected")

            valid, error = validate_anthropic_key("sk-ant-api03-testkey")
            assert not valid
            assert "authentication error" in error.lower()

    def test_generic_exception_unknown_assumed_valid(self):
        """Test an unrecognized generic exception falls back to assuming key is valid."""
        with patch("visual_explainer.api_setup.anthropic") as mock_anthropic_mod:
            mock_client = MagicMock()
            mock_anthropic_mod.Anthropic.return_value = mock_client
            mock_anthropic_mod.AuthenticationError = type("AuthenticationError", (Exception,), {})
            mock_anthropic_mod.PermissionDeniedError = type(
                "PermissionDeniedError", (Exception,), {}
            )
            mock_anthropic_mod.RateLimitError = type("RateLimitError", (Exception,), {})
            mock_anthropic_mod.APIConnectionError = type("APIConnectionError", (Exception,), {})
            mock_client.messages.create.side_effect = RuntimeError("Something else broke")

            valid, error = validate_anthropic_key("sk-ant-api03-testkey")
            assert valid


# ---------------------------------------------------------------------------
# create_env_file Extra Branch Tests
# ---------------------------------------------------------------------------


class TestCreateEnvFileExtra:
    """Additional branch coverage for create_env_file."""

    def test_default_path_uses_cwd(self, monkeypatch, tmp_path):
        """Test omitting `path` defaults to cwd/.env."""
        monkeypatch.chdir(tmp_path)

        result_path = create_env_file("g-key", "sk-ant-key")

        assert result_path.resolve() == (tmp_path / ".env").resolve()
        assert result_path.exists()
        assert "GOOGLE_API_KEY=g-key" in result_path.read_text(encoding="utf-8")

    def test_chmod_failure_is_ignored(self, monkeypatch, tmp_path):
        """Test OSError from os.chmod is swallowed and file is still created."""
        monkeypatch.setattr(
            "visual_explainer.api_setup.os.chmod",
            MagicMock(side_effect=OSError("no permission")),
        )

        path = create_env_file("g-key", "a-key", tmp_path / ".env")

        assert path.exists()
        assert "GOOGLE_API_KEY=g-key" in path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# display_header Tests
# ---------------------------------------------------------------------------


class TestDisplayHeader:
    """Tests for display_header."""

    def test_prints_panel_with_title(self, monkeypatch):
        """Test display_header prints a panel with the expected title."""
        from visual_explainer.api_setup import display_header

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        display_header()

        mock_console.print.assert_called_once()
        panel_arg = mock_console.print.call_args[0][0]
        assert "API Key Setup Required" in panel_arg.title


# ---------------------------------------------------------------------------
# display_key_status Tests
# ---------------------------------------------------------------------------


class TestDisplayKeyStatus:
    """Tests for display_key_status covering all status branches."""

    def test_present_and_configured(self, monkeypatch):
        """Test a present, valid (or unchecked) key prints 'configured'."""
        from visual_explainer.api_setup import display_key_status

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        status = {
            "google": {"present": True, "valid": None, "error": None},
        }
        display_key_status(status)

        printed = " ".join(str(call.args[0]) for call in mock_console.print.call_args_list)
        assert "GOOGLE_API_KEY" in printed
        assert "configured" in printed

    def test_present_invalid_with_error_message(self, monkeypatch):
        """Test a present but invalid key with an error message displays it."""
        from visual_explainer.api_setup import display_key_status

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        status = {
            "anthropic": {"present": True, "valid": False, "error": "bad format"},
        }
        display_key_status(status)

        printed = " ".join(str(call.args[0]) for call in mock_console.print.call_args_list)
        assert "ANTHROPIC_API_KEY" in printed
        assert "invalid - bad format" in printed

    def test_present_invalid_without_error_message(self, monkeypatch):
        """Test a present but invalid key with no error message falls back to generic text."""
        from visual_explainer.api_setup import display_key_status

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        status = {
            "google": {"present": True, "valid": False, "error": None},
        }
        display_key_status(status)

        printed = " ".join(str(call.args[0]) for call in mock_console.print.call_args_list)
        assert "invalid format" in printed

    def test_not_present(self, monkeypatch):
        """Test a missing key prints 'not found'."""
        from visual_explainer.api_setup import display_key_status

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        status = {
            "anthropic": {"present": False, "valid": None, "error": None},
        }
        display_key_status(status)

        printed = " ".join(str(call.args[0]) for call in mock_console.print.call_args_list)
        assert "not found" in printed


# ---------------------------------------------------------------------------
# display_google_instructions / display_anthropic_instructions Tests
# ---------------------------------------------------------------------------


class TestDisplayGoogleInstructions:
    """Tests for display_google_instructions."""

    def test_prints_panel_with_instructions(self, monkeypatch):
        """Test the Google instructions panel is printed with expected content."""
        from visual_explainer.api_setup import display_google_instructions

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        display_google_instructions()

        mock_console.print.assert_called_once()
        panel_arg = mock_console.print.call_args[0][0]
        assert "Google Gemini API Key" in panel_arg.renderable
        assert "aistudio.google.com" in panel_arg.renderable


class TestDisplayAnthropicInstructions:
    """Tests for display_anthropic_instructions."""

    def test_prints_panel_with_instructions(self, monkeypatch):
        """Test the Anthropic instructions panel is printed with expected content."""
        from visual_explainer.api_setup import display_anthropic_instructions

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        display_anthropic_instructions()

        mock_console.print.assert_called_once()
        panel_arg = mock_console.print.call_args[0][0]
        assert "Anthropic API Key" in panel_arg.renderable
        assert "console.anthropic.com" in panel_arg.renderable


# ---------------------------------------------------------------------------
# display_cost_information Tests
# ---------------------------------------------------------------------------


class TestDisplayCostInformation:
    """Tests for display_cost_information."""

    def test_interactive_waits_for_input(self, monkeypatch):
        """Test interactive mode prints the table/scenarios and waits for Enter."""
        from visual_explainer.api_setup import display_cost_information

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)
        monkeypatch.setattr("visual_explainer.api_setup.is_interactive", lambda: True)
        mock_input = MagicMock(return_value="")
        monkeypatch.setattr("builtins.input", mock_input)

        display_cost_information()

        mock_input.assert_called_once()
        assert mock_console.print.call_count >= 2

    def test_non_interactive_skips_input(self, monkeypatch):
        """Test non-interactive mode does not block on input()."""
        from visual_explainer.api_setup import display_cost_information

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)
        monkeypatch.setattr("visual_explainer.api_setup.is_interactive", lambda: False)
        mock_input = MagicMock()
        monkeypatch.setattr("builtins.input", mock_input)

        display_cost_information()

        mock_input.assert_not_called()


# ---------------------------------------------------------------------------
# display_env_file_created Tests
# ---------------------------------------------------------------------------


class TestDisplayEnvFileCreated:
    """Tests for display_env_file_created covering key-masking branches."""

    def test_both_keys_masked_in_preview(self, monkeypatch, tmp_path):
        """Test both keys are present and masked in the preview panel."""
        from visual_explainer.api_setup import display_env_file_created

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        display_env_file_created(tmp_path / ".env", "google-key-123456", "sk-ant-api03-abcdef")

        assert mock_console.print.call_count == 3
        panel_arg = mock_console.print.call_args_list[0].args[0]
        assert "GOOGLE_API_KEY=google-key..." in panel_arg.renderable
        assert "ANTHROPIC_API_KEY=sk-ant-api03..." in panel_arg.renderable
        summary = " ".join(str(call.args[0]) for call in mock_console.print.call_args_list[1:])
        assert "created successfully" in summary
        assert "gitignore" in summary.lower()

    def test_google_key_only(self, monkeypatch, tmp_path):
        """Test only the Google key is present; Anthropic shows commented placeholder."""
        from visual_explainer.api_setup import display_env_file_created

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        display_env_file_created(tmp_path / ".env", "google-key-123456", None)

        panel_arg = mock_console.print.call_args_list[0].args[0]
        assert "GOOGLE_API_KEY=google-key..." in panel_arg.renderable
        assert "# ANTHROPIC_API_KEY=..." in panel_arg.renderable

    def test_neither_key_present(self, monkeypatch, tmp_path):
        """Test neither key present shows both as commented placeholders."""
        from visual_explainer.api_setup import display_env_file_created

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)

        display_env_file_created(tmp_path / ".env", None, None)

        panel_arg = mock_console.print.call_args_list[0].args[0]
        assert "# GOOGLE_API_KEY=..." in panel_arg.renderable
        assert "# ANTHROPIC_API_KEY=..." in panel_arg.renderable


# ---------------------------------------------------------------------------
# prompt_for_key Tests
# ---------------------------------------------------------------------------


class TestPromptForKey:
    """Tests for prompt_for_key covering skip, retry, and validation paths."""

    def test_skip_immediately(self, monkeypatch):
        """Test typing 'skip' returns (None, True) without validating."""
        from visual_explainer.api_setup import prompt_for_key

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)
        monkeypatch.setattr("visual_explainer.api_setup.Prompt.ask", MagicMock(return_value="skip"))

        validator = MagicMock()
        key, skipped = prompt_for_key("Google API", validator, is_async=False)

        assert key is None
        assert skipped is True
        validator.assert_not_called()

    def test_empty_input_then_valid_key(self, monkeypatch):
        """Test blank input is rejected and looped past to a valid key."""
        from visual_explainer.api_setup import prompt_for_key

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)
        monkeypatch.setattr(
            "visual_explainer.api_setup.Prompt.ask",
            MagicMock(side_effect=["   ", "sk-ant-real-key"]),
        )
        validator = MagicMock(return_value=(True, None))

        key, skipped = prompt_for_key("Anthropic API", validator, is_async=False)

        assert key == "sk-ant-real-key"
        assert skipped is False
        validator.assert_called_once_with("sk-ant-real-key")

    def test_invalid_key_decline_retry(self, monkeypatch):
        """Test an invalid key followed by declining retry returns (None, True)."""
        from visual_explainer.api_setup import prompt_for_key

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)
        monkeypatch.setattr(
            "visual_explainer.api_setup.Prompt.ask",
            MagicMock(side_effect=["bad-key", "n"]),
        )
        validator = MagicMock(return_value=(False, "invalid"))

        key, skipped = prompt_for_key("Google API", validator, is_async=False)

        assert key is None
        assert skipped is True

    def test_invalid_key_retry_then_skip(self, monkeypatch):
        """Test an invalid key, accepting retry, then skipping on the next attempt."""
        from visual_explainer.api_setup import prompt_for_key

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)
        monkeypatch.setattr(
            "visual_explainer.api_setup.Prompt.ask",
            MagicMock(side_effect=["bad-key", "y", "skip"]),
        )
        validator = MagicMock(return_value=(False, "invalid"))

        key, skipped = prompt_for_key("Google API", validator, is_async=False)

        assert key is None
        assert skipped is True
        assert validator.call_count == 1

    def test_async_validator_success(self, monkeypatch):
        """Test the is_async=True path drives an async validator via asyncio.run."""
        from visual_explainer.api_setup import prompt_for_key

        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)
        good_key = "AIzaSy" + "x" * 30
        monkeypatch.setattr(
            "visual_explainer.api_setup.Prompt.ask", MagicMock(return_value=good_key)
        )

        async def fake_validator(key):
            return True, None

        key, skipped = prompt_for_key("Google API", fake_validator, is_async=True)

        assert key == good_key
        assert skipped is False


# ---------------------------------------------------------------------------
# run_setup_wizard Tests
# ---------------------------------------------------------------------------


class TestRunSetupWizard:
    """Tests for run_setup_wizard covering the main orchestration branches."""

    async def test_non_interactive_raises(self, monkeypatch):
        """Test RuntimeError is raised in non-interactive mode."""
        import pytest

        from visual_explainer.api_setup import run_setup_wizard

        monkeypatch.setattr("visual_explainer.api_setup.is_interactive", lambda: False)

        with pytest.raises(RuntimeError, match="non-interactive mode"):
            await run_setup_wizard()

    async def test_all_keys_present_returns_early(self, monkeypatch):
        """Test both keys already valid short-circuits without prompting."""
        from visual_explainer.api_setup import run_setup_wizard

        monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy" + "x" * 30)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-" + "x" * 30)
        monkeypatch.setattr("visual_explainer.api_setup.is_interactive", lambda: True)
        mock_console = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: mock_console)
        mock_display_header = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.display_header", mock_display_header)

        result = await run_setup_wizard()

        assert result["env_file_created"] is False
        assert result["env_file_path"] is None
        assert result["skipped"] is False
        assert result["google"]["present"] is True
        assert result["anthropic"]["present"] is True
        mock_display_header.assert_not_called()
        mock_console.print.assert_called_once()

    async def test_full_flow_creates_env_file(self, monkeypatch, tmp_path):
        """Test both keys obtained via prompt results in a created .env file."""
        from visual_explainer.api_setup import run_setup_wizard

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr("visual_explainer.api_setup.is_interactive", lambda: True)
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_header", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_key_status", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_google_instructions", MagicMock())
        monkeypatch.setattr(
            "visual_explainer.api_setup.display_anthropic_instructions", MagicMock()
        )
        monkeypatch.setattr("visual_explainer.api_setup.display_cost_information", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_env_file_created", MagicMock())

        env_path = tmp_path / ".env"
        mock_create_env_file = MagicMock(return_value=env_path)
        monkeypatch.setattr("visual_explainer.api_setup.create_env_file", mock_create_env_file)

        def fake_prompt_for_key(key_name, validator, is_async=False):
            if "Google" in key_name:
                return "google-key-val", False
            return "sk-ant-key-val", False

        monkeypatch.setattr("visual_explainer.api_setup.prompt_for_key", fake_prompt_for_key)

        result = await run_setup_wizard(env_path=env_path)

        assert result["env_file_created"] is True
        assert result["env_file_path"] == str(env_path)
        assert result["skipped"] is False
        assert result["google"]["present"] is True
        assert result["anthropic"]["present"] is True
        mock_create_env_file.assert_called_once_with("google-key-val", "sk-ant-key-val", env_path)

    async def test_both_keys_skipped_no_env_file(self, monkeypatch):
        """Test both keys skipped by the user results in no .env file creation."""
        from visual_explainer.api_setup import run_setup_wizard

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr("visual_explainer.api_setup.is_interactive", lambda: True)
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_header", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_key_status", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_google_instructions", MagicMock())
        monkeypatch.setattr(
            "visual_explainer.api_setup.display_anthropic_instructions", MagicMock()
        )
        mock_create_env_file = MagicMock()
        monkeypatch.setattr("visual_explainer.api_setup.create_env_file", mock_create_env_file)
        monkeypatch.setattr(
            "visual_explainer.api_setup.prompt_for_key",
            MagicMock(return_value=(None, True)),
        )

        result = await run_setup_wizard(force=True)

        assert result["env_file_created"] is False
        assert result["env_file_path"] is None
        assert result["skipped"] is True
        mock_create_env_file.assert_not_called()

    async def test_only_google_needed_skips_anthropic_prompt(self, monkeypatch, tmp_path):
        """Test only google_needed True hits the google branch, skipping anthropic prompting."""
        from visual_explainer.api_setup import run_setup_wizard

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-" + "x" * 30)
        monkeypatch.setattr("visual_explainer.api_setup.is_interactive", lambda: True)
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_header", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_key_status", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_google_instructions", MagicMock())
        mock_anthropic_instructions = MagicMock()
        monkeypatch.setattr(
            "visual_explainer.api_setup.display_anthropic_instructions",
            mock_anthropic_instructions,
        )
        monkeypatch.setattr("visual_explainer.api_setup.display_cost_information", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_env_file_created", MagicMock())
        env_path = tmp_path / ".env"
        monkeypatch.setattr(
            "visual_explainer.api_setup.create_env_file",
            MagicMock(return_value=env_path),
        )
        mock_prompt_for_key = MagicMock(return_value=("google-key-val", False))
        monkeypatch.setattr("visual_explainer.api_setup.prompt_for_key", mock_prompt_for_key)

        result = await run_setup_wizard(env_path=env_path)

        assert result["env_file_created"] is True
        mock_anthropic_instructions.assert_not_called()
        mock_prompt_for_key.assert_called_once()

    async def test_only_anthropic_needed_skips_google_prompt(self, monkeypatch, tmp_path):
        """Test only anthropic_needed True hits the anthropic branch, skipping google prompting."""
        from visual_explainer.api_setup import run_setup_wizard

        monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy" + "x" * 30)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr("visual_explainer.api_setup.is_interactive", lambda: True)
        monkeypatch.setattr("visual_explainer.api_setup.get_console", lambda: MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_header", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_key_status", MagicMock())
        mock_google_instructions = MagicMock()
        monkeypatch.setattr(
            "visual_explainer.api_setup.display_google_instructions",
            mock_google_instructions,
        )
        monkeypatch.setattr(
            "visual_explainer.api_setup.display_anthropic_instructions", MagicMock()
        )
        monkeypatch.setattr("visual_explainer.api_setup.display_cost_information", MagicMock())
        monkeypatch.setattr("visual_explainer.api_setup.display_env_file_created", MagicMock())
        env_path = tmp_path / ".env"
        monkeypatch.setattr(
            "visual_explainer.api_setup.create_env_file",
            MagicMock(return_value=env_path),
        )
        mock_prompt_for_key = MagicMock(return_value=("sk-ant-key-val", False))
        monkeypatch.setattr("visual_explainer.api_setup.prompt_for_key", mock_prompt_for_key)

        result = await run_setup_wizard(env_path=env_path)

        assert result["env_file_created"] is True
        mock_google_instructions.assert_not_called()
        mock_prompt_for_key.assert_called_once()


# ---------------------------------------------------------------------------
# run_setup_wizard_sync Tests
# ---------------------------------------------------------------------------


class TestRunSetupWizardSync:
    """Tests for run_setup_wizard_sync."""

    def test_delegates_to_asyncio_run(self, monkeypatch):
        """Test run_setup_wizard_sync drives run_setup_wizard via asyncio.run."""
        from visual_explainer.api_setup import APIKeySetupResult, run_setup_wizard_sync

        fake_result = APIKeySetupResult(
            google={"present": True, "valid": True, "error": None},
            anthropic={"present": True, "valid": True, "error": None},
            env_file_created=True,
            env_file_path="/tmp/.env",
            skipped=False,
        )
        mock_run_setup_wizard = AsyncMock(return_value=fake_result)
        monkeypatch.setattr("visual_explainer.api_setup.run_setup_wizard", mock_run_setup_wizard)

        result = run_setup_wizard_sync(force=True, env_path=None)

        assert result == fake_result
        mock_run_setup_wizard.assert_called_once_with(force=True, env_path=None)


# ---------------------------------------------------------------------------
# check_keys_and_prompt_if_missing Extra Branch Tests
# ---------------------------------------------------------------------------


class TestCheckKeysAndPromptExtra:
    """Additional branch coverage for check_keys_and_prompt_if_missing."""

    def test_only_anthropic_missing_non_interactive(self, monkeypatch, capsys):
        """Test only the Anthropic key missing is reported alone."""
        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy" + "x" * 30)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with patch("dotenv.load_dotenv"):
            with patch("visual_explainer.api_setup.is_interactive", return_value=False):
                result = check_keys_and_prompt_if_missing()

        assert result is False
        captured = capsys.readouterr()
        assert "ANTHROPIC_API_KEY" in captured.out
        assert "GOOGLE_API_KEY" not in captured.out

    def test_only_google_missing_non_interactive(self, monkeypatch, capsys):
        """Test only the Google key missing is reported alone."""
        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-" + "x" * 30)

        with patch("dotenv.load_dotenv"):
            with patch("visual_explainer.api_setup.is_interactive", return_value=False):
                result = check_keys_and_prompt_if_missing()

        assert result is False
        captured = capsys.readouterr()
        assert "GOOGLE_API_KEY" in captured.out
        assert "ANTHROPIC_API_KEY" not in captured.out

    def test_interactive_user_declines_setup(self, monkeypatch):
        """Test declining the interactive setup prompt returns False."""
        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        mock_console = MagicMock()
        with (
            patch("dotenv.load_dotenv"),
            patch("visual_explainer.api_setup.is_interactive", return_value=True),
            patch("visual_explainer.api_setup.get_console", return_value=mock_console),
            patch("visual_explainer.api_setup.Prompt.ask", return_value="n"),
        ):
            result = check_keys_and_prompt_if_missing()

        assert result is False

    def test_interactive_user_accepts_setup_runs_wizard(self, monkeypatch):
        """Test accepting the interactive setup prompt runs the wizard and returns its verdict."""
        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        mock_console = MagicMock()
        fake_result = {
            "google": {"present": True, "valid": True, "error": None},
            "anthropic": {"present": True, "valid": True, "error": None},
            "env_file_created": True,
            "env_file_path": "/tmp/.env",
            "skipped": False,
        }
        with (
            patch("dotenv.load_dotenv"),
            patch("visual_explainer.api_setup.is_interactive", return_value=True),
            patch("visual_explainer.api_setup.get_console", return_value=mock_console),
            patch("visual_explainer.api_setup.Prompt.ask", return_value="y"),
            patch(
                "visual_explainer.api_setup.run_setup_wizard_sync",
                return_value=fake_result,
            ) as mock_wizard,
        ):
            result = check_keys_and_prompt_if_missing()

        assert result is True
        mock_wizard.assert_called_once_with(force=True)

    def test_interactive_only_anthropic_missing_builds_partial_list(self, monkeypatch):
        """Test interactive mode with only anthropic missing skips the google-missing append."""
        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSy" + "x" * 30)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        mock_console = MagicMock()
        with (
            patch("dotenv.load_dotenv"),
            patch("visual_explainer.api_setup.is_interactive", return_value=True),
            patch("visual_explainer.api_setup.get_console", return_value=mock_console),
            patch("visual_explainer.api_setup.Prompt.ask", return_value="n"),
        ):
            result = check_keys_and_prompt_if_missing()

        assert result is False
        printed = " ".join(
            str(call.args[0]) for call in mock_console.print.call_args_list if call.args
        )
        assert "ANTHROPIC_API_KEY" in printed
        assert "GOOGLE_API_KEY" not in printed

    def test_interactive_only_google_missing_builds_partial_list(self, monkeypatch):
        """Test interactive mode with only google missing skips the anthropic-missing append."""
        from visual_explainer.api_setup import check_keys_and_prompt_if_missing

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-" + "x" * 30)

        mock_console = MagicMock()
        with (
            patch("dotenv.load_dotenv"),
            patch("visual_explainer.api_setup.is_interactive", return_value=True),
            patch("visual_explainer.api_setup.get_console", return_value=mock_console),
            patch("visual_explainer.api_setup.Prompt.ask", return_value="n"),
        ):
            result = check_keys_and_prompt_if_missing()

        assert result is False
        printed = " ".join(
            str(call.args[0]) for call in mock_console.print.call_args_list if call.args
        )
        assert "GOOGLE_API_KEY" in printed
        assert "ANTHROPIC_API_KEY" not in printed


# ---------------------------------------------------------------------------
# handle_setup_keys_flag Extra Branch Tests
# ---------------------------------------------------------------------------


class TestHandleSetupKeysFlagExtra:
    """Additional branch coverage for handle_setup_keys_flag."""

    def test_success_both_keys_present(self, monkeypatch):
        """Test both keys present after wizard returns exit code 0."""
        from visual_explainer.api_setup import handle_setup_keys_flag

        mock_console = MagicMock()
        fake_result = {
            "google": {"present": True, "valid": True, "error": None},
            "anthropic": {"present": True, "valid": True, "error": None},
            "env_file_created": True,
            "env_file_path": "/tmp/.env",
            "skipped": False,
        }
        with (
            patch("visual_explainer.api_setup.is_interactive", return_value=True),
            patch("visual_explainer.api_setup.get_console", return_value=mock_console),
            patch("visual_explainer.api_setup.run_setup_wizard_sync", return_value=fake_result),
        ):
            result = handle_setup_keys_flag()

        assert result == 0

    def test_skipped_result_returns_1(self, monkeypatch):
        """Test a skipped setup returns exit code 1."""
        from visual_explainer.api_setup import handle_setup_keys_flag

        mock_console = MagicMock()
        fake_result = {
            "google": {"present": False, "valid": None, "error": None},
            "anthropic": {"present": True, "valid": True, "error": None},
            "env_file_created": False,
            "env_file_path": None,
            "skipped": True,
        }
        with (
            patch("visual_explainer.api_setup.is_interactive", return_value=True),
            patch("visual_explainer.api_setup.get_console", return_value=mock_console),
            patch("visual_explainer.api_setup.run_setup_wizard_sync", return_value=fake_result),
        ):
            result = handle_setup_keys_flag()

        assert result == 1

    def test_failed_result_returns_1(self, monkeypatch):
        """Test a failed (not skipped, not complete) setup returns exit code 1."""
        from visual_explainer.api_setup import handle_setup_keys_flag

        mock_console = MagicMock()
        fake_result = {
            "google": {"present": False, "valid": None, "error": None},
            "anthropic": {"present": False, "valid": None, "error": None},
            "env_file_created": False,
            "env_file_path": None,
            "skipped": False,
        }
        with (
            patch("visual_explainer.api_setup.is_interactive", return_value=True),
            patch("visual_explainer.api_setup.get_console", return_value=mock_console),
            patch("visual_explainer.api_setup.run_setup_wizard_sync", return_value=fake_result),
        ):
            result = handle_setup_keys_flag()

        assert result == 1

    def test_keyboard_interrupt_returns_1(self, monkeypatch):
        """Test KeyboardInterrupt during the wizard is caught and returns exit code 1."""
        from visual_explainer.api_setup import handle_setup_keys_flag

        mock_console = MagicMock()
        with (
            patch("visual_explainer.api_setup.is_interactive", return_value=True),
            patch("visual_explainer.api_setup.get_console", return_value=mock_console),
            patch(
                "visual_explainer.api_setup.run_setup_wizard_sync",
                side_effect=KeyboardInterrupt(),
            ),
        ):
            result = handle_setup_keys_flag()

        assert result == 1

    def test_generic_exception_returns_1(self, monkeypatch):
        """Test a generic exception during the wizard is caught and returns exit code 1."""
        from visual_explainer.api_setup import handle_setup_keys_flag

        mock_console = MagicMock()
        with (
            patch("visual_explainer.api_setup.is_interactive", return_value=True),
            patch("visual_explainer.api_setup.get_console", return_value=mock_console),
            patch(
                "visual_explainer.api_setup.run_setup_wizard_sync",
                side_effect=RuntimeError("boom"),
            ),
        ):
            result = handle_setup_keys_flag()

        assert result == 1
