"""Tests for prompt_refiner module.

Tests the PromptRefiner class which handles iterative prompt refinement
based on evaluation feedback with escalating strategies.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from visual_explainer.models import (
    CriteriaScores,
    EvaluationResult,
    EvaluationVerdict,
    FlowConnection,
    ImagePrompt,
    PromptDetails,
)
from visual_explainer.prompt_refiner import PromptRefiner


class TestPromptRefinerInit:
    """Tests for PromptRefiner initialization."""

    def test_init_with_client(self):
        """Test initialization with a pre-configured client."""
        client = MagicMock()
        refiner = PromptRefiner(client=client, model="claude-sonnet-4-20250514")
        assert refiner.client is client
        assert refiner.model == "claude-sonnet-4-20250514"

    def test_init_uses_default_model(self):
        """Test that default model is set if not specified."""
        client = MagicMock()
        refiner = PromptRefiner(client=client)
        assert "claude" in refiner.model.lower() or "sonnet" in refiner.model.lower()

    def test_init_creates_internal_config(self):
        """Test that internal config is created if not provided."""
        client = MagicMock()
        refiner = PromptRefiner(client=client)
        assert refiner.internal_config is not None


class TestRefinementStrategies:
    """Tests for refinement strategy determination."""

    @pytest.fixture
    def refiner(self):
        """Create a refiner for testing."""
        client = MagicMock()
        return PromptRefiner(client=client)

    @pytest.fixture
    def sample_feedback(self):
        """Create sample evaluation feedback."""
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

    def test_strategy_attempt_2_is_specific_fixes(self, refiner, sample_feedback):
        """Test that attempt 2 uses specific fixes strategy."""
        strategy = refiner._get_refinement_strategy(2, sample_feedback)
        assert strategy["name"] == "specific_fixes"

    def test_strategy_attempt_3_is_strengthen_and_simplify(self, refiner, sample_feedback):
        """Test that attempt 3 uses strengthen and simplify strategy."""
        strategy = refiner._get_refinement_strategy(3, sample_feedback)
        assert strategy["name"] == "strengthen_and_simplify"

    def test_strategy_attempt_4_is_alternative_metaphor(self, refiner, sample_feedback):
        """Test that attempt 4 uses alternative metaphor strategy."""
        strategy = refiner._get_refinement_strategy(4, sample_feedback)
        assert strategy["name"] == "alternative_metaphor"

    def test_strategy_attempt_5_is_fundamental_restructure(self, refiner, sample_feedback):
        """Test that attempt 5+ uses fundamental restructure strategy."""
        strategy = refiner._get_refinement_strategy(5, sample_feedback)
        assert strategy["name"] == "fundamental_restructure"

    def test_strategy_attempt_6_also_uses_restructure(self, refiner, sample_feedback):
        """Test that attempt 6 also uses fundamental restructure."""
        strategy = refiner._get_refinement_strategy(6, sample_feedback)
        assert strategy["name"] == "fundamental_restructure"

    def test_all_strategies_are_unique(self, refiner, sample_feedback):
        """Test that each attempt produces a unique strategy name."""
        strategies = [refiner._get_refinement_strategy(i, sample_feedback) for i in range(2, 6)]
        names = [s["name"] for s in strategies]
        assert len(set(names)) == 4

    def test_strategy_identifies_weakest_criterion(self, refiner):
        """Test that strategy identifies the weakest criterion."""
        feedback = EvaluationResult(
            image_id=1,
            iteration=1,
            overall_score=0.65,
            criteria_scores=CriteriaScores(
                concept_clarity=0.30,
                visual_appeal=0.80,
                audience_appropriateness=0.70,
                flow_continuity=0.75,
            ),
            verdict=EvaluationVerdict.NEEDS_REFINEMENT,
        )
        strategy = refiner._get_refinement_strategy(3, feedback)
        assert "concept_clarity" in str(strategy["instructions"]).lower() or "0.30" in str(
            strategy["instructions"]
        )

    def test_strategy_attempt_2_preserves_strengths(self, refiner, sample_feedback):
        """Test that attempt 2 strategy includes strengths to preserve."""
        strategy = refiner._get_refinement_strategy(2, sample_feedback)
        assert strategy["preserve"] == sample_feedback.strengths

    def test_strategy_attempt_4_has_empty_preserve(self, refiner, sample_feedback):
        """Test that attempt 4 strategy has empty preserve list (fresh approach)."""
        strategy = refiner._get_refinement_strategy(4, sample_feedback)
        assert strategy["preserve"] == []

    def test_strategy_has_required_keys(self, refiner, sample_feedback):
        """Test that every strategy has the required keys."""
        for attempt in range(2, 6):
            strategy = refiner._get_refinement_strategy(attempt, sample_feedback)
            assert "name" in strategy
            assert "description" in strategy
            assert "instructions" in strategy
            assert "focus_areas" in strategy
            assert "preserve" in strategy


class TestBuildRefinementPrompt:
    """Tests for building refinement prompts."""

    @pytest.fixture
    def refiner(self):
        """Create a refiner for testing."""
        client = MagicMock()
        return PromptRefiner(client=client)

    @pytest.fixture
    def sample_original(self):
        """Create a sample original prompt."""
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
            success_criteria=["Criterion 1"],
            flow_connection=FlowConnection(previous=None, next_image=2),
        )

    @pytest.fixture
    def sample_feedback(self):
        """Create sample feedback."""
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
            weaknesses=["Unclear"],
            missing_elements=["Hierarchy"],
            verdict=EvaluationVerdict.NEEDS_REFINEMENT,
            refinement_suggestions=["Simplify"],
        )

    def test_build_refinement_prompt_includes_original(
        self, refiner, sample_original, sample_feedback
    ):
        """Test that the refinement prompt includes original prompt details."""
        strategy = refiner._get_refinement_strategy(2, sample_feedback)
        prompt = refiner._build_refinement_prompt(
            original=sample_original,
            feedback=sample_feedback,
            strategy=strategy,
            style={"core_style": "test", "color_constraints": "blue"},
        )
        assert "Original prompt text" in prompt
        assert "Test Image" in prompt

    def test_build_refinement_prompt_includes_feedback(
        self, refiner, sample_original, sample_feedback
    ):
        """Test that the refinement prompt includes feedback."""
        strategy = refiner._get_refinement_strategy(2, sample_feedback)
        prompt = refiner._build_refinement_prompt(
            original=sample_original,
            feedback=sample_feedback,
            strategy=strategy,
            style={"core_style": "test"},
        )
        assert "0.65" in prompt  # overall score
        assert "Good colors" in prompt  # strength
        assert "Unclear" in prompt  # weakness

    def test_build_refinement_prompt_includes_strategy(
        self, refiner, sample_original, sample_feedback
    ):
        """Test that the refinement prompt includes strategy name."""
        strategy = refiner._get_refinement_strategy(2, sample_feedback)
        prompt = refiner._build_refinement_prompt(
            original=sample_original,
            feedback=sample_feedback,
            strategy=strategy,
            style={},
        )
        assert "specific_fixes" in prompt


class TestParseRefinementResponse:
    """Tests for parsing refinement responses."""

    @pytest.fixture
    def refiner(self):
        """Create a refiner for testing."""
        client = MagicMock()
        return PromptRefiner(client=client)

    def test_parse_json_directly(self, refiner):
        """Test parsing a direct JSON response."""
        data = {"main_prompt": "refined", "style_guidance": "new style"}
        result = refiner._parse_refinement_response(json.dumps(data))
        assert result["main_prompt"] == "refined"

    def test_parse_json_in_code_block(self, refiner):
        """Test parsing JSON wrapped in a markdown code block."""
        data = {"main_prompt": "refined"}
        result = refiner._parse_refinement_response(f"```json\n{json.dumps(data)}\n```")
        assert result["main_prompt"] == "refined"

    def test_parse_json_in_plain_code_block(self, refiner):
        """Test parsing JSON wrapped in a plain code block."""
        data = {"main_prompt": "refined"}
        result = refiner._parse_refinement_response(f"```\n{json.dumps(data)}\n```")
        assert result["main_prompt"] == "refined"

    def test_parse_json_with_surrounding_text(self, refiner):
        """Test parsing JSON object from text containing other content."""
        data = {"main_prompt": "refined"}
        result = refiner._parse_refinement_response(
            f"Here is the result: {json.dumps(data)} Hope this helps!"
        )
        assert result["main_prompt"] == "refined"


class TestBuildRefinedPrompt:
    """Tests for building refined ImagePrompt objects."""

    @pytest.fixture
    def refiner(self):
        """Create a refiner for testing."""
        client = MagicMock()
        return PromptRefiner(client=client)

    @pytest.fixture
    def sample_original(self):
        """Create a sample original prompt."""
        return ImagePrompt(
            image_number=1,
            image_title="Test Image",
            concepts_covered=[1, 2],
            visual_intent="Test intent",
            prompt=PromptDetails(
                main_prompt="Original prompt",
                style_guidance="Original style",
                color_palette="Original colors",
                composition="Original composition",
                avoid="Original avoid",
            ),
            success_criteria=["Original criterion"],
            flow_connection=FlowConnection(previous=None, next_image=2),
        )

    def test_build_refined_prompt_updates_main_prompt(self, refiner, sample_original):
        """Test that refined data updates the main prompt."""
        refined_data = {"main_prompt": "New refined prompt"}
        result = refiner._build_refined_prompt(sample_original, refined_data, attempt=2)
        assert result.prompt.main_prompt == "New refined prompt"

    def test_build_refined_prompt_preserves_image_number(self, refiner, sample_original):
        """Test that image number is preserved."""
        refined_data = {"main_prompt": "Refined"}
        result = refiner._build_refined_prompt(sample_original, refined_data, attempt=2)
        assert result.image_number == 1

    def test_build_refined_prompt_preserves_concepts(self, refiner, sample_original):
        """Test that concepts covered are preserved."""
        refined_data = {"main_prompt": "Refined"}
        result = refiner._build_refined_prompt(sample_original, refined_data, attempt=2)
        assert result.concepts_covered == [1, 2]

    def test_build_refined_prompt_preserves_flow_connection(self, refiner, sample_original):
        """Test that flow connection is preserved."""
        refined_data = {"main_prompt": "Refined"}
        result = refiner._build_refined_prompt(sample_original, refined_data, attempt=2)
        assert result.flow_connection.next_image == 2

    def test_build_refined_prompt_uses_original_if_missing(self, refiner, sample_original):
        """Test that original values are used if not in refined data."""
        refined_data = {}  # Empty - should use all originals
        result = refiner._build_refined_prompt(sample_original, refined_data, attempt=2)
        assert result.prompt.main_prompt == "Original prompt"
        assert result.prompt.style_guidance == "Original style"

    def test_build_refined_prompt_updates_success_criteria(self, refiner, sample_original):
        """Test that success criteria can be updated."""
        refined_data = {"success_criteria": ["New criterion 1", "New criterion 2"]}
        result = refiner._build_refined_prompt(sample_original, refined_data, attempt=2)
        assert result.success_criteria == ["New criterion 1", "New criterion 2"]

    def test_build_refined_prompt_keeps_original_criteria_if_empty(self, refiner, sample_original):
        """Test that original criteria are kept if refined provides empty list."""
        refined_data = {"success_criteria": []}
        result = refiner._build_refined_prompt(sample_original, refined_data, attempt=2)
        assert result.success_criteria == ["Original criterion"]


class TestRefinePromptEndToEnd:
    """End-to-end tests for the refine_prompt method."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Anthropic client."""
        return MagicMock()

    @pytest.fixture
    def refiner(self, mock_client):
        """Create a refiner with mocked client."""
        return PromptRefiner(client=mock_client)

    @pytest.fixture
    def sample_original(self):
        """Create a sample original prompt."""
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
            success_criteria=["Criterion 1"],
            flow_connection=FlowConnection(previous=None, next_image=2),
        )

    @pytest.fixture
    def sample_feedback(self):
        """Create sample feedback."""
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
            weaknesses=["Unclear"],
            missing_elements=["Hierarchy"],
            verdict=EvaluationVerdict.NEEDS_REFINEMENT,
            refinement_suggestions=["Simplify"],
        )

    def test_refine_prompt_returns_image_prompt(
        self, refiner, mock_client, sample_original, sample_feedback, sample_style_config
    ):
        """Test that refine_prompt returns an ImagePrompt."""
        refined_response = {
            "main_prompt": "Refined prompt text",
            "style_guidance": "Refined style",
            "success_criteria": ["New criterion"],
        }
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(refined_response))]
        mock_client.messages.create.return_value = mock_response

        result = refiner.refine_prompt(
            original=sample_original,
            feedback=sample_feedback,
            attempt=2,
            style=sample_style_config,
        )
        assert isinstance(result, ImagePrompt)
        assert result.prompt.main_prompt == "Refined prompt text"

    def test_refine_prompt_calls_api(
        self, refiner, mock_client, sample_original, sample_feedback, sample_style_config
    ):
        """Test that refine_prompt calls the Claude API."""
        refined_response = {"main_prompt": "Refined"}
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(refined_response))]
        mock_client.messages.create.return_value = mock_response

        refiner.refine_prompt(
            original=sample_original,
            feedback=sample_feedback,
            attempt=2,
            style=sample_style_config,
        )
        mock_client.messages.create.assert_called_once()

    def test_refine_prompt_raises_on_api_error(
        self, refiner, mock_client, sample_original, sample_feedback, sample_style_config
    ):
        """Test that API errors are wrapped in PromptGenerationError."""
        import anthropic

        from visual_explainer.prompt_generator import PromptGenerationError

        mock_client.messages.create.side_effect = anthropic.APIError(
            message="API Error",
            request=MagicMock(),
            body=None,
        )
        with pytest.raises(PromptGenerationError):
            refiner.refine_prompt(
                original=sample_original,
                feedback=sample_feedback,
                attempt=2,
                style=sample_style_config,
            )
