"""Tests for recovery strategies."""

import pytest
from pathlib import Path

from bpmn2drawio.recovery import RecoveryStrategy, recover_model
from bpmn2drawio.models import BPMNModel, BPMNElement, BPMNFlow
from bpmn2drawio.parser import parse_bpmn


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestRecoverMissingCoordinates:
    """Tests for coordinate recovery."""

    def test_recover_missing_x_y(self):
        """Test recovering missing x/y coordinates."""
        strategy = RecoveryStrategy()
        element = BPMNElement(id="Task_1", type="task")

        strategy.recover_missing_coordinates(element, index=0)

        assert element.x is not None
        assert element.y is not None

    def test_recover_preserves_existing(self):
        """Test existing coordinates are preserved."""
        strategy = RecoveryStrategy()
        element = BPMNElement(id="Task_1", type="task", x=500, y=300)

        strategy.recover_missing_coordinates(element, index=0)

        # Should keep original values
        assert element.x == 500
        assert element.y == 300

    def test_recover_assigns_dimensions(self):
        """Test missing dimensions are assigned."""
        strategy = RecoveryStrategy()
        element = BPMNElement(id="Task_1", type="task")

        strategy.recover_missing_coordinates(element, index=0)

        assert element.width == 120
        assert element.height == 80

    def test_recover_event_dimensions(self):
        """Test event gets correct dimensions."""
        strategy = RecoveryStrategy()
        element = BPMNElement(id="Start_1", type="startEvent")

        strategy.recover_missing_coordinates(element, index=0)

        assert element.width == 36
        assert element.height == 36


class TestRecoverInvalidParent:
    """Tests for parent recovery."""

    def test_valid_parent_unchanged(self):
        """Test valid parent is not changed."""
        strategy = RecoveryStrategy()
        element = BPMNElement(id="Task_1", type="task", parent_id="Lane_1")
        valid_parents = {"Lane_1", "Pool_1"}

        strategy.recover_invalid_parent(element, valid_parents)

        assert element.parent_id == "Lane_1"

    def test_invalid_parent_cleared(self):
        """Test invalid parent is cleared."""
        strategy = RecoveryStrategy()
        element = BPMNElement(id="Task_1", type="task", parent_id="Invalid_Parent")
        valid_parents = {"Lane_1", "Pool_1"}

        strategy.recover_invalid_parent(element, valid_parents)

        assert element.parent_id is None


class TestRecoverUnknownElementType:
    """Tests for element type recovery."""

    def test_known_type_returns_style(self):
        """Test known type returns correct style."""
        strategy = RecoveryStrategy()
        element = BPMNElement(id="Task_1", type="task")

        style = strategy.recover_unknown_element_type(element)

        assert "rounded=1" in style

    def test_unknown_type_returns_task_style(self):
        """Test unknown type returns task style."""
        strategy = RecoveryStrategy()
        element = BPMNElement(id="Unknown_1", type="unknownElementType")

        style = strategy.recover_unknown_element_type(element)

        assert "rounded=1" in style  # Task style
        assert strategy.get_recovery_count() == 1


class TestRecoverInvalidFlow:
    """Tests for flow recovery."""

    def test_valid_flow_returns_true(self):
        """Test valid flow returns True."""
        strategy = RecoveryStrategy()
        flow = BPMNFlow(id="Flow_1", type="sequenceFlow",
                        source_ref="Start_1", target_ref="Task_1")
        element_ids = {"Start_1", "Task_1", "End_1"}

        result = strategy.recover_invalid_flow(flow, element_ids)

        assert result is True

    def test_invalid_source_returns_false(self):
        """Test flow with invalid source returns False."""
        strategy = RecoveryStrategy()
        flow = BPMNFlow(id="Flow_1", type="sequenceFlow",
                        source_ref="Invalid", target_ref="Task_1")
        element_ids = {"Start_1", "Task_1", "End_1"}

        result = strategy.recover_invalid_flow(flow, element_ids)

        assert result is False
        assert strategy.get_recovery_count() == 1

    def test_invalid_target_returns_false(self):
        """Test flow with invalid target returns False."""
        strategy = RecoveryStrategy()
        flow = BPMNFlow(id="Flow_1", type="sequenceFlow",
                        source_ref="Start_1", target_ref="Invalid")
        element_ids = {"Start_1", "Task_1", "End_1"}

        result = strategy.recover_invalid_flow(flow, element_ids)

        assert result is False


class TestRecoverGraphvizFailure:
    """Tests for Graphviz failure recovery."""

    def test_grid_layout_generated(self):
        """Test grid layout is generated on failure."""
        strategy = RecoveryStrategy()
        model = BPMNModel(
            elements=[
                BPMNElement(id="Start_1", type="startEvent"),
                BPMNElement(id="Task_1", type="task"),
                BPMNElement(id="End_1", type="endEvent"),
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        positions = strategy.recover_graphviz_failure(model)

        assert len(positions) == 3
        assert "Start_1" in positions
        assert "Task_1" in positions
        assert "End_1" in positions

    def test_grid_positions_are_distinct(self):
        """Test grid positions don't overlap."""
        strategy = RecoveryStrategy()
        model = BPMNModel(
            elements=[
                BPMNElement(id=f"E_{i}", type="task")
                for i in range(10)
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        positions = strategy.recover_graphviz_failure(model)

        # All positions should be unique
        pos_set = set(positions.values())
        assert len(pos_set) == 10


class TestRecoverModelFunction:
    """Tests for recover_model convenience function."""

    def test_recover_minimal_model(self):
        """Test recovering minimal model."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Start_1", type="startEvent"),
                BPMNElement(id="Task_1", type="task"),
                BPMNElement(id="End_1", type="endEvent"),
            ],
            flows=[
                BPMNFlow(id="Flow_1", type="sequenceFlow",
                         source_ref="Start_1", target_ref="Task_1"),
                BPMNFlow(id="Flow_2", type="sequenceFlow",
                         source_ref="Task_1", target_ref="End_1"),
            ],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        recovered, count = recover_model(model)

        # All elements should have coordinates
        for elem in recovered.elements:
            assert elem.x is not None
            assert elem.y is not None
            assert elem.width is not None
            assert elem.height is not None

    def test_recover_filters_invalid_flows(self):
        """Test invalid flows are filtered out."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Task_1", type="task"),
            ],
            flows=[
                BPMNFlow(id="Flow_Valid", type="sequenceFlow",
                         source_ref="Task_1", target_ref="Task_1"),
                BPMNFlow(id="Flow_Invalid", type="sequenceFlow",
                         source_ref="Invalid", target_ref="Task_1"),
            ],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        recovered, count = recover_model(model)

        assert len(recovered.flows) == 1
        assert recovered.flows[0].id == "Flow_Valid"


class TestRecoveryWithRealFiles:
    """Tests using real BPMN fixtures."""

    def test_recover_invalid_refs_file(self):
        """Test recovery with invalid references file."""
        model = parse_bpmn(FIXTURES_DIR / "invalid_refs.bpmn")

        recovered, count = recover_model(model)

        # Invalid flows should be filtered
        assert len(recovered.flows) == 2  # Only valid flows remain

    def test_recover_empty_file(self):
        """Test recovery with empty process."""
        model = parse_bpmn(FIXTURES_DIR / "empty.bpmn")

        recovered, count = recover_model(model)

        assert len(recovered.elements) == 0
        assert len(recovered.flows) == 0
