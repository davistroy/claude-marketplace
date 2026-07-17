"""Tests for BPMN parser."""

from pathlib import Path

import pytest

from bpmn2drawio.exceptions import BPMNParseError
from bpmn2drawio.parser import parse_bpmn

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


class TestGeometricLaneAssignment:
    """Tests for assigning elements to lanes/pools by DI geometry.

    Covers BPMN exports (e.g. Bizagi) whose lanes carry DI bounds but do not
    declare ``flowNodeRef`` children, so lane membership must be inferred from
    the diagram geometry.
    """

    def test_lanes_have_no_flow_node_refs(self):
        """The fixture's lanes intentionally declare no flowNodeRef."""
        model = parse_bpmn(FIXTURES_DIR / "geometric_lanes.bpmn")

        for lane in model.lanes:
            assert lane.element_refs == []

    def test_elements_assigned_to_containing_lane(self):
        """Elements are assigned to the lane whose DI bounds contain them."""
        model = parse_bpmn(FIXTURES_DIR / "geometric_lanes.bpmn")

        # Start_1 (center y=208) and Task_1 (center y=220) fall in Lane_Top,
        # End_1 (center y=328) falls in Lane_Bottom.
        assert model.get_element_by_id("Start_1").parent_id == "Lane_Top"
        assert model.get_element_by_id("Task_1").parent_id == "Lane_Top"
        assert model.get_element_by_id("End_1").parent_id == "Lane_Bottom"

    def test_no_element_assigned_to_phantom_pool(self):
        """Elements are never captured by the empty overlapping phantom pool."""
        model = parse_bpmn(FIXTURES_DIR / "geometric_lanes.bpmn")

        assert all(e.parent_id != "Pool_Phantom" for e in model.elements)

    def test_assignment_respects_element_dimensions(self):
        """All work elements receive a lane parent (none left unparented)."""
        model = parse_bpmn(FIXTURES_DIR / "geometric_lanes.bpmn")

        work_ids = {"Start_1", "Task_1", "End_1"}
        for element in model.elements:
            if element.id in work_ids:
                assert element.parent_id in {"Lane_Top", "Lane_Bottom"}

    def test_flow_node_refs_take_precedence_over_geometry(self):
        """When flowNodeRef exists it is honoured (geometry does not override)."""
        # swimlanes.bpmn declares flowNodeRef membership explicitly.
        model = parse_bpmn(FIXTURES_DIR / "swimlanes.bpmn")

        assert model.get_element_by_id("Start_Customer").parent_id == "Lane_User"
        assert model.get_element_by_id("Task_Request").parent_id == "Lane_User"
        assert model.get_element_by_id("Task_Confirm").parent_id == "Lane_Manager"
        assert model.get_element_by_id("End_Customer").parent_id == "Lane_Manager"


class TestBestContainerHelper:
    """Unit tests for the BPMNParser._best_container geometric matcher."""

    @staticmethod
    def _lane(x, y, w, h, id="L"):
        from bpmn2drawio.models import Lane

        return Lane(id=id, x=x, y=y, width=w, height=h)

    def test_empty_candidates_returns_none(self):
        """No candidates -> no container."""
        from bpmn2drawio.parser import BPMNParser

        assert BPMNParser._best_container(10, 10, []) is None

    def test_containment_prefers_smallest_area(self):
        """When several containers hold the point, the smallest (most specific) wins."""
        from bpmn2drawio.parser import BPMNParser

        big = self._lane(0, 0, 200, 200, id="big")
        small = self._lane(0, 0, 100, 100, id="small")

        chosen = BPMNParser._best_container(10, 10, [big, small])
        assert chosen.id == "small"

    def test_nearest_used_when_point_not_contained(self):
        """With no containing candidate, the nearest by edge distance is chosen."""
        from bpmn2drawio.parser import BPMNParser

        near = self._lane(0, 0, 50, 50, id="near")
        far = self._lane(0, 500, 50, 50, id="far")

        # Point sits 10px below 'near' and far from 'far'.
        chosen = BPMNParser._best_container(25, 60, [near, far])
        assert chosen.id == "near"

    def test_nearest_uses_horizontal_distance(self):
        """Horizontal edge distance is considered when shapes share a row."""
        from bpmn2drawio.parser import BPMNParser

        left = self._lane(0, 0, 50, 50, id="left")
        right = self._lane(300, 0, 50, 50, id="right")

        # Point (200, 25) is 150px right of 'left' and 100px left of 'right'.
        chosen = BPMNParser._best_container(200, 25, [left, right])
        assert chosen.id == "right"


class TestGeometricParentAssignmentUnit:
    """Unit tests for BPMNParser._assign_geometric_parents edge cases."""

    def test_element_without_coordinates_is_skipped(self):
        """An element with no centre (missing coords) is left unparented."""
        from bpmn2drawio.models import BPMNElement, BPMNModel, Lane
        from bpmn2drawio.parser import BPMNParser

        model = BPMNModel()
        model.lanes.append(Lane(id="L1", process_id="P", x=0, y=0, width=100, height=100))
        element = BPMNElement(id="E", type="task", x=None, y=None, width=80, height=60)
        element.properties["_process_id"] = "P"
        model.elements.append(element)

        BPMNParser()._assign_geometric_parents(model)

        assert element.parent_id is None

    def test_falls_back_to_laneless_pool_of_same_process(self):
        """Element whose process has no lanes lands in its own laneless pool."""
        from bpmn2drawio.models import BPMNElement, BPMNModel, Lane, Pool
        from bpmn2drawio.parser import BPMNParser

        model = BPMNModel()
        # Lanes belong to a different process (PY).
        model.lanes.append(
            Lane(id="LY", process_id="PY", parent_pool_id="PoolY", x=0, y=0, width=100, height=100)
        )
        model.pools.append(Pool(id="PoolY", process_ref="PY", x=0, y=0, width=100, height=100))
        # Laneless pool for the element's own process (PX).
        model.pools.append(Pool(id="PoolX", process_ref="PX", x=0, y=200, width=300, height=120))

        element = BPMNElement(id="E", type="task", x=50, y=230, width=80, height=60)
        element.properties["_process_id"] = "PX"
        model.elements.append(element)

        BPMNParser()._assign_geometric_parents(model)

        assert element.parent_id == "PoolX"

    def test_element_not_pulled_into_other_process_lane(self):
        """With no lane and no pool for its process, the element stays unparented."""
        from bpmn2drawio.models import BPMNElement, BPMNModel, Lane, Pool
        from bpmn2drawio.parser import BPMNParser

        model = BPMNModel()
        model.lanes.append(
            Lane(id="LY", process_id="PY", parent_pool_id="PoolY", x=0, y=0, width=100, height=100)
        )
        model.pools.append(Pool(id="PoolY", process_ref="PY", x=0, y=0, width=100, height=100))

        element = BPMNElement(id="E", type="task", x=50, y=50, width=80, height=60)
        element.properties["_process_id"] = "PX"
        model.elements.append(element)

        BPMNParser()._assign_geometric_parents(model)

        # Must NOT be misassigned to PY's lane.
        assert element.parent_id != "LY"
        assert element.parent_id is None

    def test_noop_when_no_lanes_or_pools_with_di(self):
        """With no DI lanes or pools, the method returns without changes."""
        from bpmn2drawio.models import BPMNElement, BPMNModel
        from bpmn2drawio.parser import BPMNParser

        model = BPMNModel()
        element = BPMNElement(id="E", type="task", x=10, y=10, width=80, height=60)
        model.elements.append(element)

        BPMNParser()._assign_geometric_parents(model)

        assert element.parent_id is None

    def test_subprocess_children_are_skipped(self):
        """Elements owned by a subprocess are not reparented by geometry."""
        from bpmn2drawio.models import BPMNElement, BPMNModel, Lane
        from bpmn2drawio.parser import BPMNParser

        model = BPMNModel()
        model.lanes.append(Lane(id="L1", process_id="P", x=0, y=0, width=200, height=200))
        element = BPMNElement(id="E", type="task", x=50, y=50, width=80, height=60)
        element.subprocess_id = "SP"  # belongs to a subprocess container
        element.properties["_process_id"] = "P"
        model.elements.append(element)

        BPMNParser()._assign_geometric_parents(model)

        assert element.parent_id is None

    def test_widens_to_all_lanes_without_process_info(self):
        """When the element has no process id, geometry uses every lane."""
        from bpmn2drawio.models import BPMNElement, BPMNModel, Lane
        from bpmn2drawio.parser import BPMNParser

        model = BPMNModel()
        model.lanes.append(Lane(id="L1", x=0, y=0, width=200, height=200))
        element = BPMNElement(id="E", type="task", x=50, y=50, width=80, height=60)
        # No _process_id set -> elem_proc is None -> consider all lanes.
        model.elements.append(element)

        BPMNParser()._assign_geometric_parents(model)

        assert element.parent_id == "L1"


class TestDataReferenceLabels:
    """Tests for resolving labels of data store / data object references.

    A ``dataStoreReference`` or ``dataObjectReference`` usually has no name of
    its own and inherits the label from the referenced definition.
    """

    XML = """<?xml version="1.0" encoding="UTF-8"?>
    <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
      <bpmn:dataStore id="DS_1" name="Semaphore Table (ERP)"/>
      <bpmn:process id="Process_1">
        <bpmn:dataObject id="DO_1" name="Object Definition"/>
        <bpmn:dataStoreReference id="DSR_1" dataStoreRef="DS_1"/>
        <bpmn:dataObjectReference id="DOR_unnamed" dataObjectRef="DO_1"/>
        <bpmn:dataObjectReference id="DOR_named" dataObjectRef="DO_1" name="Explicit"/>
      </bpmn:process>
    </bpmn:definitions>
    """

    def test_data_store_reference_inherits_definition_name(self):
        """A nameless dataStoreReference takes the referenced dataStore's name."""
        model = parse_bpmn(self.XML)

        ref = model.get_element_by_id("DSR_1")
        assert ref is not None
        assert ref.type == "dataStoreReference"
        assert ref.name == "Semaphore Table (ERP)"

    def test_data_object_reference_inherits_definition_name(self):
        """A nameless dataObjectReference takes the referenced dataObject's name."""
        model = parse_bpmn(self.XML)

        ref = model.get_element_by_id("DOR_unnamed")
        assert ref is not None
        assert ref.name == "Object Definition"

    def test_explicit_reference_name_is_not_overridden(self):
        """A reference that has its own name keeps it."""
        model = parse_bpmn(self.XML)

        ref = model.get_element_by_id("DOR_named")
        assert ref is not None
        assert ref.name == "Explicit"
