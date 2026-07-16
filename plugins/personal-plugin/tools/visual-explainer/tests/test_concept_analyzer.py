"""Tests for concept_analyzer module.

Tests concept extraction with mocked Claude API.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from visual_explainer.concept_analyzer import (
    analyze_document,
    analyze_document_sync,
    call_claude_for_analysis,
    compute_content_hash,
    detect_input_type,
    load_from_cache,
    read_input,
    save_to_cache,
)
from visual_explainer.config import GenerationConfig, InternalConfig
from visual_explainer.models import (
    Complexity,
    ConceptAnalysis,
    VisualPotential,
)


class TestComputeContentHash:
    """Tests for compute_content_hash function."""

    def test_returns_hex_string(self):
        """Test that hash is returned as hex string."""
        result = compute_content_hash("Test content")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 produces 64 hex chars

    def test_same_content_same_hash(self):
        """Test that same content produces same hash."""
        hash1 = compute_content_hash("Test content")
        hash2 = compute_content_hash("Test content")
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Test that different content produces different hash."""
        hash1 = compute_content_hash("Test content 1")
        hash2 = compute_content_hash("Test content 2")
        assert hash1 != hash2

    def test_handles_unicode(self):
        """Test that unicode content is handled correctly."""
        result = compute_content_hash("Test with unicode: \u00e9\u00e8\u00ea")
        assert isinstance(result, str)
        assert len(result) == 64


class TestDetectInputType:
    """Tests for detect_input_type function."""

    def test_detects_url_http(self):
        """Test detection of HTTP URLs."""
        input_type, path = detect_input_type("http://example.com/page")
        assert input_type == "url"
        assert path == "http://example.com/page"

    def test_detects_url_https(self):
        """Test detection of HTTPS URLs."""
        input_type, path = detect_input_type("https://example.com/page")
        assert input_type == "url"
        assert path == "https://example.com/page"

    def test_detects_url_www(self):
        """Test detection of www URLs (auto-adds https)."""
        input_type, path = detect_input_type("www.example.com/page")
        assert input_type == "url"
        assert path == "https://www.example.com/page"

    def test_detects_existing_file(self, tmp_path: Path):
        """Test detection of existing file paths."""
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")

        input_type, path = detect_input_type(str(test_file))
        assert input_type == "file"
        assert path == str(test_file.resolve())

    def test_detects_file_like_path(self):
        """Test detection of file-like paths that don't exist."""
        input_type, path = detect_input_type("path/to/document.md")
        assert input_type == "file"
        assert path == "path/to/document.md"

    def test_detects_raw_text(self):
        """Test detection of raw text content."""
        long_text = "This is a long piece of text that doesn't look like a file path or URL. " * 20
        input_type, path = detect_input_type(long_text)
        assert input_type == "text"
        assert path is None

    def test_short_text_without_path_chars(self):
        """Test that short text without path characters is detected as text."""
        input_type, path = detect_input_type("Machine learning is fascinating")
        assert input_type == "text"
        assert path is None


class TestCaching:
    """Tests for cache-related functions."""

    def test_save_and_load_cache(
        self,
        sample_concept_analysis: ConceptAnalysis,
        temp_cache_dir: Path,
    ):
        """Test saving and loading from cache."""
        content_hash = "abc123def456789012345678901234567890123456789012345678901234"

        # Save to cache
        cache_path = save_to_cache(sample_concept_analysis, content_hash, temp_cache_dir)
        assert cache_path.exists()

        # Load from cache
        loaded = load_from_cache(content_hash, temp_cache_dir)
        assert loaded is not None
        assert loaded.title == sample_concept_analysis.title
        assert len(loaded.concepts) == len(sample_concept_analysis.concepts)

    def test_load_returns_none_for_missing(self, temp_cache_dir: Path):
        """Test that load returns None for missing cache."""
        result = load_from_cache("nonexistent_hash", temp_cache_dir)
        assert result is None

    def test_load_returns_none_for_hash_mismatch(self, temp_cache_dir: Path):
        """Test that load returns None if stored hash doesn't match."""
        # Create a cache file with wrong hash
        cache_path = temp_cache_dir / "concepts-wronghash1234567.json"
        temp_cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "content_hash": "different_hash",
                    "title": "Test",
                    "summary": "Test",
                    "concepts": [{"id": 1, "name": "Test", "description": "Test"}],
                    "recommended_image_count": 1,
                }
            )
        )

        result = load_from_cache("wronghash12345678", temp_cache_dir)
        assert result is None

    def test_cache_creates_directory(
        self, tmp_path: Path, sample_concept_analysis: ConceptAnalysis
    ):
        """Test that save creates cache directory if needed."""
        cache_dir = tmp_path / "new_cache_dir"
        assert not cache_dir.exists()

        save_to_cache(
            sample_concept_analysis,
            "testhash1234567890123456789012345678901234567890123456789012",
            cache_dir,
        )
        assert cache_dir.exists()


class TestReadInput:
    """Tests for read_input function."""

    @pytest.mark.asyncio
    async def test_read_raw_text(self):
        """Test reading raw text input."""
        content, input_type, path = await read_input("This is raw text content for testing.")
        assert content == "This is raw text content for testing."
        assert input_type == "text"
        assert path is None

    @pytest.mark.asyncio
    async def test_read_text_file(self, tmp_path: Path):
        """Test reading a text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content from text file", encoding="utf-8")

        content, input_type, path = await read_input(str(test_file))
        assert content == "Content from text file"
        assert input_type == "file"
        assert path == str(test_file.resolve())

    @pytest.mark.asyncio
    async def test_read_markdown_file(self, tmp_path: Path):
        """Test reading a markdown file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Markdown Content\n\nSome text here.", encoding="utf-8")

        content, input_type, path = await read_input(str(test_file))
        assert "# Markdown Content" in content
        assert input_type == "file"

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """Test that reading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            await read_input("/path/to/nonexistent/file.md")


class TestCallClaudeForAnalysis:
    """Tests for call_claude_for_analysis function."""

    @pytest.mark.asyncio
    async def test_calls_anthropic_api(
        self,
        sample_internal_config: InternalConfig,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
    ):
        """Test that Claude API is called correctly."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_concept_analysis_response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await call_claude_for_analysis(
                "Test content about machine learning",
                sample_internal_config,
            )

            assert result["title"] == "Machine Learning Fundamentals"
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_without_api_key(
        self,
        sample_internal_config: InternalConfig,
        monkeypatch,
    ):
        """Test that missing API key raises ValueError."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            await call_claude_for_analysis("Test content", sample_internal_config)

    @pytest.mark.asyncio
    async def test_handles_json_in_code_block(
        self,
        sample_internal_config: InternalConfig,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
    ):
        """Test parsing JSON wrapped in markdown code block."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        response_text = f"```json\n{json.dumps(mock_claude_concept_analysis_response)}\n```"
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=response_text)]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await call_claude_for_analysis(
                "Test content",
                sample_internal_config,
            )

            assert result["title"] == "Machine Learning Fundamentals"

    @pytest.mark.asyncio
    async def test_handles_json_with_extra_text(
        self,
        sample_internal_config: InternalConfig,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
    ):
        """Test parsing JSON with extra text before/after."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        response_text = f"Here is the analysis:\n{json.dumps(mock_claude_concept_analysis_response)}\nHope this helps!"
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=response_text)]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await call_claude_for_analysis(
                "Test content",
                sample_internal_config,
            )

            assert result["title"] == "Machine Learning Fundamentals"

    @pytest.mark.asyncio
    async def test_raises_on_invalid_json(
        self,
        sample_internal_config: InternalConfig,
        monkeypatch,
    ):
        """Test that invalid JSON raises ValueError."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="{ invalid json }")]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ValueError, match="JSON"):
                await call_claude_for_analysis(
                    "Test content",
                    sample_internal_config,
                )


class TestAnalyzeDocument:
    """Tests for analyze_document function."""

    @pytest.mark.asyncio
    async def test_returns_concept_analysis(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
    ):
        """Test that analyze_document returns a ConceptAnalysis object."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_concept_analysis_response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                "Test content about machine learning.",
                sample_generation_config,
                sample_internal_config,
            )

            assert isinstance(result, ConceptAnalysis)
            assert result.title == "Machine Learning Fundamentals"
            assert len(result.concepts) == 2

    @pytest.mark.asyncio
    async def test_uses_cache_when_available(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        sample_concept_analysis: ConceptAnalysis,
    ):
        """Test that cached analysis is returned when available."""
        # Disable no_cache to use caching
        config = GenerationConfig(
            input_source=sample_generation_config.input_source,
            style=sample_generation_config.style,
            output_dir=sample_generation_config.output_dir,
            no_cache=False,
        )

        # Save to cache first
        content_hash = compute_content_hash(config.input_source)
        save_to_cache(sample_concept_analysis, content_hash, sample_internal_config.cache_dir)

        # Should return cached result without API call
        result = await analyze_document(
            config.input_source,
            config,
            sample_internal_config,
        )

        assert isinstance(result, ConceptAnalysis)
        assert result.title == sample_concept_analysis.title

    @pytest.mark.asyncio
    async def test_skips_cache_when_no_cache_true(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        sample_concept_analysis: ConceptAnalysis,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
    ):
        """Test that cache is skipped when no_cache=True."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # Ensure config has no_cache=True
        config = GenerationConfig(
            input_source=sample_generation_config.input_source,
            style=sample_generation_config.style,
            output_dir=sample_generation_config.output_dir,
            no_cache=True,
        )

        # Save stale cache
        content_hash = compute_content_hash(config.input_source)
        sample_concept_analysis.title = "Old Cached Title"
        save_to_cache(sample_concept_analysis, content_hash, sample_internal_config.cache_dir)

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_concept_analysis_response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                config.input_source,
                config,
                sample_internal_config,
            )

            # Should return fresh result, not cached
            assert result.title == "Machine Learning Fundamentals"

    @pytest.mark.asyncio
    async def test_raises_on_empty_content(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
    ):
        """Test that empty content raises ValueError."""
        config = GenerationConfig(
            input_source="   ",  # Whitespace only
            style=sample_generation_config.style,
            output_dir=sample_generation_config.output_dir,
        )

        with pytest.raises(ValueError, match="empty"):
            await analyze_document(
                config.input_source,
                config,
                sample_internal_config,
            )

    @pytest.mark.asyncio
    async def test_sets_content_hash_and_word_count(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
    ):
        """Test that content hash and word count are set on the analysis."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_concept_analysis_response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            test_content = "This is a test document with exactly ten words here."
            config = GenerationConfig(
                input_source=test_content,
                style="professional-clean",
                output_dir=sample_generation_config.output_dir,
                no_cache=True,
            )

            result = await analyze_document(
                test_content,
                config,
                sample_internal_config,
            )

            assert result.content_hash != ""
            assert result.word_count == 10


class TestAnalyzeDocumentSync:
    """Tests for analyze_document_sync function."""

    def test_sync_wrapper_works(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
    ):
        """Test that sync wrapper calls async function correctly."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_concept_analysis_response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = analyze_document_sync(
                "Test content about machine learning.",
                sample_generation_config,
                sample_internal_config,
            )

            assert isinstance(result, ConceptAnalysis)
            assert result.title == "Machine Learning Fundamentals"


class TestConceptAnalysisParsing:
    """Tests for parsing concept analysis responses."""

    @pytest.mark.asyncio
    async def test_concepts_have_correct_complexity(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        monkeypatch,
    ):
        """Test that concept complexity is correctly parsed."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        response = {
            "title": "Test",
            "summary": "Test summary",
            "concepts": [
                {
                    "id": 1,
                    "name": "Simple Concept",
                    "description": "Easy concept",
                    "complexity": "simple",
                    "visual_potential": "high",
                }
            ],
            "recommended_image_count": 1,
            "reasoning": "Test",
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                "Test content",
                sample_generation_config,
                sample_internal_config,
            )

            assert result.concepts[0].complexity == Complexity.SIMPLE

    @pytest.mark.asyncio
    async def test_concepts_have_correct_visual_potential(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        monkeypatch,
    ):
        """Test that visual potential is correctly parsed."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        response = {
            "title": "Test",
            "summary": "Test summary",
            "concepts": [
                {
                    "id": 1,
                    "name": "Visual Concept",
                    "description": "Very visual",
                    "complexity": "moderate",
                    "visual_potential": "high",
                }
            ],
            "recommended_image_count": 1,
            "reasoning": "Test",
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                "Test content",
                sample_generation_config,
                sample_internal_config,
            )

            assert result.concepts[0].visual_potential == VisualPotential.HIGH

    @pytest.mark.asyncio
    async def test_logical_flow_parsed_correctly(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        monkeypatch,
    ):
        """Test that logical flow is parsed correctly."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        response = {
            "title": "Test",
            "summary": "Test summary",
            "concepts": [
                {"id": 1, "name": "A", "description": "A"},
                {"id": 2, "name": "B", "description": "B"},
            ],
            "logical_flow": [
                {"from": 1, "to": 2, "relationship": "leads_to"},
            ],
            "recommended_image_count": 2,
            "reasoning": "Test",
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                "Test content",
                sample_generation_config,
                sample_internal_config,
            )

            assert len(result.logical_flow) == 1
            assert result.logical_flow[0].from_concept == 1
            assert result.logical_flow[0].to_concept == 2

    @pytest.mark.asyncio
    async def test_handles_missing_optional_fields(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        monkeypatch,
    ):
        """Test parsing handles missing optional fields gracefully."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        response = {
            "title": "Test",
            "summary": "Test summary",
            "concepts": [{"id": 1, "name": "A", "description": "A"}],
            "recommended_image_count": 1,
            # Missing: reasoning, logical_flow, target_audience
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                "Test content",
                sample_generation_config,
                sample_internal_config,
            )

            assert result.title == "Test"
            assert result.logical_flow == []


# =============================================================================
# Additional imports for extended coverage tests (appended below)
# =============================================================================

import socket  # noqa: E402
from unittest.mock import AsyncMock  # noqa: E402

import httpx  # noqa: E402

from visual_explainer.concept_analyzer import (  # noqa: E402
    SSRFError,
    _check_host_is_safe,
    _extract_json_from_response,
    _parse_content_type,
    _parse_content_types_list,
    _parse_page_plan,
    _parse_page_type,
    _validate_url_target,
    fetch_url_content,
    get_cache_path,
    read_docx_file,
    read_pdf_file,
    read_text_file,
)
from visual_explainer.models import ContentType, PageType  # noqa: E402


class _MockAsyncClientCM:
    """Minimal async context manager wrapping a mock httpx client for `async with` use."""

    def __init__(self, client):
        self._client = client

    async def __aenter__(self):
        return self._client

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _make_mock_async_client(get_side_effect):
    """Build an httpx.AsyncClient()-compatible mock whose `.get()` yields get_side_effect."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=get_side_effect)
    return _MockAsyncClientCM(mock_client)


# A getaddrinfo result that resolves to a safe, public IPv4 address.
_SAFE_ADDRINFO = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]


class TestDetectInputTypeOverlongInput:
    """Tests for the very-long-input guard in detect_input_type."""

    def test_returns_text_for_overlong_non_url_input(self):
        """Test that inputs longer than 4096 chars are treated as raw text."""
        overlong = "a" * 5000
        input_type, path = detect_input_type(overlong)
        assert input_type == "text"
        assert path is None


class TestReadTextFileEncodingFallback:
    """Tests for read_text_file's latin-1 fallback behavior."""

    def test_falls_back_to_latin1_on_unicode_decode_error(self, tmp_path: Path):
        """Test that invalid UTF-8 bytes are successfully read via latin-1 fallback."""
        test_file = tmp_path / "latin1.txt"
        # 0xe9 alone is not valid UTF-8, but is a valid latin-1 byte (e-acute).
        test_file.write_bytes(b"Caf\xe9 with an invalid utf-8 byte")

        content = read_text_file(test_file)

        assert "Caf" in content
        assert "with an invalid utf-8 byte" in content

    def test_raises_value_error_when_latin1_fallback_also_fails(self, tmp_path: Path):
        """Test that a failure in the latin-1 fallback raises ValueError."""
        test_file = tmp_path / "broken.txt"
        test_file.write_bytes(b"some bytes")

        with patch.object(Path, "read_text") as mock_read_text:
            mock_read_text.side_effect = [
                UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
                OSError("disk read failure"),
            ]
            with pytest.raises(ValueError, match="Could not read file"):
                read_text_file(test_file)


class TestReadDocxFile:
    """Tests for read_docx_file."""

    def test_raises_import_error_when_docx_unavailable(self, tmp_path: Path):
        """Test that missing python-docx raises ImportError."""
        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"data")

        with patch("visual_explainer.concept_analyzer.DOCX_AVAILABLE", False):
            with pytest.raises(ImportError, match="python-docx"):
                read_docx_file(test_file)

    def test_raises_file_not_found(self, tmp_path: Path):
        """Test that a missing file raises FileNotFoundError."""
        with patch("visual_explainer.concept_analyzer.DOCX_AVAILABLE", True):
            with pytest.raises(FileNotFoundError):
                read_docx_file(tmp_path / "nonexistent.docx")

    def test_extracts_nonblank_paragraphs(self, tmp_path: Path):
        """Test that non-blank paragraphs are joined with double newlines."""
        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"fake docx binary content")

        mock_doc = MagicMock()
        mock_doc.paragraphs = [
            MagicMock(text="Paragraph one"),
            MagicMock(text="   "),
            MagicMock(text="Paragraph two"),
        ]

        with (
            patch("visual_explainer.concept_analyzer.DOCX_AVAILABLE", True),
            patch("visual_explainer.concept_analyzer.DocxDocument", create=True) as mock_docx_class,
        ):
            mock_docx_class.return_value = mock_doc
            result = read_docx_file(test_file)

        assert result == "Paragraph one\n\nParagraph two"
        mock_docx_class.assert_called_once_with(str(test_file))

    def test_raises_value_error_on_read_failure(self, tmp_path: Path):
        """Test that an internal docx parsing error raises ValueError."""
        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"corrupt binary content")

        with (
            patch("visual_explainer.concept_analyzer.DOCX_AVAILABLE", True),
            patch("visual_explainer.concept_analyzer.DocxDocument", create=True) as mock_docx_class,
        ):
            mock_docx_class.side_effect = Exception("corrupt docx")
            with pytest.raises(ValueError, match="Could not read DOCX file"):
                read_docx_file(test_file)


class TestReadPdfFile:
    """Tests for read_pdf_file."""

    def test_raises_import_error_when_pdf_unavailable(self, tmp_path: Path):
        """Test that missing pypdf raises ImportError."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"data")

        with patch("visual_explainer.concept_analyzer.PDF_AVAILABLE", False):
            with pytest.raises(ImportError, match="pypdf"):
                read_pdf_file(test_file)

    def test_raises_file_not_found(self, tmp_path: Path):
        """Test that a missing file raises FileNotFoundError."""
        with patch("visual_explainer.concept_analyzer.PDF_AVAILABLE", True):
            with pytest.raises(FileNotFoundError):
                read_pdf_file(tmp_path / "nonexistent.pdf")

    def test_extracts_text_skipping_empty_pages(self, tmp_path: Path):
        """Test that page text is joined, skipping pages with no extractable text."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf binary content")

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 text"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Page 3 text"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2, mock_page3]

        with (
            patch("visual_explainer.concept_analyzer.PDF_AVAILABLE", True),
            patch("visual_explainer.concept_analyzer.PdfReader", create=True) as mock_reader_class,
        ):
            mock_reader_class.return_value = mock_reader
            result = read_pdf_file(test_file)

        assert result == "Page 1 text\n\nPage 3 text"
        mock_reader_class.assert_called_once_with(str(test_file))

    def test_raises_value_error_on_read_failure(self, tmp_path: Path):
        """Test that an internal pdf parsing error raises ValueError."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"corrupt binary content")

        with (
            patch("visual_explainer.concept_analyzer.PDF_AVAILABLE", True),
            patch("visual_explainer.concept_analyzer.PdfReader", create=True) as mock_reader_class,
        ):
            mock_reader_class.side_effect = Exception("corrupt pdf")
            with pytest.raises(ValueError, match="Could not read PDF file"):
                read_pdf_file(test_file)


class TestCheckHostIsSafe:
    """Tests for the _check_host_is_safe SSRF guard helper."""

    def test_raises_when_resolution_fails(self):
        """Test that a DNS resolution failure raises SSRFError."""
        with patch(
            "visual_explainer.concept_analyzer.socket.getaddrinfo",
            side_effect=socket.gaierror("name resolution failed"),
        ):
            with pytest.raises(SSRFError, match="Could not resolve host"):
                _check_host_is_safe("nonexistent.invalid")

    def test_raises_when_no_addr_infos_returned(self):
        """Test that an empty resolution result raises SSRFError."""
        with patch(
            "visual_explainer.concept_analyzer.socket.getaddrinfo",
            return_value=[],
        ):
            with pytest.raises(SSRFError, match="Could not resolve host"):
                _check_host_is_safe("empty.example.com")

    def test_raises_when_address_unparsable(self):
        """Test that an unparsable resolved address raises SSRFError."""
        with patch(
            "visual_explainer.concept_analyzer.socket.getaddrinfo",
            return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("not-an-ip", 0))],
        ):
            with pytest.raises(SSRFError, match="Could not parse resolved address"):
                _check_host_is_safe("weird.example.com")

    @pytest.mark.parametrize(
        "blocked_ip",
        ["10.0.0.5", "127.0.0.1", "169.254.169.254", "224.0.0.1", "0.0.0.0"],
    )
    def test_raises_for_disallowed_addresses(self, blocked_ip: str):
        """Test that private/loopback/link-local/multicast/unspecified addresses are blocked."""
        with patch(
            "visual_explainer.concept_analyzer.socket.getaddrinfo",
            return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", (blocked_ip, 0))],
        ):
            with pytest.raises(SSRFError, match="Blocked URL target"):
                _check_host_is_safe("blocked.example.com")

    def test_passes_for_public_address(self):
        """Test that a public IP address does not raise."""
        with patch(
            "visual_explainer.concept_analyzer.socket.getaddrinfo",
            return_value=_SAFE_ADDRINFO,
        ):
            _check_host_is_safe("public.example.com")  # Should not raise.


class TestValidateUrlTarget:
    """Tests for the _validate_url_target function."""

    def test_raises_for_disallowed_scheme(self):
        """Test that a non-http(s) scheme raises SSRFError."""
        with pytest.raises(SSRFError, match="Unsupported URL scheme"):
            _validate_url_target("ftp://example.com/file")

    def test_raises_when_no_hostname(self):
        """Test that a URL without a hostname raises SSRFError."""
        with pytest.raises(SSRFError, match="URL has no hostname"):
            _validate_url_target("http:///path/only")

    def test_delegates_to_host_check_for_valid_url(self):
        """Test that a well-formed URL proceeds to the host safety check."""
        with patch(
            "visual_explainer.concept_analyzer.socket.getaddrinfo",
            return_value=_SAFE_ADDRINFO,
        ):
            _validate_url_target("https://example.com/page")  # Should not raise.


class TestFetchUrlContent:
    """Tests for fetch_url_content, covering the SSRF guard, redirects, and HTML parsing."""

    @pytest.mark.asyncio
    async def test_raises_without_url_deps(self):
        """Test that missing httpx/bs4 raises ImportError."""
        with patch("visual_explainer.concept_analyzer.URL_AVAILABLE", False):
            with pytest.raises(ImportError, match="httpx"):
                await fetch_url_content("http://example.com")

    @pytest.mark.asyncio
    async def test_ssrf_blocks_before_any_request(self):
        """Test that a private-address target is blocked before the HTTP client is used."""
        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0))],
            ),
            patch("visual_explainer.concept_analyzer.httpx.AsyncClient") as mock_client_class,
        ):
            with pytest.raises(SSRFError):
                await fetch_url_content("http://internal.example.com/")
            mock_client_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_successful_fetch_extracts_main_content(self):
        """Test that script/style/nav/header/footer are stripped and <main> content wins."""
        html = """
        <html><head><script>bad_script();</script><style>.x{color:red}</style></head>
        <body>
        <nav>Nav Link</nav>
        <header>Header stuff</header>
        <main>
          <h1>Title Here</h1>
          <p>First paragraph.</p>
          <p>Second paragraph.</p>
        </main>
        <footer>Footer stuff</footer>
        </body></html>
        """
        response = MagicMock()
        response.is_redirect = False
        response.raise_for_status = MagicMock()
        response.headers = {"content-type": "text/html; charset=utf-8"}
        response.text = html

        mock_client = _make_mock_async_client([response])

        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=_SAFE_ADDRINFO,
            ),
            patch(
                "visual_explainer.concept_analyzer.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await fetch_url_content("http://example.com/article")

        assert "Title Here" in result
        assert "First paragraph." in result
        assert "Second paragraph." in result
        assert "Nav Link" not in result
        assert "Header stuff" not in result
        assert "Footer stuff" not in result
        assert "bad_script();" not in result

    @pytest.mark.asyncio
    async def test_falls_back_to_body_when_no_main_or_article(self):
        """Test that <body> content is used when there is no <main> or <article>."""
        html = "<html><body><p>Body only content.</p></body></html>"
        response = MagicMock()
        response.is_redirect = False
        response.raise_for_status = MagicMock()
        response.headers = {"content-type": "text/html"}
        response.text = html

        mock_client = _make_mock_async_client([response])

        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=_SAFE_ADDRINFO,
            ),
            patch(
                "visual_explainer.concept_analyzer.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await fetch_url_content("http://example.com/plain")

        assert result == "Body only content."

    @pytest.mark.asyncio
    async def test_falls_back_to_full_soup_when_no_containers(self):
        """Test that the whole soup is used when there's no main/article/body tag."""
        html = "<div>Fragment content only.</div>"
        response = MagicMock()
        response.is_redirect = False
        response.raise_for_status = MagicMock()
        response.headers = {"content-type": "text/plain"}
        response.text = html

        mock_client = _make_mock_async_client([response])

        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=_SAFE_ADDRINFO,
            ),
            patch(
                "visual_explainer.concept_analyzer.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await fetch_url_content("http://example.com/fragment")

        assert result == "Fragment content only."

    @pytest.mark.asyncio
    async def test_follows_redirect_then_succeeds(self):
        """Test that a redirect hop is re-validated and followed to a final response."""
        redirect_resp = MagicMock()
        redirect_resp.is_redirect = True
        redirect_resp.headers = {"location": "/final"}
        redirect_resp.url = httpx.URL("http://example.com/start")

        final_resp = MagicMock()
        final_resp.is_redirect = False
        final_resp.raise_for_status = MagicMock()
        final_resp.headers = {"content-type": "text/html"}
        final_resp.text = "<body><p>Final content.</p></body>"

        mock_client = _make_mock_async_client([redirect_resp, final_resp])

        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=_SAFE_ADDRINFO,
            ),
            patch(
                "visual_explainer.concept_analyzer.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            result = await fetch_url_content("http://example.com/start")

        assert result == "Final content."

    @pytest.mark.asyncio
    async def test_redirect_without_location_breaks_and_checks_content_type(self):
        """Test that a redirect response missing a location header still finalizes."""
        redirect_resp = MagicMock()
        redirect_resp.is_redirect = True
        redirect_resp.headers = {}
        redirect_resp.raise_for_status = MagicMock()
        redirect_resp.text = "<body><p>Whatever.</p></body>"

        mock_client = _make_mock_async_client([redirect_resp])

        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=_SAFE_ADDRINFO,
            ),
            patch(
                "visual_explainer.concept_analyzer.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            with pytest.raises(ValueError, match="Unsupported content type"):
                await fetch_url_content("http://example.com/loop")

        redirect_resp.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_after_too_many_redirects(self):
        """Test that an unbroken chain of redirects eventually raises ValueError."""

        def make_redirect(n: int) -> MagicMock:
            resp = MagicMock()
            resp.is_redirect = True
            resp.headers = {"location": f"/hop{n}"}
            resp.url = httpx.URL(f"http://example.com/hop{n - 1}")
            return resp

        responses = [make_redirect(i) for i in range(1, 8)]
        mock_client = _make_mock_async_client(responses)

        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=_SAFE_ADDRINFO,
            ),
            patch(
                "visual_explainer.concept_analyzer.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            with pytest.raises(ValueError, match="Too many redirects"):
                await fetch_url_content("http://example.com/start")

    @pytest.mark.asyncio
    async def test_raises_for_unsupported_content_type(self):
        """Test that a non-HTML/text response raises ValueError."""
        response = MagicMock()
        response.is_redirect = False
        response.raise_for_status = MagicMock()
        response.headers = {"content-type": "application/json"}
        response.text = "{}"

        mock_client = _make_mock_async_client([response])

        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=_SAFE_ADDRINFO,
            ),
            patch(
                "visual_explainer.concept_analyzer.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            with pytest.raises(ValueError, match="Unsupported content type"):
                await fetch_url_content("http://example.com/data.json")

    @pytest.mark.asyncio
    async def test_raises_on_http_status_error(self):
        """Test that an httpx.HTTPStatusError is wrapped in a ValueError."""
        request = httpx.Request("GET", "http://example.com/missing")
        response_obj = httpx.Response(404, request=request)
        error = httpx.HTTPStatusError("Not Found", request=request, response=response_obj)

        mock_client = _make_mock_async_client(error)

        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=_SAFE_ADDRINFO,
            ),
            patch(
                "visual_explainer.concept_analyzer.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            with pytest.raises(ValueError, match="HTTP error fetching URL"):
                await fetch_url_content("http://example.com/missing")

    @pytest.mark.asyncio
    async def test_raises_on_request_error(self):
        """Test that an httpx.RequestError is wrapped in a ValueError."""
        request = httpx.Request("GET", "http://example.com/")
        error = httpx.ConnectError("Connection refused", request=request)

        mock_client = _make_mock_async_client(error)

        with (
            patch(
                "visual_explainer.concept_analyzer.socket.getaddrinfo",
                return_value=_SAFE_ADDRINFO,
            ),
            patch(
                "visual_explainer.concept_analyzer.httpx.AsyncClient",
                return_value=mock_client,
            ),
        ):
            with pytest.raises(ValueError, match="Error fetching URL"):
                await fetch_url_content("http://example.com/")


class TestReadInputAdditionalDispatch:
    """Tests for read_input's URL, docx, pdf, and unsupported-extension dispatch."""

    @pytest.mark.asyncio
    async def test_dispatches_to_fetch_url_content(self):
        """Test that URL inputs are routed through fetch_url_content."""
        with patch(
            "visual_explainer.concept_analyzer.fetch_url_content",
            new=AsyncMock(return_value="Fetched page content"),
        ) as mock_fetch:
            content, input_type, path = await read_input("https://example.com/doc")

        assert content == "Fetched page content"
        assert input_type == "url"
        assert path == "https://example.com/doc"
        mock_fetch.assert_called_once_with("https://example.com/doc")

    @pytest.mark.asyncio
    async def test_dispatches_to_read_docx_file(self):
        """Test that .docx paths are routed through read_docx_file."""
        with patch(
            "visual_explainer.concept_analyzer.read_docx_file",
            return_value="Docx content here",
        ) as mock_read_docx:
            content, input_type, _path = await read_input("report.docx")

        assert content == "Docx content here"
        assert input_type == "file"
        mock_read_docx.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatches_to_read_pdf_file(self):
        """Test that .pdf paths are routed through read_pdf_file."""
        with patch(
            "visual_explainer.concept_analyzer.read_pdf_file",
            return_value="PDF content here",
        ) as mock_read_pdf:
            content, input_type, _path = await read_input("report.pdf")

        assert content == "PDF content here"
        assert input_type == "file"
        mock_read_pdf.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsupported_extension_raises_value_error(self):
        """Test that an unrecognized, nonexistent file extension raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported file type"):
            await read_input("some/nonexistent/dir/mystery-file.xyz")


class TestLoadFromCacheEdgeCases:
    """Additional edge cases for load_from_cache's parsing and error handling."""

    def test_returns_none_when_stored_hash_mismatches_at_correct_path(self, temp_cache_dir: Path):
        """Test the hash-mismatch branch is hit when the cache file path itself matches."""
        lookup_hash = "b" * 64
        stored_hash = "a" * 64
        cache_path = get_cache_path(lookup_hash, temp_cache_dir)
        cache_path.write_text(
            json.dumps(
                {
                    "content_hash": stored_hash,
                    "title": "Test",
                    "summary": "Test",
                    "concepts": [{"id": 1, "name": "Test", "description": "Test"}],
                    "recommended_image_count": 1,
                }
            ),
            encoding="utf-8",
        )

        result = load_from_cache(lookup_hash, temp_cache_dir)

        assert result is None

    def test_handles_missing_logical_flow_key(self, temp_cache_dir: Path):
        """Test that cache data with no logical_flow key at all parses cleanly."""
        content_hash = "c" * 64
        cache_path = get_cache_path(content_hash, temp_cache_dir)
        data = {
            "content_hash": content_hash,
            "title": "No Flow Doc",
            "summary": "A document with no logical_flow key at all.",
            "concepts": [{"id": 1, "name": "Solo Concept", "description": "Only one"}],
            "recommended_image_count": 1,
        }
        cache_path.write_text(json.dumps(data), encoding="utf-8")

        result = load_from_cache(content_hash, temp_cache_dir)

        assert result is not None
        assert result.title == "No Flow Doc"
        assert result.logical_flow == []

    def test_normalizes_api_format_flow_with_multiple_items(self, temp_cache_dir: Path):
        """Test that already-API-format (from/to) flow entries with 2+ items parse cleanly."""
        content_hash = "d" * 64
        cache_path = get_cache_path(content_hash, temp_cache_dir)
        data = {
            "content_hash": content_hash,
            "title": "API Format Flow",
            "summary": "Uses from/to keys directly, not from_concept/to_concept.",
            "concepts": [
                {"id": 1, "name": "A", "description": "First"},
                {"id": 2, "name": "B", "description": "Second"},
            ],
            "logical_flow": [
                {"from": 1, "to": 2, "relationship": "leads_to"},
                {"from": 2, "to": 1, "relationship": "contrasts"},
            ],
            "recommended_image_count": 1,
        }
        cache_path.write_text(json.dumps(data), encoding="utf-8")

        result = load_from_cache(content_hash, temp_cache_dir)

        assert result is not None
        assert len(result.logical_flow) == 2
        assert result.logical_flow[0].from_concept == 1
        assert result.logical_flow[0].to_concept == 2
        assert result.logical_flow[1].from_concept == 2
        assert result.logical_flow[1].to_concept == 1

    def test_returns_none_for_corrupt_json(self, temp_cache_dir: Path):
        """Test that a syntactically invalid cache file returns None instead of raising."""
        content_hash = "e" * 64
        cache_path = get_cache_path(content_hash, temp_cache_dir)
        cache_path.write_text("{ this is not valid json at all !!", encoding="utf-8")

        result = load_from_cache(content_hash, temp_cache_dir)

        assert result is None


class TestParseHelperFunctions:
    """Direct unit tests for the small _parse_* enum-coercion helpers."""

    def test_parse_content_type_invalid_returns_none(self):
        """Test that an unrecognized content type string returns None."""
        assert _parse_content_type("not-a-real-type") is None

    def test_parse_content_type_valid(self):
        """Test that a valid content type string parses to the matching enum member."""
        assert _parse_content_type("STATISTICS") == ContentType.STATISTICS

    def test_parse_page_type_invalid_defaults_to_hero_summary(self):
        """Test that an unrecognized page type string defaults to HERO_SUMMARY."""
        assert _parse_page_type("not-a-real-page-type") == PageType.HERO_SUMMARY

    def test_parse_page_type_valid(self):
        """Test that a valid page type string parses to the matching enum member."""
        assert _parse_page_type("comparison_matrix") == PageType.COMPARISON_MATRIX

    def test_parse_content_types_list_filters_invalid_entries(self):
        """Test that invalid entries are dropped while valid ones are kept in order."""
        result = _parse_content_types_list(["statistics", "bogus", "process"])
        assert result == [ContentType.STATISTICS, ContentType.PROCESS]

    def test_parse_page_plan_applies_defaults(self):
        """Test that _parse_page_plan fills in sensible defaults for missing fields."""
        plan = _parse_page_plan({"page_number": 1})
        assert plan.title == "Untitled Page"
        assert plan.content_focus == ""
        assert plan.page_type == PageType.HERO_SUMMARY
        assert plan.concepts_covered == []


class TestPageRecommendationParsing:
    """Tests exercising the full page_recommendation parsing path via analyze_document."""

    @pytest.mark.asyncio
    async def test_parses_full_page_recommendation_and_corrects_bad_ids(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        monkeypatch,
    ):
        """Test id-correction, content-type filtering, and page_recommendation parsing."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        response = {
            "title": "Full Page Rec Test",
            "summary": "Testing page recommendation parsing.",
            "concepts": [
                {"id": 0, "name": "Zero Id Concept", "description": "Should be corrected"},
                {"id": 2, "name": "Second Concept", "description": "Fine"},
            ],
            "logical_flow": [
                {"from": 0, "to": -1, "relationship": "leads_to"},
            ],
            "content_types_detected": ["statistics", "not-real"],
            "page_recommendation": {
                "page_count": 2,
                "rationale": "Two pages needed",
                "pages": [
                    {
                        "page_number": 1,
                        "page_type": "hero_summary",
                        "title": "Overview",
                        "content_focus": "Executive summary",
                        "concepts_covered": [1],
                        "content_types_present": ["statistics", "bogus"],
                        "zone_assignments": {"hero_stat": "Key stat"},
                        "cross_references": [],
                    },
                    {
                        "page_number": 2,
                        "page_type": "comparison_matrix",
                        "title": "Comparison",
                        "content_focus": "Compare options",
                        "concepts_covered": [2],
                        "content_types_present": ["comparison"],
                        "zone_assignments": {},
                        "cross_references": ["See page 1"],
                    },
                ],
                "compression_warnings": ["Topic X may be over-compressed"],
            },
            "recommended_image_count": 1,
            "reasoning": "Test reasoning",
        }

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                "Test content for page recommendation parsing.",
                sample_generation_config,
                sample_internal_config,
            )

        # Concept id 0 is below the model minimum and gets corrected (line 738).
        assert result.concepts[0].id == 1
        # Logical flow from/to ids below 1 get corrected (lines 771, 773).
        assert result.logical_flow[0].from_concept == 1
        assert result.logical_flow[0].to_concept == 1
        # Invalid content type strings are filtered out.
        assert result.content_types_detected == [ContentType.STATISTICS]
        # page_recommendation is fully parsed into a PageRecommendation model.
        assert result.page_recommendation is not None
        assert result.page_recommendation.page_count == 2
        assert len(result.page_recommendation.pages) == 2
        assert result.page_recommendation.pages[0].page_type == PageType.HERO_SUMMARY
        assert result.page_recommendation.pages[1].page_type == PageType.COMPARISON_MATRIX
        assert result.page_recommendation.pages[0].content_types_present == [ContentType.STATISTICS]
        # recommended_image_count is overridden by page_recommendation.page_count (797-799).
        assert result.recommended_image_count == 2

    @pytest.mark.asyncio
    async def test_defaults_concept_when_none_provided(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        monkeypatch,
    ):
        """Test that an empty concepts list is replaced with a default placeholder concept."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        response = {
            "title": "No concepts here",
            "summary": "Summary text",
            "concepts": [],
            "recommended_image_count": 1,
            "reasoning": "test",
        }
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                "Test content",
                sample_generation_config,
                sample_internal_config,
            )

        assert len(result.concepts) == 1
        assert result.concepts[0].name == "Main Concept"


class TestExtractJsonFromResponseEdgeCases:
    """Additional edge cases for _extract_json_from_response's fallback chain."""

    def test_falls_through_when_fenced_json_is_invalid(self):
        """Test that invalid JSON inside a code fence falls through to the brace search."""
        text = "```json\n{not valid json at all}\n```"
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            _extract_json_from_response(text)

    def test_raises_when_no_braces_present(self):
        """Test that text with no JSON-like structure at all raises ValueError."""
        text = "This response has no JSON structure whatsoever."
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            _extract_json_from_response(text)


class TestCallClaudeContentTruncation:
    """Tests for the long-document truncation guard in call_claude_for_analysis."""

    @pytest.mark.asyncio
    async def test_truncates_very_long_content(
        self,
        sample_internal_config: InternalConfig,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
    ):
        """Test that content over 100,000 chars is truncated before being sent to Claude."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        long_content = "word " * 25000  # well over 100,000 characters
        assert len(long_content) > 100000

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_concept_analysis_response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            await call_claude_for_analysis(long_content, sample_internal_config)

            call_kwargs = mock_client.messages.create.call_args.kwargs
            sent_prompt = call_kwargs["messages"][0]["content"]

        assert "[Content truncated...]" in sent_prompt


class TestAnalyzeDocumentAdditional:
    """Additional analyze_document tests for default config and cache-miss-with-caching."""

    @pytest.mark.asyncio
    async def test_uses_default_internal_config_when_none_provided(
        self,
        sample_generation_config: GenerationConfig,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
        tmp_path: Path,
    ):
        """Test that internal_config=None falls back to InternalConfig.from_env()."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        default_cache_dir = tmp_path / "default-cache"
        monkeypatch.setenv("VISUAL_EXPLAINER_CACHE_DIR", str(default_cache_dir))

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_concept_analysis_response))]

        config = GenerationConfig(
            input_source=sample_generation_config.input_source,
            style=sample_generation_config.style,
            output_dir=sample_generation_config.output_dir,
            no_cache=True,
        )

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                config.input_source,
                config,
                internal_config=None,
            )

        assert result.title == "Machine Learning Fundamentals"
        assert default_cache_dir.exists()

    @pytest.mark.asyncio
    async def test_cache_miss_with_caching_enabled_calls_claude_and_saves(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        mock_claude_concept_analysis_response: dict[str, Any],
        monkeypatch,
    ):
        """Test the no_cache=False + no-prior-cache-file path still calls Claude and saves."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        config = GenerationConfig(
            input_source="Fresh content never analyzed before, unique text.",
            style=sample_generation_config.style,
            output_dir=sample_generation_config.output_dir,
            no_cache=False,
        )

        assert not any(sample_internal_config.cache_dir.glob("concepts-*.json"))

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(mock_claude_concept_analysis_response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                config.input_source,
                config,
                sample_internal_config,
            )

        mock_client.messages.create.assert_called_once()
        assert result.title == "Machine Learning Fundamentals"
        content_hash = compute_content_hash(config.input_source)
        cache_path = get_cache_path(content_hash, sample_internal_config.cache_dir)
        assert cache_path.exists()


# =============================================================================
# Further additional imports for remaining enum-fallback and branch coverage
# =============================================================================

from visual_explainer.concept_analyzer import (  # noqa: E402
    _parse_complexity,
    _parse_page_recommendation,
    _parse_relationship_type,
    _parse_visual_potential,
)
from visual_explainer.models import PageRecommendation, RelationshipType  # noqa: E402


class TestParseEnumHelperFallbacks:
    """Direct tests for the remaining _parse_complexity/_visual_potential/_relationship_type
    fallback branches (invalid string -> default enum member)."""

    def test_parse_complexity_invalid_defaults_to_moderate(self):
        """Test that an unrecognized complexity string falls back to MODERATE."""
        assert _parse_complexity("not-a-real-complexity") == Complexity.MODERATE

    def test_parse_complexity_valid(self):
        """Test that a valid complexity string parses to the matching enum member."""
        assert _parse_complexity("SIMPLE") == Complexity.SIMPLE

    def test_parse_visual_potential_invalid_defaults_to_medium(self):
        """Test that an unrecognized visual potential string falls back to MEDIUM."""
        assert _parse_visual_potential("not-a-real-potential") == VisualPotential.MEDIUM

    def test_parse_visual_potential_valid(self):
        """Test that a valid visual potential string parses to the matching enum member."""
        assert _parse_visual_potential("HIGH") == VisualPotential.HIGH

    def test_parse_relationship_type_invalid_defaults_to_leads_to(self):
        """Test that an unrecognized relationship type string falls back to LEADS_TO."""
        assert _parse_relationship_type("not-a-real-relationship") == RelationshipType.LEADS_TO

    def test_parse_relationship_type_valid(self):
        """Test that a valid relationship type string parses to the matching enum member."""
        assert _parse_relationship_type("supports") == RelationshipType.SUPPORTS


class TestParsePageRecommendationEdgeCases:
    """Tests for _parse_page_recommendation's empty-pages default-hero-page branch."""

    def test_creates_default_hero_page_when_pages_list_is_empty(self):
        """Test that an empty `pages` list still yields one default hero-summary page."""
        result = _parse_page_recommendation(
            {
                "page_count": 3,
                "rationale": "No explicit pages provided",
                "pages": [],
            }
        )

        assert isinstance(result, PageRecommendation)
        assert result.page_count == 3
        assert len(result.pages) == 1
        assert result.pages[0].title == "Document Overview"
        assert result.pages[0].page_type == PageType.HERO_SUMMARY


class TestAnalyzeDocumentRecommendedCountEdgeCase:
    """Tests for the recommended_image_count legacy-fallback branch (no page_recommendation)."""

    @pytest.mark.asyncio
    async def test_zero_recommended_count_without_page_recommendation_defaults_to_one(
        self,
        sample_generation_config: GenerationConfig,
        sample_internal_config: InternalConfig,
        monkeypatch,
    ):
        """Test that recommended_image_count=0 with no page_recommendation still clamps to 1."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        response = {
            "title": "Zero Count Doc",
            "summary": "No page recommendation, and a zero recommended image count.",
            "concepts": [{"id": 1, "name": "Only", "description": "One"}],
            "recommended_image_count": 0,
            "reasoning": "test",
        }
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(response))]

        with patch("visual_explainer.concept_analyzer.anthropic.Anthropic") as mock_client_class:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = await analyze_document(
                "Test content",
                sample_generation_config,
                sample_internal_config,
            )

        assert result.page_recommendation is None
        assert result.recommended_image_count == 1
