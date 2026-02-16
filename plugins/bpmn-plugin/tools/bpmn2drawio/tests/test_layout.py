"""Tests for layout engine."""

from pathlib import Path

from bpmn2drawio.parser import parse_bpmn
from bpmn2drawio.layout import LayoutEngine
from bpmn2drawio.position_resolver import PositionResolver, resolve_positions
from bpmn2drawio.models import BPMNElement, BPMNFlow, BPMNModel


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestLayoutEngine:
    """Tests for LayoutEngine class."""

    def test_layout_linear_flow(self):
        """Test layout for linear flow."""
        elements = [
            BPMNElement(id="start", type="startEvent"),
            BPMNElement(id="task", type="task"),
            BPMNElement(id="end", type="endEvent"),
        ]
        flows = [
            BPMNFlow(
                id="f1", type="sequenceFlow", source_ref="start", target_ref="task"
            ),
            BPMNFlow(id="f2", type="sequenceFlow", source_ref="task", target_ref="end"),
        ]

        engine = LayoutEngine(direction="LR")
        positions = engine.calculate_layout(elements, flows)

        assert "start" in positions
        assert "task" in positions
        assert "end" in positions

        # Start should be left of task, task left of end
        assert positions["start"][0] < positions["task"][0]
        assert positions["task"][0] < positions["end"][0]

    def test_layout_empty_elements(self):
        """Test layout with no elements."""
        engine = LayoutEngine()
        positions = engine.calculate_layout([], [])
        assert positions == {}

    def test_layout_single_element(self):
        """Test layout with single element."""
        elements = [BPMNElement(id="start", type="startEvent")]
        engine = LayoutEngine()
        positions = engine.calculate_layout(elements, [])

        assert "start" in positions
        assert positions["start"][0] >= 0
        assert positions["start"][1] >= 0

    def test_layout_direction_tb(self):
        """Test top-to-bottom layout direction."""
        elements = [
            BPMNElement(id="start", type="startEvent"),
            BPMNElement(id="task", type="task"),
            BPMNElement(id="end", type="endEvent"),
        ]
        flows = [
            BPMNFlow(
                id="f1", type="sequenceFlow", source_ref="start", target_ref="task"
            ),
            BPMNFlow(id="f2", type="sequenceFlow", source_ref="task", target_ref="end"),
        ]

        engine = LayoutEngine(direction="TB")
        positions = engine.calculate_layout(elements, flows)

        # In TB layout, start should be above task, task above end
        assert positions["start"][1] < positions["task"][1]
        assert positions["task"][1] < positions["end"][1]

    def test_no_overlapping_elements(self):
        """Test that elements don't overlap."""
        elements = [
            BPMNElement(id="start", type="startEvent", width=36, height=36),
            BPMNElement(id="task1", type="task", width=120, height=80),
            BPMNElement(id="task2", type="task", width=120, height=80),
            BPMNElement(id="end", type="endEvent", width=36, height=36),
        ]
        flows = [
            BPMNFlow(
                id="f1", type="sequenceFlow", source_ref="start", target_ref="task1"
            ),
            BPMNFlow(
                id="f2", type="sequenceFlow", source_ref="task1", target_ref="task2"
            ),
            BPMNFlow(
                id="f3", type="sequenceFlow", source_ref="task2", target_ref="end"
            ),
        ]

        engine = LayoutEngine()
        positions = engine.calculate_layout(elements, flows)

        # Check no two positions are identical
        pos_list = list(positions.values())
        for i, pos1 in enumerate(pos_list):
            for pos2 in pos_list[i + 1 :]:
                # Positions should be different
                assert pos1 != pos2


class TestPositionResolver:
    """Tests for PositionResolver class."""

    def test_resolve_di_coordinates_preserved(self):
        """Test that DI coordinates are preserved."""
        model = parse_bpmn(FIXTURES_DIR / "with_di.bpmn")
        resolver = PositionResolver()

        resolved = resolver.resolve(model)

        # Original DI coordinates should be preserved
        start = resolved.get_element_by_id("Start_1")
        assert start.x == 100
        assert start.y == 100

    def test_resolve_missing_coordinates(self):
        """Test that missing coordinates are calculated."""
        model = parse_bpmn(FIXTURES_DIR / "no_di.bpmn")
        resolver = PositionResolver()

        resolved = resolver.resolve(model)

        # All elements should have coordinates
        for element in resolved.elements:
            assert element.x is not None
            assert element.y is not None

    def test_resolve_dimensions_assigned(self):
        """Test that dimensions are assigned to elements."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        resolver = PositionResolver()

        resolved = resolver.resolve(model)

        for element in resolved.elements:
            assert element.width is not None
            assert element.height is not None

    def test_resolve_preserve_mode(self):
        """Test preserve mode doesn't calculate layout."""
        model = BPMNModel(elements=[BPMNElement(id="task1", type="task")])
        resolver = PositionResolver(use_layout="preserve")

        resolved = resolver.resolve(model)

        # Should have fallback position
        task = resolved.get_element_by_id("task1")
        assert task.x is not None
        assert task.y is not None


class TestResolvePositionsFunction:
    """Tests for resolve_positions convenience function."""

    def test_resolve_positions_lr(self):
        """Test resolve_positions with LR direction."""
        model = parse_bpmn(FIXTURES_DIR / "no_di.bpmn")
        resolved = resolve_positions(model, direction="LR")

        # All elements should have positions
        for element in resolved.elements:
            assert element.has_coordinates()

    def test_resolve_positions_tb(self):
        """Test resolve_positions with TB direction."""
        model = parse_bpmn(FIXTURES_DIR / "no_di.bpmn")
        resolved = resolve_positions(model, direction="TB")

        # All elements should have positions
        for element in resolved.elements:
            assert element.has_coordinates()


class TestLayoutWithRealFiles:
    """Integration tests with real BPMN files."""

    def test_layout_no_di_file(self):
        """Test layout calculation for file without DI."""
        model = parse_bpmn(FIXTURES_DIR / "no_di.bpmn")

        assert not model.has_di_coordinates

        resolved = resolve_positions(model)

        # Check linear ordering (LR layout)
        start = resolved.get_element_by_id("Start_1")
        task1 = resolved.get_element_by_id("Task_1")
        task2 = resolved.get_element_by_id("Task_2")
        task3 = resolved.get_element_by_id("Task_3")
        end = resolved.get_element_by_id("End_1")

        # Elements should be positioned left to right
        assert start.x < task1.x
        assert task1.x < task2.x
        assert task2.x < task3.x
        assert task3.x < end.x

    def test_layout_with_gateway(self):
        """Test layout with gateway branching."""
        model = parse_bpmn(FIXTURES_DIR / "with_gateway.bpmn")
        resolved = resolve_positions(model)

        # All elements should have positions
        for element in resolved.elements:
            assert element.has_coordinates()

        # Gateway branches should be separated
        gateway = resolved.get_element_by_id("Gateway_1")
        task_yes = resolved.get_element_by_id("Task_Yes")
        task_no = resolved.get_element_by_id("Task_No")

        assert gateway is not None
        assert task_yes is not None
        assert task_no is not None

        # Branch tasks should have different Y coordinates
        assert task_yes.y != task_no.y

    def test_layout_complex_multi_pool(self):
        """Test layout with complex multi-pool, multi-lane, multiple gateway types."""
        model = parse_bpmn(FIXTURES_DIR / "complex_layout.bpmn")
        resolved = resolve_positions(model)

        # All elements should have positions
        for element in resolved.elements:
            assert element.has_coordinates(), f"Element {element.id} has no coordinates"

        # Coordinates should be in reasonable range (not scaled to huge values)
        for element in resolved.elements:
            assert element.x < 10000, f"Element {element.id} x={element.x} is too large"
            assert element.y < 10000, f"Element {element.id} y={element.y} is too large"
            assert element.x >= 0, f"Element {element.id} x={element.x} is negative"
            assert element.y >= 0, f"Element {element.id} y={element.y} is negative"

        # Check that parallel gateway branches are separated
        # In the Sales process, Gateway_Parallel_Split should lead to 3 tasks
        # that have different positions
        payment = resolved.get_element_by_id("Task_ProcessPayment")
        invoice = resolved.get_element_by_id("Task_GenerateInvoice")
        crm = resolved.get_element_by_id("Task_UpdateCRM")

        if payment and invoice and crm:
            # All three parallel tasks should have different positions
            positions = {(payment.x, payment.y), (invoice.x, invoice.y), (crm.x, crm.y)}
            assert len(positions) == 3, "Parallel tasks should have unique positions"

        # Check shipping method branches in Fulfillment
        standard = resolved.get_element_by_id("Task_StandardShip")
        express = resolved.get_element_by_id("Task_ExpressShip")
        freight = resolved.get_element_by_id("Task_FreightShip")

        if standard and express and freight:
            # All three shipping methods should have different Y positions
            y_positions = {standard.y, express.y, freight.y}
            assert len(y_positions) == 3, (
                "Shipping method branches should have different Y positions"
            )
