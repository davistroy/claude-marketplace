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
