"""Integration tests for the Q&A workflow chain.

Tests validate the complete workflow:
1. /define-questions output conforms to schemas/questions.json
2. /ask-questions can parse /define-questions output
3. /finish-document updates documents correctly with answers

These tests validate schema compliance and data flow between commands.
"""

import json
import pytest
from pathlib import Path

from tests.helpers.schema_validator import (
    validate_against_schema,
    get_validation_errors,
    validate_questions_structure,
    validate_answers_structure,
)
from tests.helpers.file_comparator import (
    compare_markdown_content,
    extract_tbd_markers,
    count_resolved_tbds,
)


class TestQuestionsSchemaCompliance:
    """Tests for /define-questions output schema compliance."""

    def test_expected_questions_validates_against_schema(
        self, expected_questions: dict, questions_schema: dict
    ):
        """Verify expected questions fixture validates against schema."""
        assert validate_against_schema(expected_questions, questions_schema)

    def test_questions_schema_validation_errors_empty(
        self, expected_questions: dict, questions_schema: dict
    ):
        """Verify no validation errors for expected questions."""
        errors = get_validation_errors(expected_questions, questions_schema)
        assert errors == [], f"Validation errors: {errors}"

    def test_questions_has_required_metadata(self, expected_questions: dict):
        """Verify questions output has required metadata fields."""
        metadata = expected_questions.get("metadata", {})

        assert "source_document" in metadata
        assert "generated_at" in metadata
        assert "total_questions" in metadata

    def test_questions_count_matches_metadata(self, expected_questions: dict):
        """Verify questions count matches metadata total."""
        metadata = expected_questions.get("metadata", {})
        questions = expected_questions.get("questions", [])

        assert len(questions) == metadata.get("total_questions")

    def test_questions_have_required_fields(self, expected_questions: dict):
        """Verify each question has required fields."""
        questions = expected_questions.get("questions", [])

        for i, question in enumerate(questions):
            assert "id" in question, f"Question {i} missing 'id'"
            # Either 'text' or 'question' is acceptable
            has_text = "text" in question or "question" in question
            assert has_text, f"Question {i} missing 'text' or 'question'"
            assert "context" in question, f"Question {i} missing 'context'"

    def test_questions_ids_are_unique(self, expected_questions: dict):
        """Verify all question IDs are unique."""
        questions = expected_questions.get("questions", [])
        ids = [q.get("id") for q in questions]

        assert len(ids) == len(set(ids)), "Duplicate question IDs found"

    def test_questions_structure_validation(self, expected_questions: dict):
        """Verify questions pass structural validation."""
        issues = validate_questions_structure(expected_questions)
        assert issues == [], f"Structural issues: {issues}"


class TestAnswersSchemaCompliance:
    """Tests for /ask-questions output schema compliance."""

    def test_sample_answers_validates_against_schema(
        self, sample_answers: dict, answers_schema: dict
    ):
        """Verify sample answers fixture validates against schema."""
        assert validate_against_schema(sample_answers, answers_schema)

    def test_answers_schema_validation_errors_empty(
        self, sample_answers: dict, answers_schema: dict
    ):
        """Verify no validation errors for sample answers."""
        errors = get_validation_errors(sample_answers, answers_schema)
        assert errors == [], f"Validation errors: {errors}"

    def test_answers_has_required_metadata(self, sample_answers: dict):
        """Verify answers output has required metadata fields."""
        metadata = sample_answers.get("metadata", {})

        assert "source_document" in metadata
        assert "total_questions" in metadata

    def test_answers_count_matches_metadata(self, sample_answers: dict):
        """Verify answers count matches metadata totals."""
        metadata = sample_answers.get("metadata", {})
        answers = sample_answers.get("answers", [])

        assert len(answers) == metadata.get("total_questions")

    def test_answers_have_required_fields(self, sample_answers: dict):
        """Verify each answer has required fields."""
        answers = sample_answers.get("answers", [])

        for i, answer in enumerate(answers):
            assert "id" in answer, f"Answer {i} missing 'id'"
            assert "selected_answer" in answer, f"Answer {i} missing 'selected_answer'"

    def test_answer_types_are_valid(self, sample_answers: dict):
        """Verify all answer types are valid."""
        valid_types = {"recommended", "alternative", "custom", "skipped"}
        answers = sample_answers.get("answers", [])

        for i, answer in enumerate(answers):
            answer_type = answer.get("answer_type")
            if answer_type:
                assert answer_type in valid_types, (
                    f"Answer {i} has invalid type '{answer_type}'"
                )

    def test_answers_structure_validation(self, sample_answers: dict):
        """Verify answers pass structural validation."""
        issues = validate_answers_structure(sample_answers)
        assert issues == [], f"Structural issues: {issues}"


class TestWorkflowDataFlow:
    """Tests for data flow between Q&A workflow commands."""

    def test_questions_ids_match_answers_ids(
        self, expected_questions: dict, sample_answers: dict
    ):
        """Verify answer IDs correspond to question IDs."""
        question_ids = {q.get("id") for q in expected_questions.get("questions", [])}
        answer_ids = {a.get("id") for a in sample_answers.get("answers", [])}

        assert question_ids == answer_ids, (
            f"ID mismatch - Questions: {question_ids}, Answers: {answer_ids}"
        )

    def test_answers_reference_correct_source_file(
        self, expected_questions: dict, sample_answers: dict
    ):
        """Verify answers reference the correct source document."""
        questions_source = expected_questions.get("metadata", {}).get("source_document")
        answers_source = sample_answers.get("metadata", {}).get("source_document")

        assert questions_source == answers_source, (
            f"Source mismatch - Questions: {questions_source}, Answers: {answers_source}"
        )

    def test_answer_summary_counts_match(self, sample_answers: dict):
        """Verify answer summary counts match actual answers."""
        metadata = sample_answers.get("metadata", {})
        summary = metadata.get("answer_summary", {})
        answers = sample_answers.get("answers", [])

        # Count actual answer types
        type_counts = {"recommended": 0, "alternative": 0, "custom": 0, "skipped": 0}
        for answer in answers:
            answer_type = answer.get("answer_type")
            if answer_type in type_counts:
                type_counts[answer_type] += 1

        for answer_type, expected_count in summary.items():
            actual_count = type_counts.get(answer_type, 0)
            assert expected_count == actual_count, (
                f"Type '{answer_type}': expected {expected_count}, got {actual_count}"
            )


class TestDocumentUpdate:
    """Tests for /finish-document document update functionality."""

    def test_original_prd_has_tbd_markers(self, sample_prd: str):
        """Verify original PRD contains TBD markers."""
        markers = extract_tbd_markers(sample_prd)
        assert len(markers) > 0, "Original PRD should contain TBD markers"

    def test_updated_prd_has_fewer_tbd_markers(
        self, sample_prd: str, expected_updated_prd: str
    ):
        """Verify updated PRD has fewer TBD markers than original."""
        original_markers = extract_tbd_markers(sample_prd)
        updated_markers = extract_tbd_markers(expected_updated_prd)

        assert len(updated_markers) < len(original_markers), (
            f"Expected fewer TBD markers. Original: {len(original_markers)}, "
            f"Updated: {len(updated_markers)}"
        )

    def test_resolved_tbd_count_matches_answered(
        self, sample_prd: str, expected_updated_prd: str, sample_answers: dict
    ):
        """Verify number of resolved TBDs matches non-skipped answers."""
        counts = count_resolved_tbds(sample_prd, expected_updated_prd)
        metadata = sample_answers.get("metadata", {})

        # Count non-skipped answers (answered + alternative + custom)
        summary = metadata.get("answer_summary", {})
        answered_count = (
            summary.get("recommended", 0)
            + summary.get("alternative", 0)
            + summary.get("custom", 0)
        )

        # Resolved should match answered (skipped questions remain as TBD)
        assert counts["resolved"] == answered_count, (
            f"Resolved TBDs ({counts['resolved']}) should match "
            f"answered questions ({answered_count})"
        )

    def test_skipped_questions_remain_as_tbd(
        self, expected_updated_prd: str, sample_answers: dict
    ):
        """Verify skipped questions remain as TBD in updated document."""
        # Get skipped questions
        skipped = [
            a for a in sample_answers.get("answers", [])
            if a.get("answer_type") == "skipped"
        ]

        # Check that their original text markers still exist
        remaining_markers = extract_tbd_markers(expected_updated_prd)

        # There should be at least as many remaining TBDs as skipped answers
        assert len(remaining_markers) >= len(skipped), (
            f"Expected at least {len(skipped)} remaining TBDs for skipped questions, "
            f"found {len(remaining_markers)}"
        )


class TestInvalidInput:
    """Tests for handling invalid input data."""

    def test_questions_missing_metadata_fails_schema(self, questions_schema: dict):
        """Verify questions without metadata fail validation."""
        invalid_data = {
            "questions": [
                {"id": 1, "text": "Test?", "context": "Test context"}
            ]
        }

        assert not validate_against_schema(invalid_data, questions_schema)
        errors = get_validation_errors(invalid_data, questions_schema)
        assert any("metadata" in e.lower() for e in errors)

    def test_questions_missing_questions_array_fails_schema(
        self, questions_schema: dict
    ):
        """Verify questions without questions array fail validation."""
        invalid_data = {
            "metadata": {
                "source_document": "test.md",
                "generated_at": "2026-01-14T10:00:00Z",
                "total_questions": 0
            }
        }

        assert not validate_against_schema(invalid_data, questions_schema)
        errors = get_validation_errors(invalid_data, questions_schema)
        assert any("questions" in e.lower() for e in errors)

    def test_answer_invalid_type_fails_schema(self, answers_schema: dict):
        """Verify answers with invalid answer_type fail validation."""
        invalid_data = {
            "metadata": {
                "source_document": "test.md",
                "total_questions": 1
            },
            "answers": [
                {
                    "id": 1,
                    "selected_answer": "test",
                    "answer_type": "invalid_type"  # Not a valid enum value
                }
            ]
        }

        assert not validate_against_schema(invalid_data, answers_schema)
        errors = get_validation_errors(invalid_data, answers_schema)
        assert any("answer_type" in e.lower() or "invalid" in e.lower() for e in errors)

    def test_question_invalid_priority_fails_validation(self):
        """Verify questions with invalid priority fail structural validation."""
        invalid_questions = {
            "metadata": {
                "source_document": "test.md",
                "generated_at": "2026-01-14T10:00:00Z",
                "total_questions": 1
            },
            "questions": [
                {
                    "id": 1,
                    "text": "Test question?",
                    "context": "Test context",
                    "priority": "urgent"  # Not a valid priority
                }
            ]
        }

        issues = validate_questions_structure(invalid_questions)
        assert any("priority" in issue.lower() for issue in issues)


class TestFixtureIntegrity:
    """Tests to ensure test fixtures are properly formatted."""

    def test_sample_prd_is_valid_markdown(self, sample_prd: str):
        """Verify sample PRD is valid markdown content."""
        assert len(sample_prd) > 0
        assert "# " in sample_prd  # Has headings
        assert "## " in sample_prd  # Has subheadings

    def test_expected_questions_is_valid_json(self, expected_questions: dict):
        """Verify expected questions is valid JSON structure."""
        assert isinstance(expected_questions, dict)
        assert "metadata" in expected_questions
        assert "questions" in expected_questions

    def test_sample_answers_is_valid_json(self, sample_answers: dict):
        """Verify sample answers is valid JSON structure."""
        assert isinstance(sample_answers, dict)
        assert "metadata" in sample_answers
        assert "answers" in sample_answers

    def test_expected_updated_prd_is_valid_markdown(self, expected_updated_prd: str):
        """Verify expected updated PRD is valid markdown content."""
        assert len(expected_updated_prd) > 0
        assert "# " in expected_updated_prd

    def test_fixtures_are_consistent(
        self,
        sample_prd: str,
        expected_questions: dict,
        sample_answers: dict,
        expected_updated_prd: str,
    ):
        """Verify all fixtures are internally consistent."""
        # Questions reference the same document
        assert expected_questions["metadata"]["source_document"] == "sample-prd.md"

        # Answers reference the same document
        assert sample_answers["metadata"]["source_document"] == "sample-prd.md"

        # Question count matches
        q_count = len(expected_questions["questions"])
        a_count = len(sample_answers["answers"])
        assert q_count == a_count, f"Question count ({q_count}) != answer count ({a_count})"
