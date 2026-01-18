"""Tests for prompt_generator module.

Tests prompt generation and refinement with mocked Claude API.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from visual_explainer.config import GenerationConfig, PromptRecipe, StyleConfig
from visual_explainer.models import (
    ConceptAnalysis,
    CriteriaScores,
    EvaluationResult,
    EvaluationVerdict,
    FlowConnection,
    ImagePrompt,
    PromptDetails,
)
from visual_explainer.prompt_generator import (
    PromptGenerationError,
    PromptGenerator,
    create_prompt_generator,
    generate_prompts,
    refine_prompt,
)


class TestPromptGenerator:
    """Tests for PromptGenerator class."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client."""
        return MagicMock()

    @pytest.fixture
    def generator(self, mock_anthropic_client):
        """Create a generator with mocked client."""
        with patch("visual_explainer.prompt_generator.anthropic.Anthropic") as mock:
            mock.return_value = mock_anthropic_client
            gen = PromptGenerator(api_key="test-key")
            gen.client = mock_anthropic_client
            return gen

    def test_init_with_api_key(self):
        """Test initializing with explicit API key."""
        with patch("visual_explainer.prompt_generator.anthropic.Anthropic") as mock:
            gen = PromptGenerator(api_key="test-key")
            mock.assert_called_once()

    def test_init_with_custom_model(self):
        """Test initializing with custom model."""
        with patch("visual_explainer.prompt_generator.anthropic.Anthropic"):
            gen = PromptGenerator(api_key="test-key", model="claude-opus-4-20250514")
            assert "opus" in gen.model.lower()

    def test_generate_prompts_returns_list(
        self,
        generator,
        mock_anthropic_client,
        sample_concept_analysis,
        sample_style_config,
        mock_claude_prompt_generation_response,
    ):
        """Test that generate_prompts returns a list of ImagePrompt."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps(mock_claude_prompt_generation_response))
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = generator.generate_prompts(sample_concept_analysis, sample_style_config)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, ImagePrompt) for p in result)

    def test_generate_prompts_sets_image_numbers(
        self,
        generator,
        mock_anthropic_client,
        sample_concept_analysis,
        sample_style_config,
        mock_claude_prompt_generation_response,
    ):
        """Test that image numbers are correctly set."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps(mock_claude_prompt_generation_response))
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = generator.generate_prompts(sample_concept_analysis, sample_style_config)

        assert result[0].image_number == 1
        assert result[1].image_number == 2

    def test_generate_prompts_sets_flow_connections(
        self,
        generator,
        mock_anthropic_client,
        sample_concept_analysis,
        sample_style_config,
        mock_claude_prompt_generation_response,
    ):
        """Test that flow connections are correctly set."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps(mock_claude_prompt_generation_response))
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = generator.generate_prompts(sample_concept_analysis, sample_style_config)

        # First image has no previous
        assert result[0].flow_connection.previous is None
        assert result[0].flow_connection.next_image == 2

        # Last image has no next
        assert result[1].flow_connection.previous == 1
        assert result[1].flow_connection.next_image is None

    def test_generate_prompts_injects_style(
        self,
        generator,
        mock_anthropic_client,
        sample_concept_analysis,
        sample_style_config,
        mock_claude_prompt_generation_response,
    ):
        """Test that style is injected into prompts."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text=json.dumps(mock_claude_prompt_generation_response))
        ]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = generator.generate_prompts(sample_concept_analysis, sample_style_config)

        # Style should be reflected in the call to Claude
        call_args = mock_anthropic_client.messages.create.call_args
        call_content = str(call_args)
        # The style should be mentioned in the prompt
        assert "style" in call_content.lower()

    def test_generate_prompts_handles_json_in_code_block(
        self,
        generator,
        mock_anthropic_client,
        sample_concept_analysis,
        sample_style_config,
        mock_claude_prompt_generation_response,
    ):
        """Test parsing JSON wrapped in markdown code block."""
        response_text = f"```json\n{json.dumps(mock_claude_prompt_generation_response)}\n```"
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=response_text)]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = generator.generate_prompts(sample_concept_analysis, sample_style_config)

        assert len(result) == 2

    def test_generate_prompts_raises_on_invalid_json(
        self,
        generator,
        mock_anthropic_client,
        sample_concept_analysis,
        sample_style_config,
    ):
        """Test that invalid JSON raises PromptGenerationError."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="{ invalid json }")]
        mock_anthropic_client.messages.create.return_value = mock_response

        with pytest.raises(PromptGenerationError):
            generator.generate_prompts(sample_concept_analysis, sample_style_config)

    def test_generate_prompts_raises_on_api_error(
        self,
        generator,
        mock_anthropic_client,
        sample_concept_analysis,
        sample_style_config,
    ):
        """Test that API errors are wrapped in PromptGenerationError."""
        import anthropic

        mock_anthropic_client.messages.create.side_effect = anthropic.APIError(
            message="API Error",
            request=MagicMock(),
            body=None,
        )

        with pytest.raises(PromptGenerationError):
            generator.generate_prompts(sample_concept_analysis, sample_style_config)


class TestPromptRefinement:
    """Tests for prompt refinement functionality."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client."""
        return MagicMock()

    @pytest.fixture
    def generator(self, mock_anthropic_client):
        """Create a generator with mocked client."""
        with patch("visual_explainer.prompt_generator.anthropic.Anthropic") as mock:
            mock.return_value = mock_anthropic_client
            gen = PromptGenerator(api_key="test-key")
            gen.client = mock_anthropic_client
            return gen

    @pytest.fixture
    def sample_original_prompt(self):
        """Create a sample original prompt for refinement."""
        return ImagePrompt(
            image_number=1,
            image_title="Test Image",
            concepts_covered=[1],
            visual_intent="Test intent",
            prompt=PromptDetails(
                main_prompt="Original prompt text",
                style_guidance="Original style",
                color_palette="Original colors",
                composition="Original composition",
                avoid="Original avoid",
            ),
            success_criteria=["Criterion 1", "Criterion 2"],
            flow_connection=FlowConnection(previous=None, next_image=2),
        )

    @pytest.fixture
    def sample_feedback(self):
        """Create sample evaluation feedback for refinement."""
        return EvaluationResult(
            image_id=1,
            iteration=1,
            overall_score=0.65,
            criteria_scores=CriteriaScores(
                concept_clarity=0.60,
                visual_appeal=0.70,
                audience_appropriateness=0.65,
                flow_continuity=0.65,
            ),
            strengths=["Good colors"],
            weaknesses=["Unclear concept", "Too crowded"],
            missing_elements=["Clear hierarchy"],
            verdict=EvaluationVerdict.NEEDS_REFINEMENT,
            refinement_suggestions=["Simplify layout", "Add more contrast"],
        )

    def test_refine_prompt_returns_image_prompt(
        self,
        generator,
        mock_anthropic_client,
        sample_original_prompt,
        sample_feedback,
        sample_style_config,
    ):
        """Test that refine_prompt returns an ImagePrompt."""
        refined_response = {
            "main_prompt": "Refined prompt text",
            "style_guidance": "Refined style",
            "composition": "Refined composition",
            "color_palette": "Refined colors",
            "avoid": "Refined avoid",
            "success_criteria": ["New criterion"],
            "refinement_reasoning": "Made it simpler",
        }
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(refined_response))]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = generator.refine_prompt(
            original=sample_original_prompt,
            feedback=sample_feedback,
            attempt=2,
            style=sample_style_config,
        )

        assert isinstance(result, ImagePrompt)
        assert result.prompt.main_prompt == "Refined prompt text"

    def test_refine_prompt_preserves_image_number(
        self,
        generator,
        mock_anthropic_client,
        sample_original_prompt,
        sample_feedback,
        sample_style_config,
    ):
        """Test that image number is preserved during refinement."""
        refined_response = {
            "main_prompt": "Refined",
            "style_guidance": "Refined",
        }
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(refined_response))]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = generator.refine_prompt(
            original=sample_original_prompt,
            feedback=sample_feedback,
            attempt=2,
            style=sample_style_config,
        )

        assert result.image_number == sample_original_prompt.image_number

    def test_refinement_strategy_attempt_2(
        self,
        generator,
        sample_feedback,
    ):
        """Test refinement strategy for attempt 2 (specific fixes)."""
        strategy = generator._get_refinement_strategy(2, sample_feedback)
        assert strategy["name"] == "specific_fixes"
        assert "feedback" in strategy["description"].lower() or "fixes" in strategy["description"].lower()

    def test_refinement_strategy_attempt_3(
        self,
        generator,
        sample_feedback,
    ):
        """Test refinement strategy for attempt 3 (strengthen and simplify)."""
        strategy = generator._get_refinement_strategy(3, sample_feedback)
        assert strategy["name"] == "strengthen_and_simplify"
        assert "simplify" in strategy["description"].lower() or "strengthen" in strategy["description"].lower()

    def test_refinement_strategy_attempt_4(
        self,
        generator,
        sample_feedback,
    ):
        """Test refinement strategy for attempt 4 (alternative metaphor)."""
        strategy = generator._get_refinement_strategy(4, sample_feedback)
        assert strategy["name"] == "alternative_metaphor"
        assert "metaphor" in strategy["description"].lower() or "alternative" in strategy["description"].lower()

    def test_refinement_strategy_attempt_5_plus(
        self,
        generator,
        sample_feedback,
    ):
        """Test refinement strategy for attempt 5+ (fundamental restructure)."""
        strategy = generator._get_refinement_strategy(5, sample_feedback)
        assert strategy["name"] == "fundamental_restructure"
        assert "restructure" in strategy["description"].lower() or "fundamental" in strategy["description"].lower()

    def test_refinement_strategies_are_different(
        self,
        generator,
        sample_feedback,
    ):
        """Test that different attempts produce different strategies."""
        strategy2 = generator._get_refinement_strategy(2, sample_feedback)
        strategy3 = generator._get_refinement_strategy(3, sample_feedback)
        strategy4 = generator._get_refinement_strategy(4, sample_feedback)
        strategy5 = generator._get_refinement_strategy(5, sample_feedback)

        names = [s["name"] for s in [strategy2, strategy3, strategy4, strategy5]]
        assert len(set(names)) == 4  # All unique

    def test_refinement_identifies_weakest_criterion(
        self,
        generator,
    ):
        """Test that refinement identifies the weakest criterion."""
        feedback = EvaluationResult(
            image_id=1,
            iteration=1,
            overall_score=0.65,
            criteria_scores=CriteriaScores(
                concept_clarity=0.30,  # Weakest
                visual_appeal=0.80,
                audience_appropriateness=0.70,
                flow_continuity=0.75,
            ),
            verdict=EvaluationVerdict.NEEDS_REFINEMENT,
        )

        strategy = generator._get_refinement_strategy(3, feedback)
        # Strategy should focus on the weakest area
        assert "concept_clarity" in str(strategy["instructions"]).lower() or "0.30" in str(strategy["instructions"])


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_generate_prompts_function(
        self,
        sample_concept_analysis,
        sample_style_config,
        mock_claude_prompt_generation_response,
    ):
        """Test the generate_prompts convenience function."""
        with patch("visual_explainer.prompt_generator.PromptGenerator") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            mock_instance.generate_prompts.return_value = [MagicMock(spec=ImagePrompt)]

            result = generate_prompts(
                analysis=sample_concept_analysis,
                style=sample_style_config,
                api_key="test-key",
            )

            mock_class.assert_called_once()
            mock_instance.generate_prompts.assert_called_once()

    def test_refine_prompt_function(
        self,
        sample_style_config,
    ):
        """Test the refine_prompt convenience function."""
        original = ImagePrompt(
            image_number=1,
            image_title="Test",
            visual_intent="Test",
            prompt=PromptDetails(main_prompt="Test"),
            success_criteria=["Test"],
        )
        feedback = EvaluationResult(
            image_id=1,
            iteration=1,
            overall_score=0.65,
            criteria_scores=CriteriaScores(
                concept_clarity=0.65,
                visual_appeal=0.65,
                audience_appropriateness=0.65,
                flow_continuity=0.65,
            ),
            verdict=EvaluationVerdict.NEEDS_REFINEMENT,
        )

        with patch("visual_explainer.prompt_generator.PromptGenerator") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            mock_instance.refine_prompt.return_value = MagicMock(spec=ImagePrompt)

            refine_prompt(
                original=original,
                feedback=feedback,
                attempt=2,
                style=sample_style_config,
                api_key="test-key",
            )

            mock_class.assert_called_once()
            mock_instance.refine_prompt.assert_called_once()

    def test_create_prompt_generator_function(self):
        """Test the create_prompt_generator factory function."""
        with patch("visual_explainer.prompt_generator.anthropic.Anthropic"):
            gen = create_prompt_generator(api_key="test-key")
            assert isinstance(gen, PromptGenerator)


class TestNegativePromptCombination:
    """Tests for combining negative prompts."""

    @pytest.fixture
    def generator(self):
        """Create a generator for testing."""
        with patch("visual_explainer.prompt_generator.anthropic.Anthropic"):
            return PromptGenerator(api_key="test-key")

    def test_combine_single_prompt(self, generator):
        """Test combining a single negative prompt."""
        result = generator._combine_negative_prompts("text, labels")
        assert "text" in result
        assert "labels" in result

    def test_combine_multiple_prompts(self, generator):
        """Test combining multiple negative prompts."""
        result = generator._combine_negative_prompts(
            "text, labels",
            "clutter, noise",
            "neon colors",
        )
        assert "text" in result
        assert "clutter" in result
        assert "neon" in result

    def test_deduplicates_entries(self, generator):
        """Test that duplicate entries are removed."""
        result = generator._combine_negative_prompts(
            "text, labels, text",  # Duplicate within
            "labels",  # Duplicate across
        )
        count = result.lower().count("text")
        assert count == 1

    def test_handles_empty_prompts(self, generator):
        """Test handling of empty prompts."""
        result = generator._combine_negative_prompts("", "text", "", "labels", "")
        assert "text" in result
        assert "labels" in result

    def test_strips_whitespace(self, generator):
        """Test that whitespace is stripped."""
        result = generator._combine_negative_prompts("  text  ,  labels  ")
        assert result.startswith("text") or result.endswith("text")  # Not starting/ending with spaces


class TestDefaultCriteriaGeneration:
    """Tests for default success criteria generation."""

    @pytest.fixture
    def generator(self):
        """Create a generator for testing."""
        with patch("visual_explainer.prompt_generator.anthropic.Anthropic"):
            return PromptGenerator(api_key="test-key")

    def test_generates_default_criteria(self, generator):
        """Test that default criteria are generated."""
        prompt_data = {"concepts_covered": [1, 2]}
        criteria = generator._generate_default_criteria(prompt_data)
        assert len(criteria) >= 3

    def test_includes_concept_criterion(self, generator):
        """Test that concept-specific criterion is included."""
        prompt_data = {"concepts_covered": [1, 2]}
        criteria = generator._generate_default_criteria(prompt_data)
        # Should have a criterion mentioning the concepts
        assert any("1" in c or "2" in c or "concept" in c.lower() for c in criteria)

    def test_handles_no_concepts(self, generator):
        """Test handling when no concepts are covered."""
        prompt_data = {"concepts_covered": []}
        criteria = generator._generate_default_criteria(prompt_data)
        assert len(criteria) >= 3


class TestPromptFormatting:
    """Tests for prompt formatting in PromptGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a generator for testing."""
        with patch("visual_explainer.prompt_generator.anthropic.Anthropic"):
            return PromptGenerator(api_key="test-key")

    def test_format_concepts_for_prompt(self, generator, sample_concept_analysis):
        """Test formatting concepts for the generation prompt."""
        formatted = generator._format_concepts_for_prompt(sample_concept_analysis)
        assert "Neural Networks" in formatted
        assert "Training Data" in formatted

    def test_format_logical_flow(self, generator, sample_concept_analysis):
        """Test formatting logical flow for the prompt."""
        formatted = generator._format_logical_flow(sample_concept_analysis)
        # Should describe the flow relationships
        assert "leads_to" in formatted.lower() or "depends_on" in formatted.lower() or "--" in formatted

    def test_format_logical_flow_empty(self, generator, sample_concepts):
        """Test formatting when no logical flow exists."""
        analysis = ConceptAnalysis(
            title="Test",
            summary="Test",
            concepts=sample_concepts,
            logical_flow=[],  # Empty
        )
        formatted = generator._format_logical_flow(analysis)
        assert "linear" in formatted.lower() or formatted == ""
