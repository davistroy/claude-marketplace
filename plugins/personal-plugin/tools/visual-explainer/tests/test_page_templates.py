"""Tests for page_templates module.

Tests the page layout templates including:
- All 8 page types have layouts defined
- Zone specifications for each layout
- get_layout_for_page_type function
- get_all_layouts function
- get_zone_prompt_guidance function
- Zone content types and positions
- Typography specifications
"""

from __future__ import annotations

import pytest

from visual_explainer.models import ContentType, ContentZone, PageLayout, PageType
from visual_explainer.page_templates import (
    PAGE_LAYOUTS,
    get_all_layouts,
    get_layout_for_page_type,
    get_zone_prompt_guidance,
)

# ---------------------------------------------------------------------------
# PAGE_LAYOUTS Registry Tests
# ---------------------------------------------------------------------------


class TestPageLayoutsRegistry:
    """Tests for the PAGE_LAYOUTS dictionary."""

    def test_all_page_types_present(self):
        """Test all PageType enum values have layouts."""
        for page_type in PageType:
            assert page_type in PAGE_LAYOUTS, f"Missing layout for {page_type.value}"

    def test_layout_count(self):
        """Test the expected number of layouts."""
        assert len(PAGE_LAYOUTS) == 8

    def test_all_values_are_page_layouts(self):
        """Test all values are PageLayout instances."""
        for page_type, layout in PAGE_LAYOUTS.items():
            assert isinstance(layout, PageLayout), f"{page_type}: not a PageLayout"


# ---------------------------------------------------------------------------
# get_layout_for_page_type Tests
# ---------------------------------------------------------------------------


class TestGetLayoutForPageType:
    """Tests for the get_layout_for_page_type function."""

    def test_hero_summary(self):
        """Test getting Hero Summary layout."""
        layout = get_layout_for_page_type(PageType.HERO_SUMMARY)
        assert layout.page_type == PageType.HERO_SUMMARY
        assert len(layout.zones) > 0

    def test_problem_landscape(self):
        """Test getting Problem Landscape layout."""
        layout = get_layout_for_page_type(PageType.PROBLEM_LANDSCAPE)
        assert layout.page_type == PageType.PROBLEM_LANDSCAPE

    def test_framework_overview(self):
        """Test getting Framework Overview layout."""
        layout = get_layout_for_page_type(PageType.FRAMEWORK_OVERVIEW)
        assert layout.page_type == PageType.FRAMEWORK_OVERVIEW

    def test_framework_deep_dive(self):
        """Test getting Framework Deep-Dive layout."""
        layout = get_layout_for_page_type(PageType.FRAMEWORK_DEEP_DIVE)
        assert layout.page_type == PageType.FRAMEWORK_DEEP_DIVE

    def test_comparison_matrix(self):
        """Test getting Comparison Matrix layout."""
        layout = get_layout_for_page_type(PageType.COMPARISON_MATRIX)
        assert layout.page_type == PageType.COMPARISON_MATRIX

    def test_dimensions_variations(self):
        """Test getting Dimensions/Variations layout."""
        layout = get_layout_for_page_type(PageType.DIMENSIONS_VARIATIONS)
        assert layout.page_type == PageType.DIMENSIONS_VARIATIONS

    def test_reference_action(self):
        """Test getting Reference/Action layout."""
        layout = get_layout_for_page_type(PageType.REFERENCE_ACTION)
        assert layout.page_type == PageType.REFERENCE_ACTION

    def test_data_evidence(self):
        """Test getting Data/Evidence layout."""
        layout = get_layout_for_page_type(PageType.DATA_EVIDENCE)
        assert layout.page_type == PageType.DATA_EVIDENCE

    def test_invalid_type_raises(self):
        """Test that invalid page type raises KeyError."""
        with pytest.raises(KeyError):
            get_layout_for_page_type("invalid_type")


# ---------------------------------------------------------------------------
# get_all_layouts Tests
# ---------------------------------------------------------------------------


class TestGetAllLayouts:
    """Tests for the get_all_layouts function."""

    def test_returns_copy(self):
        """Test get_all_layouts returns a copy."""
        layouts = get_all_layouts()
        assert layouts is not PAGE_LAYOUTS
        assert len(layouts) == len(PAGE_LAYOUTS)

    def test_modifications_dont_affect_original(self):
        """Test modifications to returned dict don't affect module-level dict."""
        layouts = get_all_layouts()
        layouts.pop(PageType.HERO_SUMMARY)
        assert PageType.HERO_SUMMARY in PAGE_LAYOUTS


# ---------------------------------------------------------------------------
# Zone Specification Tests (per layout)
# ---------------------------------------------------------------------------


class TestHeroSummaryZones:
    """Tests for Hero Summary page zones."""

    def test_has_page_header(self):
        """Test Hero Summary has page_header zone."""
        layout = get_layout_for_page_type(PageType.HERO_SUMMARY)
        names = [z.name for z in layout.zones]
        assert "page_header" in names

    def test_has_hero_stat(self):
        """Test Hero Summary has hero_stat zone."""
        layout = get_layout_for_page_type(PageType.HERO_SUMMARY)
        names = [z.name for z in layout.zones]
        assert "hero_stat" in names

    def test_has_main_framework(self):
        """Test Hero Summary has main_framework zone."""
        layout = get_layout_for_page_type(PageType.HERO_SUMMARY)
        names = [z.name for z in layout.zones]
        assert "main_framework" in names

    def test_zone_count(self):
        """Test Hero Summary has expected zone count."""
        layout = get_layout_for_page_type(PageType.HERO_SUMMARY)
        assert len(layout.zones) == 6

    def test_header_uses_headline_typography(self):
        """Test page_header uses headline typography."""
        layout = get_layout_for_page_type(PageType.HERO_SUMMARY)
        header = next(z for z in layout.zones if z.name == "page_header")
        assert header.typography_scale == "headline"

    def test_has_design_notes(self):
        """Test Hero Summary has design notes."""
        layout = get_layout_for_page_type(PageType.HERO_SUMMARY)
        assert len(layout.design_notes) > 0


class TestProblemLandscapeZones:
    """Tests for Problem Landscape page zones."""

    def test_has_problem_tree(self):
        """Test Problem Landscape has problem_tree zone."""
        layout = get_layout_for_page_type(PageType.PROBLEM_LANDSCAPE)
        names = [z.name for z in layout.zones]
        assert "problem_tree" in names

    def test_problem_tree_is_hierarchy(self):
        """Test problem_tree zone uses HIERARCHY content type."""
        layout = get_layout_for_page_type(PageType.PROBLEM_LANDSCAPE)
        tree = next(z for z in layout.zones if z.name == "problem_tree")
        assert tree.content_type == ContentType.HIERARCHY


class TestFrameworkOverviewZones:
    """Tests for Framework Overview page zones."""

    def test_has_process_flow(self):
        """Test Framework Overview has process_flow zone."""
        layout = get_layout_for_page_type(PageType.FRAMEWORK_OVERVIEW)
        names = [z.name for z in layout.zones]
        assert "process_flow" in names

    def test_process_flow_is_process_type(self):
        """Test process_flow uses PROCESS content type."""
        layout = get_layout_for_page_type(PageType.FRAMEWORK_OVERVIEW)
        flow = next(z for z in layout.zones if z.name == "process_flow")
        assert flow.content_type == ContentType.PROCESS


class TestComparisonMatrixZones:
    """Tests for Comparison Matrix page zones."""

    def test_has_comparison_table(self):
        """Test Comparison Matrix has comparison_table zone."""
        layout = get_layout_for_page_type(PageType.COMPARISON_MATRIX)
        names = [z.name for z in layout.zones]
        assert "comparison_table" in names

    def test_comparison_table_is_matrix(self):
        """Test comparison_table uses MATRIX content type."""
        layout = get_layout_for_page_type(PageType.COMPARISON_MATRIX)
        table = next(z for z in layout.zones if z.name == "comparison_table")
        assert table.content_type == ContentType.MATRIX


class TestDataEvidenceZones:
    """Tests for Data/Evidence page zones."""

    def test_has_primary_chart(self):
        """Test Data Evidence has primary_chart zone."""
        layout = get_layout_for_page_type(PageType.DATA_EVIDENCE)
        names = [z.name for z in layout.zones]
        assert "primary_chart" in names

    def test_has_stat_callouts(self):
        """Test Data Evidence has stat_callouts zone."""
        layout = get_layout_for_page_type(PageType.DATA_EVIDENCE)
        names = [z.name for z in layout.zones]
        assert "stat_callouts" in names


# ---------------------------------------------------------------------------
# Common Zone Properties Tests
# ---------------------------------------------------------------------------


class TestCommonZoneProperties:
    """Tests for common zone properties across all layouts."""

    @pytest.mark.parametrize("page_type", list(PageType))
    def test_all_layouts_have_page_footer(self, page_type):
        """Test all layouts have a page_footer zone."""
        layout = get_layout_for_page_type(page_type)
        names = [z.name for z in layout.zones]
        assert "page_footer" in names

    @pytest.mark.parametrize("page_type", list(PageType))
    def test_all_layouts_have_page_header(self, page_type):
        """Test all layouts have a page_header zone."""
        layout = get_layout_for_page_type(page_type)
        names = [z.name for z in layout.zones]
        assert "page_header" in names

    @pytest.mark.parametrize("page_type", list(PageType))
    def test_all_zones_have_valid_percentages(self, page_type):
        """Test all zones have valid width and height percentages."""
        layout = get_layout_for_page_type(page_type)
        for zone in layout.zones:
            assert 5 <= zone.width_percent <= 100, f"{zone.name}: invalid width"
            assert 5 <= zone.height_percent <= 100, f"{zone.name}: invalid height"

    @pytest.mark.parametrize("page_type", list(PageType))
    def test_all_zones_have_content_guidance(self, page_type):
        """Test all zones have non-empty content guidance."""
        layout = get_layout_for_page_type(page_type)
        for zone in layout.zones:
            assert len(zone.content_guidance) > 0, f"{zone.name}: empty content guidance"

    @pytest.mark.parametrize("page_type", list(PageType))
    def test_all_layouts_have_description(self, page_type):
        """Test all layouts have a description."""
        layout = get_layout_for_page_type(page_type)
        assert len(layout.description) > 0


# ---------------------------------------------------------------------------
# get_zone_prompt_guidance Tests
# ---------------------------------------------------------------------------


class TestGetZonePromptGuidance:
    """Tests for the get_zone_prompt_guidance function."""

    def test_guidance_includes_zone_name(self):
        """Test guidance includes the zone name."""
        zone = ContentZone(
            name="test_zone",
            position="center",
            width_percent=50,
            height_percent=50,
            content_type=ContentType.NARRATIVE,
            content_guidance="Test content",
        )
        guidance = get_zone_prompt_guidance(zone)
        assert "test_zone" in guidance

    def test_guidance_includes_position(self):
        """Test guidance includes position info."""
        zone = ContentZone(
            name="test",
            position="top_left",
            width_percent=30,
            height_percent=20,
            content_type=ContentType.STATISTICS,
            content_guidance="Stats",
        )
        guidance = get_zone_prompt_guidance(zone)
        assert "top_left" in guidance

    def test_guidance_includes_size(self):
        """Test guidance includes size percentages."""
        zone = ContentZone(
            name="test",
            position="center",
            width_percent=60,
            height_percent=40,
            content_type=ContentType.PROCESS,
            content_guidance="Flow",
        )
        guidance = get_zone_prompt_guidance(zone)
        assert "60%" in guidance
        assert "40%" in guidance

    def test_guidance_includes_typography(self):
        """Test guidance includes typography specification."""
        zone = ContentZone(
            name="test",
            position="center",
            width_percent=50,
            height_percent=50,
            content_type=ContentType.NARRATIVE,
            content_guidance="Text",
            typography_scale="headline",
        )
        guidance = get_zone_prompt_guidance(zone)
        assert "72pt bold" in guidance

    def test_guidance_includes_content_type_style(self):
        """Test guidance includes content type style info."""
        zone = ContentZone(
            name="test",
            position="center",
            width_percent=50,
            height_percent=50,
            content_type=ContentType.STATISTICS,
            content_guidance="Numbers",
        )
        guidance = get_zone_prompt_guidance(zone)
        assert "numbers prominently" in guidance.lower() or "Display" in guidance

    @pytest.mark.parametrize(
        "content_type",
        [
            ContentType.STATISTICS,
            ContentType.PROCESS,
            ContentType.COMPARISON,
            ContentType.HIERARCHY,
            ContentType.TIMELINE,
            ContentType.FRAMEWORK,
            ContentType.NARRATIVE,
            ContentType.LIST,
            ContentType.MATRIX,
        ],
    )
    def test_all_content_types_have_guidance(self, content_type):
        """Test all content types produce non-empty guidance."""
        zone = ContentZone(
            name="test",
            position="center",
            width_percent=50,
            height_percent=50,
            content_type=content_type,
            content_guidance="Test",
        )
        guidance = get_zone_prompt_guidance(zone)
        assert len(guidance) > 0

    @pytest.mark.parametrize(
        "scale",
        ["headline", "subhead", "body", "caption"],
    )
    def test_all_typography_scales(self, scale):
        """Test all typography scales produce different guidance."""
        zone = ContentZone(
            name="test",
            position="center",
            width_percent=50,
            height_percent=50,
            content_type=ContentType.NARRATIVE,
            content_guidance="Text",
            typography_scale=scale,
        )
        guidance = get_zone_prompt_guidance(zone)
        assert "Typography" in guidance
