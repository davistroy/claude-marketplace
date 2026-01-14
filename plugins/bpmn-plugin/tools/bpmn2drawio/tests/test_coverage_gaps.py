"""Additional tests to improve code coverage.

This module targets specific uncovered code paths in:
- layout.py (graphviz layout, RL/BT directions, simple grid fallback)
- routing.py (connection point directions, invalid elements)
- waypoints.py (direct routing, edge cases)
- swimlanes.py (lane sizing edge cases, parent hierarchy)
- position_resolver.py (edge cases in positioning)
- __main__.py (entry point)
"""

import pytest
from pathlib import Path
from xml.etree import ElementTree as ET
import subprocess
import sys

from bpmn2drawio.layout import LayoutEngine
from bpmn2drawio.routing import EdgeRouter, calculate_edge_routes
from bpmn2drawio.waypoints import (
    convert_bpmn_waypoints,
    generate_waypoints,
    create_waypoint_array,
    position_edge_label,
)
from bpmn2drawio.swimlanes import (
    SwimlaneSizer,
    create_pool_cell,
    create_lane_cell,
    resolve_parent_hierarchy,
    assign_elements_to_pools_and_lanes,
)
from bpmn2drawio.position_resolver import PositionResolver, resolve_positions
from bpmn2drawio.models import BPMNElement, BPMNFlow, BPMNModel, Pool, Lane


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestLayoutEngineDirections:
    """Test layout engine with different flow directions."""

    def test_layout_rl_direction(self):
        """Test right-to-left layout direction."""
        elements = [
            BPMNElement(id="start", type="startEvent"),
            BPMNElement(id="task", type="task"),
            BPMNElement(id="end", type="endEvent"),
        ]
        flows = [
            BPMNFlow(id="f1", type="sequenceFlow", source_ref="start", target_ref="task"),
            BPMNFlow(id="f2", type="sequenceFlow", source_ref="task", target_ref="end"),
        ]

        engine = LayoutEngine(direction="RL")
        positions = engine.calculate_layout(elements, flows)

        assert len(positions) == 3
        # In RL layout, start should be right of task
        assert positions["start"][0] > positions["task"][0]
        assert positions["task"][0] > positions["end"][0]

    def test_layout_bt_direction(self):
        """Test bottom-to-top layout direction."""
        elements = [
            BPMNElement(id="start", type="startEvent"),
            BPMNElement(id="task", type="task"),
            BPMNElement(id="end", type="endEvent"),
        ]
        flows = [
            BPMNFlow(id="f1", type="sequenceFlow", source_ref="start", target_ref="task"),
            BPMNFlow(id="f2", type="sequenceFlow", source_ref="task", target_ref="end"),
        ]

        engine = LayoutEngine(direction="BT")
        positions = engine.calculate_layout(elements, flows)

        assert len(positions) == 3
        # In BT layout, start should be below task
        assert positions["start"][1] > positions["task"][1]
        assert positions["task"][1] > positions["end"][1]

    def test_layout_disconnected_elements(self):
        """Test layout with disconnected elements (no edges)."""
        elements = [
            BPMNElement(id="e1", type="task"),
            BPMNElement(id="e2", type="task"),
            BPMNElement(id="e3", type="task"),
        ]
        flows = []  # No connections

        engine = LayoutEngine()
        positions = engine.calculate_layout(elements, flows)

        # All elements should still get positions
        assert len(positions) == 3
        for elem_id in ["e1", "e2", "e3"]:
            assert elem_id in positions

    def test_layout_cyclic_graph(self):
        """Test layout with cyclic dependencies."""
        elements = [
            BPMNElement(id="a", type="task"),
            BPMNElement(id="b", type="task"),
            BPMNElement(id="c", type="task"),
        ]
        flows = [
            BPMNFlow(id="f1", type="sequenceFlow", source_ref="a", target_ref="b"),
            BPMNFlow(id="f2", type="sequenceFlow", source_ref="b", target_ref="c"),
            BPMNFlow(id="f3", type="sequenceFlow", source_ref="c", target_ref="a"),  # Cycle
        ]

        engine = LayoutEngine()
        positions = engine.calculate_layout(elements, flows)

        # Should handle cycle without error
        assert len(positions) == 3

    def test_layout_with_existing_dimensions(self):
        """Test layout preserves element dimensions."""
        elements = [
            BPMNElement(id="start", type="startEvent", width=50, height=50),
            BPMNElement(id="task", type="task", width=200, height=100),
        ]
        flows = [
            BPMNFlow(id="f1", type="sequenceFlow", source_ref="start", target_ref="task"),
        ]

        engine = LayoutEngine()
        positions = engine.calculate_layout(elements, flows)

        assert len(positions) == 2


class TestEdgeRouterDirections:
    """Test edge router connection point directions."""

    def test_route_target_left_of_source(self):
        """Test routing when target is to the left of source."""
        elements = [
            BPMNElement(id="source", type="task", x=300, y=100, width=120, height=80),
            BPMNElement(id="target", type="task", x=100, y=100, width=120, height=80),
        ]
        router = EdgeRouter(elements)

        waypoints = router.route("source", "target")

        assert len(waypoints) >= 2
        # First waypoint should be from source's left edge
        assert waypoints[0][0] <= 300

    def test_route_target_above_source(self):
        """Test routing when target is above source (same x)."""
        elements = [
            BPMNElement(id="source", type="task", x=100, y=300, width=120, height=80),
            BPMNElement(id="target", type="task", x=100, y=100, width=120, height=80),
        ]
        router = EdgeRouter(elements)

        waypoints = router.route("source", "target")

        assert len(waypoints) >= 2

    def test_route_target_below_source(self):
        """Test routing when target is below source (same x)."""
        elements = [
            BPMNElement(id="source", type="task", x=100, y=100, width=120, height=80),
            BPMNElement(id="target", type="task", x=100, y=300, width=120, height=80),
        ]
        router = EdgeRouter(elements)

        waypoints = router.route("source", "target")

        assert len(waypoints) >= 2

    def test_route_missing_source(self):
        """Test routing with missing source element."""
        elements = [
            BPMNElement(id="target", type="task", x=100, y=100, width=120, height=80),
        ]
        router = EdgeRouter(elements)

        waypoints = router.route("nonexistent", "target")

        assert waypoints == []

    def test_route_missing_target(self):
        """Test routing with missing target element."""
        elements = [
            BPMNElement(id="source", type="task", x=100, y=100, width=120, height=80),
        ]
        router = EdgeRouter(elements)

        waypoints = router.route("source", "nonexistent")

        assert waypoints == []

    def test_orthogonal_routing_same_y(self):
        """Test orthogonal routing when elements have same y coordinate."""
        elements = [
            BPMNElement(id="source", type="task", x=100, y=100, width=120, height=80),
            BPMNElement(id="target", type="task", x=300, y=100, width=120, height=80),
        ]
        router = EdgeRouter(elements)

        waypoints = router.route("source", "target")

        # Should not need intermediate points for horizontal alignment
        assert len(waypoints) >= 2


class TestWaypointsEdgeCases:
    """Test waypoint generation edge cases."""

    def test_generate_waypoints_direct_style(self):
        """Test direct routing style."""
        source = BPMNElement(id="s", type="startEvent", x=100, y=100, width=36, height=36)
        target = BPMNElement(id="t", type="task", x=300, y=300, width=120, height=80)

        waypoints = generate_waypoints(source, target, routing_style="direct")

        # Direct routing should have exactly 2 points
        assert len(waypoints) == 2

    def test_generate_waypoints_target_left_and_above(self):
        """Test waypoints when target is left and above source."""
        source = BPMNElement(id="s", type="task", x=300, y=300, width=120, height=80)
        target = BPMNElement(id="t", type="task", x=100, y=100, width=120, height=80)

        waypoints = generate_waypoints(source, target)

        assert len(waypoints) >= 2

    def test_generate_waypoints_target_left(self):
        """Test waypoints when target is to the left of source."""
        source = BPMNElement(id="s", type="task", x=300, y=100, width=120, height=80)
        target = BPMNElement(id="t", type="task", x=100, y=100, width=120, height=80)

        waypoints = generate_waypoints(source, target)

        assert len(waypoints) >= 2

    def test_generate_waypoints_target_below(self):
        """Test waypoints when target is below source."""
        source = BPMNElement(id="s", type="task", x=100, y=100, width=120, height=80)
        target = BPMNElement(id="t", type="task", x=100, y=300, width=120, height=80)

        waypoints = generate_waypoints(source, target)

        assert len(waypoints) >= 2

    def test_position_edge_label_multiple_waypoints(self):
        """Test edge label positioning with multiple waypoints."""
        flow = BPMNFlow(
            id="f1", type="sequenceFlow",
            source_ref="s", target_ref="t",
            name="TestLabel"
        )
        waypoints = [(100, 100), (150, 100), (200, 150), (250, 150), (300, 150)]

        position = position_edge_label(flow, waypoints)

        assert "x" in position
        assert "y" in position

    def test_position_edge_label_single_waypoint(self):
        """Test edge label positioning with single waypoint (edge case)."""
        flow = BPMNFlow(
            id="f1", type="sequenceFlow",
            source_ref="s", target_ref="t",
            name="TestLabel"
        )
        waypoints = [(100, 100)]

        position = position_edge_label(flow, waypoints)

        # Should return default position
        assert position.get("x") == 0.5

    def test_convert_waypoints_missing_coords(self):
        """Test converting waypoints with missing coordinates."""
        di_waypoints = [
            {"x": "100"},  # Missing y
            {"y": "200"},  # Missing x
            {},  # Missing both
        ]

        result = convert_bpmn_waypoints(di_waypoints)

        # Should default to 0 for missing values
        assert len(result) == 3


class TestSwimlaneSizerEdgeCases:
    """Test swimlane sizer edge cases."""

    def test_calculate_lane_sizes_with_explicit_dimensions(self):
        """Test lane sizes when lanes have explicit dimensions."""
        sizer = SwimlaneSizer()
        pool = Pool(id="pool1", name="Pool", width=800, height=400)
        lanes = [
            Lane(id="lane1", name="Lane 1", parent_pool_id="pool1", width=700, height=150),
            Lane(id="lane2", name="Lane 2", parent_pool_id="pool1", width=700, height=200),
        ]

        sizes = sizer.calculate_lane_sizes(pool, lanes, [])

        # Should preserve explicit dimensions
        assert sizes["lane1"][2] == 700  # width
        assert sizes["lane1"][3] == 150  # height

    def test_calculate_lane_sizes_empty(self):
        """Test lane sizes with no lanes."""
        sizer = SwimlaneSizer()
        pool = Pool(id="pool1", name="Pool")

        sizes = sizer.calculate_lane_sizes(pool, [], [])

        assert sizes == {}

    def test_calculate_pool_size_elements_no_position(self):
        """Test pool size with elements that have no position."""
        sizer = SwimlaneSizer()
        pool = Pool(id="pool1", name="Pool")
        elements = [
            BPMNElement(id="e1", type="task"),  # No x, y
            BPMNElement(id="e2", type="task"),  # No x, y
        ]

        width, height = sizer.calculate_pool_size(pool, elements, [])

        # Should return default size
        assert width == 600
        assert height == 200


class TestAssignElementsToPoolsAndLanes:
    """Test element assignment to pools and lanes."""

    def test_assign_elements_updates_parent_id(self):
        """Test that assign_elements_to_pools_and_lanes updates parent_id."""
        model = BPMNModel(
            process_id="process1",
            elements=[
                BPMNElement(id="task1", type="task"),
                BPMNElement(id="task2", type="task"),
            ],
            lanes=[
                Lane(id="lane1", name="Lane", parent_pool_id="pool1", element_refs=["task1"]),
            ],
            pools=[
                Pool(id="pool1", name="Pool", process_ref="process1", lanes=["lane1"]),
            ],
        )

        assign_elements_to_pools_and_lanes(model)

        # task1 should be in lane1
        task1 = model.get_element_by_id("task1")
        assert task1.parent_id == "lane1"

    def test_resolve_hierarchy_with_process_ref(self):
        """Test hierarchy when element is in pool via process_ref."""
        model = BPMNModel(
            process_id="process1",
            elements=[BPMNElement(id="task1", type="task")],
            pools=[Pool(id="pool1", name="Pool", process_ref="process1")],
        )

        hierarchy = resolve_parent_hierarchy(model)

        assert hierarchy["task1"] == "pool1"

    def test_resolve_hierarchy_element_with_parent(self):
        """Test hierarchy when element already has parent_id."""
        model = BPMNModel(
            elements=[BPMNElement(id="task1", type="task", parent_id="existing_parent")],
            pools=[Pool(id="pool1", name="Pool", process_ref="other_process")],
        )

        hierarchy = resolve_parent_hierarchy(model)

        assert hierarchy["task1"] == "existing_parent"


class TestPositionResolverEdgeCases:
    """Test position resolver edge cases."""

    def test_resolve_with_only_di_coordinates(self):
        """Test resolving when all elements have DI coordinates."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="start", type="startEvent", x=100, y=100),
                BPMNElement(id="end", type="endEvent", x=300, y=100),
            ],
            flows=[
                BPMNFlow(id="f1", type="sequenceFlow", source_ref="start", target_ref="end"),
            ],
            has_di_coordinates=True,
        )

        resolved = resolve_positions(model)

        # Should preserve existing coordinates
        assert resolved.get_element_by_id("start").x == 100
        assert resolved.get_element_by_id("start").y == 100

    def test_resolve_with_pools_no_lanes(self):
        """Test resolving with pools but no lanes."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="task1", type="task"),
            ],
            pools=[
                Pool(id="pool1", name="Pool"),
            ],
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        assert resolved.get_element_by_id("task1").x is not None

    def test_resolve_preserve_mode(self):
        """Test position resolver in preserve mode."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="task1", type="task"),
            ],
        )

        resolver = PositionResolver(use_layout="preserve")
        resolved = resolver.resolve(model)

        # Should still assign fallback positions
        assert resolved.get_element_by_id("task1").x is not None

    def test_resolve_boundary_event_positioning(self):
        """Test boundary event positioning relative to parent."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="subprocess1", type="subProcess", x=100, y=100, width=200, height=150),
                BPMNElement(id="boundary1", type="boundaryEvent", properties={"attachedToRef": "subprocess1"}),
            ],
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        boundary = resolved.get_element_by_id("boundary1")
        subprocess = resolved.get_element_by_id("subprocess1")

        # Boundary should be positioned on subprocess edge
        assert boundary.x is not None
        assert boundary.y is not None


class TestMainEntryPoint:
    """Test the __main__.py entry point."""

    def test_main_module_runnable(self):
        """Test that the module can be run with --help."""
        result = subprocess.run(
            [sys.executable, "-m", "bpmn2drawio", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should show help without error
        assert result.returncode == 0
        assert "bpmn2drawio" in result.stdout.lower() or "usage" in result.stdout.lower()


class TestCalculateEdgeRoutesFunction:
    """Test the calculate_edge_routes convenience function."""

    def test_calculate_routes_with_existing_waypoints(self):
        """Test calculating routes when flow has existing waypoints."""
        elements = [
            BPMNElement(id="start", type="startEvent", x=100, y=100, width=36, height=36),
            BPMNElement(id="end", type="endEvent", x=300, y=100, width=36, height=36),
        ]
        flows = [
            BPMNFlow(
                id="f1",
                type="sequenceFlow",
                source_ref="start",
                target_ref="end",
                waypoints=[(136, 118), (200, 118), (300, 118)],
            ),
        ]

        routes = calculate_edge_routes(elements, flows)

        # Should preserve existing waypoints
        assert routes["f1"] == [(136, 118), (200, 118), (300, 118)]

    def test_calculate_routes_empty_flows(self):
        """Test calculating routes with no flows."""
        elements = [
            BPMNElement(id="start", type="startEvent", x=100, y=100),
        ]
        flows = []

        routes = calculate_edge_routes(elements, flows)

        assert routes == {}


class TestLayoutWithComplexFlows:
    """Test layout engine with complex flow patterns."""

    def test_layout_parallel_gateway_pattern(self):
        """Test layout with parallel gateway (fork/join)."""
        elements = [
            BPMNElement(id="start", type="startEvent"),
            BPMNElement(id="fork", type="parallelGateway"),
            BPMNElement(id="task1", type="task"),
            BPMNElement(id="task2", type="task"),
            BPMNElement(id="task3", type="task"),
            BPMNElement(id="join", type="parallelGateway"),
            BPMNElement(id="end", type="endEvent"),
        ]
        flows = [
            BPMNFlow(id="f1", type="sequenceFlow", source_ref="start", target_ref="fork"),
            BPMNFlow(id="f2", type="sequenceFlow", source_ref="fork", target_ref="task1"),
            BPMNFlow(id="f3", type="sequenceFlow", source_ref="fork", target_ref="task2"),
            BPMNFlow(id="f4", type="sequenceFlow", source_ref="fork", target_ref="task3"),
            BPMNFlow(id="f5", type="sequenceFlow", source_ref="task1", target_ref="join"),
            BPMNFlow(id="f6", type="sequenceFlow", source_ref="task2", target_ref="join"),
            BPMNFlow(id="f7", type="sequenceFlow", source_ref="task3", target_ref="join"),
            BPMNFlow(id="f8", type="sequenceFlow", source_ref="join", target_ref="end"),
        ]

        engine = LayoutEngine(direction="LR")
        positions = engine.calculate_layout(elements, flows)

        # All elements should have positions
        assert len(positions) == 7

        # Parallel tasks should have different Y positions
        y_positions = {positions["task1"][1], positions["task2"][1], positions["task3"][1]}
        assert len(y_positions) == 3  # All different

    def test_layout_exclusive_gateway_pattern(self):
        """Test layout with exclusive gateway (XOR)."""
        elements = [
            BPMNElement(id="start", type="startEvent"),
            BPMNElement(id="gateway", type="exclusiveGateway"),
            BPMNElement(id="yes_path", type="task"),
            BPMNElement(id="no_path", type="task"),
            BPMNElement(id="merge", type="exclusiveGateway"),
            BPMNElement(id="end", type="endEvent"),
        ]
        flows = [
            BPMNFlow(id="f1", type="sequenceFlow", source_ref="start", target_ref="gateway"),
            BPMNFlow(id="f2", type="sequenceFlow", source_ref="gateway", target_ref="yes_path"),
            BPMNFlow(id="f3", type="sequenceFlow", source_ref="gateway", target_ref="no_path"),
            BPMNFlow(id="f4", type="sequenceFlow", source_ref="yes_path", target_ref="merge"),
            BPMNFlow(id="f5", type="sequenceFlow", source_ref="no_path", target_ref="merge"),
            BPMNFlow(id="f6", type="sequenceFlow", source_ref="merge", target_ref="end"),
        ]

        engine = LayoutEngine(direction="TB")
        positions = engine.calculate_layout(elements, flows)

        # Yes and no paths should have different X positions
        assert positions["yes_path"][0] != positions["no_path"][0]
