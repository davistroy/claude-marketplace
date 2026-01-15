"""Schema validation utilities for testing."""

from typing import Any
from jsonschema import Draft202012Validator, ValidationError
from jsonschema.exceptions import best_match


def validate_against_schema(data: dict, schema: dict) -> bool:
    """
    Validate JSON data against a schema.

    Args:
        data: The JSON data to validate
        schema: The JSON schema to validate against

    Returns:
        True if valid, False otherwise
    """
    validator = Draft202012Validator(schema)
    return validator.is_valid(data)


def get_validation_errors(data: dict, schema: dict) -> list[str]:
    """
    Get all validation errors for JSON data against a schema.

    Args:
        data: The JSON data to validate
        schema: The JSON schema to validate against

    Returns:
        List of error messages, empty if valid
    """
    validator = Draft202012Validator(schema)
    errors = []

    for error in sorted(validator.iter_errors(data), key=lambda e: e.path):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"{path}: {error.message}")

    return errors


def get_best_error(data: dict, schema: dict) -> str | None:
    """
    Get the most relevant validation error.

    Args:
        data: The JSON data to validate
        schema: The JSON schema to validate against

    Returns:
        The most relevant error message, or None if valid
    """
    validator = Draft202012Validator(schema)
    error = best_match(validator.iter_errors(data))

    if error is None:
        return None

    path = ".".join(str(p) for p in error.absolute_path) or "(root)"
    return f"{path}: {error.message}"


def validate_required_fields(data: dict, required_fields: list[str]) -> list[str]:
    """
    Check that required fields are present in data.

    Args:
        data: The data dictionary to check
        required_fields: List of required field names

    Returns:
        List of missing field names
    """
    return [field for field in required_fields if field not in data]


def validate_questions_structure(questions_data: dict) -> list[str]:
    """
    Validate the structure of questions output beyond JSON schema.

    Checks for:
    - Unique question IDs
    - Consistent topic references
    - Valid priority values
    - Non-empty question text

    Args:
        questions_data: The questions JSON data

    Returns:
        List of structural issues found
    """
    issues = []
    seen_ids = set()

    if "questions" not in questions_data:
        issues.append("Missing 'questions' array")
        return issues

    for i, question in enumerate(questions_data["questions"]):
        q_id = question.get("id")

        # Check for duplicate IDs
        if q_id in seen_ids:
            issues.append(f"Question {i}: Duplicate ID '{q_id}'")
        else:
            seen_ids.add(q_id)

        # Check for empty question text
        text = question.get("text") or question.get("question")
        if not text or not text.strip():
            issues.append(f"Question {i} (ID={q_id}): Empty question text")

        # Check priority if present
        priority = question.get("priority")
        if priority and priority not in ("high", "medium", "low"):
            issues.append(
                f"Question {i} (ID={q_id}): Invalid priority '{priority}'"
            )

    return issues


def validate_answers_structure(answers_data: dict) -> list[str]:
    """
    Validate the structure of answers output beyond JSON schema.

    Checks for:
    - Unique answer IDs
    - Valid answer types
    - Consistency between counts and actual answers

    Args:
        answers_data: The answers JSON data

    Returns:
        List of structural issues found
    """
    issues = []
    seen_ids = set()

    if "answers" not in answers_data:
        issues.append("Missing 'answers' array")
        return issues

    answer_type_counts = {
        "recommended": 0,
        "alternative": 0,
        "custom": 0,
        "skipped": 0,
    }

    for i, answer in enumerate(answers_data["answers"]):
        a_id = answer.get("id")

        # Check for duplicate IDs
        if a_id in seen_ids:
            issues.append(f"Answer {i}: Duplicate ID '{a_id}'")
        else:
            seen_ids.add(a_id)

        # Count answer types
        answer_type = answer.get("answer_type")
        if answer_type in answer_type_counts:
            answer_type_counts[answer_type] += 1

        # Check that non-skipped answers have content
        if answer_type != "skipped":
            selected = answer.get("selected_answer", "")
            if not selected or not selected.strip():
                issues.append(
                    f"Answer {i} (ID={a_id}): Non-skipped answer has empty content"
                )

    # Validate counts match metadata if present
    metadata = answers_data.get("metadata", {})
    summary = metadata.get("answer_summary", {})

    for answer_type, expected in summary.items():
        actual = answer_type_counts.get(answer_type, 0)
        if actual != expected:
            issues.append(
                f"Answer type '{answer_type}': metadata says {expected}, "
                f"but found {actual}"
            )

    return issues
