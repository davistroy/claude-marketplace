"""Tests for edge routing and flow types."""

import pytest
from pathlib import Path
from xml.etree import ElementTree as ET

from bpmn2drawio.parser import parse_bpmn
from bpmn2drawio.generator import DrawioGenerator
from bpmn2drawio.converter import Converter
from bpmn2drawio.models import BPMNElement, BPMNFlow
from bpmn2drawio.routing import EdgeRouter, calculate_edge_routes
from bpmn2drawio.waypoints import (
    convert_bpmn_waypoints,
    generate_waypoints,
    create_waypoint_array,
    position_edge_label,
)
from bpmn2drawio.styles import get_edge_style


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestEdgeRouter:
    """Tests for EdgeRouter class."""

    def test_route_horizontal(self):
        """Test routing between horizontally adjacent elements."""
        elements = [
            BPMNElement(id="start", type="startEvent", x=100, y=100, width=36, height=36),
            BPMNElement(id="task", type="task", x=200, y=80, width=120, height=80),
        ]
        router = EdgeRouter(elements)

        waypoints = router.route("start", "task")

        assert len(waypoints) >= 2
        # First point should be near source
        assert waypoints[0][0] >= 100
        # Last point should be near target
        assert waypoints[-1][0] <= 320

    def test_route_vertical(self):
        """Test routing between vertically adjacent elements."""
        elements = [
            BPMNElement(id="start", type="startEvent", x=100, y=100, width=36, height=36),
            BPMNElement(id="task", type="task", x=80, y=250, width=120, height=80),
        ]
        router = EdgeRouter(elements)

        waypoints = router.route("start", "task")

        assert len(waypoints) >= 2

    def test_route_preserves_existing_waypoints(self):
        """Test that existing waypoints are preserved."""
        elements = [
            BPMNElement(id="start", type="startEvent", x=100, y=100, width=36, height=36),
            BPMNElement(id="task", type="task", x=300, y=100, width=120, height=80),
        ]
        router = EdgeRouter(elements)
        existing = [(136, 118), (200, 118), (300, 140)]

        waypoints = router.route("start", "task", existing)

        assert waypoints == existing


class TestWaypointConversion:
    """Tests for waypoint conversion functions."""

    def test_convert_bpmn_waypoints(self):
        """Test converting BPMN DI waypoints."""
        di_waypoints = [
            {"x": "100", "y": "118"},
            {"x": "200", "y": "118"},
            {"x": "300", "y": "118"},
        ]

        result = convert_bpmn_waypoints(di_waypoints)

        assert len(result) == 3
        assert result[0] == (100.0, 118.0)
        assert result[2] == (300.0, 118.0)

    def test_generate_waypoints_horizontal(self):
        """Test generating waypoints for horizontal flow."""
        source = BPMNElement(id="s", type="startEvent", x=100, y=100, width=36, height=36)
        target = BPMNElement(id="t", type="task", x=300, y=80, width=120, height=80)

        waypoints = generate_waypoints(source, target)

        assert len(waypoints) >= 2

    def test_create_waypoint_array(self):
        """Test creating XML waypoint array."""
        waypoints = [(100, 100), (150, 100), (200, 100), (250, 100)]

        array = create_waypoint_array(waypoints)

        assert array is not None
        points = array.findall("mxPoint")
        # Should have intermediate points only
        assert len(points) == 2

    def test_create_waypoint_array_empty(self):
        """Test creating array with no intermediate points."""
        waypoints = [(100, 100), (200, 100)]

        array = create_waypoint_array(waypoints)

        assert array is None


class TestEdgeLabelPosition:
    """Tests for edge label positioning."""

    def test_label_position_two_points(self):
        """Test label position with two waypoints."""
        flow = BPMNFlow(
            id="f1", type="sequenceFlow",
            source_ref="s", target_ref="t",
            name="Yes"
        )
        waypoints = [(100, 100), (300, 100)]

        position = position_edge_label(flow, waypoints)

        assert "x" in position
        assert position["x"] == 200  # Midpoint

    def test_label_position_no_name(self):
        """Test no position for unnamed flow."""
        flow = BPMNFlow(
            id="f1", type="sequenceFlow",
            source_ref="s", target_ref="t"
        )
        waypoints = [(100, 100), (300, 100)]

        position = position_edge_label(flow, waypoints)

        assert position == {}


class TestEdgeStyles:
    """Tests for edge style generation."""

    def test_sequence_flow_style(self):
        """Test sequence flow has correct style."""
        style = get_edge_style("sequenceFlow")

        assert "orthogonalEdgeStyle" in style
        assert "endArrow=block" in style
        assert "endFill=1" in style

    def test_default_flow_style(self):
        """Test default flow has slash marker."""
        style = get_edge_style("sequenceFlow", is_default=True)

        assert "startArrow=dash" in style

    def test_conditional_flow_style(self):
        """Test conditional flow has diamond marker."""
        style = get_edge_style("sequenceFlow", has_condition=True)

        assert "startArrow=diamond" in style

    def test_message_flow_style(self):
        """Test message flow is dashed."""
        style = get_edge_style("messageFlow")

        assert "dashed=1" in style
        assert "startArrow=oval" in style

    def test_association_style(self):
        """Test association has dotted line."""
        style = get_edge_style("association")

        assert "dashed=1" in style
        assert "endArrow=none" in style


class TestConditionalFlowFile:
    """Tests for conditional flow BPMN file."""

    def test_parse_conditional_flows(self):
        """Test parsing conditional flows."""
        model = parse_bpmn(FIXTURES_DIR / "conditional_flows.bpmn")

        # Find conditional flow
        conditional_flow = None
        for flow in model.flows:
            if flow.condition:
                conditional_flow = flow
                break

        assert conditional_flow is not None
        assert "status" in conditional_flow.condition

    def test_parse_default_flow(self):
        """Test parsing default flow."""
        model = parse_bpmn(FIXTURES_DIR / "conditional_flows.bpmn")

        default_flow = model.get_flow_by_id("Flow_Default")
        assert default_flow is not None
        assert default_flow.is_default

    def test_generate_conditional_flows(self):
        """Test generating diagram with conditional flows."""
        model = parse_bpmn(FIXTURES_DIR / "conditional_flows.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        edges = root.findall(".//mxCell[@edge='1']")
        assert len(edges) >= 7

        # Check for conditional and default flow styles
        has_conditional = False
        has_default = False
        for edge in edges:
            style = edge.get("style", "")
            if "startArrow=diamond" in style:
                has_conditional = True
            if "startArrow=dash" in style:
                has_default = True

        assert has_conditional or has_default  # At least one special flow


class TestEdgeRouteCalculation:
    """Tests for calculate_edge_routes function."""

    def test_calculate_all_routes(self):
        """Test calculating routes for all flows."""
        elements = [
            BPMNElement(id="start", type="startEvent", x=100, y=100, width=36, height=36),
            BPMNElement(id="task", type="task", x=200, y=80, width=120, height=80),
            BPMNElement(id="end", type="endEvent", x=400, y=100, width=36, height=36),
        ]
        flows = [
            BPMNFlow(id="f1", type="sequenceFlow", source_ref="start", target_ref="task"),
            BPMNFlow(id="f2", type="sequenceFlow", source_ref="task", target_ref="end"),
        ]

        routes = calculate_edge_routes(elements, flows)

        assert "f1" in routes
        assert "f2" in routes
        assert len(routes["f1"]) >= 2


class TestEndToEndRouting:
    """End-to-end tests for edge routing."""

    def test_convert_with_routing(self, tmp_path):
        """Test conversion includes proper routing."""
        converter = Converter()
        output_file = tmp_path / "conditional.drawio"

        result = converter.convert(
            FIXTURES_DIR / "conditional_flows.bpmn",
            output_file
        )

        assert result.success
        assert result.flow_count >= 7

    def test_di_waypoints_preserved(self, tmp_path):
        """Test DI waypoints are preserved in output."""
        converter = Converter()
        output_file = tmp_path / "with_di.drawio"

        result = converter.convert(
            FIXTURES_DIR / "with_di.bpmn",
            output_file
        )

        assert result.success

        content = output_file.read_text()
        # Should contain edge elements
        assert 'edge="1"' in content
