"""Tests for Draw.io style mappings and style generation functions."""

from bpmn2drawio.styles import (
    STYLE_MAP,
    EDGE_STYLES,
    SWIMLANE_STYLES,
    get_element_style,
    get_edge_style,
)
from bpmn2drawio.themes import BPMNTheme, get_theme


class TestStyleMapDefinitions:
    """Tests for STYLE_MAP dictionary completeness and structure."""

    EXPECTED_ELEMENT_TYPES = [
        "startEvent",
        "endEvent",
        "intermediateCatchEvent",
        "intermediateThrowEvent",
        "boundaryEvent",
        "task",
        "userTask",
        "serviceTask",
        "scriptTask",
        "sendTask",
        "receiveTask",
        "businessRuleTask",
        "manualTask",
        "callActivity",
        "subProcess",
        "exclusiveGateway",
        "parallelGateway",
        "inclusiveGateway",
        "eventBasedGateway",
        "complexGateway",
        "dataObject",
        "dataObjectReference",
        "dataStore",
        "dataStoreReference",
        "textAnnotation",
        "group",
    ]

    def test_all_expected_element_types_in_style_map(self):
        """All standard BPMN element types have style mappings."""
        for elem_type in self.EXPECTED_ELEMENT_TYPES:
            assert elem_type in STYLE_MAP, f"Missing style for {elem_type}"

    def test_style_values_are_nonempty_strings(self):
        """All style values are non-empty strings."""
        for elem_type, style in STYLE_MAP.items():
            assert isinstance(style, str), f"{elem_type} style is not a string"
            assert len(style) > 0, f"{elem_type} style is empty"

    def test_style_strings_end_with_semicolon(self):
        """All style strings end with a semicolon (Draw.io convention)."""
        for elem_type, style in STYLE_MAP.items():
            assert style.endswith(";"), (
                f"{elem_type} style does not end with semicolon: {style[-20:]}"
            )

    def test_style_strings_contain_html_flag(self):
        """All element styles include html=1 for Draw.io rendering."""
        for elem_type, style in STYLE_MAP.items():
            assert "html=1" in style, f"{elem_type} missing html=1"

    def test_events_use_ellipse_shape(self):
        """Event element types use ellipse shape."""
        event_types = [
            "startEvent",
            "endEvent",
            "intermediateCatchEvent",
            "intermediateThrowEvent",
            "boundaryEvent",
        ]
        for event_type in event_types:
            assert "ellipse" in STYLE_MAP[event_type], (
                f"{event_type} missing ellipse shape"
            )

    def test_tasks_use_rounded_shape(self):
        """Task element types use rounded rectangle shape."""
        task_types = [
            "task",
            "userTask",
            "serviceTask",
            "scriptTask",
            "sendTask",
            "receiveTask",
            "businessRuleTask",
            "manualTask",
        ]
        for task_type in task_types:
            assert "rounded=1" in STYLE_MAP[task_type], f"{task_type} missing rounded=1"

    def test_gateways_use_rhombus_shape(self):
        """Gateway element types use rhombus shape."""
        gw_types = [
            "exclusiveGateway",
            "parallelGateway",
            "inclusiveGateway",
            "eventBasedGateway",
            "complexGateway",
        ]
        for gw_type in gw_types:
            assert "rhombus" in STYLE_MAP[gw_type], f"{gw_type} missing rhombus shape"

    def test_end_event_has_thick_stroke(self):
        """End event has strokeWidth=3 for visual distinction."""
        assert "strokeWidth=3" in STYLE_MAP["endEvent"]

    def test_call_activity_has_thick_stroke(self):
        """Call activity has strokeWidth=3 (BPMN spec: bold border)."""
        assert "strokeWidth=3" in STYLE_MAP["callActivity"]

    def test_script_task_has_distinct_color(self):
        """Script task has purple fill (#e1d5e7) distinct from other tasks."""
        assert "#e1d5e7" in STYLE_MAP["scriptTask"]
        assert "#e1d5e7" not in STYLE_MAP["task"]

    def test_business_rule_task_has_distinct_color(self):
        """Business rule task has orange fill (#ffe6cc) distinct from other tasks."""
        assert "#ffe6cc" in STYLE_MAP["businessRuleTask"]
        assert "#ffe6cc" not in STYLE_MAP["task"]


class TestEdgeStyleDefinitions:
    """Tests for EDGE_STYLES dictionary."""

    EXPECTED_FLOW_TYPES = [
        "sequenceFlow",
        "messageFlow",
        "association",
        "dataInputAssociation",
        "dataOutputAssociation",
    ]

    def test_all_expected_flow_types_in_edge_styles(self):
        """All standard BPMN flow types have edge styles."""
        for flow_type in self.EXPECTED_FLOW_TYPES:
            assert flow_type in EDGE_STYLES, f"Missing edge style for {flow_type}"

    def test_edge_style_values_are_nonempty_strings(self):
        """All edge style values are non-empty strings."""
        for flow_type, style in EDGE_STYLES.items():
            assert isinstance(style, str), f"{flow_type} edge style is not a string"
            assert len(style) > 0, f"{flow_type} edge style is empty"

    def test_sequence_flow_has_filled_arrow(self):
        """Sequence flow has filled block arrow."""
        style = EDGE_STYLES["sequenceFlow"]
        assert "endArrow=block" in style
        assert "endFill=1" in style

    def test_message_flow_is_dashed(self):
        """Message flow uses dashed line style."""
        style = EDGE_STYLES["messageFlow"]
        assert "dashed=1" in style

    def test_association_has_no_end_arrow(self):
        """Association flow has no arrow head."""
        style = EDGE_STYLES["association"]
        assert "endArrow=none" in style

    def test_all_edge_styles_use_orthogonal_routing(self):
        """All edge styles use orthogonal edge routing."""
        for flow_type, style in EDGE_STYLES.items():
            assert "orthogonalEdgeStyle" in style, (
                f"{flow_type} missing orthogonal routing"
            )


class TestSwimlaneStyleDefinitions:
    """Tests for SWIMLANE_STYLES dictionary."""

    def test_pool_style_exists(self):
        """Pool swimlane style is defined."""
        assert "pool" in SWIMLANE_STYLES

    def test_lane_style_exists(self):
        """Lane swimlane style is defined."""
        assert "lane" in SWIMLANE_STYLES

    def test_pool_vertical_style_exists(self):
        """Vertical pool style is defined."""
        assert "pool_vertical" in SWIMLANE_STYLES

    def test_pool_is_horizontal(self):
        """Pool style uses horizontal=0 (horizontal swimlane orientation)."""
        assert "horizontal=0" in SWIMLANE_STYLES["pool"]

    def test_swimlanes_are_not_collapsible(self):
        """Pool and lane styles are not collapsible."""
        assert "collapsible=0" in SWIMLANE_STYLES["pool"]
        assert "collapsible=0" in SWIMLANE_STYLES["lane"]

    def test_swimlane_styles_contain_swimlane_flag(self):
        """All swimlane styles include the swimlane shape type."""
        for key, style in SWIMLANE_STYLES.items():
            assert style.startswith("swimlane;"), (
                f"{key} does not start with 'swimlane;'"
            )


class TestGetElementStyle:
    """Tests for get_element_style function."""

    def test_known_element_type_returns_mapped_style(self):
        """Known element type returns its exact style from STYLE_MAP."""
        style = get_element_style("startEvent")
        assert style == STYLE_MAP["startEvent"]

    def test_unknown_element_type_falls_back_to_task_style(self):
        """Unknown element type returns the 'task' style as fallback."""
        style = get_element_style("completelyUnknownType")
        assert style == STYLE_MAP["task"]

    def test_each_style_map_entry_accessible(self):
        """Every element type in STYLE_MAP is returned correctly by get_element_style."""
        for elem_type in STYLE_MAP:
            style = get_element_style(elem_type)
            assert style == STYLE_MAP[elem_type], f"Mismatch for {elem_type}"

    def test_empty_string_falls_back_to_task(self):
        """Empty string element type falls back to task style."""
        style = get_element_style("")
        assert style == STYLE_MAP["task"]


class TestGetEdgeStyle:
    """Tests for get_edge_style function."""

    def test_sequence_flow_basic(self):
        """Basic sequence flow returns standard style."""
        style = get_edge_style("sequenceFlow")
        assert style == EDGE_STYLES["sequenceFlow"]

    def test_message_flow_returns_dashed_style(self):
        """Message flow returns its dashed line style."""
        style = get_edge_style("messageFlow")
        assert style == EDGE_STYLES["messageFlow"]
        assert "dashed=1" in style

    def test_unknown_flow_type_falls_back_to_sequence_flow(self):
        """Unknown flow type defaults to sequence flow style."""
        style = get_edge_style("unknownFlowType")
        assert style == EDGE_STYLES["sequenceFlow"]

    def test_default_flow_adds_slash_marker(self):
        """Default sequence flow adds startArrow=dash marker."""
        style = get_edge_style("sequenceFlow", is_default=True)
        assert "startArrow=dash" in style
        assert "startFill=0" in style
        assert "endArrow=block" in style

    def test_conditional_flow_adds_diamond_marker(self):
        """Conditional sequence flow adds startArrow=diamond marker."""
        style = get_edge_style("sequenceFlow", has_condition=True)
        assert "startArrow=diamond" in style
        assert "startFill=0" in style
        assert "endArrow=block" in style

    def test_default_takes_precedence_over_condition(self):
        """When both is_default and has_condition are True, default marker wins."""
        style = get_edge_style("sequenceFlow", is_default=True, has_condition=True)
        assert "startArrow=dash" in style
        assert "startArrow=diamond" not in style

    def test_default_flag_only_affects_sequence_flow(self):
        """is_default flag does not modify non-sequence flow styles."""
        style = get_edge_style("messageFlow", is_default=True)
        # Should be unchanged from base messageFlow style
        assert style == EDGE_STYLES["messageFlow"]

    def test_condition_flag_only_affects_sequence_flow(self):
        """has_condition flag does not modify non-sequence flow styles."""
        style = get_edge_style("association", has_condition=True)
        assert style == EDGE_STYLES["association"]

    def test_plain_sequence_flow_has_no_start_arrow(self):
        """Basic sequence flow (not default, not conditional) has no start arrow marker."""
        style = get_edge_style("sequenceFlow")
        assert "startArrow=" not in style


class TestThemeStyleIntegration:
    """Tests for theme-based style generation."""

    def test_default_theme_style_matches_style_map(self):
        """Default theme style_for produces same values as STYLE_MAP for common types."""
        theme = BPMNTheme()
        # Both should produce the same start event style
        theme_style = theme.style_for("startEvent")
        map_style = STYLE_MAP["startEvent"]
        assert theme_style == map_style

    def test_custom_theme_modifies_fill_color(self):
        """Custom theme colors appear in generated styles."""
        theme = BPMNTheme(task_fill="#ff0000", task_stroke="#00ff00")
        style = theme.style_for("task")
        assert "#ff0000" in style
        assert "#00ff00" in style

    def test_blueprint_theme_uses_blue_palette(self):
        """Blueprint theme generates styles with blue colors."""
        theme = get_theme("blueprint")
        style = theme.style_for("task")
        assert "#1976d2" in style

    def test_monochrome_theme_uses_grayscale(self):
        """Monochrome theme generates styles with grayscale colors."""
        theme = get_theme("monochrome")
        style = theme.style_for("startEvent")
        assert "#ffffff" in style
        assert "#333333" in style

    def test_high_contrast_theme_differentiates_element_types(self):
        """High contrast theme uses distinct colors for different event types."""
        theme = get_theme("high_contrast")
        start_style = theme.style_for("startEvent")
        end_style = theme.style_for("endEvent")
        assert start_style != end_style

    def test_theme_style_for_gateway(self):
        """Theme generates gateway styles with rhombus shape."""
        theme = BPMNTheme()
        style = theme.style_for("exclusiveGateway")
        assert "rhombus" in style

    def test_theme_unknown_type_falls_back_to_task(self):
        """Theme style_for with unknown type falls back to task style."""
        theme = BPMNTheme()
        style = theme.style_for("totallyUnknown")
        task_style = theme.style_for("task")
        assert style == task_style

    def test_theme_subprocess_style_distinct_from_task(self):
        """Theme generates distinct style for subProcess including container properties."""
        theme = BPMNTheme()
        sub_style = theme.style_for("subProcess")
        task_style = theme.style_for("task")
        assert sub_style != task_style
        assert "container=1" in sub_style
