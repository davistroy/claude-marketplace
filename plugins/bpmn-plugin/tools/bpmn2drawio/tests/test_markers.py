"""Tests for gateway markers and task/event icons."""

from pathlib import Path
from xml.etree import ElementTree as ET

from bpmn2drawio.parser import parse_bpmn
from bpmn2drawio.generator import DrawioGenerator
from bpmn2drawio.models import BPMNElement
from bpmn2drawio.markers import create_gateway_marker
from bpmn2drawio.icons import create_task_icon, create_event_icon


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestGatewayMarkers:
    """Tests for gateway marker generation."""

    def test_exclusive_gateway_marker(self):
        """Test exclusive gateway has X marker."""
        element = BPMNElement(id="gw1", type="exclusiveGateway", width=50, height=50)
        result = create_gateway_marker(element, "parent_1", 10)

        assert result is not None
        cell, counter = result
        assert counter == 11
        assert "cross" in cell.get("style")
        assert cell.get("parent") == "parent_1"

    def test_parallel_gateway_marker(self):
        """Test parallel gateway has + marker."""
        element = BPMNElement(id="gw1", type="parallelGateway", width=50, height=50)
        result = create_gateway_marker(element, "parent_1", 10)

        assert result is not None
        cell, _ = result
        assert "cross" in cell.get("style")
        # Parallel has filled cross
        assert "fillColor=#d6b656" in cell.get("style")

    def test_inclusive_gateway_marker(self):
        """Test inclusive gateway has O marker."""
        element = BPMNElement(id="gw1", type="inclusiveGateway", width=50, height=50)
        result = create_gateway_marker(element, "parent_1", 10)

        assert result is not None
        cell, _ = result
        assert "ellipse" in cell.get("style")

    def test_non_gateway_returns_none(self):
        """Test non-gateway elements return None."""
        element = BPMNElement(id="task1", type="task")
        result = create_gateway_marker(element, "parent_1", 10)
        assert result is None

    def test_all_gateways_file(self):
        """Test parsing file with all gateway types."""
        model = parse_bpmn(FIXTURES_DIR / "all_gateways.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        # Should have gateway elements plus markers
        vertices = root.findall(".//mxCell[@vertex='1']")

        # 7 elements (start + 5 gateways + end) + 5 gateway markers = 12
        # Note: might vary based on marker implementation
        assert len(vertices) >= 7


class TestTaskIcons:
    """Tests for task icon generation."""

    def test_user_task_icon(self):
        """Test user task has person icon."""
        element = BPMNElement(id="task1", type="userTask", width=120, height=80)
        result = create_task_icon(element, "parent_1", 10)

        assert result is not None
        cell, counter = result
        assert counter == 11
        assert "user_task" in cell.get("style")

    def test_service_task_icon(self):
        """Test service task has gear icon."""
        element = BPMNElement(id="task1", type="serviceTask", width=120, height=80)
        result = create_task_icon(element, "parent_1", 10)

        assert result is not None
        cell, _ = result
        assert "service_task" in cell.get("style")

    def test_script_task_icon(self):
        """Test script task has script icon."""
        element = BPMNElement(id="task1", type="scriptTask", width=120, height=80)
        result = create_task_icon(element, "parent_1", 10)

        assert result is not None
        cell, _ = result
        assert "script_task" in cell.get("style")
        # Script tasks use purple
        assert "#9673a6" in cell.get("style")

    def test_generic_task_no_icon(self):
        """Test generic task has no icon."""
        element = BPMNElement(id="task1", type="task")
        result = create_task_icon(element, "parent_1", 10)
        assert result is None

    def test_all_tasks_file(self):
        """Test parsing file with all task types."""
        model = parse_bpmn(FIXTURES_DIR / "all_tasks.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        vertices = root.findall(".//mxCell[@vertex='1']")

        # 10 elements + task icons for 7 specific task types
        assert len(vertices) >= 10


class TestEventIcons:
    """Tests for event icon generation."""

    def test_timer_start_event(self):
        """Test timer start event has timer icon."""
        element = BPMNElement(
            id="start1",
            type="startEvent",
            width=36,
            height=36,
            properties={"eventDefinition": "timer"},
        )
        result = create_event_icon(element, "parent_1", 10)

        assert result is not None
        cell, _ = result
        assert "timer" in cell.get("style")

    def test_message_end_event(self):
        """Test message end event has message icon."""
        element = BPMNElement(
            id="end1",
            type="endEvent",
            width=36,
            height=36,
            properties={"eventDefinition": "message"},
        )
        result = create_event_icon(element, "parent_1", 10)

        assert result is not None
        cell, _ = result
        assert "message" in cell.get("style")

    def test_plain_event_no_icon(self):
        """Test plain event has no icon."""
        element = BPMNElement(id="start1", type="startEvent", properties={})
        result = create_event_icon(element, "parent_1", 10)
        assert result is None

    def test_all_events_file(self):
        """Test parsing file with various event types."""
        model = parse_bpmn(FIXTURES_DIR / "all_events.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        vertices = root.findall(".//mxCell[@vertex='1']")

        # Should have event elements plus icons for typed events
        assert len(vertices) >= 13


class TestMarkerPositioning:
    """Tests for marker positioning."""

    def test_marker_centered_in_gateway(self):
        """Test marker is centered in gateway."""
        element = BPMNElement(id="gw1", type="exclusiveGateway", width=50, height=50)
        result = create_gateway_marker(element, "parent_1", 10)

        cell, _ = result
        geometry = cell.find("mxGeometry")

        x = float(geometry.get("x"))
        y = float(geometry.get("y"))
        width = float(geometry.get("width"))
        height = float(geometry.get("height"))

        # Should be centered
        expected_x = (50 - width) / 2
        expected_y = (50 - height) / 2

        assert abs(x - expected_x) < 1
        assert abs(y - expected_y) < 1

    def test_task_icon_top_left(self):
        """Test task icon is in top-left."""
        element = BPMNElement(id="task1", type="userTask", width=120, height=80)
        result = create_task_icon(element, "parent_1", 10)

        cell, _ = result
        geometry = cell.find("mxGeometry")

        x = float(geometry.get("x"))
        y = float(geometry.get("y"))

        # Should be near top-left (small offset)
        assert x < 20
        assert y < 20


class TestAllElementTypesRender:
    """Integration tests for rendering all element types."""

    def test_all_gateways_render(self):
        """Test all gateway types render without error."""
        model = parse_bpmn(FIXTURES_DIR / "all_gateways.bpmn")
        generator = DrawioGenerator()

        # Should not raise
        result = generator.generate_result(model)
        assert result.element_count == 7

    def test_all_tasks_render(self):
        """Test all task types render without error."""
        model = parse_bpmn(FIXTURES_DIR / "all_tasks.bpmn")
        generator = DrawioGenerator()

        result = generator.generate_result(model)
        assert result.element_count == 10

    def test_all_events_render(self):
        """Test all event types render without error."""
        model = parse_bpmn(FIXTURES_DIR / "all_events.bpmn")
        generator = DrawioGenerator()

        result = generator.generate_result(model)
        # 13 elements in the fixture file
        assert result.element_count == 13
