"""Tests for infographic_builder module.

Tests the InfographicPromptBuilder class which handles zone-based
infographic prompt construction and response parsing.
"""

from __future__ import annotations

import json

import pytest

from visual_explainer.config import AspectRatio, GenerationConfig
from visual_explainer.infographic_builder import InfographicPromptBuilder
from visual_explainer.models import (
    Complexity,
    Concept,
    ConceptAnalysis,
    ContentType,
    ContentZone,
    ImagePrompt,
    LogicalFlowStep,
    PageLayout,
    PagePlan,
    PageType,
    RelationshipType,
    VisualPotential,
)


@pytest.fixture
def builder():
    """Create an InfographicPromptBuilder for testing."""
    return InfographicPromptBuilder()


@pytest.fixture
def sample_layout():
    """Create a sample PageLayout for testing."""
    return PageLayout(
        page_type=PageType.HERO_SUMMARY,
        description="Executive overview page",
        zones=[
            ContentZone(
                name="page_header",
                position="top",
                width_percent=100,
                height_percent=15,
                content_type=ContentType.NARRATIVE,
                content_guidance="Main title and subtitle",
                typography_scale="headline",
            ),
            ContentZone(
                name="hero_stat",
                position="center_left",
                width_percent=50,
                height_percent=40,
                content_type=ContentType.STATISTICS,
                content_guidance="Key metric or statistic",
                typography_scale="headline",
            ),
            ContentZone(
                name="supporting_content",
                position="center_right",
                width_percent=50,
                height_percent=40,
                content_type=ContentType.FRAMEWORK,
                content_guidance="Supporting framework or process",
                typography_scale="body",
            ),
        ],
        design_notes="Focus on high-impact visual hierarchy",
    )


@pytest.fixture
def sample_page_plan():
    """Create a sample PagePlan for testing."""
    return PagePlan(
        page_number=1,
        page_type=PageType.HERO_SUMMARY,
        title="Machine Learning Overview",
        content_focus="Executive summary of ML concepts",
        concepts_covered=[1, 2],
        content_types_present=[ContentType.STATISTICS, ContentType.NARRATIVE],
        zone_assignments={
            "page_header": "Machine Learning: A Visual Guide",
            "hero_stat": "95% accuracy achieved",
        },
        cross_references=["See page 2 for deep dive"],
    )


@pytest.fixture
def sample_analysis():
    """Create a sample ConceptAnalysis for testing."""
    return ConceptAnalysis(
        title="Introduction to Machine Learning",
        summary="An overview of ML concepts.",
        target_audience="Technical professionals",
        concepts=[
            Concept(
                id=1,
                name="Neural Networks",
                description="Computational systems inspired by biological neural networks",
                relationships=["concept_id:2"],
                complexity=Complexity.MODERATE,
                visual_potential=VisualPotential.HIGH,
            ),
            Concept(
                id=2,
                name="Training Data",
                description="Data used to train models",
                relationships=["concept_id:1"],
                complexity=Complexity.SIMPLE,
                visual_potential=VisualPotential.MEDIUM,
            ),
        ],
        logical_flow=[
            LogicalFlowStep(
                from_concept=1,
                to_concept=2,
                relationship=RelationshipType.DEPENDS_ON,
            ),
        ],
        recommended_image_count=2,
        content_hash="sha256:test",
        word_count=500,
    )


@pytest.fixture
def sample_style_injection():
    """Create sample style injection data."""
    return {
        "core_style": "professional, clean, modern",
        "color_constraints": "blue and gray tones",
        "style_prefix": "Professional illustration",
        "negative": "cluttered, messy",
    }


class TestInfographicPromptBuilderInit:
    """Tests for InfographicPromptBuilder initialization."""

    def test_init_creates_internal_config(self):
        """Test that internal config is created if not provided."""
        builder = InfographicPromptBuilder()
        assert builder.internal_config is not None

    def test_init_accepts_internal_config(self, sample_internal_config):
        """Test that custom internal config is accepted."""
        builder = InfographicPromptBuilder(internal_config=sample_internal_config)
        assert builder.internal_config is sample_internal_config


class TestBuildInfographicPagePrompt:
    """Tests for building infographic page prompts."""

    def test_prompt_includes_document_context(
        self, builder, sample_analysis, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that the prompt includes document title and summary."""
        prompt = builder.build_infographic_page_prompt(
            analysis=sample_analysis,
            page_plan=sample_page_plan,
            layout=sample_layout,
            style_injection=sample_style_injection,
            total_pages=3,
        )
        assert "Introduction to Machine Learning" in prompt
        assert "An overview of ML concepts" in prompt

    def test_prompt_includes_page_specification(
        self, builder, sample_analysis, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that the prompt includes page number and type."""
        prompt = builder.build_infographic_page_prompt(
            analysis=sample_analysis,
            page_plan=sample_page_plan,
            layout=sample_layout,
            style_injection=sample_style_injection,
            total_pages=3,
        )
        assert "1 of 3" in prompt
        assert "hero_summary" in prompt
        assert "Machine Learning Overview" in prompt

    def test_prompt_includes_zone_specifications(
        self, builder, sample_analysis, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that the prompt includes zone details."""
        prompt = builder.build_infographic_page_prompt(
            analysis=sample_analysis,
            page_plan=sample_page_plan,
            layout=sample_layout,
            style_injection=sample_style_injection,
            total_pages=3,
        )
        assert "page_header" in prompt
        assert "hero_stat" in prompt
        assert "supporting_content" in prompt

    def test_prompt_includes_style_requirements(
        self, builder, sample_analysis, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that the prompt includes style injection."""
        prompt = builder.build_infographic_page_prompt(
            analysis=sample_analysis,
            page_plan=sample_page_plan,
            layout=sample_layout,
            style_injection=sample_style_injection,
            total_pages=3,
        )
        assert "professional, clean, modern" in prompt
        assert "blue and gray tones" in prompt

    def test_prompt_includes_cross_references(
        self, builder, sample_analysis, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that cross-references are included."""
        prompt = builder.build_infographic_page_prompt(
            analysis=sample_analysis,
            page_plan=sample_page_plan,
            layout=sample_layout,
            style_injection=sample_style_injection,
            total_pages=3,
        )
        assert "See page 2 for deep dive" in prompt

    def test_prompt_includes_zone_assignments(
        self, builder, sample_analysis, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that zone assignments are included."""
        prompt = builder.build_infographic_page_prompt(
            analysis=sample_analysis,
            page_plan=sample_page_plan,
            layout=sample_layout,
            style_injection=sample_style_injection,
            total_pages=3,
        )
        assert "Machine Learning: A Visual Guide" in prompt
        assert "95% accuracy achieved" in prompt

    def test_prompt_uses_config_aspect_ratio(
        self,
        builder,
        sample_analysis,
        sample_page_plan,
        sample_layout,
        sample_style_injection,
        tmp_path,
    ):
        """Test that config aspect ratio is used."""
        config = GenerationConfig(
            input_source="test",
            style="test",
            output_dir=tmp_path,
            aspect_ratio=AspectRatio.LANDSCAPE_16_9,
        )
        prompt = builder.build_infographic_page_prompt(
            analysis=sample_analysis,
            page_plan=sample_page_plan,
            layout=sample_layout,
            style_injection=sample_style_injection,
            total_pages=3,
            config=config,
        )
        assert "16:9" in prompt

    def test_prompt_defaults_to_16_9(
        self, builder, sample_analysis, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that aspect ratio defaults to 16:9 without config."""
        prompt = builder.build_infographic_page_prompt(
            analysis=sample_analysis,
            page_plan=sample_page_plan,
            layout=sample_layout,
            style_injection=sample_style_injection,
            total_pages=3,
        )
        assert "16:9" in prompt


class TestParseInfographicResponse:
    """Tests for parsing infographic API responses."""

    def test_parse_json_directly(self, builder):
        """Test parsing a direct JSON response."""
        data = {"main_prompt": "test prompt", "page_title": "Test"}
        result = builder.parse_infographic_response(json.dumps(data))
        assert result["main_prompt"] == "test prompt"

    def test_parse_json_in_code_block(self, builder):
        """Test parsing JSON wrapped in markdown code block."""
        data = {"main_prompt": "test prompt"}
        result = builder.parse_infographic_response(f"```json\n{json.dumps(data)}\n```")
        assert result["main_prompt"] == "test prompt"

    def test_parse_json_with_surrounding_text(self, builder):
        """Test parsing JSON from text with surrounding content."""
        data = {"main_prompt": "test prompt"}
        result = builder.parse_infographic_response(f"Here is the result: {json.dumps(data)}")
        assert result["main_prompt"] == "test prompt"

    def test_parse_invalid_json_raises(self, builder):
        """Test that invalid JSON raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            builder.parse_infographic_response("not valid json at all")


class TestBuildInfographicImagePrompt:
    """Tests for building ImagePrompt from infographic response data."""

    def test_builds_valid_image_prompt(
        self, builder, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that a valid ImagePrompt is built."""
        prompt_data = {
            "page_title": "ML Overview",
            "main_prompt": "A professional infographic about ML",
            "style_guidance": "Clean modern style",
            "color_palette": "Blue tones",
            "composition": "Grid layout",
            "avoid": "Clutter",
            "success_criteria": ["Clear layout", "Readable text"],
        }
        result = builder.build_infographic_image_prompt(
            prompt_data=prompt_data,
            page_plan=sample_page_plan,
            layout=sample_layout,
            total_pages=3,
            style_injection=sample_style_injection,
        )
        assert isinstance(result, ImagePrompt)
        assert result.image_number == 1
        assert result.title == "ML Overview"

    def test_adds_style_prefix(
        self, builder, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that style prefix is added to main prompt."""
        prompt_data = {
            "main_prompt": "An infographic about ML",
        }
        result = builder.build_infographic_image_prompt(
            prompt_data=prompt_data,
            page_plan=sample_page_plan,
            layout=sample_layout,
            total_pages=3,
            style_injection=sample_style_injection,
        )
        assert "Professional illustration" in result.prompt.main_prompt

    def test_does_not_duplicate_style_prefix(
        self, builder, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that style prefix is not duplicated if already present."""
        prompt_data = {
            "main_prompt": "Professional illustration of ML concepts",
        }
        result = builder.build_infographic_image_prompt(
            prompt_data=prompt_data,
            page_plan=sample_page_plan,
            layout=sample_layout,
            total_pages=3,
            style_injection=sample_style_injection,
        )
        count = result.prompt.main_prompt.count("Professional illustration")
        assert count == 1

    def test_adds_typography_spec(
        self, builder, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that typography specifications are added to prompt."""
        prompt_data = {
            "main_prompt": "An infographic",
            "typography_spec": {
                "headline_text": ["Main Title"],
                "body_text": ["Description text"],
            },
        }
        result = builder.build_infographic_image_prompt(
            prompt_data=prompt_data,
            page_plan=sample_page_plan,
            layout=sample_layout,
            total_pages=3,
            style_injection=sample_style_injection,
        )
        assert "HEADLINE TEXT" in result.prompt.main_prompt
        assert "Main Title" in result.prompt.main_prompt

    def test_sets_flow_connection_for_middle_page(
        self, builder, sample_layout, sample_style_injection
    ):
        """Test flow connections for a middle page."""
        page_plan = PagePlan(
            page_number=2,
            page_type=PageType.FRAMEWORK_OVERVIEW,
            title="Details",
            content_focus="Framework details",
        )
        prompt_data = {"main_prompt": "test"}
        result = builder.build_infographic_image_prompt(
            prompt_data=prompt_data,
            page_plan=page_plan,
            layout=sample_layout,
            total_pages=3,
            style_injection=sample_style_injection,
        )
        assert result.flow_connection.previous == 1
        assert result.flow_connection.next_image == 3

    def test_sets_flow_connection_for_last_page(
        self, builder, sample_layout, sample_style_injection
    ):
        """Test flow connections for the last page."""
        page_plan = PagePlan(
            page_number=3,
            page_type=PageType.REFERENCE_ACTION,
            title="Reference",
            content_focus="Quick reference",
        )
        prompt_data = {"main_prompt": "test"}
        result = builder.build_infographic_image_prompt(
            prompt_data=prompt_data,
            page_plan=page_plan,
            layout=sample_layout,
            total_pages=3,
            style_injection=sample_style_injection,
        )
        assert result.flow_connection.previous == 2
        assert result.flow_connection.next_image is None
        assert "Final page" in result.flow_connection.transition_intent

    def test_generates_default_criteria_if_missing(
        self, builder, sample_page_plan, sample_layout, sample_style_injection
    ):
        """Test that default criteria are generated when not in response."""
        prompt_data = {"main_prompt": "test"}
        result = builder.build_infographic_image_prompt(
            prompt_data=prompt_data,
            page_plan=sample_page_plan,
            layout=sample_layout,
            total_pages=3,
            style_injection=sample_style_injection,
        )
        assert len(result.success_criteria) > 0
        assert any("content_focus" in c or "presents" in c.lower() for c in result.success_criteria)


class TestFormatConceptsDetail:
    """Tests for formatting concepts for infographic prompts."""

    def test_formats_concepts_with_details(self, builder):
        """Test that concepts are formatted with full details."""
        concepts = [
            Concept(
                id=1,
                name="Neural Networks",
                description="Computational systems",
                complexity=Complexity.MODERATE,
                visual_potential=VisualPotential.HIGH,
            ),
        ]
        result = builder._format_concepts_detail(concepts)
        assert "Neural Networks" in result
        assert "Computational systems" in result
        assert "high" in result
        assert "moderate" in result

    def test_handles_empty_concepts(self, builder):
        """Test handling of empty concept list."""
        result = builder._format_concepts_detail([])
        assert "No specific concepts" in result

    def test_formats_multiple_concepts(self, builder):
        """Test formatting multiple concepts."""
        concepts = [
            Concept(id=1, name="Concept A", description="Desc A"),
            Concept(id=2, name="Concept B", description="Desc B"),
        ]
        result = builder._format_concepts_detail(concepts)
        assert "Concept A" in result
        assert "Concept B" in result


class TestBuildZoneSpecifications:
    """Tests for building zone specifications."""

    def test_includes_all_zones(self, builder, sample_layout, sample_page_plan, sample_analysis):
        """Test that all zones from layout are included."""
        result = builder._build_zone_specifications(
            layout=sample_layout,
            page_plan=sample_page_plan,
            analysis=sample_analysis,
        )
        assert "page_header" in result
        assert "hero_stat" in result
        assert "supporting_content" in result

    def test_includes_zone_properties(
        self, builder, sample_layout, sample_page_plan, sample_analysis
    ):
        """Test that zone properties are included."""
        result = builder._build_zone_specifications(
            layout=sample_layout,
            page_plan=sample_page_plan,
            analysis=sample_analysis,
        )
        assert "Position" in result
        assert "Size" in result
        assert "Content Type" in result
        assert "Typography Scale" in result

    def test_includes_zone_assignments(
        self, builder, sample_layout, sample_page_plan, sample_analysis
    ):
        """Test that zone assignments are included."""
        result = builder._build_zone_specifications(
            layout=sample_layout,
            page_plan=sample_page_plan,
            analysis=sample_analysis,
        )
        assert "Machine Learning: A Visual Guide" in result


class TestGetCrossReferencesText:
    """Tests for generating cross-reference text."""

    def test_returns_empty_for_no_references(self, builder):
        """Test that empty string is returned when no cross-references."""
        page_plan = PagePlan(
            page_number=1,
            page_type=PageType.HERO_SUMMARY,
            title="Test",
            content_focus="Test",
            cross_references=[],
        )
        result = builder._get_cross_references_text(page_plan)
        assert result == ""

    def test_formats_cross_references(self, builder):
        """Test that cross-references are properly formatted."""
        page_plan = PagePlan(
            page_number=1,
            page_type=PageType.HERO_SUMMARY,
            title="Test",
            content_focus="Test",
            cross_references=["See page 2", "See page 3"],
        )
        result = builder._get_cross_references_text(page_plan)
        assert "See page 2" in result
        assert "See page 3" in result


class TestFormatTypographyForPrompt:
    """Tests for typography formatting."""

    def test_formats_headline_text(self, builder):
        """Test headline text formatting."""
        spec = {"headline_text": ["Main Title", "Key Stat"]}
        result = builder._format_typography_for_prompt(spec)
        assert "HEADLINE TEXT" in result
        assert "Main Title" in result
        assert "48-72pt" in result

    def test_formats_subhead_text(self, builder):
        """Test subhead text formatting."""
        spec = {"subhead_text": ["Section A"]}
        result = builder._format_typography_for_prompt(spec)
        assert "SUBHEAD TEXT" in result
        assert "Section A" in result

    def test_formats_body_text(self, builder):
        """Test body text formatting."""
        spec = {"body_text": ["Paragraph content"]}
        result = builder._format_typography_for_prompt(spec)
        assert "BODY TEXT" in result
        assert "Paragraph content" in result

    def test_formats_caption_text(self, builder):
        """Test caption text formatting."""
        spec = {"caption_text": ["Source: Data Corp"]}
        result = builder._format_typography_for_prompt(spec)
        assert "CAPTION TEXT" in result
        assert "Source: Data Corp" in result

    def test_handles_empty_spec(self, builder):
        """Test handling of empty typography spec."""
        result = builder._format_typography_for_prompt({})
        assert "TEXT CONTENT SPECIFICATIONS" in result


class TestGenerateInfographicCriteria:
    """Tests for generating default infographic criteria."""

    def test_generates_criteria_list(self, builder, sample_page_plan, sample_layout):
        """Test that criteria list is generated."""
        criteria = builder._generate_infographic_criteria(sample_page_plan, sample_layout)
        assert len(criteria) >= 5

    def test_includes_content_focus(self, builder, sample_page_plan, sample_layout):
        """Test that criteria include content focus."""
        criteria = builder._generate_infographic_criteria(sample_page_plan, sample_layout)
        assert any("Executive summary" in c for c in criteria)

    def test_includes_zone_count(self, builder, sample_page_plan, sample_layout):
        """Test that criteria mention zone count."""
        criteria = builder._generate_infographic_criteria(sample_page_plan, sample_layout)
        assert any("3" in c and "zone" in c.lower() for c in criteria)

    def test_adds_consistency_for_non_first_page(self, builder, sample_layout):
        """Test that visual consistency criterion is added for pages > 1."""
        page_plan = PagePlan(
            page_number=2,
            page_type=PageType.FRAMEWORK_OVERVIEW,
            title="Details",
            content_focus="Details",
        )
        criteria = builder._generate_infographic_criteria(page_plan, sample_layout)
        assert any("consistency" in c.lower() for c in criteria)

    def test_no_consistency_for_first_page(self, builder, sample_page_plan, sample_layout):
        """Test that first page does not get consistency criterion."""
        criteria = builder._generate_infographic_criteria(sample_page_plan, sample_layout)
        # First page should not have consistency criterion
        consistency_criteria = [
            c for c in criteria if "consistency" in c.lower() and "previous" in c.lower()
        ]
        assert len(consistency_criteria) == 0


class TestCombineNegativePrompts:
    """Tests for combining negative prompts."""

    def test_combines_multiple_prompts(self, builder):
        """Test combining multiple negative prompts."""
        result = builder._combine_negative_prompts("text, labels", "clutter")
        assert "text" in result
        assert "labels" in result
        assert "clutter" in result

    def test_deduplicates(self, builder):
        """Test that duplicate entries are removed."""
        result = builder._combine_negative_prompts("text, text", "text")
        assert result.count("text") == 1

    def test_handles_empty(self, builder):
        """Test handling of empty prompts."""
        result = builder._combine_negative_prompts("", "", "text")
        assert "text" in result
