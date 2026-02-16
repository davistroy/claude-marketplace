"""Shared fixtures for feedback-docx-generator tests."""

import pytest


@pytest.fixture
def sample_feedback_data():
    """Complete, valid feedback data with all sections populated."""
    return {
        "employee_name": "Jane Doe",
        "assessment_period": {
            "start": "2025-01-01",
            "end": "2025-06-30",
        },
        "generation_date": "2025-07-15",
        "total_entries": 5,
        "synthesis": {
            "executive_summary": "Jane has demonstrated strong leadership and technical skills.",
            "strengths": [
                {
                    "name": "Technical Leadership",
                    "description": "Consistently delivers high-quality technical solutions.",
                    "frequency": "Frequent",
                    "evidence": [
                        {
                            "date": "2025-02-15",
                            "summary": "Led the migration to microservices architecture.",
                        },
                        {
                            "date": "2025-04-10",
                            "summary": "Mentored three junior developers on best practices.",
                        },
                    ],
                },
                {
                    "name": "Communication",
                    "description": "Excellent at conveying complex ideas to stakeholders.",
                    "frequency": "Regular",
                    "evidence": [
                        {
                            "date": "2025-03-20",
                            "summary": "Presented quarterly tech review to executive team.",
                        },
                    ],
                },
            ],
            "areas_for_development": [
                {
                    "name": "Time Management",
                    "description": "Occasionally struggles with prioritizing competing deadlines.",
                    "pattern": "End-of-sprint crunch",
                    "evidence": [
                        {
                            "date": "2025-05-01",
                            "summary": "Missed sprint delivery target by two days.",
                        },
                    ],
                },
            ],
            "patterns_and_themes": {
                "trends": "Improvement in delegation over the period.",
                "relationships": "Strong correlation between mentoring and team velocity.",
                "situational": "Performs best when given clear sprint objectives.",
            },
            "recommendations": [
                {
                    "type": "Continue",
                    "recommendation": "Continue leading architecture decisions.",
                    "rationale": "Proven track record of sound technical judgment.",
                },
                {
                    "type": "Develop",
                    "recommendation": "Improve sprint planning estimation.",
                    "rationale": "Would reduce end-of-sprint pressure.",
                },
                {
                    "type": "Stretch",
                    "recommendation": "Take on cross-team technical leadership role.",
                    "rationale": "Builds on existing strengths in communication.",
                },
            ],
        },
        "entries": [
            {
                "title": "Architecture Review",
                "date": "2025-02-15",
                "feedback_type": "Observation",
                "summary": "Led a successful architecture review meeting.",
                "context": "Quarterly architecture review for the platform team.",
                "actionable_items": "Schedule follow-up reviews monthly.",
                "raw_transcript": "The meeting went well. Jane presented...",
                "tags": ["leadership", "architecture"],
            },
            {
                "title": "Sprint Retrospective",
                "date": "2025-05-01",
                "feedback_type": "Feedback",
                "summary": "Missed sprint delivery target.",
                "context": "Sprint 12 retrospective discussion.",
                "actionable_items": "Break large stories into smaller tasks.",
                "tags": ["planning", "sprint"],
            },
        ],
    }


@pytest.fixture
def empty_feedback_data():
    """Minimal data with empty/missing optional sections."""
    return {
        "employee_name": "",
        "synthesis": {},
        "entries": [],
    }


@pytest.fixture
def malformed_feedback_data():
    """Data with wrong types and unexpected structures."""
    return {
        "employee_name": 12345,
        "assessment_period": "not-a-dict",
        "total_entries": "not-a-number",
        "synthesis": {
            "strengths": "not-a-list",
            "areas_for_development": None,
            "patterns_and_themes": [1, 2, 3],
            "recommendations": "also-not-a-list",
        },
        "entries": "not-a-list",
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary output directory path."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
