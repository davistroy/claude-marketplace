"""Tests for visual_explainer.pipeline.

Covers the phase helpers (_analyze_concepts, _generate_prompts,
_evaluate_and_refine, _execute_generation_loop, _save_outputs) and the two
top-level orchestrators (run_generation_pipeline, load_checkpoint_and_resume).

Sibling collaborators (concept_analyzer, style_loader, prompt_generator,
image_generator, image_evaluator) are patched at their *source* module
because pipeline.py imports them with function-scoped ``from ... import``
statements, which re-resolve the name from the source module on every call.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from unittest.mock import AsyncMock, MagicMock, patch

from visual_explainer.config import GenerationConfig
from visual_explainer.image_generator import GenerationResult, GenerationStatus
from visual_explainer.models import (
    CriteriaScores,
    EvaluationResult,
    EvaluationVerdict,
    ImagePrompt,
    ImageResult,
)
from visual_explainer.pipeline import (
    _analyze_concepts,
    _evaluate_and_refine,
    _execute_generation_loop,
    _generate_prompts,
    _generate_single_image,
    _save_outputs,
    load_checkpoint_and_resume,
    run_generation_pipeline,
)


def _prompt_with_number(base: ImagePrompt, number: int) -> ImagePrompt:
    """Return a copy of an ImagePrompt fixture with a different image_number."""
    return base.model_copy(update={"image_number": number})


def _make_evaluation(
    score: float, verdict: EvaluationVerdict, iteration: int = 1
) -> EvaluationResult:
    return EvaluationResult(
        image_id=1,
        iteration=iteration,
        overall_score=score,
        criteria_scores=CriteriaScores(
            concept_clarity=score,
            visual_appeal=score,
            audience_appropriateness=score,
            flow_continuity=score,
        ),
        strengths=[],
        weaknesses=["needs work"],
        missing_elements=[],
        verdict=verdict,
        refinement_suggestions=["improve it"],
    )


# =============================================================================
# _analyze_concepts
# =============================================================================


class TestAnalyzeConcepts:
    async def test_returns_analysis_style_and_api_calls(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
    ):
        with (
            patch(
                "visual_explainer.concept_analyzer.analyze_document",
                new_callable=AsyncMock,
                return_value=sample_concept_analysis,
            ) as mock_analyze,
            patch(
                "visual_explainer.style_loader.load_style",
                return_value=sample_style_config,
            ) as mock_load_style,
        ):
            analysis, style, style_display_name, api_calls = await _analyze_concepts(
                sample_generation_config,
                sample_internal_config,
                "professional-clean",
                None,
                False,
            )

        mock_load_style.assert_called_once_with("professional-clean")
        mock_analyze.assert_awaited_once_with(
            sample_generation_config.input_source,
            sample_generation_config,
            sample_internal_config,
            infographic_mode=False,
        )
        assert analysis is sample_concept_analysis
        assert style is sample_style_config
        assert style_display_name == sample_style_config.style_name
        assert api_calls == 1

    async def test_falls_back_to_style_name_when_style_not_found(
        self, sample_generation_config, sample_internal_config, sample_concept_analysis
    ):
        with (
            patch(
                "visual_explainer.concept_analyzer.analyze_document",
                new_callable=AsyncMock,
                return_value=sample_concept_analysis,
            ),
            patch("visual_explainer.style_loader.load_style", return_value=None),
        ):
            _, style, style_display_name, _ = await _analyze_concepts(
                sample_generation_config,
                sample_internal_config,
                "missing-style",
                None,
                False,
            )

        assert style is None
        assert style_display_name == "missing-style"

    async def test_prints_progress_and_summary_when_console_provided(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
    ):
        console = MagicMock()
        with (
            patch(
                "visual_explainer.concept_analyzer.analyze_document",
                new_callable=AsyncMock,
                return_value=sample_concept_analysis,
            ),
            patch("visual_explainer.style_loader.load_style", return_value=sample_style_config),
            patch("visual_explainer.pipeline.display_analysis_summary") as mock_display,
        ):
            await _analyze_concepts(
                sample_generation_config,
                sample_internal_config,
                "professional-clean",
                console,
                True,
            )

        assert console.print.call_count == 2
        printed = " ".join(str(c.args[0]) for c in console.print.call_args_list)
        assert "infographic pages" in printed
        mock_display.assert_called_once_with(sample_concept_analysis, infographic_mode=True)


# =============================================================================
# _generate_prompts
# =============================================================================


class TestGeneratePrompts:
    def test_standard_generation_truncates_to_config_image_count(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
    ):
        prompt2 = _prompt_with_number(sample_image_prompt, 2)
        prompt3 = _prompt_with_number(sample_image_prompt, 3)
        mock_generator = MagicMock()
        mock_generator.generate_prompts.return_value = [sample_image_prompt, prompt2, prompt3]

        with patch(
            "visual_explainer.prompt_generator.PromptGenerator", return_value=mock_generator
        ) as mock_cls:
            prompts, prompt_generator, api_calls = _generate_prompts(
                sample_generation_config,
                sample_internal_config,
                sample_concept_analysis,
                sample_style_config,
                None,
                False,
            )

        mock_cls.assert_called_once_with(
            internal_config=sample_internal_config, model=sample_internal_config.claude_model
        )
        mock_generator.generate_prompts.assert_called_once_with(
            sample_concept_analysis, sample_style_config, sample_generation_config
        )
        # sample_generation_config.image_count == 2, generator returned 3 -> truncated
        assert [p.image_number for p in prompts] == [1, 2]
        assert prompt_generator is mock_generator
        assert api_calls == 1

    def test_uses_recommended_image_count_when_config_image_count_is_zero(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
    ):
        config = sample_generation_config.model_copy(update={"image_count": 0})
        mock_generator = MagicMock()
        mock_generator.generate_prompts.return_value = [sample_image_prompt]

        with patch(
            "visual_explainer.prompt_generator.PromptGenerator", return_value=mock_generator
        ):
            prompts, _, _ = _generate_prompts(
                config,
                sample_internal_config,
                sample_concept_analysis,
                sample_style_config,
                None,
                False,
            )

        # recommended_image_count == 2, only 1 prompt returned -> nothing truncated
        assert len(prompts) == 1

    def test_infographic_mode_generates_one_prompt_per_page(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_style_config,
        sample_image_prompt,
    ):
        analysis = MagicMock()
        analysis.page_recommendation = MagicMock()
        analysis.page_recommendation.pages = [MagicMock(), MagicMock(), MagicMock()]

        prompt2 = _prompt_with_number(sample_image_prompt, 2)
        prompt3 = _prompt_with_number(sample_image_prompt, 3)
        mock_generator = MagicMock()
        mock_generator.generate_infographic_prompts.return_value = [
            sample_image_prompt,
            prompt2,
            prompt3,
        ]

        with patch(
            "visual_explainer.prompt_generator.PromptGenerator", return_value=mock_generator
        ):
            prompts, _, api_calls = _generate_prompts(
                sample_generation_config,
                sample_internal_config,
                analysis,
                sample_style_config,
                None,
                True,
            )

        mock_generator.generate_infographic_prompts.assert_called_once_with(
            analysis, sample_style_config, sample_generation_config
        )
        # No truncation applied on the infographic branch, even though
        # config.image_count (2) < len(prompts) (3).
        assert len(prompts) == 3
        assert api_calls == 3  # one API call counted per page

    def test_prints_progress_when_console_provided(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
    ):
        console = MagicMock()
        mock_generator = MagicMock()
        mock_generator.generate_prompts.return_value = [sample_image_prompt]

        with patch(
            "visual_explainer.prompt_generator.PromptGenerator", return_value=mock_generator
        ):
            _generate_prompts(
                sample_generation_config,
                sample_internal_config,
                sample_concept_analysis,
                sample_style_config,
                console,
                False,
            )

        console.print.assert_called_once()
        assert "image prompts" in str(console.print.call_args.args[0])


# =============================================================================
# _evaluate_and_refine
# =============================================================================


class TestEvaluateAndRefine:
    async def test_needs_refinement_refines_prompt_and_writes_files(
        self,
        temp_output_dir,
        sample_image_prompt,
        sample_concept_analysis,
        sample_evaluation_result,
        sample_generation_config,
        sample_style_config,
    ):
        image_dir = temp_output_dir / "image-01"
        image_dir.mkdir()

        gen_result = MagicMock(image_data=b"fake-jpg-bytes", duration_seconds=2.5)
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image.return_value = sample_evaluation_result

        refined_prompt = sample_image_prompt.model_copy(
            update={
                "prompt": sample_image_prompt.prompt.model_copy(
                    update={"main_prompt": "REFINED PROMPT TEXT"}
                )
            }
        )
        prompt_generator = MagicMock()
        prompt_generator.refine_prompt.return_value = refined_prompt

        progress = MagicMock()
        result = ImageResult(image_number=1, title="Test Image")

        eval_result, new_current_prompt, api_calls = await _evaluate_and_refine(
            gen_result=gen_result,
            current_prompt=sample_image_prompt,
            prompt=sample_image_prompt,
            attempt=1,
            image_dir=image_dir,
            image_evaluator=image_evaluator,
            analysis=sample_concept_analysis,
            total_prompts=2,
            style_display_name="Test_Style",
            result=result,
            progress=progress,
            prompt_generator=prompt_generator,
            style=sample_style_config,
            config=sample_generation_config,  # max_iterations=3
        )

        assert eval_result is sample_evaluation_result
        assert new_current_prompt is refined_prompt
        assert api_calls == 2  # 1 evaluation + 1 refinement

        image_file = image_dir / "attempt-01.jpg"
        assert image_file.read_bytes() == b"fake-jpg-bytes"
        eval_file = image_dir / "evaluation-01.json"
        saved = json.loads(eval_file.read_text(encoding="utf-8"))
        assert saved["overall_score"] == sample_evaluation_result.overall_score

        assert result.total_attempts == 1
        assert result.attempts[0].evaluation is sample_evaluation_result
        assert result.attempts[0].duration_seconds == 2.5

        prompt_generator.refine_prompt.assert_called_once_with(
            original=sample_image_prompt,
            feedback=sample_evaluation_result,
            attempt=2,
            style=sample_style_config,
            config=sample_generation_config,
        )
        progress.show_evaluation.assert_called_once_with(sample_evaluation_result)
        progress.update_status.assert_any_call("Evaluating...")
        progress.update_status.assert_any_call("Refining prompt...")

    async def test_pass_verdict_does_not_refine(
        self,
        temp_output_dir,
        sample_image_prompt,
        sample_concept_analysis,
        sample_passing_evaluation,
        sample_generation_config,
        sample_style_config,
    ):
        image_dir = temp_output_dir / "image-01"
        image_dir.mkdir()
        gen_result = MagicMock(image_data=b"jpg-bytes", duration_seconds=1.0)
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image.return_value = sample_passing_evaluation
        prompt_generator = MagicMock()
        progress = MagicMock()
        result = ImageResult(image_number=1, title="Test Image")

        eval_result, new_current_prompt, api_calls = await _evaluate_and_refine(
            gen_result=gen_result,
            current_prompt=sample_image_prompt,
            prompt=sample_image_prompt,
            attempt=1,
            image_dir=image_dir,
            image_evaluator=image_evaluator,
            analysis=sample_concept_analysis,
            total_prompts=1,
            style_display_name="Test_Style",
            result=result,
            progress=progress,
            prompt_generator=prompt_generator,
            style=sample_style_config,
            config=sample_generation_config,
        )

        assert eval_result.verdict == EvaluationVerdict.PASS
        assert new_current_prompt is sample_image_prompt  # unchanged, no refinement
        assert api_calls == 1
        prompt_generator.refine_prompt.assert_not_called()

    async def test_needs_refinement_at_max_iterations_does_not_refine(
        self,
        temp_output_dir,
        sample_image_prompt,
        sample_concept_analysis,
        sample_evaluation_result,
        sample_style_config,
    ):
        config = GenerationConfig(
            input_source="text",
            output_dir=temp_output_dir,
            max_iterations=1,
        )
        image_dir = temp_output_dir / "image-01"
        image_dir.mkdir()
        gen_result = MagicMock(image_data=b"jpg-bytes", duration_seconds=1.0)
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image.return_value = sample_evaluation_result  # NEEDS_REFINEMENT
        prompt_generator = MagicMock()
        progress = MagicMock()
        result = ImageResult(image_number=1, title="Test Image")

        eval_result, new_current_prompt, api_calls = await _evaluate_and_refine(
            gen_result=gen_result,
            current_prompt=sample_image_prompt,
            prompt=sample_image_prompt,
            attempt=1,  # equals config.max_iterations -> attempt < max_iterations is False
            image_dir=image_dir,
            image_evaluator=image_evaluator,
            analysis=sample_concept_analysis,
            total_prompts=1,
            style_display_name="Test_Style",
            result=result,
            progress=progress,
            prompt_generator=prompt_generator,
            style=sample_style_config,
            config=config,
        )

        assert eval_result.verdict == EvaluationVerdict.NEEDS_REFINEMENT
        assert new_current_prompt is sample_image_prompt
        assert api_calls == 1
        prompt_generator.refine_prompt.assert_not_called()


# =============================================================================
# _execute_generation_loop
# =============================================================================


class TestExecuteGenerationLoop:
    async def _run(
        self,
        prompts,
        config,
        internal_config,
        analysis,
        style,
        style_display_name,
        prompt_generator,
        output_dir,
        image_generator,
        image_evaluator,
    ):
        with (
            patch(
                "visual_explainer.image_generator.GeminiImageGenerator",
                return_value=image_generator,
            ),
            patch(
                "visual_explainer.image_evaluator.ImageEvaluator",
                return_value=image_evaluator,
            ),
        ):
            return await _execute_generation_loop(
                prompts,
                config,
                internal_config,
                analysis,
                style,
                style_display_name,
                prompt_generator,
                output_dir,
                quiet=True,
                json_output=False,
            )

    async def test_success_on_first_attempt(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        sample_passing_evaluation,
        temp_output_dir,
    ):
        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(
            return_value=GenerationResult(
                status=GenerationStatus.SUCCESS, image_data=b"img-bytes-1", duration_seconds=1.5
            )
        )
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image.return_value = sample_passing_evaluation
        prompt_generator = MagicMock()

        results, api_calls = await self._run(
            [sample_image_prompt],
            sample_generation_config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            "Test_Style",
            prompt_generator,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        assert len(results) == 1
        result = results[0]
        assert result.status == "complete"
        assert result.final_attempt == 1
        assert result.final_score == sample_passing_evaluation.overall_score
        assert result.total_attempts == 1
        assert api_calls == 2  # 1 generation + 1 evaluation, no refinement

        image_generator.generate_image.assert_awaited_once()
        image_evaluator.evaluate_image.assert_called_once()
        prompt_generator.refine_prompt.assert_not_called()

        image_dir = temp_output_dir / "image-01"
        assert (image_dir / "prompt-v1.txt").read_text(
            encoding="utf-8"
        ) == sample_image_prompt.prompt.main_prompt
        assert (image_dir / "attempt-01.jpg").read_bytes() == b"img-bytes-1"
        assert (image_dir / "final.jpg").read_bytes() == b"img-bytes-1"
        assert (image_dir / "evaluation-01.json").exists()

    async def test_refinement_then_pass_on_second_attempt(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        sample_evaluation_result,
        sample_passing_evaluation,
        temp_output_dir,
    ):
        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(
            side_effect=[
                GenerationResult(
                    status=GenerationStatus.SUCCESS, image_data=b"attempt-1", duration_seconds=1.0
                ),
                GenerationResult(
                    status=GenerationStatus.SUCCESS, image_data=b"attempt-2", duration_seconds=1.0
                ),
            ]
        )
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image.side_effect = [
            sample_evaluation_result,
            sample_passing_evaluation,
        ]

        refined_prompt = sample_image_prompt.model_copy(
            update={
                "prompt": sample_image_prompt.prompt.model_copy(update={"main_prompt": "REFINED"})
            }
        )
        prompt_generator = MagicMock()
        prompt_generator.refine_prompt.return_value = refined_prompt

        results, api_calls = await self._run(
            [sample_image_prompt],
            sample_generation_config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            "Test_Style",
            prompt_generator,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        assert image_generator.generate_image.await_count == 2
        assert image_evaluator.evaluate_image.call_count == 2
        prompt_generator.refine_prompt.assert_called_once()
        assert api_calls == 5  # 2 generations + 2 evaluations + 1 refinement

        result = results[0]
        assert result.total_attempts == 2
        assert result.final_attempt == 2  # attempt 2 scored higher
        assert result.status == "complete"

        image_dir = temp_output_dir / "image-01"
        assert (image_dir / "prompt-v2.txt").read_text(encoding="utf-8") == "REFINED"
        assert (image_dir / "final.jpg").read_bytes() == b"attempt-2"

    async def test_max_iterations_reached_without_pass_uses_best_attempt(
        self,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = GenerationConfig(input_source="text", output_dir=temp_output_dir, max_iterations=2)
        eval1 = _make_evaluation(0.6, EvaluationVerdict.NEEDS_REFINEMENT, iteration=1)
        eval2 = _make_evaluation(0.7, EvaluationVerdict.NEEDS_REFINEMENT, iteration=2)

        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(
            side_effect=[
                GenerationResult(
                    status=GenerationStatus.SUCCESS, image_data=b"a1", duration_seconds=1.0
                ),
                GenerationResult(
                    status=GenerationStatus.SUCCESS, image_data=b"a2", duration_seconds=1.0
                ),
            ]
        )
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image.side_effect = [eval1, eval2]
        prompt_generator = MagicMock()
        prompt_generator.refine_prompt.return_value = sample_image_prompt

        results, api_calls = await self._run(
            [sample_image_prompt],
            config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            "Test_Style",
            prompt_generator,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        assert image_generator.generate_image.await_count == 2
        assert image_evaluator.evaluate_image.call_count == 2
        # Refinement only happens after attempt 1 (attempt < max_iterations);
        # attempt 2 == max_iterations so no further refinement is attempted.
        prompt_generator.refine_prompt.assert_called_once()
        assert api_calls == 5  # 2 generations + 2 evaluations + 1 refinement

        result = results[0]
        assert result.status == "complete"  # best-so-far is still selected even without a PASS
        assert result.final_attempt == 2
        assert result.final_score == 0.7
        assert (temp_output_dir / "image-01" / "final.jpg").read_bytes() == b"a2"

    async def test_generation_failure_marks_image_failed(
        self,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = GenerationConfig(input_source="text", output_dir=temp_output_dir, max_iterations=2)
        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(
            return_value=GenerationResult(
                status=GenerationStatus.ERROR,
                image_data=None,
                error_message="boom",
                duration_seconds=0.1,
            )
        )
        image_evaluator = MagicMock()
        prompt_generator = MagicMock()

        results, api_calls = await self._run(
            [sample_image_prompt],
            config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            "Test_Style",
            prompt_generator,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        assert image_generator.generate_image.await_count == 2  # both attempts fail generation
        image_evaluator.evaluate_image.assert_not_called()
        assert api_calls == 2  # generation attempts only, no evaluation ever ran

        result = results[0]
        assert result.status == "failed"
        assert result.total_attempts == 0
        assert not (temp_output_dir / "image-01" / "final.jpg").exists()

    async def test_later_attempt_with_lower_score_does_not_override_best(
        self,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = GenerationConfig(input_source="text", output_dir=temp_output_dir, max_iterations=2)
        eval1 = _make_evaluation(0.8, EvaluationVerdict.NEEDS_REFINEMENT, iteration=1)
        eval2 = _make_evaluation(0.5, EvaluationVerdict.NEEDS_REFINEMENT, iteration=2)  # worse

        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(
            side_effect=[
                GenerationResult(
                    status=GenerationStatus.SUCCESS, image_data=b"a1", duration_seconds=1.0
                ),
                GenerationResult(
                    status=GenerationStatus.SUCCESS, image_data=b"a2", duration_seconds=1.0
                ),
            ]
        )
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image.side_effect = [eval1, eval2]
        prompt_generator = MagicMock()
        prompt_generator.refine_prompt.return_value = sample_image_prompt

        results, _ = await self._run(
            [sample_image_prompt],
            config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            "Test_Style",
            prompt_generator,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        result = results[0]
        # Attempt 2 scored lower than attempt 1, so attempt 1's image stays "best".
        assert result.final_attempt == 1
        assert result.final_score == 0.8
        assert (temp_output_dir / "image-01" / "final.jpg").read_bytes() == b"a1"


# =============================================================================
# _save_outputs
# =============================================================================


class TestSaveOutputs:
    def test_writes_all_images_metadata_concepts_and_summary(
        self,
        temp_output_dir,
        sample_generation_config,
        sample_concept_analysis,
        sample_image_prompt,
    ):
        final_src_dir = temp_output_dir / "image-01"
        final_src_dir.mkdir()
        final_src = final_src_dir / "final.jpg"
        final_src.write_bytes(b"final-image-bytes")

        result1 = ImageResult(image_number=1, title="Neural Network Architecture")
        result1.status = "complete"
        result1.final_attempt = 2
        result1.final_score = 0.9
        result1.final_path = str(final_src)
        result1.add_attempt(image_path=str(final_src), prompt_version=1, duration_seconds=1.0)
        result1.add_attempt(image_path=str(final_src), prompt_version=2, duration_seconds=1.0)

        result2 = ImageResult(image_number=2, title="Second Image")
        result2.status = "failed"

        prompt2 = _prompt_with_number(sample_image_prompt, 2)

        _save_outputs(
            image_results=[result1, result2],
            prompts=[sample_image_prompt, prompt2],
            output_dir=temp_output_dir,
            config=sample_generation_config,
            analysis=sample_concept_analysis,
            style_display_name="Test_Style",
            timestamp="20260716-120000",
            topic_slug="test-topic",
            total_api_calls=7,
        )

        all_images_dir = temp_output_dir / "all-images"
        assert all_images_dir.is_dir()
        copied = list(all_images_dir.iterdir())
        assert len(copied) == 1  # only the "complete" result is copied
        assert copied[0].name == "01-neural-network-architecture.jpg"
        assert copied[0].read_bytes() == b"final-image-bytes"

        metadata = json.loads((temp_output_dir / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["generation_id"] == "20260716-120000-test-topic"
        assert metadata["input"]["type"] == "text"
        assert metadata["input"]["content_hash"] == sample_concept_analysis.content_hash
        assert metadata["results"]["images_planned"] == 2
        assert metadata["results"]["images_generated"] == 1
        assert metadata["results"]["total_attempts"] == 2
        assert metadata["results"]["total_api_calls"] == 7
        assert len(metadata["images"]) == 2
        assert metadata["images"][0]["status"] == "complete"
        assert metadata["images"][1]["status"] == "failed"

        concepts = json.loads((temp_output_dir / "concepts.json").read_text(encoding="utf-8"))
        assert concepts == sample_concept_analysis.model_dump(mode="json")

        summary = (temp_output_dir / "summary.md").read_text(encoding="utf-8")
        assert "Images generated: 1 of 2" in summary
        assert "Total attempts: 2" in summary
        assert "[check] **1. Neural Network Architecture** - Score: 90%" in summary
        assert "[x] **2. Second Image** - Score: N/A" in summary

    def test_no_successful_images_avoids_division_by_zero(
        self,
        temp_output_dir,
        sample_generation_config,
        sample_concept_analysis,
        sample_image_prompt,
    ):
        result1 = ImageResult(image_number=1, title="Failed Image")
        result1.status = "failed"

        _save_outputs(
            image_results=[result1],
            prompts=[sample_image_prompt],
            output_dir=temp_output_dir,
            config=sample_generation_config,
            analysis=sample_concept_analysis,
            style_display_name="Test_Style",
            timestamp="20260716-120000",
            topic_slug="none-succeeded",
            total_api_calls=1,
        )

        assert list((temp_output_dir / "all-images").iterdir()) == []
        summary = (temp_output_dir / "summary.md").read_text(encoding="utf-8")
        assert "Average score: 0%" in summary


# =============================================================================
# run_generation_pipeline
# =============================================================================


class TestRunGenerationPipeline:
    async def test_dry_run_returns_plan_without_generating(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
    ):
        config = sample_generation_config.model_copy(update={"dry_run": True})
        prompt_generator = MagicMock()

        with (
            patch(
                "visual_explainer.pipeline._analyze_concepts",
                new_callable=AsyncMock,
                return_value=(sample_concept_analysis, sample_style_config, "Test_Style", 1),
            ) as mock_analyze,
            patch(
                "visual_explainer.pipeline._generate_prompts",
                return_value=([sample_image_prompt], prompt_generator, 1),
            ) as mock_gen_prompts,
            patch("visual_explainer.pipeline.display_dry_run_plan") as mock_display,
            patch(
                "visual_explainer.pipeline._execute_generation_loop", new_callable=AsyncMock
            ) as mock_loop,
            patch("visual_explainer.pipeline._save_outputs") as mock_save,
        ):
            result = await run_generation_pipeline(
                config, sample_internal_config, "professional-clean", quiet=True
            )

        assert result == {
            "status": "dry_run",
            "image_count": 1,
            "prompts": [sample_image_prompt.model_dump(mode="json")],
        }
        mock_display.assert_called_once_with(
            sample_concept_analysis, [sample_image_prompt], config, "Test_Style"
        )
        mock_loop.assert_not_awaited()
        mock_save.assert_not_called()
        mock_analyze.assert_awaited_once()
        mock_gen_prompts.assert_called_once()

    async def test_full_pipeline_success_orchestrates_all_phases(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
    ):
        prompt2 = _prompt_with_number(sample_image_prompt, 2)
        prompt_generator = MagicMock()

        result1 = ImageResult(image_number=1, title="Image One")
        result1.status = "complete"
        result1.add_attempt(image_path="p", prompt_version=1, duration_seconds=1.0)
        result2 = ImageResult(image_number=2, title="Image Two")
        result2.status = "failed"

        with (
            patch(
                "visual_explainer.pipeline._analyze_concepts",
                new_callable=AsyncMock,
                return_value=(sample_concept_analysis, sample_style_config, "Test_Style", 2),
            ),
            patch(
                "visual_explainer.pipeline._generate_prompts",
                return_value=([sample_image_prompt, prompt2], prompt_generator, 1),
            ),
            patch(
                "visual_explainer.pipeline._execute_generation_loop",
                new_callable=AsyncMock,
                return_value=([result1, result2], 6),
            ) as mock_loop,
            patch("visual_explainer.pipeline._save_outputs") as mock_save,
            patch("visual_explainer.pipeline.display_completion_summary") as mock_completion,
        ):
            result = await run_generation_pipeline(
                sample_generation_config,
                sample_internal_config,
                "professional-clean",
                quiet=True,
            )

        assert result["status"] == "complete"
        assert result["images_generated"] == 1
        assert result["total_images"] == 2
        assert result["total_attempts"] == 1
        assert result["total_api_calls"] == 9  # 2 (analyze) + 1 (prompts) + 6 (loop)
        assert result["image_results"] == [
            result1.model_dump(mode="json"),
            result2.model_dump(mode="json"),
        ]

        mock_completion.assert_not_called()  # quiet=True suppresses the summary display
        mock_save.assert_called_once()
        save_args = mock_save.call_args.args
        assert save_args[0] == [result1, result2]
        assert save_args[1] == [sample_image_prompt, prompt2]
        output_dir = save_args[2]
        assert output_dir.exists()
        sanitized_title = re.sub(r'[<>:"/\\|?*]', "", sample_concept_analysis.title)
        expected_slug = sanitized_title.lower().replace(" ", "-")[:30]
        assert expected_slug in output_dir.name
        assert re.search(r"visual-explainer-.*-\d{8}-\d{6}$", output_dir.name)
        assert save_args[8] == 9  # total_api_calls threaded through to _save_outputs

        loop_args = mock_loop.call_args.args
        assert loop_args[0] == [sample_image_prompt, prompt2]
        assert loop_args[7] == output_dir

    async def test_displays_completion_summary_when_not_quiet(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
    ):
        prompt_generator = MagicMock()
        result1 = ImageResult(image_number=1, title="Image One")
        result1.status = "complete"
        mock_console = MagicMock()

        with (
            patch("visual_explainer.terminal.get_console", return_value=mock_console),
            patch(
                "visual_explainer.pipeline._analyze_concepts",
                new_callable=AsyncMock,
                return_value=(sample_concept_analysis, sample_style_config, "Test_Style", 1),
            ) as mock_analyze,
            patch(
                "visual_explainer.pipeline._generate_prompts",
                return_value=([sample_image_prompt], prompt_generator, 0),
            ),
            patch(
                "visual_explainer.pipeline._execute_generation_loop",
                new_callable=AsyncMock,
                return_value=([result1], 2),
            ),
            patch("visual_explainer.pipeline._save_outputs"),
            patch("visual_explainer.pipeline.display_completion_summary") as mock_completion,
        ):
            await run_generation_pipeline(
                sample_generation_config,
                sample_internal_config,
                "professional-clean",
                quiet=False,
                json_output=False,
            )

        mock_completion.assert_called_once()
        assert mock_completion.call_args.args[0] == [result1]
        assert mock_completion.call_args.args[3] == 3  # total_api_calls (1 + 0 + 2)
        # console built via terminal.get_console() was threaded into _analyze_concepts
        assert mock_analyze.call_args.args[3] is mock_console


# =============================================================================
# load_checkpoint_and_resume
# =============================================================================


class TestLoadCheckpointAndResume:
    async def test_missing_checkpoint_file_returns_error(self, tmp_path):
        missing = tmp_path / "nope" / "checkpoint.json"
        result = await load_checkpoint_and_resume(missing, MagicMock(), quiet=True)
        assert result["status"] == "error"
        assert "not found" in result["error"]

    async def test_invalid_json_checkpoint_returns_error(self, tmp_path):
        checkpoint_path = tmp_path / "checkpoint.json"
        checkpoint_path.write_text("{not valid json", encoding="utf-8")
        result = await load_checkpoint_and_resume(checkpoint_path, MagicMock(), quiet=True)
        assert result["status"] == "error"
        assert "Invalid checkpoint" in result["error"]

    async def test_fully_complete_checkpoint_is_a_no_op(self, tmp_path):
        checkpoint_data = {
            "generation_id": "gen-complete",
            "started_at": "2026-01-01T00:00:00",
            "total_images": 2,
            "config": {"style": "professional-clean"},
            "analysis_hash": "sha256:abc",
            "completed_images": [1, 2],
            "image_results": {
                "1": {
                    "image_number": 1,
                    "title": "One",
                    "final_attempt": 1,
                    "final_score": 0.9,
                    "final_path": "x",
                    "status": "complete",
                    "total_attempts": 1,
                },
                "2": {
                    "image_number": 2,
                    "title": "Two",
                    "final_attempt": 1,
                    "final_score": 0.8,
                    "final_path": "y",
                    "status": "complete",
                    "total_attempts": 1,
                },
            },
            "status": "completed",
            "topic": "Topic",
            "session_name": "session",
        }
        checkpoint_path = tmp_path / "checkpoint.json"
        checkpoint_path.write_text(json.dumps(checkpoint_data), encoding="utf-8")

        result = await load_checkpoint_and_resume(checkpoint_path, MagicMock(), quiet=True)

        assert result["status"] == "complete"
        assert result["images_generated"] == 2
        assert result["images_already_complete"] == 2
        assert result["images_newly_generated"] == 0
        assert result["resumed"] is True
        assert result["total_attempts"] == 2
        assert len(result["image_results"]) == 2

    async def test_partial_checkpoint_resumes_only_remaining_images(
        self,
        checkpoint_file,
        sample_checkpoint_data,
        sample_concept_analysis,
        sample_style_config,
    ):
        mock_config = MagicMock()
        mock_config.style = "professional-clean"

        prompt1 = MagicMock(image_number=1)
        prompt2 = MagicMock(image_number=2)
        prompt3 = MagicMock(image_number=3)
        prompt_generator = MagicMock()

        new_result_2 = ImageResult(image_number=2, title="Second Image")
        new_result_2.status = "complete"
        new_result_2.final_score = 0.91
        new_result_3 = ImageResult(image_number=3, title="Third Image")
        new_result_3.status = "complete"
        new_result_3.final_score = 0.87

        with (
            patch(
                "visual_explainer.pipeline._analyze_concepts",
                new_callable=AsyncMock,
                return_value=(
                    sample_concept_analysis,
                    sample_style_config,
                    "professional-clean",
                    1,
                ),
            ) as mock_analyze,
            patch(
                "visual_explainer.pipeline._generate_prompts",
                return_value=([prompt1, prompt2, prompt3], prompt_generator, 1),
            ),
            patch(
                "visual_explainer.pipeline._execute_generation_loop",
                new_callable=AsyncMock,
                return_value=([new_result_2, new_result_3], 8),
            ) as mock_loop,
            patch("visual_explainer.pipeline._save_outputs") as mock_save,
        ):
            result = await load_checkpoint_and_resume(checkpoint_file, mock_config, quiet=True)

        assert result["status"] == "complete"
        assert result["resumed"] is True
        assert result["images_already_complete"] == 1
        assert result["images_newly_generated"] == 2
        assert result["total_images"] == 3
        assert result["total_api_calls"] == 1 + 1 + 8

        # Only the remaining (not-yet-completed) prompts were sent to the loop.
        remaining = mock_loop.call_args.args[0]
        assert [p.image_number for p in remaining] == [2, 3]

        # config.style (truthy) took precedence over checkpoint config's style.
        assert mock_analyze.call_args.args[2] == "professional-clean"

        # Previously completed image #1 was reconstructed from checkpoint data
        # and merged with the newly generated results, sorted by image number.
        all_results = mock_save.call_args.args[0]
        assert [r.image_number for r in all_results] == [1, 2, 3]
        assert (
            all_results[0].final_score
            == sample_checkpoint_data["image_results"]["1"]["final_score"]
        )
        assert all_results[0].status == "complete"

    async def test_style_falls_back_to_hardcoded_default_when_unset(
        self, tmp_path, sample_concept_analysis, sample_style_config
    ):
        checkpoint_data = {
            "generation_id": "gen-style-fallback",
            "started_at": "2026-01-01T00:00:00",
            "total_images": 1,
            "config": {},  # no "style" key -> falls through to hardcoded default
            "analysis_hash": "sha256:abc",
            "completed_images": [],
            "image_results": {},
            "status": "in_progress",
            "topic": "Topic",
            "session_name": "session",
        }
        checkpoint_path = tmp_path / "checkpoint.json"
        checkpoint_path.write_text(json.dumps(checkpoint_data), encoding="utf-8")

        mock_config = MagicMock()
        mock_config.style = None  # falsy -> fall back to checkpoint config, then default

        prompt1 = MagicMock(image_number=1)
        new_result = ImageResult(image_number=1, title="Only")
        new_result.status = "complete"

        with (
            patch(
                "visual_explainer.pipeline._analyze_concepts",
                new_callable=AsyncMock,
                return_value=(
                    sample_concept_analysis,
                    sample_style_config,
                    "professional-clean",
                    0,
                ),
            ) as mock_analyze,
            patch(
                "visual_explainer.pipeline._generate_prompts",
                return_value=([prompt1], MagicMock(), 0),
            ),
            patch(
                "visual_explainer.pipeline._execute_generation_loop",
                new_callable=AsyncMock,
                return_value=([new_result], 1),
            ),
            patch("visual_explainer.pipeline._save_outputs"),
        ):
            await load_checkpoint_and_resume(checkpoint_path, mock_config, quiet=True)

        assert mock_analyze.call_args.args[2] == "professional-clean"

    async def test_missing_checkpoint_file_prints_error_when_console_enabled(self, tmp_path):
        missing = tmp_path / "nope" / "checkpoint.json"
        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            result = await load_checkpoint_and_resume(
                missing, MagicMock(), quiet=False, json_output=False
            )

        assert result["status"] == "error"
        mock_console.print.assert_called_once()
        assert "not found" in str(mock_console.print.call_args.args[0])

    async def test_invalid_json_checkpoint_prints_error_when_console_enabled(self, tmp_path):
        checkpoint_path = tmp_path / "checkpoint.json"
        checkpoint_path.write_text("{not valid json", encoding="utf-8")
        mock_console = MagicMock()
        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            result = await load_checkpoint_and_resume(
                checkpoint_path, MagicMock(), quiet=False, json_output=False
            )

        assert result["status"] == "error"
        # First print is "Loading checkpoint: ...", second is the error message.
        assert mock_console.print.call_count == 2
        assert "Invalid checkpoint" in str(mock_console.print.call_args.args[0])

    async def test_fully_complete_checkpoint_prints_summary_when_console_enabled(self, tmp_path):
        checkpoint_data = {
            "generation_id": "gen-complete-console",
            "started_at": "2026-01-01T00:00:00",
            "total_images": 2,
            "config": {"style": "professional-clean"},
            "analysis_hash": "sha256:abc",
            "completed_images": [1, 2],
            "image_results": {
                "1": {
                    "image_number": 1,
                    "title": "One",
                    "final_attempt": 1,
                    "final_score": 0.9,
                    "final_path": "x",
                    "status": "complete",
                    "total_attempts": 1,
                },
                "2": {
                    "image_number": 2,
                    "title": "Two",
                    "final_attempt": 1,
                    "final_score": 0.8,
                    "final_path": "y",
                    "status": "complete",
                    "total_attempts": 1,
                },
            },
            "status": "completed",
            "topic": "Topic",
            "session_name": "session",
        }
        checkpoint_path = tmp_path / "checkpoint.json"
        checkpoint_path.write_text(json.dumps(checkpoint_data), encoding="utf-8")
        mock_console = MagicMock()

        with patch("visual_explainer.terminal.get_console", return_value=mock_console):
            result = await load_checkpoint_and_resume(
                checkpoint_path, MagicMock(), quiet=False, json_output=False
            )

        assert result["status"] == "complete"
        # Checkpoint summary panel + field lines + the "already completed" message.
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "already completed" in printed
        assert "Total images: 2" in printed

    async def test_partial_resume_with_console_prints_progress_and_completion_summary(
        self, checkpoint_file, sample_checkpoint_data, sample_concept_analysis, sample_style_config
    ):
        mock_config = MagicMock()
        mock_config.style = "professional-clean"
        mock_console = MagicMock()

        prompt1 = MagicMock(image_number=1)
        prompt2 = MagicMock(image_number=2)
        prompt3 = MagicMock(image_number=3)
        prompt_generator = MagicMock()

        new_result_2 = ImageResult(image_number=2, title="Second Image")
        new_result_2.status = "complete"
        new_result_3 = ImageResult(image_number=3, title="Third Image")
        new_result_3.status = "complete"

        with (
            patch("visual_explainer.terminal.get_console", return_value=mock_console),
            patch(
                "visual_explainer.pipeline._analyze_concepts",
                new_callable=AsyncMock,
                return_value=(
                    sample_concept_analysis,
                    sample_style_config,
                    "professional-clean",
                    1,
                ),
            ),
            patch(
                "visual_explainer.pipeline._generate_prompts",
                return_value=([prompt1, prompt2, prompt3], prompt_generator, 1),
            ),
            patch(
                "visual_explainer.pipeline._execute_generation_loop",
                new_callable=AsyncMock,
                return_value=([new_result_2, new_result_3], 4),
            ),
            patch("visual_explainer.pipeline._save_outputs"),
            patch("visual_explainer.pipeline.display_completion_summary") as mock_completion,
        ):
            result = await load_checkpoint_and_resume(
                checkpoint_file, mock_config, quiet=False, json_output=False
            )

        assert result["status"] == "complete"
        mock_completion.assert_called_once()
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "Restoring pipeline state" in printed
        assert "Resuming generation" in printed

    async def test_completed_image_missing_from_results_is_skipped_on_reconstruct(
        self, tmp_path, sample_concept_analysis, sample_style_config
    ):
        checkpoint_data = {
            "generation_id": "gen-missing-result",
            "started_at": "2026-01-01T00:00:00",
            "total_images": 2,
            "config": {"style": "professional-clean"},
            "analysis_hash": "sha256:abc",
            "completed_images": [1],  # marked complete...
            "image_results": {},  # ...but no result data was ever recorded for it
            "status": "in_progress",
            "topic": "Topic",
            "session_name": "session",
        }
        checkpoint_path = tmp_path / "checkpoint.json"
        checkpoint_path.write_text(json.dumps(checkpoint_data), encoding="utf-8")

        mock_config = MagicMock()
        mock_config.style = "professional-clean"

        prompt1 = MagicMock(image_number=1)
        prompt2 = MagicMock(image_number=2)
        new_result_2 = ImageResult(image_number=2, title="Second Image")
        new_result_2.status = "complete"

        with (
            patch(
                "visual_explainer.pipeline._analyze_concepts",
                new_callable=AsyncMock,
                return_value=(
                    sample_concept_analysis,
                    sample_style_config,
                    "professional-clean",
                    0,
                ),
            ),
            patch(
                "visual_explainer.pipeline._generate_prompts",
                return_value=([prompt1, prompt2], MagicMock(), 0),
            ),
            patch(
                "visual_explainer.pipeline._execute_generation_loop",
                new_callable=AsyncMock,
                return_value=([new_result_2], 1),
            ),
            patch("visual_explainer.pipeline._save_outputs") as mock_save,
        ):
            result = await load_checkpoint_and_resume(checkpoint_path, mock_config, quiet=True)

        assert result["images_already_complete"] == 1  # len(completed_images), reported as-is
        all_results = mock_save.call_args.args[0]
        # Image 1 has no reconstructable data, so only the newly generated image 2 appears.
        assert [r.image_number for r in all_results] == [2]


# =============================================================================
# Concurrent generation (PERF-01 / issue #128)
# =============================================================================


def _success_result(image_number: int) -> GenerationResult:
    """A successful GenerationResult carrying image-number-tagged bytes."""
    return GenerationResult(
        status=GenerationStatus.SUCCESS,
        image_data=f"img-{image_number}".encode(),
        duration_seconds=0.01,
    )


async def _run_execute_loop(
    prompts,
    config,
    internal_config,
    analysis,
    style,
    output_dir,
    image_generator,
    image_evaluator,
    *,
    quiet=True,
    json_output=False,
):
    """Invoke _execute_generation_loop with the generator/evaluator patched.

    Mirrors TestExecuteGenerationLoop._run but supports multi-prompt runs and a
    toggleable quiet flag so both the concurrent and serial branches (and their
    progress reporting) can be exercised.
    """
    prompt_generator = MagicMock()
    prompt_generator.refine_prompt.side_effect = lambda **kw: kw["original"]
    with (
        patch(
            "visual_explainer.image_generator.GeminiImageGenerator",
            return_value=image_generator,
        ),
        patch(
            "visual_explainer.image_evaluator.ImageEvaluator",
            return_value=image_evaluator,
        ),
    ):
        return await _execute_generation_loop(
            prompts,
            config,
            internal_config,
            analysis,
            style,
            "Test_Style",
            prompt_generator,
            output_dir,
            quiet=quiet,
            json_output=json_output,
        )


class TestConcurrentGeneration:
    """Parallel image generation with a memory-bounded concurrency cap."""

    def _prompts(self, base: ImagePrompt, numbers: list[int]) -> list[ImagePrompt]:
        return [_prompt_with_number(base, n) for n in numbers]

    async def test_results_ordered_by_image_number_despite_out_of_order_completion(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = sample_generation_config.model_copy(update={"concurrency": 3})
        prompts = self._prompts(sample_image_prompt, [1, 2, 3])

        # Later images finish FIRST (shorter sleeps): completion order is 3, 2, 1.
        delays = {1: 0.03, 2: 0.02, 3: 0.01}

        async def fake_generate(**kwargs):
            n = kwargs["image_number"]
            await asyncio.sleep(delays[n])
            return _success_result(n)

        image_generator = MagicMock()
        image_generator.generate_image = fake_generate
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image = MagicMock(
            return_value=_make_evaluation(0.95, EvaluationVerdict.PASS)
        )

        results, api_calls = await _run_execute_loop(
            prompts,
            config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        # gather preserves prompt order regardless of which image finished first.
        assert [r.image_number for r in results] == [1, 2, 3]
        for n in (1, 2, 3):
            r = results[n - 1]
            assert r.status == "complete"
            assert r.final_attempt == 1
            final = temp_output_dir / f"image-{n:02d}" / "final.jpg"
            # Each image kept its own content — no cross-image bleed.
            assert final.read_bytes() == f"img-{n}".encode()
        # 3 images x (1 generation + 1 evaluation).
        assert api_calls == 6

    async def test_semaphore_bounds_max_concurrency(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = sample_generation_config.model_copy(update={"concurrency": 2})
        prompts = self._prompts(sample_image_prompt, [1, 2, 3, 4])

        state = {"depth": 0, "max_depth": 0}

        async def fake_generate(**kwargs):
            # Increment/record with no await in between, so the sample is atomic
            # w.r.t. the event loop; the sleep then yields to let peers enter.
            state["depth"] += 1
            state["max_depth"] = max(state["max_depth"], state["depth"])
            await asyncio.sleep(0.01)
            state["depth"] -= 1
            return _success_result(kwargs["image_number"])

        image_generator = MagicMock()
        image_generator.generate_image = fake_generate
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image = MagicMock(
            return_value=_make_evaluation(0.95, EvaluationVerdict.PASS)
        )

        results, _ = await _run_execute_loop(
            prompts,
            config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        assert [r.image_number for r in results] == [1, 2, 3, 4]
        assert all(r.status == "complete" for r in results)
        # The semaphore cap of 2 is never exceeded...
        assert state["max_depth"] <= 2
        # ...and real parallelism happened (it isn't accidentally serial).
        assert state["max_depth"] == 2

    async def test_api_calls_summed_across_concurrent_images_with_refinement(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = sample_generation_config.model_copy(update={"concurrency": 3, "max_iterations": 3})
        prompts = self._prompts(sample_image_prompt, [1, 2, 3])

        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(
            return_value=GenerationResult(
                status=GenerationStatus.SUCCESS, image_data=b"x", duration_seconds=0.01
            )
        )

        def eval_side_effect(**kwargs):
            if kwargs["iteration"] == 1:
                return _make_evaluation(0.6, EvaluationVerdict.NEEDS_REFINEMENT, iteration=1)
            return _make_evaluation(0.95, EvaluationVerdict.PASS, iteration=kwargs["iteration"])

        image_evaluator = MagicMock()
        image_evaluator.evaluate_image = MagicMock(side_effect=eval_side_effect)

        results, api_calls = await _run_execute_loop(
            prompts,
            config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        assert [r.image_number for r in results] == [1, 2, 3]
        assert all(r.status == "complete" for r in results)
        assert all(r.total_attempts == 2 for r in results)
        # Per image: attempt 1 (gen + eval + refine = 3) + attempt 2 (gen + eval = 2) = 5.
        # 3 images -> 15, summed from each task's own returned count (not the
        # generator's shared internal counter).
        assert api_calls == 15

    async def test_serial_fallback_with_concurrency_one_preserves_order(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = sample_generation_config.model_copy(update={"concurrency": 1})
        prompts = self._prompts(sample_image_prompt, [1, 2, 3])

        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(
            side_effect=[_success_result(1), _success_result(2), _success_result(3)]
        )
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image = MagicMock(
            return_value=_make_evaluation(0.95, EvaluationVerdict.PASS)
        )

        results, api_calls = await _run_execute_loop(
            prompts,
            config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        assert [r.image_number for r in results] == [1, 2, 3]
        assert all(r.status == "complete" for r in results)
        assert api_calls == 6
        # concurrency=1 -> serial path -> exactly one generation per image.
        assert image_generator.generate_image.await_count == 3

    async def test_single_prompt_uses_serial_path_regardless_of_concurrency(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = sample_generation_config.model_copy(update={"concurrency": 8})
        prompts = [sample_image_prompt]  # single prompt -> serial regardless of cap

        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(return_value=_success_result(1))
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image = MagicMock(
            return_value=_make_evaluation(0.95, EvaluationVerdict.PASS)
        )

        results, api_calls = await _run_execute_loop(
            prompts,
            config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            temp_output_dir,
            image_generator,
            image_evaluator,
        )

        assert len(results) == 1
        assert results[0].status == "complete"
        assert api_calls == 2

    async def test_concurrent_generation_overlaps_wall_clock(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        delay = 0.05
        prompts = self._prompts(sample_image_prompt, [1, 2, 3])

        async def fake_generate(**kwargs):
            await asyncio.sleep(delay)
            return _success_result(kwargs["image_number"])

        def build_mocks():
            gen = MagicMock()
            gen.generate_image = fake_generate
            ev = MagicMock()
            ev.evaluate_image = MagicMock(
                return_value=_make_evaluation(0.95, EvaluationVerdict.PASS)
            )
            return gen, ev

        # Concurrent: 3 images overlap -> ~1x delay.
        gen_c, ev_c = build_mocks()
        config_c = sample_generation_config.model_copy(update={"concurrency": 3})
        out_c = temp_output_dir / "concurrent"
        out_c.mkdir()
        t0 = time.perf_counter()
        results_c, _ = await _run_execute_loop(
            prompts,
            config_c,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            out_c,
            gen_c,
            ev_c,
        )
        concurrent_elapsed = time.perf_counter() - t0

        # Serial: same 3 images one after another -> ~3x delay.
        gen_s, ev_s = build_mocks()
        config_s = sample_generation_config.model_copy(update={"concurrency": 1})
        out_s = temp_output_dir / "serial"
        out_s.mkdir()
        t0 = time.perf_counter()
        results_s, _ = await _run_execute_loop(
            prompts,
            config_s,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            out_s,
            gen_s,
            ev_s,
        )
        serial_elapsed = time.perf_counter() - t0

        assert all(r.status == "complete" for r in results_c)
        assert all(r.status == "complete" for r in results_s)
        # Concurrent run overlapped: well under the serial 3x wall clock.
        assert concurrent_elapsed < 2 * delay
        assert concurrent_elapsed < serial_elapsed

    async def test_concurrent_mode_emits_started_and_completed_lines(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = sample_generation_config.model_copy(update={"concurrency": 2})
        prompts = self._prompts(sample_image_prompt, [1, 2])

        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(return_value=_success_result(1))
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image = MagicMock(
            return_value=_make_evaluation(0.95, EvaluationVerdict.PASS)
        )

        mock_console = MagicMock()
        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=mock_console),
        ):
            results, _ = await _run_execute_loop(
                prompts,
                config,
                sample_internal_config,
                sample_concept_analysis,
                sample_style_config,
                temp_output_dir,
                image_generator,
                image_evaluator,
                quiet=False,
                json_output=False,
            )

        assert all(r.status == "complete" for r in results)
        printed = " ".join(str(c.args[0]) for c in mock_console.print.call_args_list)
        assert "Image 1/2 started" in printed
        assert "Image 2/2 started" in printed
        assert "Image 1/2 complete" in printed
        assert "Image 2/2 complete" in printed

    async def test_concurrent_mode_logs_failed_image(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        config = sample_generation_config.model_copy(update={"concurrency": 2, "max_iterations": 2})
        prompts = self._prompts(sample_image_prompt, [1, 2])

        async def fake_generate(**kwargs):
            if kwargs["image_number"] == 2:
                return GenerationResult(
                    status=GenerationStatus.ERROR,
                    image_data=None,
                    error_message="boom",
                    duration_seconds=0.01,
                )
            return _success_result(kwargs["image_number"])

        image_generator = MagicMock()
        image_generator.generate_image = fake_generate
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image = MagicMock(
            return_value=_make_evaluation(0.95, EvaluationVerdict.PASS)
        )

        mock_console = MagicMock()
        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=mock_console),
        ):
            results, _ = await _run_execute_loop(
                prompts,
                config,
                sample_internal_config,
                sample_concept_analysis,
                sample_style_config,
                temp_output_dir,
                image_generator,
                image_evaluator,
                quiet=False,
                json_output=False,
            )

        by_num = {r.image_number: r for r in results}
        assert by_num[1].status == "complete"
        assert by_num[2].status == "failed"
        printed = " ".join(str(c.args[0]) for c in mock_console.print.call_args_list)
        assert "Image 1/2 complete" in printed
        assert "Image 2/2 failed" in printed

    async def test_generate_single_image_concurrent_returns_result_and_count(
        self,
        sample_generation_config,
        sample_internal_config,
        sample_concept_analysis,
        sample_style_config,
        sample_image_prompt,
        temp_output_dir,
    ):
        from visual_explainer.reporting import ConcurrentGenerationProgress

        image_generator = MagicMock()
        image_generator.generate_image = AsyncMock(return_value=_success_result(1))
        image_evaluator = MagicMock()
        image_evaluator.evaluate_image = MagicMock(
            return_value=_make_evaluation(0.95, EvaluationVerdict.PASS)
        )
        prompt_generator = MagicMock()
        progress = ConcurrentGenerationProgress(
            1, sample_generation_config.max_iterations, quiet=True
        )

        result, api_calls = await _generate_single_image(
            sample_image_prompt,
            sample_generation_config,
            sample_internal_config,
            sample_concept_analysis,
            sample_style_config,
            "Test_Style",
            prompt_generator,
            temp_output_dir,
            image_generator,
            image_evaluator,
            progress,
            concurrent=True,
        )

        assert result.image_number == 1
        assert result.status == "complete"
        assert result.final_attempt == 1
        assert api_calls == 2
        assert (temp_output_dir / "image-01" / "final.jpg").read_bytes() == b"img-1"


class TestConcurrentGenerationProgressReporter:
    """Unit coverage for the concurrency-safe progress reporter itself."""

    def test_quiet_mode_suppresses_all_lines(self):
        from visual_explainer.reporting import ConcurrentGenerationProgress

        mock_console = MagicMock()
        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=mock_console),
        ):
            progress = ConcurrentGenerationProgress(3, 5, quiet=True)

        # Per-attempt hooks are always no-ops.
        progress.start_attempt(1)
        progress.update_status("Generating...")
        progress.show_evaluation(_make_evaluation(0.9, EvaluationVerdict.PASS))
        # Discrete per-image lines are suppressed when quiet.
        progress.start_image(1, "One")
        progress.complete_image(1, 2, 0.9)
        progress.fail_image(2, "Two")

        mock_console.print.assert_not_called()

    def test_non_quiet_mode_emits_lines_with_correct_pluralization(self):
        from visual_explainer.reporting import ConcurrentGenerationProgress

        mock_console = MagicMock()
        with (
            patch("visual_explainer.terminal.RICH_AVAILABLE", True),
            patch("visual_explainer.terminal.get_console", return_value=mock_console),
        ):
            progress = ConcurrentGenerationProgress(2, 5, quiet=False)

        progress.start_image(1, "One")
        progress.complete_image(1, 1, 0.9)  # best_attempt 1 -> singular "1 attempt"
        progress.complete_image(2, 3, 0.8)  # best_attempt 3 -> plural "3 attempts"
        progress.fail_image(2, "Two")
        # Per-attempt hooks stay no-ops even when not quiet.
        progress.start_attempt(1)
        progress.update_status("ignored")
        progress.show_evaluation(_make_evaluation(0.9, EvaluationVerdict.PASS))

        printed = " ".join(str(c.args[0]) for c in mock_console.print.call_args_list)
        assert "Image 1/2 started" in printed
        assert "(score 90%, 1 attempt)" in printed
        assert "(score 80%, 3 attempts)" in printed
        assert "Image 2/2 failed" in printed
