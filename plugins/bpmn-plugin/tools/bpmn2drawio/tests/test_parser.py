"""Tests for BPMN parser."""

import pytest
from pathlib import Path
from bpmn2drawio.parser import parse_bpmn, BPMNParser
from bpmn2drawio.exceptions import BPMNParseError


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestParseMinimalBPMN:
    """Tests for parsing minimal BPMN file."""

    def test_parse_minimal_bpmn_file(self):
        """Test parsing minimal.bpmn file."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")

        assert model.process_id == "Process_1"
        assert model.process_name == "Minimal Process"
        assert len(model.elements) == 3
        assert len(model.flows) == 2

    def test_parse_minimal_elements(self):
        """Test that correct elements are extracted."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")

        # Check element types
        element_types = {e.type for e in model.elements}
        assert "startEvent" in element_types
        assert "task" in element_types
        assert "endEvent" in element_types

        # Check element names
        start = model.get_element_by_id("Start_1")
        assert start is not None
        assert start.name == "Start"

        task = model.get_element_by_id("Task_1")
        assert task is not None
        assert task.name == "Do Something"

    def test_parse_minimal_flows(self):
        """Test that flows have correct references."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")

        flow1 = model.get_flow_by_id("Flow_1")
        assert flow1 is not None
        assert flow1.source_ref == "Start_1"
        assert flow1.target_ref == "Task_1"

        flow2 = model.get_flow_by_id("Flow_2")
        assert flow2 is not None
        assert flow2.source_ref == "Task_1"
        assert flow2.target_ref == "End_1"


class TestParseGatewayBPMN:
    """Tests for parsing BPMN with gateways."""

    def test_parse_gateway(self):
        """Test parsing with_gateway.bpmn file."""
        model = parse_bpmn(FIXTURES_DIR / "with_gateway.bpmn")

        # Check for exclusive gateway
        gateway = model.get_element_by_id("Gateway_1")
        assert gateway is not None
        assert gateway.type == "exclusiveGateway"
        assert gateway.name == "Decision?"

    def test_parse_conditional_flow(self):
        """Test parsing conditional flow."""
        model = parse_bpmn(FIXTURES_DIR / "with_gateway.bpmn")

        flow = model.get_flow_by_id("Flow_Yes")
        assert flow is not None
        assert flow.name == "Yes"
        assert flow.condition is not None
        assert "condition" in flow.condition

    def test_parse_default_flow(self):
        """Test parsing default flow."""
        model = parse_bpmn(FIXTURES_DIR / "with_gateway.bpmn")

        flow = model.get_flow_by_id("Flow_Default")
        assert flow is not None
        assert flow.is_default


class TestParseDICoordinates:
    """Tests for parsing BPMN DI coordinates."""

    def test_parse_with_di(self):
        """Test parsing BPMN with DI coordinates."""
        model = parse_bpmn(FIXTURES_DIR / "with_di.bpmn")

        assert model.has_di_coordinates

        # Check element coordinates
        start = model.get_element_by_id("Start_1")
        assert start is not None
        assert start.x == 100
        assert start.y == 100
        assert start.width == 36
        assert start.height == 36

        task = model.get_element_by_id("Task_1")
        assert task is not None
        assert task.x == 200
        assert task.y == 78
        assert task.width == 120
        assert task.height == 80

    def test_parse_edge_waypoints(self):
        """Test parsing edge waypoints."""
        model = parse_bpmn(FIXTURES_DIR / "with_di.bpmn")

        flow = model.get_flow_by_id("Flow_1")
        assert flow is not None
        assert flow.has_waypoints()
        assert len(flow.waypoints) == 2
        assert flow.waypoints[0] == (136, 118)
        assert flow.waypoints[1] == (200, 118)

    def test_parse_without_di(self):
        """Test parsing BPMN without DI coordinates."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")

        assert not model.has_di_coordinates

        # Elements should not have coordinates
        start = model.get_element_by_id("Start_1")
        assert start is not None
        assert not start.has_coordinates()


class TestParseSimpleProcess:
    """Tests for parsing simple process with different task types."""

    def test_parse_task_types(self):
        """Test parsing different task types."""
        model = parse_bpmn(FIXTURES_DIR / "simple_process.bpmn")

        user_task = model.get_element_by_id("Task_1")
        assert user_task is not None
        assert user_task.type == "userTask"

        service_task = model.get_element_by_id("Task_2")
        assert service_task is not None
        assert service_task.type == "serviceTask"

    def test_parse_event_definition(self):
        """Test parsing event definitions."""
        model = parse_bpmn(FIXTURES_DIR / "simple_process.bpmn")

        start = model.get_element_by_id("Start_1")
        assert start is not None
        assert start.properties.get("eventDefinition") == "timer"


class TestParseXMLString:
    """Tests for parsing BPMN XML strings."""

    def test_parse_xml_string(self):
        """Test parsing BPMN from XML string."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:process id="Process_1">
            <bpmn:startEvent id="Start_1"/>
            <bpmn:endEvent id="End_1"/>
            <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="End_1"/>
          </bpmn:process>
        </bpmn:definitions>
        """
        model = parse_bpmn(xml)
        assert len(model.elements) == 2
        assert len(model.flows) == 1


class TestParseErrors:
    """Tests for parse error handling."""

    def test_invalid_xml(self):
        """Test that invalid XML raises BPMNParseError."""
        with pytest.raises(BPMNParseError) as exc_info:
            parse_bpmn("<invalid>xml")
        assert "Invalid XML" in str(exc_info.value)

    def test_missing_file(self):
        """Test that missing file raises BPMNParseError."""
        with pytest.raises(BPMNParseError) as exc_info:
            parse_bpmn("/nonexistent/file.bpmn")
        assert "not found" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()
