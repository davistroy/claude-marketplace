"""Tests for BPMN data models."""

import pytest
from bpmn2drawio.models import (
    BPMNElement,
    BPMNFlow,
    Pool,
    Lane,
    BPMNModel,
)


class TestBPMNElement:
    """Tests for BPMNElement dataclass."""

    def test_element_creation(self):
        """Test basic element creation."""
        element = BPMNElement(
            id="task1",
            type="userTask",
            name="Review Document",
        )
        assert element.id == "task1"
        assert element.type == "userTask"
        assert element.name == "Review Document"
        assert element.x is None
        assert element.y is None

    def test_element_with_coordinates(self):
        """Test element with DI coordinates."""
        element = BPMNElement(
            id="task1",
            type="userTask",
            x=100.0,
            y=200.0,
            width=120.0,
            height=80.0,
        )
        assert element.has_coordinates()
        assert element.has_dimensions()
        assert element.center() == (160.0, 240.0)

    def test_element_without_coordinates(self):
        """Test element without coordinates."""
        element = BPMNElement(id="task1", type="task")
        assert not element.has_coordinates()
        assert element.center() is None

    def test_element_properties(self):
        """Test element properties dict."""
        element = BPMNElement(
            id="gateway1",
            type="exclusiveGateway",
            properties={"defaultFlow": "flow1"},
        )
        assert element.properties["defaultFlow"] == "flow1"


class TestBPMNFlow:
    """Tests for BPMNFlow dataclass."""

    def test_flow_creation(self):
        """Test basic flow creation."""
        flow = BPMNFlow(
            id="flow1",
            type="sequenceFlow",
            source_ref="task1",
            target_ref="task2",
        )
        assert flow.id == "flow1"
        assert flow.type == "sequenceFlow"
        assert flow.source_ref == "task1"
        assert flow.target_ref == "task2"
        assert not flow.is_default
        assert not flow.has_waypoints()

    def test_flow_with_waypoints(self):
        """Test flow with waypoints."""
        flow = BPMNFlow(
            id="flow1",
            type="sequenceFlow",
            source_ref="task1",
            target_ref="task2",
            waypoints=[(100, 100), (150, 100), (200, 100)],
        )
        assert flow.has_waypoints()
        assert len(flow.waypoints) == 3

    def test_conditional_flow(self):
        """Test conditional flow."""
        flow = BPMNFlow(
            id="flow1",
            type="sequenceFlow",
            source_ref="gateway1",
            target_ref="task1",
            name="Yes",
            condition="approved == true",
        )
        assert flow.condition == "approved == true"
        assert flow.name == "Yes"

    def test_default_flow(self):
        """Test default flow."""
        flow = BPMNFlow(
            id="flow1",
            type="sequenceFlow",
            source_ref="gateway1",
            target_ref="task1",
            is_default=True,
        )
        assert flow.is_default


class TestPool:
    """Tests for Pool dataclass."""

    def test_pool_creation(self):
        """Test basic pool creation."""
        pool = Pool(
            id="pool1",
            name="Customer",
            process_ref="process1",
        )
        assert pool.id == "pool1"
        assert pool.name == "Customer"
        assert pool.process_ref == "process1"
        assert pool.is_horizontal

    def test_pool_with_coordinates(self):
        """Test pool with coordinates."""
        pool = Pool(
            id="pool1",
            name="Customer",
            x=50.0,
            y=100.0,
            width=800.0,
            height=300.0,
        )
        assert pool.has_coordinates()


class TestLane:
    """Tests for Lane dataclass."""

    def test_lane_creation(self):
        """Test basic lane creation."""
        lane = Lane(
            id="lane1",
            name="Manager",
            parent_pool_id="pool1",
            element_refs=["task1", "task2"],
        )
        assert lane.id == "lane1"
        assert lane.name == "Manager"
        assert lane.parent_pool_id == "pool1"
        assert "task1" in lane.element_refs


class TestBPMNModel:
    """Tests for BPMNModel dataclass."""

    def test_empty_model(self):
        """Test empty model creation."""
        model = BPMNModel()
        assert len(model.elements) == 0
        assert len(model.flows) == 0
        assert len(model.pools) == 0
        assert len(model.lanes) == 0
        assert not model.has_di_coordinates

    def test_model_with_elements(self):
        """Test model with elements."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="start1", type="startEvent"),
                BPMNElement(id="task1", type="task"),
                BPMNElement(id="end1", type="endEvent"),
            ],
            flows=[
                BPMNFlow(id="flow1", type="sequenceFlow", source_ref="start1", target_ref="task1"),
                BPMNFlow(id="flow2", type="sequenceFlow", source_ref="task1", target_ref="end1"),
            ],
            process_id="process1",
            process_name="Test Process",
        )
        assert len(model.elements) == 3
        assert len(model.flows) == 2
        assert model.process_id == "process1"

    def test_get_element_by_id(self):
        """Test getting element by ID."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="task1", type="task", name="First Task"),
                BPMNElement(id="task2", type="task", name="Second Task"),
            ]
        )
        element = model.get_element_by_id("task1")
        assert element is not None
        assert element.name == "First Task"

        missing = model.get_element_by_id("nonexistent")
        assert missing is None

    def test_get_start_end_events(self):
        """Test getting start and end events."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="start1", type="startEvent"),
                BPMNElement(id="task1", type="task"),
                BPMNElement(id="end1", type="endEvent"),
            ]
        )
        starts = model.get_start_events()
        ends = model.get_end_events()
        assert len(starts) == 1
        assert starts[0].id == "start1"
        assert len(ends) == 1
        assert ends[0].id == "end1"

    def test_get_flows(self):
        """Test getting incoming/outgoing flows."""
        model = BPMNModel(
            flows=[
                BPMNFlow(id="flow1", type="sequenceFlow", source_ref="start1", target_ref="task1"),
                BPMNFlow(id="flow2", type="sequenceFlow", source_ref="task1", target_ref="end1"),
            ]
        )
        outgoing = model.get_outgoing_flows("task1")
        incoming = model.get_incoming_flows("task1")
        assert len(outgoing) == 1
        assert outgoing[0].target_ref == "end1"
        assert len(incoming) == 1
        assert incoming[0].source_ref == "start1"
