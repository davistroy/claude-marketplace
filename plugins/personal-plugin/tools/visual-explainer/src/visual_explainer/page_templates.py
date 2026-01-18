"""Page templates for infographic generation.

This module defines layout templates for different page types used in
visual explanation infographics. Each template specifies:

- Content zones with positions and sizes
- Typography guidance per zone
- Content type expectations
- Design notes for prompt generation

Page templates are designed for 11x17 inch landscape (5100x3300 pixels at 300 DPI)
4K infographics that can hold significant information density.

Usage:
    from visual_explainer.page_templates import get_layout_for_page_type, PAGE_LAYOUTS

    layout = get_layout_for_page_type(PageType.HERO_SUMMARY)
    for zone in layout.zones:
        print(f"{zone.name}: {zone.content_guidance}")
"""

from __future__ import annotations

from .models import ContentType, ContentZone, PageLayout, PageType


def _create_hero_summary_layout() -> PageLayout:
    """Create layout for Hero Summary page.

    The executive overview page - if someone sees ONE page, this is it.
    Contains: core thesis, key stats, framework preview.
    """
    return PageLayout(
        page_type=PageType.HERO_SUMMARY,
        description="Executive overview - the 'one page' view of the entire document",
        zones=[
            ContentZone(
                name="page_header",
                position="top_full",
                width_percent=100,
                height_percent=8,
                content_type=ContentType.NARRATIVE,
                content_guidance="Document title in large headline, page subtitle, page number indicator",
                typography_scale="headline",
            ),
            ContentZone(
                name="hero_stat",
                position="top_center",
                width_percent=40,
                height_percent=20,
                content_type=ContentType.STATISTICS,
                content_guidance="Single most impactful statistic or key insight in very large typography with brief context",
                typography_scale="headline",
            ),
            ContentZone(
                name="main_framework",
                position="center",
                width_percent=60,
                height_percent=45,
                content_type=ContentType.FRAMEWORK,
                content_guidance="Primary framework diagram, process overview, or conceptual model. Include labels and annotations.",
                typography_scale="subhead",
            ),
            ContentZone(
                name="left_rail",
                position="left",
                width_percent=18,
                height_percent=65,
                content_type=ContentType.LIST,
                content_guidance="Key definitions, legend, or quick reference items. 3-5 bullet points with icons.",
                typography_scale="body",
            ),
            ContentZone(
                name="detail_cards",
                position="bottom_right",
                width_percent=80,
                height_percent=22,
                content_type=ContentType.LIST,
                content_guidance="3-4 detail cards showing key concepts, each with icon, title, and 1-2 sentence description",
                typography_scale="body",
            ),
            ContentZone(
                name="page_footer",
                position="bottom_full",
                width_percent=100,
                height_percent=5,
                content_type=ContentType.NARRATIVE,
                content_guidance="Source citation, cross-references to other pages, document metadata",
                typography_scale="caption",
            ),
        ],
        design_notes=(
            "Hero page should be visually striking with clear focal point. "
            "Use largest typography for the hero stat. Framework diagram should be "
            "detailed enough to be meaningful but not overwhelming. Detail cards "
            "preview what's covered in subsequent pages."
        ),
    )


def _create_problem_landscape_layout() -> PageLayout:
    """Create layout for Problem Landscape page.

    Why this matters, failure modes, risks, current state analysis.
    """
    return PageLayout(
        page_type=PageType.PROBLEM_LANDSCAPE,
        description="Problem definition, failure modes, risks, and why this matters",
        zones=[
            ContentZone(
                name="page_header",
                position="top_full",
                width_percent=100,
                height_percent=8,
                content_type=ContentType.NARRATIVE,
                content_guidance="Page title emphasizing the problem/challenge, page number",
                typography_scale="headline",
            ),
            ContentZone(
                name="problem_tree",
                position="center",
                width_percent=55,
                height_percent=55,
                content_type=ContentType.HIERARCHY,
                content_guidance="Failure taxonomy tree, risk hierarchy, or problem decomposition diagram with branches and sub-branches labeled",
                typography_scale="body",
            ),
            ContentZone(
                name="stats_column",
                position="right",
                width_percent=25,
                height_percent=55,
                content_type=ContentType.STATISTICS,
                content_guidance="4-6 key statistics with large numbers and brief context. Stack vertically.",
                typography_scale="subhead",
            ),
            ContentZone(
                name="context_panel",
                position="left",
                width_percent=18,
                height_percent=55,
                content_type=ContentType.NARRATIVE,
                content_guidance="Why this matters now, target audience impact, urgency indicators",
                typography_scale="body",
            ),
            ContentZone(
                name="warning_signs",
                position="bottom",
                width_percent=100,
                height_percent=25,
                content_type=ContentType.LIST,
                content_guidance="Warning signs checklist or symptoms grid. 6-8 items in 2-3 columns with icons.",
                typography_scale="body",
            ),
            ContentZone(
                name="page_footer",
                position="bottom_full",
                width_percent=100,
                height_percent=5,
                content_type=ContentType.NARRATIVE,
                content_guidance="Cross-reference to solution pages",
                typography_scale="caption",
            ),
        ],
        design_notes=(
            "Use warning colors (amber, red accents) strategically for high-risk items. "
            "Problem tree should show clear cause-effect or categorization. "
            "Statistics should be impactful numbers that drive urgency."
        ),
    )


def _create_framework_overview_layout() -> PageLayout:
    """Create layout for Framework Overview page.

    High-level view of methodology, process, or conceptual framework.
    """
    return PageLayout(
        page_type=PageType.FRAMEWORK_OVERVIEW,
        description="High-level process, methodology, or framework visualization",
        zones=[
            ContentZone(
                name="page_header",
                position="top_full",
                width_percent=100,
                height_percent=8,
                content_type=ContentType.NARRATIVE,
                content_guidance="Framework/process name, brief tagline, page number",
                typography_scale="headline",
            ),
            ContentZone(
                name="process_flow",
                position="center",
                width_percent=100,
                height_percent=50,
                content_type=ContentType.PROCESS,
                content_guidance="Full horizontal or circular process flow with all stages. Each stage has: number, name, icon, key activity. Show arrows/connections between stages.",
                typography_scale="subhead",
            ),
            ContentZone(
                name="phase_details",
                position="bottom",
                width_percent=100,
                height_percent=30,
                content_type=ContentType.LIST,
                content_guidance="Stage detail cards aligned with process flow above. Each card: stage name, 2-3 key activities, primary deliverable",
                typography_scale="body",
            ),
            ContentZone(
                name="framework_metadata",
                position="left_bottom",
                width_percent=20,
                height_percent=15,
                content_type=ContentType.NARRATIVE,
                content_guidance="Framework attribution, version, or key principles in sidebar",
                typography_scale="caption",
            ),
            ContentZone(
                name="page_footer",
                position="bottom_full",
                width_percent=100,
                height_percent=5,
                content_type=ContentType.NARRATIVE,
                content_guidance="Cross-reference to deep-dive pages for each stage",
                typography_scale="caption",
            ),
        ],
        design_notes=(
            "Process flow should read left-to-right or clockwise. Use consistent "
            "color coding per stage that carries through to detail cards. "
            "Ensure clear visual connection between overview and detail sections."
        ),
    )


def _create_framework_deep_dive_layout() -> PageLayout:
    """Create layout for Framework Deep-Dive page.

    Detailed breakdown of specific stages, activities, and deliverables.
    """
    return PageLayout(
        page_type=PageType.FRAMEWORK_DEEP_DIVE,
        description="Detailed breakdown of framework stages with activities and deliverables",
        zones=[
            ContentZone(
                name="page_header",
                position="top_full",
                width_percent=100,
                height_percent=8,
                content_type=ContentType.NARRATIVE,
                content_guidance="Stage names covered on this page (e.g., 'Stages 1-3: Discovery Phase'), page number",
                typography_scale="headline",
            ),
            ContentZone(
                name="stage_1",
                position="left_third",
                width_percent=32,
                height_percent=75,
                content_type=ContentType.PROCESS,
                content_guidance="First stage panel: Stage icon/number at top, stage name, diverge/converge indicator, list of 4-6 activities, key deliverables, decision criteria, example artifacts",
                typography_scale="body",
            ),
            ContentZone(
                name="stage_2",
                position="center_third",
                width_percent=32,
                height_percent=75,
                content_type=ContentType.PROCESS,
                content_guidance="Second stage panel with same structure as stage_1",
                typography_scale="body",
            ),
            ContentZone(
                name="stage_3",
                position="right_third",
                width_percent=32,
                height_percent=75,
                content_type=ContentType.PROCESS,
                content_guidance="Third stage panel with same structure as stage_1",
                typography_scale="body",
            ),
            ContentZone(
                name="cross_stage_guidance",
                position="bottom",
                width_percent=100,
                height_percent=12,
                content_type=ContentType.NARRATIVE,
                content_guidance="Cross-stage relationships, handoff points, or shared resources. Include navigation arrows between stages.",
                typography_scale="body",
            ),
            ContentZone(
                name="page_footer",
                position="bottom_full",
                width_percent=100,
                height_percent=5,
                content_type=ContentType.NARRATIVE,
                content_guidance="Cross-reference to other deep-dive pages and reference page",
                typography_scale="caption",
            ),
        ],
        design_notes=(
            "Each stage panel should be a complete mini-infographic. Use consistent "
            "structure across panels so reader can scan. Include checklists or "
            "numbered lists for activities. Color-code to match overview page."
        ),
    )


def _create_comparison_matrix_layout() -> PageLayout:
    """Create layout for Comparison Matrix page.

    Side-by-side analysis of options, vendors, or alternatives.
    """
    return PageLayout(
        page_type=PageType.COMPARISON_MATRIX,
        description="Side-by-side comparison of options, vendors, or approaches",
        zones=[
            ContentZone(
                name="page_header",
                position="top_full",
                width_percent=100,
                height_percent=8,
                content_type=ContentType.NARRATIVE,
                content_guidance="Comparison title (e.g., 'Vendor Comparison Matrix'), page number",
                typography_scale="headline",
            ),
            ContentZone(
                name="comparison_table",
                position="center",
                width_percent=85,
                height_percent=65,
                content_type=ContentType.MATRIX,
                content_guidance="Full comparison matrix: column headers for each option/vendor, row headers for criteria. Use icons and color coding (green/yellow/red) for ratings. Include specific values where available.",
                typography_scale="body",
            ),
            ContentZone(
                name="legend",
                position="left",
                width_percent=12,
                height_percent=30,
                content_type=ContentType.LIST,
                content_guidance="Color coding legend, rating scale explanation, icons key",
                typography_scale="caption",
            ),
            ContentZone(
                name="key_insights",
                position="bottom",
                width_percent=100,
                height_percent=15,
                content_type=ContentType.LIST,
                content_guidance="3-4 key insights or recommendations from the comparison. What to choose when.",
                typography_scale="body",
            ),
            ContentZone(
                name="page_footer",
                position="bottom_full",
                width_percent=100,
                height_percent=5,
                content_type=ContentType.NARRATIVE,
                content_guidance="Data sources, evaluation date, disclaimer if applicable",
                typography_scale="caption",
            ),
        ],
        design_notes=(
            "Matrix should be the dominant element. Use color coding consistently: "
            "green=good, yellow=partial, red=concern. Ensure text in cells is "
            "readable. Key insights should help reader make decisions."
        ),
    )


def _create_dimensions_variations_layout() -> PageLayout:
    """Create layout for Dimensions/Variations page.

    How the framework adapts across different contexts, scales, or audiences.
    """
    return PageLayout(
        page_type=PageType.DIMENSIONS_VARIATIONS,
        description="How the framework adapts to different contexts, scales, or applications",
        zones=[
            ContentZone(
                name="page_header",
                position="top_full",
                width_percent=100,
                height_percent=8,
                content_type=ContentType.NARRATIVE,
                content_guidance="Page title emphasizing adaptability, page number",
                typography_scale="headline",
            ),
            ContentZone(
                name="primary_matrix",
                position="top_center",
                width_percent=60,
                height_percent=40,
                content_type=ContentType.MATRIX,
                content_guidance="Main dimensions matrix (e.g., 3x3 for horizons x dimensions). Each cell has label and brief description.",
                typography_scale="body",
            ),
            ContentZone(
                name="scale_table",
                position="bottom_left",
                width_percent=48,
                height_percent=35,
                content_type=ContentType.COMPARISON,
                content_guidance="Scale/size variations table (e.g., Small/Medium/Large projects). Columns for resources, team size, duration, deliverables.",
                typography_scale="body",
            ),
            ContentZone(
                name="audience_variations",
                position="bottom_right",
                width_percent=48,
                height_percent=35,
                content_type=ContentType.LIST,
                content_guidance="Audience-specific adaptations or use case variations. 3-5 items with icons.",
                typography_scale="body",
            ),
            ContentZone(
                name="selection_guidance",
                position="right",
                width_percent=18,
                height_percent=40,
                content_type=ContentType.NARRATIVE,
                content_guidance="How to determine which variation applies. Decision criteria or diagnostic questions.",
                typography_scale="body",
            ),
            ContentZone(
                name="page_footer",
                position="bottom_full",
                width_percent=100,
                height_percent=5,
                content_type=ContentType.NARRATIVE,
                content_guidance="Cross-reference to reference page for quick application",
                typography_scale="caption",
            ),
        ],
        design_notes=(
            "Use visual encoding to show relationships (e.g., gradient for uncertainty, "
            "size for resource intensity). Matrices should have clear axes. "
            "Help reader quickly locate their situation."
        ),
    )


def _create_reference_action_layout() -> PageLayout:
    """Create layout for Reference/Action page.

    Checklists, decision trees, quick reference, actionable guidance.
    """
    return PageLayout(
        page_type=PageType.REFERENCE_ACTION,
        description="Quick reference, checklists, decision trees, and action items",
        zones=[
            ContentZone(
                name="page_header",
                position="top_full",
                width_percent=100,
                height_percent=8,
                content_type=ContentType.NARRATIVE,
                content_guidance="'Quick Reference' or 'Action Guide' title, page number",
                typography_scale="headline",
            ),
            ContentZone(
                name="decision_tree",
                position="left",
                width_percent=45,
                height_percent=50,
                content_type=ContentType.HIERARCHY,
                content_guidance="Decision tree or diagnostic flowchart. Start with question, branch to outcomes. Include 'you are here' type navigation.",
                typography_scale="body",
            ),
            ContentZone(
                name="checklist_1",
                position="right_top",
                width_percent=50,
                height_percent=30,
                content_type=ContentType.LIST,
                content_guidance="Primary checklist (e.g., '90-day action plan' or 'Getting Started'). 6-8 items with checkboxes.",
                typography_scale="body",
            ),
            ContentZone(
                name="checklist_2",
                position="right_bottom",
                width_percent=50,
                height_percent=30,
                content_type=ContentType.LIST,
                content_guidance="Secondary checklist (e.g., 'Common Pitfalls to Avoid'). 4-6 items with warning icons.",
                typography_scale="body",
            ),
            ContentZone(
                name="quick_reference",
                position="bottom",
                width_percent=100,
                height_percent=25,
                content_type=ContentType.LIST,
                content_guidance="Quick reference cards: 4-6 cards in a row. Each card: term/concept, 1-2 sentence definition or key point. Include key contacts or resources if applicable.",
                typography_scale="body",
            ),
            ContentZone(
                name="page_footer",
                position="bottom_full",
                width_percent=100,
                height_percent=5,
                content_type=ContentType.NARRATIVE,
                content_guidance="Contact information, resources links, version date",
                typography_scale="caption",
            ),
        ],
        design_notes=(
            "This page should be immediately actionable. Decision tree helps reader "
            "locate themselves. Checklists are for direct use. Quick reference cards "
            "summarize key concepts from the full document."
        ),
    )


def _create_data_evidence_layout() -> PageLayout:
    """Create layout for Data/Evidence page.

    Charts, statistics, research findings, quantitative analysis.
    """
    return PageLayout(
        page_type=PageType.DATA_EVIDENCE,
        description="Charts, statistics, research findings, and quantitative evidence",
        zones=[
            ContentZone(
                name="page_header",
                position="top_full",
                width_percent=100,
                height_percent=8,
                content_type=ContentType.NARRATIVE,
                content_guidance="Page title emphasizing data/research, page number",
                typography_scale="headline",
            ),
            ContentZone(
                name="primary_chart",
                position="center_left",
                width_percent=50,
                height_percent=45,
                content_type=ContentType.STATISTICS,
                content_guidance="Primary data visualization: bar chart, pie chart, or trend line. Include title, axis labels, legend, and data point labels.",
                typography_scale="body",
            ),
            ContentZone(
                name="secondary_chart",
                position="center_right",
                width_percent=45,
                height_percent=45,
                content_type=ContentType.STATISTICS,
                content_guidance="Secondary data visualization complementing the primary. Different chart type for variety.",
                typography_scale="body",
            ),
            ContentZone(
                name="stat_callouts",
                position="top_right",
                width_percent=30,
                height_percent=20,
                content_type=ContentType.STATISTICS,
                content_guidance="3-4 key statistics as large callout numbers with brief labels",
                typography_scale="headline",
            ),
            ContentZone(
                name="insights",
                position="bottom",
                width_percent=100,
                height_percent=20,
                content_type=ContentType.NARRATIVE,
                content_guidance="Key insights from the data: 3-4 bullet points explaining what the data means and implications",
                typography_scale="body",
            ),
            ContentZone(
                name="page_footer",
                position="bottom_full",
                width_percent=100,
                height_percent=5,
                content_type=ContentType.NARRATIVE,
                content_guidance="Data sources, methodology notes, date of data collection",
                typography_scale="caption",
            ),
        ],
        design_notes=(
            "Charts should be clearly labeled and easy to interpret. Use consistent "
            "colors that match overall document theme. Stat callouts should be the "
            "most impactful numbers. Insights explain 'so what' of the data."
        ),
    )


# Pre-built layouts for each page type
PAGE_LAYOUTS: dict[PageType, PageLayout] = {
    PageType.HERO_SUMMARY: _create_hero_summary_layout(),
    PageType.PROBLEM_LANDSCAPE: _create_problem_landscape_layout(),
    PageType.FRAMEWORK_OVERVIEW: _create_framework_overview_layout(),
    PageType.FRAMEWORK_DEEP_DIVE: _create_framework_deep_dive_layout(),
    PageType.COMPARISON_MATRIX: _create_comparison_matrix_layout(),
    PageType.DIMENSIONS_VARIATIONS: _create_dimensions_variations_layout(),
    PageType.REFERENCE_ACTION: _create_reference_action_layout(),
    PageType.DATA_EVIDENCE: _create_data_evidence_layout(),
}


def get_layout_for_page_type(page_type: PageType) -> PageLayout:
    """Get the layout template for a specific page type.

    Args:
        page_type: The type of page to get layout for.

    Returns:
        PageLayout template for the specified page type.

    Raises:
        KeyError: If page_type is not found in PAGE_LAYOUTS.
    """
    return PAGE_LAYOUTS[page_type]


def get_all_layouts() -> dict[PageType, PageLayout]:
    """Get all available page layouts.

    Returns:
        Dictionary mapping PageType to PageLayout.
    """
    return PAGE_LAYOUTS.copy()


def get_zone_prompt_guidance(zone: ContentZone) -> str:
    """Generate prompt guidance for a specific content zone.

    Creates specific prompt instructions based on the zone's content type
    and typography requirements.

    Args:
        zone: The content zone to generate guidance for.

    Returns:
        Prompt guidance string for this zone.
    """
    typography_specs = {
        "headline": "72pt bold, high contrast, maximum readability",
        "subhead": "36pt semi-bold, clear hierarchy",
        "body": "18-24pt regular, comfortable reading size",
        "caption": "12-14pt light, supporting information",
    }

    content_type_guidance = {
        ContentType.STATISTICS: (
            "Display numbers prominently with context. Use large typography for key "
            "figures. Include units, comparisons, or trend indicators."
        ),
        ContentType.PROCESS: (
            "Show steps in clear sequence with numbered stages, directional arrows, "
            "and stage labels. Include activity lists within each stage."
        ),
        ContentType.COMPARISON: (
            "Create side-by-side layout with consistent structure. Use color coding "
            "for positive/negative/neutral ratings."
        ),
        ContentType.HIERARCHY: (
            "Show parent-child relationships clearly with connecting lines. Use "
            "indentation or nesting to indicate levels."
        ),
        ContentType.TIMELINE: (
            "Arrange chronologically left-to-right or top-to-bottom. Mark key "
            "milestones prominently. Include date labels."
        ),
        ContentType.FRAMEWORK: (
            "Visualize conceptual model with labeled components and relationships. "
            "Use shapes consistently for different element types."
        ),
        ContentType.NARRATIVE: (
            "Present text in clear paragraphs or bullet points. Ensure high readability "
            "with appropriate line spacing."
        ),
        ContentType.LIST: (
            "Display items with consistent formatting: icons, numbers, or bullets. "
            "Keep items concise. Align items cleanly."
        ),
        ContentType.MATRIX: (
            "Create grid with clear row and column headers. Use color coding for "
            "cell values. Ensure text in cells is readable."
        ),
    }

    guidance_parts = [
        f"Zone: {zone.name}",
        f"Position: {zone.position}",
        f"Size: {zone.width_percent}% x {zone.height_percent}%",
        f"Typography: {typography_specs.get(zone.typography_scale, 'body')}",
        f"Content: {zone.content_guidance}",
        f"Style: {content_type_guidance.get(zone.content_type, 'Standard layout')}",
    ]

    return "\n".join(guidance_parts)
