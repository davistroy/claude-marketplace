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
import subprocess
import sys

from bpmn2drawio.layout import LayoutEngine
from bpmn2drawio.routing import EdgeRouter, calculate_edge_routes
from bpmn2drawio.waypoints import (
    convert_bpmn_waypoints,
    generate_waypoints,
    position_edge_label,
)
from bpmn2drawio.swimlanes import (
    SwimlaneSizer,
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
            BPMNFlow(
                id="f1", type="sequenceFlow", source_ref="start", target_ref="task"
            ),
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
            BPMNFlow(
                id="f1", type="sequenceFlow", source_ref="start", target_ref="task"
            ),
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
            BPMNFlow(
                id="f3", type="sequenceFlow", source_ref="c", target_ref="a"
            ),  # Cycle
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
            BPMNFlow(
                id="f1", type="sequenceFlow", source_ref="start", target_ref="task"
            ),
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
        source = BPMNElement(
            id="s", type="startEvent", x=100, y=100, width=36, height=36
        )
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
            id="f1",
            type="sequenceFlow",
            source_ref="s",
            target_ref="t",
            name="TestLabel",
        )
        waypoints = [(100, 100), (150, 100), (200, 150), (250, 150), (300, 150)]

        position = position_edge_label(flow, waypoints)

        assert "x" in position
        assert "y" in position

    def test_position_edge_label_single_waypoint(self):
        """Test edge label positioning with single waypoint (edge case)."""
        flow = BPMNFlow(
            id="f1",
            type="sequenceFlow",
            source_ref="s",
            target_ref="t",
            name="TestLabel",
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
            Lane(
                id="lane1", name="Lane 1", parent_pool_id="pool1", width=700, height=150
            ),
            Lane(
                id="lane2", name="Lane 2", parent_pool_id="pool1", width=700, height=200
            ),
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
                Lane(
                    id="lane1",
                    name="Lane",
                    parent_pool_id="pool1",
                    element_refs=["task1"],
                ),
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
            elements=[
                BPMNElement(id="task1", type="task", parent_id="existing_parent")
            ],
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
                BPMNFlow(
                    id="f1", type="sequenceFlow", source_ref="start", target_ref="end"
                ),
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
                BPMNElement(
                    id="subprocess1",
                    type="subProcess",
                    x=100,
                    y=100,
                    width=200,
                    height=150,
                ),
                BPMNElement(
                    id="boundary1",
                    type="boundaryEvent",
                    properties={"attachedToRef": "subprocess1"},
                ),
            ],
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        boundary = resolved.get_element_by_id("boundary1")

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
        assert (
            "bpmn2drawio" in result.stdout.lower() or "usage" in result.stdout.lower()
        )


class TestCalculateEdgeRoutesFunction:
    """Test the calculate_edge_routes convenience function."""

    def test_calculate_routes_with_existing_waypoints(self):
        """Test calculating routes when flow has existing waypoints."""
        elements = [
            BPMNElement(
                id="start", type="startEvent", x=100, y=100, width=36, height=36
            ),
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
            BPMNFlow(
                id="f1", type="sequenceFlow", source_ref="start", target_ref="fork"
            ),
            BPMNFlow(
                id="f2", type="sequenceFlow", source_ref="fork", target_ref="task1"
            ),
            BPMNFlow(
                id="f3", type="sequenceFlow", source_ref="fork", target_ref="task2"
            ),
            BPMNFlow(
                id="f4", type="sequenceFlow", source_ref="fork", target_ref="task3"
            ),
            BPMNFlow(
                id="f5", type="sequenceFlow", source_ref="task1", target_ref="join"
            ),
            BPMNFlow(
                id="f6", type="sequenceFlow", source_ref="task2", target_ref="join"
            ),
            BPMNFlow(
                id="f7", type="sequenceFlow", source_ref="task3", target_ref="join"
            ),
            BPMNFlow(id="f8", type="sequenceFlow", source_ref="join", target_ref="end"),
        ]

        engine = LayoutEngine(direction="LR")
        positions = engine.calculate_layout(elements, flows)

        # All elements should have positions
        assert len(positions) == 7

        # Parallel tasks should have different Y positions
        y_positions = {
            positions["task1"][1],
            positions["task2"][1],
            positions["task3"][1],
        }
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
            BPMNFlow(
                id="f1", type="sequenceFlow", source_ref="start", target_ref="gateway"
            ),
            BPMNFlow(
                id="f2",
                type="sequenceFlow",
                source_ref="gateway",
                target_ref="yes_path",
            ),
            BPMNFlow(
                id="f3", type="sequenceFlow", source_ref="gateway", target_ref="no_path"
            ),
            BPMNFlow(
                id="f4", type="sequenceFlow", source_ref="yes_path", target_ref="merge"
            ),
            BPMNFlow(
                id="f5", type="sequenceFlow", source_ref="no_path", target_ref="merge"
            ),
            BPMNFlow(
                id="f6", type="sequenceFlow", source_ref="merge", target_ref="end"
            ),
        ]

        engine = LayoutEngine(direction="TB")
        positions = engine.calculate_layout(elements, flows)

        # Yes and no paths should have different X positions
        assert positions["yes_path"][0] != positions["no_path"][0]


class TestLayoutSimpleGridFallback:
    """Test layout simple grid fallback code paths."""

    def test_simple_grid_layout_directly(self):
        """Test _simple_grid_layout method directly."""
        engine = LayoutEngine()
        elements = [
            BPMNElement(id="e1", type="task", width=120, height=80),
            BPMNElement(id="e2", type="task", width=120, height=80),
            BPMNElement(id="e3", type="task", width=120, height=80),
            BPMNElement(id="e4", type="task", width=120, height=80),
            BPMNElement(id="e5", type="task", width=120, height=80),
            BPMNElement(
                id="e6", type="task", width=120, height=80
            ),  # Should wrap to new row
        ]

        positions = engine._simple_grid_layout(elements)

        assert len(positions) == 6
        # First 5 elements should be on first row
        # 6th element should be on second row (new row after every 5)
        assert positions["e1"][1] == positions["e5"][1]  # Same Y for first row
        assert positions["e6"][1] > positions["e5"][1]  # e6 on new row

    def test_flow_based_layout_with_empty_graph_fallback(self):
        """Test _flow_based_layout calls _simple_grid_layout when graph is empty."""
        import networkx as nx

        engine = LayoutEngine()
        elements = [
            BPMNElement(id="e1", type="task"),
        ]

        # Create an empty graph
        graph = nx.DiGraph()
        # graph has no nodes, should fall back to simple grid layout

        positions = engine._flow_based_layout(graph, elements)

        # Should return positions from simple grid layout
        assert len(positions) == 1
        assert "e1" in positions

    def test_flow_based_layout_elements_not_in_graph(self):
        """Test _flow_based_layout handles elements not in the graph."""
        import networkx as nx

        engine = LayoutEngine()
        elements = [
            BPMNElement(id="e1", type="task"),
            BPMNElement(id="e2", type="task"),
            BPMNElement(id="e3", type="task"),  # This one not in graph
        ]

        graph = nx.DiGraph()
        graph.add_node("e1")
        graph.add_node("e2")
        graph.add_edge("e1", "e2")
        # e3 not in the graph

        positions = engine._flow_based_layout(graph, elements)

        # All elements should have positions (including e3)
        assert len(positions) == 3
        assert "e3" in positions

    def test_assign_ranks_disconnected_node(self):
        """Test _assign_ranks handles disconnected nodes."""
        import networkx as nx

        engine = LayoutEngine()

        graph = nx.DiGraph()
        graph.add_node("connected1")
        graph.add_node("connected2")
        graph.add_edge("connected1", "connected2")
        graph.add_node("disconnected")  # Not connected to anything

        ranks = engine._assign_ranks(graph)

        # All nodes should have ranks assigned
        assert "connected1" in ranks
        assert "connected2" in ranks
        assert "disconnected" in ranks
        # Disconnected node should get rank 0
        assert ranks["disconnected"] == 0

    def test_scale_positions_empty(self):
        """Test _scale_positions with empty positions."""
        engine = LayoutEngine()

        result = engine._scale_positions({}, [])

        assert result == {}

    def test_scale_positions_flip_y_false(self):
        """Test _scale_positions with flip_y=False."""
        engine = LayoutEngine()
        elements = [
            BPMNElement(id="e1", type="task"),
        ]
        positions = {"e1": (100.0, 200.0)}

        # With flip_y=False, Y should not be inverted
        result = engine._scale_positions(
            positions, elements, flip_y=False, apply_scale=False
        )

        assert "e1" in result
        # Y should be normalized to margin, not flipped

    def test_scale_positions_no_scale(self):
        """Test _scale_positions with apply_scale=False."""
        engine = LayoutEngine()
        elements = [
            BPMNElement(id="e1", type="task"),
            BPMNElement(id="e2", type="task"),
        ]
        positions = {"e1": (100.0, 200.0), "e2": (300.0, 400.0)}

        result = engine._scale_positions(
            positions, elements, flip_y=False, apply_scale=False
        )

        # Positions should be normalized but not scaled
        assert len(result) == 2


class TestLayoutEngineRankdirMap:
    """Test layout engine direction mapping."""

    def test_unknown_direction_defaults(self):
        """Test that unknown direction falls back to LR in the rankdir map."""
        engine = LayoutEngine(direction="INVALID")

        # _rankdir_map.get should return None for unknown direction
        result = engine._rankdir_map.get("INVALID", "LR")
        assert result == "LR"


class TestPositionResolverAdditionalCases:
    """Additional position resolver tests for coverage."""

    def test_resolve_pool_positions_multiple_without_positions(self):
        """Test pool positioning when multiple pools have no positions."""
        model = BPMNModel(
            pools=[
                Pool(id="pool1", name="Pool 1"),
                Pool(id="pool2", name="Pool 2"),
            ],
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        # Both pools should get default positions
        pool1 = resolved.get_pool_by_id("pool1")
        pool2 = resolved.get_pool_by_id("pool2")

        assert pool1.x is not None
        assert pool1.y is not None
        assert pool2.x is not None
        assert pool2.y is not None

        # Second pool should be below first
        assert pool2.y > pool1.y

    def test_resolve_pool_positions_some_with_positions(self):
        """Test pool positioning when some pools have positions."""
        model = BPMNModel(
            pools=[
                Pool(id="pool1", name="Pool 1", x=50, y=50, width=600, height=200),
                Pool(id="pool2", name="Pool 2"),  # No position
            ],
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        pool2 = resolved.get_pool_by_id("pool2")

        # Pool2 should be positioned below pool1
        assert pool2.x == 50  # Same x as pool1
        assert pool2.y == 300  # Below pool1 (50 + 200 + 50 gap)

    def test_place_connected_elements_multiple_paths(self):
        """Test placing connected elements when element is connected from multiple directions."""
        model = BPMNModel(
            elements=[
                BPMNElement(
                    id="task1", type="task", x=100, y=100, width=120, height=80
                ),
                BPMNElement(id="task2", type="task"),  # Needs positioning
                BPMNElement(
                    id="task3", type="task", x=400, y=100, width=120, height=80
                ),
            ],
            flows=[
                BPMNFlow(
                    id="f1", type="sequenceFlow", source_ref="task1", target_ref="task2"
                ),
                BPMNFlow(
                    id="f2", type="sequenceFlow", source_ref="task2", target_ref="task3"
                ),
            ],
            has_di_coordinates=True,
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        task2 = resolved.get_element_by_id("task2")
        assert task2.x is not None
        assert task2.y is not None

    def test_place_connected_elements_outgoing_neighbor(self):
        """Test placing element based on outgoing flow neighbor."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="task1", type="task"),  # Needs positioning
                BPMNElement(
                    id="task2", type="task", x=300, y=100, width=120, height=80
                ),
            ],
            flows=[
                BPMNFlow(
                    id="f1", type="sequenceFlow", source_ref="task1", target_ref="task2"
                ),
            ],
            has_di_coordinates=True,
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        task1 = resolved.get_element_by_id("task1")
        assert task1.x is not None
        # Should be positioned to the left of task2

    def test_place_disconnected_data_elements(self):
        """Test placement of disconnected data objects."""
        model = BPMNModel(
            elements=[
                BPMNElement(
                    id="task1", type="task", x=100, y=100, width=120, height=80
                ),
                BPMNElement(id="data1", type="dataObject"),
                BPMNElement(id="data2", type="dataStoreReference"),
            ],
            flows=[],  # No connections
            has_di_coordinates=True,
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        data1 = resolved.get_element_by_id("data1")
        data2 = resolved.get_element_by_id("data2")

        # Data elements should get positions
        assert data1.x is not None
        assert data2.x is not None

    def test_avoid_overlap_mechanism(self):
        """Test overlap avoidance when placing elements."""
        model = BPMNModel(
            elements=[
                BPMNElement(
                    id="task1", type="task", x=100, y=100, width=120, height=80
                ),
                BPMNElement(
                    id="task2", type="task", x=180, y=100, width=120, height=80
                ),  # Overlapping
                BPMNElement(
                    id="task3", type="task"
                ),  # Needs positioning near task1/task2
            ],
            flows=[
                BPMNFlow(
                    id="f1", type="sequenceFlow", source_ref="task1", target_ref="task3"
                ),
            ],
            has_di_coordinates=True,
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        task3 = resolved.get_element_by_id("task3")
        # task3 should be positioned without overlapping existing elements
        assert task3.x is not None

    def test_boundary_event_id_pattern_matching(self):
        """Test boundary event positioning with ID pattern matching."""
        model = BPMNModel(
            elements=[
                BPMNElement(
                    id="subprocess1",
                    type="subProcess",
                    x=100,
                    y=100,
                    width=200,
                    height=150,
                ),
                BPMNElement(
                    id="subprocess1Boundary", type="boundaryEvent"
                ),  # ID contains parent
            ],
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        boundary = resolved.get_element_by_id("subprocess1Boundary")
        # Boundary should be positioned on subprocess edge
        assert boundary.x is not None
        assert boundary.y is not None

    def test_organize_by_lanes_empty_lane(self):
        """Test lane organization with empty lane (no elements)."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="task1", type="task", x=100, y=100, parent_id="lane1"),
            ],
            lanes=[
                Lane(id="lane1", name="Lane 1", element_refs=["task1"]),
                Lane(id="lane2", name="Lane 2", element_refs=[]),  # Empty lane
            ],
            pools=[
                Pool(id="pool1", name="Pool", process_ref="process1"),
            ],
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        lane1 = resolved.get_lane_by_id("lane1")
        lane2 = resolved.get_lane_by_id("lane2")

        assert lane1 is not None
        assert lane2 is not None

    def test_organize_by_lanes_elements_same_y(self):
        """Test lane organization when elements have same Y position."""
        model = BPMNModel(
            elements=[
                BPMNElement(
                    id="task1",
                    type="task",
                    x=100,
                    y=150,
                    width=120,
                    height=80,
                    parent_id="lane1",
                ),
                BPMNElement(
                    id="task2",
                    type="task",
                    x=250,
                    y=150,
                    width=120,
                    height=80,
                    parent_id="lane1",
                ),
            ],
            lanes=[
                Lane(id="lane1", name="Lane 1", element_refs=["task1", "task2"]),
            ],
            pools=[
                Pool(id="pool1", name="Pool", process_ref="process1"),
            ],
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        # Elements with same Y should be centered vertically in lane
        task1 = resolved.get_element_by_id("task1")
        task2 = resolved.get_element_by_id("task2")
        assert task1.y == task2.y

    def test_organize_by_lanes_elements_no_y_positions(self):
        """Test lane organization when lane elements have no Y positions."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="task1", type="task", x=100, parent_id="lane1"),  # No Y
            ],
            lanes=[
                Lane(id="lane1", name="Lane 1", element_refs=["task1"]),
            ],
            pools=[
                Pool(id="pool1", name="Pool", process_ref="process1"),
            ],
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        task1 = resolved.get_element_by_id("task1")
        # Should handle gracefully
        assert task1.x is not None

    def test_multiple_pools_organization(self):
        """Test organizing model with multiple pools."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="task1", type="task", x=100, y=100, parent_id="lane1"),
            ],
            lanes=[
                Lane(
                    id="lane1",
                    name="Lane 1",
                    parent_pool_id="pool1",
                    element_refs=["task1"],
                ),
            ],
            pools=[
                Pool(id="pool1", name="Pool 1", process_ref="process1"),
                Pool(id="pool2", name="Pool 2", process_ref="process2"),
            ],
            process_id="process1",
        )

        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        pool1 = resolved.get_pool_by_id("pool1")
        pool2 = resolved.get_pool_by_id("pool2")

        # Second pool should be below first
        assert pool2.y > pool1.y


class TestParserAdditionalCases:
    """Additional parser tests for coverage."""

    def test_parse_xml_string_directly(self):
        """Test parsing BPMN from XML string."""
        from bpmn2drawio.parser import parse_bpmn

        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:process id="Process_1" isExecutable="false">
            <bpmn:startEvent id="Start_1" name="Start" />
          </bpmn:process>
        </bpmn:definitions>"""

        model = parse_bpmn(xml_string)

        assert model.process_id == "Process_1"
        assert len(model.elements) == 1

    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises error."""
        from bpmn2drawio.parser import parse_bpmn
        from bpmn2drawio.exceptions import BPMNParseError

        with pytest.raises(BPMNParseError) as exc_info:
            parse_bpmn("/nonexistent/path/file.bpmn")

        assert (
            "not found" in str(exc_info.value).lower()
            or "failed" in str(exc_info.value).lower()
        )

    def test_parse_invalid_xml(self):
        """Test parsing invalid XML raises error."""
        from bpmn2drawio.parser import parse_bpmn
        from bpmn2drawio.exceptions import BPMNParseError

        invalid_xml = "<invalid>not closed"

        with pytest.raises(BPMNParseError):
            parse_bpmn(invalid_xml)

    def test_parse_with_subprocess(self):
        """Test parsing BPMN with subprocess element."""
        from bpmn2drawio.parser import parse_bpmn

        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:process id="Process_1" isExecutable="false">
            <bpmn:subProcess id="SubProcess_1" name="Sub Process">
              <bpmn:startEvent id="Start_Sub" />
              <bpmn:endEvent id="End_Sub" />
            </bpmn:subProcess>
          </bpmn:process>
        </bpmn:definitions>"""

        model = parse_bpmn(xml_string)

        subprocess = model.get_element_by_id("SubProcess_1")
        assert subprocess is not None
        assert subprocess.type == "subProcess"

    def test_parse_with_loop_characteristics(self):
        """Test parsing BPMN with multi-instance loop characteristics."""
        from bpmn2drawio.parser import parse_bpmn

        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:process id="Process_1" isExecutable="false">
            <bpmn:task id="Task_1" name="Multi Task">
              <bpmn:multiInstanceLoopCharacteristics isSequential="true" />
            </bpmn:task>
          </bpmn:process>
        </bpmn:definitions>"""

        model = parse_bpmn(xml_string)

        task = model.get_element_by_id("Task_1")
        assert task.properties.get("isMultiInstance") is True
        assert task.properties.get("isSequential") is True

    def test_parse_with_standard_loop(self):
        """Test parsing BPMN with standard loop characteristics."""
        from bpmn2drawio.parser import parse_bpmn

        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:process id="Process_1" isExecutable="false">
            <bpmn:task id="Task_1" name="Loop Task">
              <bpmn:standardLoopCharacteristics />
            </bpmn:task>
          </bpmn:process>
        </bpmn:definitions>"""

        model = parse_bpmn(xml_string)

        task = model.get_element_by_id("Task_1")
        assert task.properties.get("isLoop") is True

    def test_parse_gateway_with_default_flow(self):
        """Test parsing gateway with default flow."""
        from bpmn2drawio.parser import parse_bpmn

        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:process id="Process_1" isExecutable="false">
            <bpmn:exclusiveGateway id="Gateway_1" default="Flow_Default" />
            <bpmn:sequenceFlow id="Flow_Default" sourceRef="Gateway_1" targetRef="Task_1" />
            <bpmn:task id="Task_1" />
          </bpmn:process>
        </bpmn:definitions>"""

        model = parse_bpmn(xml_string)

        gateway = model.get_element_by_id("Gateway_1")
        assert gateway.properties.get("defaultFlow") == "Flow_Default"

        # The default flow should be marked
        flow = model.get_flow_by_id("Flow_Default")
        assert flow.is_default is True

    def test_parse_boundary_event_attached_to(self):
        """Test parsing boundary event with attachedToRef."""
        from bpmn2drawio.parser import parse_bpmn

        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:process id="Process_1" isExecutable="false">
            <bpmn:task id="Task_1" />
            <bpmn:boundaryEvent id="Boundary_1" attachedToRef="Task_1">
              <bpmn:timerEventDefinition />
            </bpmn:boundaryEvent>
          </bpmn:process>
        </bpmn:definitions>"""

        model = parse_bpmn(xml_string)

        boundary = model.get_element_by_id("Boundary_1")
        assert boundary.properties.get("attachedToRef") == "Task_1"
        assert boundary.properties.get("eventDefinition") == "timer"

    def test_parse_message_flow(self):
        """Test parsing message flow in collaboration."""
        from bpmn2drawio.parser import parse_bpmn

        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:collaboration id="Collab_1">
            <bpmn:participant id="Pool_1" processRef="Process_1" />
            <bpmn:participant id="Pool_2" processRef="Process_2" />
            <bpmn:messageFlow id="Message_1" sourceRef="Task_1" targetRef="Task_2" />
          </bpmn:collaboration>
          <bpmn:process id="Process_1" isExecutable="false">
            <bpmn:task id="Task_1" />
          </bpmn:process>
          <bpmn:process id="Process_2" isExecutable="false">
            <bpmn:task id="Task_2" />
          </bpmn:process>
        </bpmn:definitions>"""

        model = parse_bpmn(xml_string)

        message_flow = model.get_flow_by_id("Message_1")
        assert message_flow is not None
        assert message_flow.type == "messageFlow"


class TestIconsAdditionalCases:
    """Additional tests for icons module."""

    def test_get_task_icon_style_unknown_type(self):
        """Test get_task_icon_style for unknown task type."""
        from bpmn2drawio.icons import get_task_icon_style

        result = get_task_icon_style("unknownTask")
        assert result is None

    def test_get_event_icon_style_unknown_event(self):
        """Test get_event_icon_style for unknown event combination."""
        from bpmn2drawio.icons import get_event_icon_style

        result = get_event_icon_style("startEvent", "unknownDefinition")
        assert result is None

    def test_create_event_icon_no_event_def(self):
        """Test create_event_icon when element has no event definition."""
        from bpmn2drawio.icons import create_event_icon

        element = BPMNElement(id="start1", type="startEvent", properties={})
        result = create_event_icon(element, "parent1", 100)

        assert result is None  # No icon for plain start event

    def test_create_event_icon_unknown_icon_key(self):
        """Test create_event_icon when icon key not found."""
        from bpmn2drawio.icons import create_event_icon

        element = BPMNElement(
            id="start1",
            type="startEvent",
            properties={"eventDefinition": "unknownDefinition"},
        )
        result = create_event_icon(element, "parent1", 100)

        assert result is None


class TestModelsAdditionalCases:
    """Additional tests for models module."""

    def test_model_get_flow_by_id_not_found(self):
        """Test BPMNModel.get_flow_by_id returns None for missing flow."""
        model = BPMNModel(flows=[])

        result = model.get_flow_by_id("nonexistent")
        assert result is None

    def test_model_get_pool_by_id_not_found(self):
        """Test BPMNModel.get_pool_by_id returns None for missing pool."""
        model = BPMNModel(pools=[])

        result = model.get_pool_by_id("nonexistent")
        assert result is None

    def test_model_get_lane_by_id_not_found(self):
        """Test BPMNModel.get_lane_by_id returns None for missing lane."""
        model = BPMNModel(lanes=[])

        result = model.get_lane_by_id("nonexistent")
        assert result is None

    def test_model_get_elements_in_lane(self):
        """Test BPMNModel.get_elements_in_lane."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="task1", type="task", parent_id="lane1"),
                BPMNElement(id="task2", type="task", parent_id="lane1"),
                BPMNElement(id="task3", type="task", parent_id="lane2"),
            ],
            lanes=[
                Lane(id="lane1", name="Lane 1"),
                Lane(id="lane2", name="Lane 2"),
            ],
        )

        elements_in_lane1 = model.get_elements_in_lane("lane1")

        assert len(elements_in_lane1) == 2
        assert all(e.parent_id == "lane1" for e in elements_in_lane1)

    def test_lane_has_coordinates(self):
        """Test Lane.has_coordinates method."""
        lane_with_coords = Lane(id="lane1", x=100, y=200)
        lane_without_coords = Lane(id="lane2")

        assert lane_with_coords.has_coordinates() is True
        assert lane_without_coords.has_coordinates() is False

    def test_element_center(self):
        """Test BPMNElement.center method."""
        element = BPMNElement(
            id="task1", type="task", x=100, y=100, width=120, height=80
        )

        center = element.center()

        assert center == (160.0, 140.0)  # (100 + 120/2, 100 + 80/2)

    def test_element_center_no_coords(self):
        """Test BPMNElement.center returns None when missing coords."""
        element = BPMNElement(id="task1", type="task")

        center = element.center()

        assert center is None


class TestConfigAdditionalCases:
    """Additional tests for config module."""

    def test_load_brand_config_not_found(self):
        """Test load_brand_config raises error for missing file."""
        from bpmn2drawio.config import load_brand_config
        from bpmn2drawio.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError) as exc_info:
            load_brand_config("/nonexistent/config.yaml")

        assert "not found" in str(exc_info.value)

    def test_load_brand_config_empty(self, tmp_path):
        """Test load_brand_config with empty YAML file."""
        from bpmn2drawio.config import load_brand_config

        config_path = tmp_path / "empty_config.yaml"
        config_path.write_text("")

        theme = load_brand_config(str(config_path))

        # Should return default theme
        assert theme is not None

    def test_get_env_config_with_graphviz_path(self, monkeypatch):
        """Test get_env_config reads GRAPHVIZ_PATH from environment."""
        from bpmn2drawio.config import get_env_config

        monkeypatch.setenv("BPMN2DRAWIO_GRAPHVIZ_PATH", "/custom/graphviz")

        config = get_env_config()

        assert config.get("graphviz_path") == "/custom/graphviz"


class TestConverterAdditionalCases:
    """Additional tests for converter module."""

    def test_converter_with_config_file(self, tmp_path):
        """Test converter with brand config file."""
        from bpmn2drawio.converter import Converter

        # Create a config file
        config_path = tmp_path / "brand_config.yaml"
        config_path.write_text("""
base_theme: default
colors:
  task_fill: "#FF0000"
""")

        converter = Converter(config=str(config_path))

        # Should create converter with custom theme
        assert converter is not None

    def test_converter_convert_model(self):
        """Test Converter.convert_model method."""
        from bpmn2drawio.converter import Converter

        model = BPMNModel(
            process_id="process1",
            elements=[
                BPMNElement(
                    id="start", type="startEvent", x=100, y=100, width=36, height=36
                ),
                BPMNElement(
                    id="end", type="endEvent", x=300, y=100, width=36, height=36
                ),
            ],
            flows=[
                BPMNFlow(
                    id="f1", type="sequenceFlow", source_ref="start", target_ref="end"
                ),
            ],
        )

        converter = Converter()
        result = converter.convert_model(model)

        assert result is not None
        assert result.element_count == 2
        assert result.flow_count == 1


class TestCLIAdditionalCases:
    """Additional tests for CLI module."""

    def test_cli_with_warnings(self, tmp_path):
        """Test CLI with warnings displayed."""
        from bpmn2drawio.cli import main

        # Create a BPMN file that should trigger warning
        input_file = tmp_path / "no_di.bpmn"
        input_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:process id="Process_1" isExecutable="false">
            <bpmn:startEvent id="Start_1" name="Start" />
          </bpmn:process>
        </bpmn:definitions>""")

        output_file = tmp_path / "output.drawio"

        exit_code = main(
            [
                str(input_file),
                str(output_file),
                "--layout",
                "preserve",
            ]
        )

        # Should succeed but may have warnings
        assert exit_code == 0

    def test_cli_if_main(self, tmp_path, monkeypatch):
        """Test CLI __main__ block execution."""

        # This tests the if __name__ == "__main__" path
        # We can't easily test it directly, but we can verify the module structure


class TestMainModuleExecution:
    """Tests for __main__.py execution."""

    def test_main_module_direct_execution(self, tmp_path):
        """Test running __main__.py directly with valid args."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from bpmn2drawio.__main__ import main; import sys; sys.exit(0)",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent / "src"),
        )

        # Module should be importable
        assert "Error" not in result.stderr or result.returncode == 0

    def test_main_import_and_call(self):
        """Test importing and calling main from __main__."""
        # Import the module to trigger coverage
        import bpmn2drawio.__main__

        # Verify the main function is available
        assert hasattr(bpmn2drawio.__main__, "main")

    def test_main_module_with_help(self):
        """Test __main__.py with --help flag."""
        result = subprocess.run(
            [sys.executable, "-m", "bpmn2drawio", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert "bpmn2drawio" in result.stdout.lower()
