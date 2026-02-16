"""Characterization tests for PositionResolver module.

These tests document the current behavior of position_resolver.py as-is.
They cover resolve(), _organize_by_lanes(), _place_connected_elements(),
_avoid_overlap(), _position_boundary_events(), and edge cases.
"""

from bpmn2drawio.models import BPMNElement, BPMNFlow, BPMNModel, Pool, Lane
from bpmn2drawio.position_resolver import PositionResolver, resolve_positions
from bpmn2drawio.constants import LayoutConstants


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def make_element(
    id,
    type="task",
    name=None,
    x=None,
    y=None,
    width=None,
    height=None,
    parent_id=None,
    subprocess_id=None,
    properties=None,
):
    """Create a BPMNElement with sensible defaults."""
    return BPMNElement(
        id=id,
        type=type,
        name=name or id,
        x=x,
        y=y,
        width=width,
        height=height,
        parent_id=parent_id,
        subprocess_id=subprocess_id,
        properties=properties or {},
    )


def make_flow(id, source_ref, target_ref, type="sequenceFlow"):
    """Create a BPMNFlow."""
    return BPMNFlow(
        id=id,
        type=type,
        source_ref=source_ref,
        target_ref=target_ref,
    )


def make_pool(id, name=None, process_ref=None, x=None, y=None, width=None, height=None):
    """Create a Pool."""
    return Pool(
        id=id,
        name=name or id,
        process_ref=process_ref,
        x=x,
        y=y,
        width=width,
        height=height,
    )


def make_lane(
    id,
    parent_pool_id="",
    name=None,
    x=None,
    y=None,
    width=None,
    height=None,
    element_refs=None,
):
    """Create a Lane."""
    return Lane(
        id=id,
        name=name or id,
        parent_pool_id=parent_pool_id,
        x=x,
        y=y,
        width=width,
        height=height,
        element_refs=element_refs or [],
    )


# ===========================================================================
# 1. resolve() — end-to-end tests
# ===========================================================================


class TestResolveSinglePoolSingleLane:
    """resolve() with a single pool containing a single lane."""

    def test_all_elements_have_positions_after_resolve(self):
        """Every element must have x and y set after resolve()."""
        lane = make_lane("lane1", parent_pool_id="pool1")
        pool = make_pool("pool1", process_ref="proc1")
        elements = [
            make_element("start", type="startEvent", parent_id="lane1"),
            make_element("task1", parent_id="lane1"),
            make_element("end", type="endEvent", parent_id="lane1"),
        ]
        flows = [
            make_flow("f1", "start", "task1"),
            make_flow("f2", "task1", "end"),
        ]
        model = BPMNModel(
            elements=elements,
            flows=flows,
            pools=[pool],
            lanes=[lane],
        )
        resolver = PositionResolver()
        resolved = resolver.resolve(model)

        for elem in resolved.elements:
            assert elem.x is not None, f"{elem.id} missing x"
            assert elem.y is not None, f"{elem.id} missing y"

    def test_dimensions_assigned(self):
        """Elements without explicit dimensions get defaults from ELEMENT_DIMENSIONS."""
        lane = make_lane("lane1", parent_pool_id="pool1")
        pool = make_pool("pool1", process_ref="proc1")
        elements = [
            make_element("start", type="startEvent", parent_id="lane1"),
            make_element("task1", type="userTask", parent_id="lane1"),
        ]
        model = BPMNModel(
            elements=elements,
            flows=[],
            pools=[pool],
            lanes=[lane],
        )
        resolved = PositionResolver().resolve(model)

        start = resolved.get_element_by_id("start")
        task = resolved.get_element_by_id("task1")
        assert start.width == 36 and start.height == 36
        assert task.width == 120 and task.height == 80

    def test_original_model_not_mutated(self):
        """resolve() must work on a deep copy, leaving the original unchanged."""
        element = make_element("t1")
        model = BPMNModel(elements=[element])
        resolver = PositionResolver()
        _ = resolver.resolve(model)

        # Original element should still have None coords
        assert model.elements[0].x is None
        assert model.elements[0].y is None


class TestResolveSinglePoolMultipleLanes:
    """resolve() with a single pool containing multiple lanes."""

    def test_lane_positions_set(self):
        """Each lane gets x, y, width, height after resolve."""
        pool = make_pool("pool1", process_ref="proc1")
        lane_a = make_lane("laneA", parent_pool_id="pool1")
        lane_b = make_lane("laneB", parent_pool_id="pool1")
        elements = [
            make_element("t1", parent_id="laneA"),
            make_element("t2", parent_id="laneB"),
        ]
        flows = [make_flow("f1", "t1", "t2")]
        model = BPMNModel(
            elements=elements,
            flows=flows,
            pools=[pool],
            lanes=[lane_a, lane_b],
        )
        resolved = PositionResolver().resolve(model)

        for lane in resolved.lanes:
            assert lane.x is not None, f"Lane {lane.id} missing x"
            assert lane.y is not None, f"Lane {lane.id} missing y"
            assert lane.width is not None
            assert lane.height is not None

    def test_lanes_stacked_vertically(self):
        """Lanes within a pool should be stacked vertically (non-overlapping)."""
        pool = make_pool("pool1", process_ref="proc1")
        lane_a = make_lane("laneA", parent_pool_id="pool1")
        lane_b = make_lane("laneB", parent_pool_id="pool1")
        elements = [
            make_element("t1", parent_id="laneA"),
            make_element("t2", parent_id="laneB"),
        ]
        model = BPMNModel(
            elements=elements,
            flows=[],
            pools=[pool],
            lanes=[lane_a, lane_b],
        )
        resolved = PositionResolver().resolve(model)

        lane_a_r = resolved.get_lane_by_id("laneA")
        lane_b_r = resolved.get_lane_by_id("laneB")
        # Second lane starts after first lane ends
        assert lane_b_r.y >= lane_a_r.y + lane_a_r.height

    def test_elements_positioned_inside_their_lane(self):
        """Element y must fall within its parent lane bounds (relative coords)."""
        pool = make_pool("pool1", process_ref="proc1")
        lane_a = make_lane("laneA", parent_pool_id="pool1")
        elements = [
            make_element("t1", parent_id="laneA"),
        ]
        model = BPMNModel(
            elements=elements,
            flows=[],
            pools=[pool],
            lanes=[lane_a],
        )
        resolved = PositionResolver().resolve(model)

        t1 = resolved.get_element_by_id("t1")
        lane = resolved.get_lane_by_id("laneA")
        # Element Y should be within 0..lane.height (relative positioning)
        assert t1.y >= 0
        assert t1.y <= lane.height


class TestResolveMultiplePools:
    """resolve() with multiple pools."""

    def test_pools_get_positions(self):
        """Each pool receives coordinates after resolve."""
        pool_a = make_pool("poolA", process_ref="procA")
        pool_b = make_pool("poolB", process_ref="procB")
        elements = [
            make_element("t1"),
            make_element("t2"),
        ]
        model = BPMNModel(
            elements=elements,
            flows=[],
            pools=[pool_a, pool_b],
            lanes=[],
        )
        resolved = PositionResolver().resolve(model)

        for pool in resolved.pools:
            assert pool.x is not None, f"Pool {pool.id} missing x"
            assert pool.y is not None, f"Pool {pool.id} missing y"

    def test_pools_not_overlapping(self):
        """Pools should be vertically stacked with a gap."""
        pool_a = make_pool("poolA", process_ref="procA")
        pool_b = make_pool("poolB", process_ref="procB")
        model = BPMNModel(
            elements=[],
            flows=[],
            pools=[pool_a, pool_b],
            lanes=[],
        )
        resolved = PositionResolver().resolve(model)

        pa = resolved.get_pool_by_id("poolA")
        pb = resolved.get_pool_by_id("poolB")
        # Pool B should start below pool A
        assert pb.y >= pa.y + pa.height

    def test_pool_with_existing_coordinates_preserved(self):
        """Pools that already have DI coordinates keep them."""
        pool = make_pool("poolA", x=100, y=200, width=800, height=300)
        model = BPMNModel(elements=[], flows=[], pools=[pool], lanes=[])
        resolved = PositionResolver().resolve(model)

        p = resolved.get_pool_by_id("poolA")
        assert p.x == 100
        assert p.y == 200


class TestResolveLanelessPool:
    """resolve() with pool that has no lanes."""

    def test_elements_get_pool_as_parent(self):
        """Elements in a laneless pool get pool.id as parent_id."""
        pool = make_pool("pool1", process_ref="proc1")
        elements = [
            make_element("t1"),
            make_element("t2"),
        ]
        model = BPMNModel(
            elements=elements,
            flows=[],
            pools=[pool],
            lanes=[],
        )
        resolved = PositionResolver().resolve(model)

        for elem in resolved.elements:
            assert elem.parent_id == "pool1"


class TestResolveEmptyModel:
    """resolve() with an empty model."""

    def test_empty_model_returns_empty(self):
        """An empty model should resolve without error and remain empty."""
        model = BPMNModel()
        resolved = PositionResolver().resolve(model)
        assert len(resolved.elements) == 0
        assert len(resolved.flows) == 0
        assert len(resolved.pools) == 0
        assert len(resolved.lanes) == 0

    def test_model_with_only_flows_no_crash(self):
        """Model with flows but no elements should not crash."""
        model = BPMNModel(flows=[make_flow("f1", "nonexist1", "nonexist2")])
        resolved = PositionResolver().resolve(model)
        assert len(resolved.elements) == 0


# ===========================================================================
# 2. _organize_by_lanes() — lane organization and coordinate calculation
# ===========================================================================


class TestOrganizeByLanes:
    """Tests for _organize_by_lanes() internal method."""

    def _build_resolver(self):
        return PositionResolver()

    def test_elements_grouped_into_correct_lanes(self):
        """Elements with parent_id matching a lane.id belong to that lane."""
        pool = make_pool("pool1", process_ref="proc1")
        lane_a = make_lane("laneA", parent_pool_id="pool1")
        lane_b = make_lane("laneB", parent_pool_id="pool1")
        elements = [
            make_element("t1", parent_id="laneA", x=100, y=100, width=120, height=80),
            make_element("t2", parent_id="laneB", x=300, y=300, width=120, height=80),
        ]
        model = BPMNModel(
            elements=elements,
            flows=[],
            pools=[pool],
            lanes=[lane_a, lane_b],
        )
        resolver = self._build_resolver()
        resolver._organize_by_lanes(model)

        # After organizing, lane positions should be set
        assert model.lanes[0].x is not None
        assert model.lanes[1].x is not None

    def test_empty_lane_gets_minimum_height(self):
        """A lane with no elements gets 120px minimum height."""
        pool = make_pool("pool1", process_ref="proc1")
        lane = make_lane("laneA", parent_pool_id="pool1")
        model = BPMNModel(
            elements=[],
            flows=[],
            pools=[pool],
            lanes=[lane],
        )
        resolver = self._build_resolver()
        resolver._organize_by_lanes(model)

        assert model.lanes[0].height >= 120

    def test_lane_height_grows_with_tall_elements(self):
        """Lane height should accommodate the tallest element plus padding."""
        pool = make_pool("pool1", process_ref="proc1")
        lane = make_lane("laneA", parent_pool_id="pool1")
        elements = [
            make_element("big", parent_id="laneA", x=50, y=50, width=200, height=200),
        ]
        model = BPMNModel(
            elements=elements,
            flows=[],
            pools=[pool],
            lanes=[lane],
        )
        resolver = self._build_resolver()
        resolver._organize_by_lanes(model)

        # Height should be at least element height + padding
        assert model.lanes[0].height >= 200

    def test_lane_x_set_to_pool_header_width(self):
        """Lane x should equal LayoutConstants.POOL_HEADER_WIDTH."""
        pool = make_pool("pool1", process_ref="proc1")
        lane = make_lane("laneA", parent_pool_id="pool1")
        model = BPMNModel(
            elements=[
                make_element(
                    "t1", parent_id="laneA", x=100, y=100, width=120, height=80
                )
            ],
            flows=[],
            pools=[pool],
            lanes=[lane],
        )
        resolver = self._build_resolver()
        resolver._organize_by_lanes(model)

        assert model.lanes[0].x == LayoutConstants.POOL_HEADER_WIDTH

    def test_multiple_lanes_sequential_y(self):
        """Lanes in same pool get sequential y positions starting at 0."""
        pool = make_pool("pool1", process_ref="proc1")
        lane_a = make_lane("laneA", parent_pool_id="pool1")
        lane_b = make_lane("laneB", parent_pool_id="pool1")
        lane_c = make_lane("laneC", parent_pool_id="pool1")
        elements = [
            make_element("t1", parent_id="laneA", x=100, y=50, width=120, height=80),
            make_element("t2", parent_id="laneB", x=100, y=200, width=120, height=80),
            make_element("t3", parent_id="laneC", x=100, y=400, width=120, height=80),
        ]
        model = BPMNModel(
            elements=elements,
            flows=[],
            pools=[pool],
            lanes=[lane_a, lane_b, lane_c],
        )
        resolver = self._build_resolver()
        resolver._organize_by_lanes(model)

        y_positions = [lane.y for lane in model.lanes]
        # First lane starts at 0
        assert y_positions[0] == 0
        # Each subsequent lane starts after the previous one ends
        for i in range(1, len(y_positions)):
            assert y_positions[i] > y_positions[i - 1]


# ===========================================================================
# 3. _place_connected_elements() — neighbor-based positioning
# ===========================================================================


class TestPlaceConnectedElements:
    """Tests for _place_connected_elements()."""

    def _build_resolver(self):
        return PositionResolver()

    def test_element_placed_right_of_source(self):
        """An element without DI is placed to the right of its incoming neighbor."""
        resolver = self._build_resolver()
        source = make_element("src", x=100, y=100, width=120, height=80)
        target = make_element("tgt")  # no DI
        flows = [make_flow("f1", "src", "tgt")]
        bounds = {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}

        resolver._place_connected_elements([target], [source], flows, bounds)

        assert target.x is not None
        assert target.y is not None
        # Should be to the right of source
        assert target.x > source.x

    def test_element_placed_left_of_target(self):
        """An element without DI is placed left of its outgoing neighbor
        when there is no incoming neighbor."""
        resolver = self._build_resolver()
        target = make_element("tgt", x=400, y=100, width=120, height=80)
        source = make_element("src")  # no DI
        flows = [make_flow("f1", "src", "tgt")]
        bounds = {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}

        resolver._place_connected_elements([source], [target], flows, bounds)

        assert source.x is not None
        assert source.x < target.x

    def test_fully_disconnected_fallback(self):
        """Elements with no connections get fallback positions below the diagram."""
        resolver = self._build_resolver()
        elem = make_element("lonely")  # no DI, no flows
        bounds = {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}

        # No flows connecting this element to anything with DI
        resolver._place_connected_elements([elem], [], [], bounds)

        # Should fall through the positioning loop and get placed below max_y
        assert elem.x is not None
        assert elem.y is not None
        assert elem.y >= bounds["max_y"]

    def test_chained_positioning(self):
        """Multiple elements are positioned iteratively (A->B->C)."""
        resolver = self._build_resolver()
        a = make_element("a", x=100, y=100, width=120, height=80)
        b = make_element("b")  # no DI
        c = make_element("c")  # no DI
        flows = [
            make_flow("f1", "a", "b"),
            make_flow("f2", "b", "c"),
        ]
        bounds = {"min_x": 50, "min_y": 50, "max_x": 2000, "max_y": 600}

        resolver._place_connected_elements([b, c], [a], flows, bounds)

        assert b.x is not None and c.x is not None
        # B should be right of A, C right of B
        assert b.x > a.x
        assert c.x > b.x

    def test_empty_elements_list_no_crash(self):
        """Passing an empty list of elements should be a no-op."""
        resolver = self._build_resolver()
        bounds = {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}
        # Should not raise
        resolver._place_connected_elements([], [], [], bounds)


# ===========================================================================
# 4. _avoid_overlap() — collision detection
# ===========================================================================


class TestAvoidOverlap:
    """Tests for _avoid_overlap()."""

    def _build_resolver(self):
        return PositionResolver()

    def test_no_overlap_returns_original(self):
        """When no positioned element conflicts, position is unchanged."""
        resolver = self._build_resolver()
        elem = make_element("new", width=120, height=80)
        positioned = {
            "other": make_element("other", x=500, y=500, width=120, height=80),
        }
        bounds = {"min_x": 50, "min_y": 50, "max_x": 1200, "max_y": 900}

        result = resolver._avoid_overlap(100, 100, elem, positioned, bounds)
        assert result == (100, 100)

    def test_overlap_shifts_position(self):
        """When an overlap exists, position should shift."""
        resolver = self._build_resolver()
        elem = make_element("new", width=120, height=80)
        positioned = {
            "blocker": make_element("blocker", x=100, y=100, width=120, height=80),
        }
        bounds = {"min_x": 50, "min_y": 50, "max_x": 1200, "max_y": 900}

        result = resolver._avoid_overlap(100, 100, elem, positioned, bounds)
        # Should be different from the original overlapping position
        assert result != (100, 100)

    def test_multiple_overlaps_resolved(self):
        """Multiple overlapping positioned elements are all avoided."""
        resolver = self._build_resolver()
        elem = make_element("new", width=120, height=80)
        positioned = {
            "b1": make_element("b1", x=100, y=100, width=120, height=80),
            "b2": make_element("b2", x=100, y=200, width=120, height=80),
            "b3": make_element("b3", x=100, y=300, width=120, height=80),
        }
        bounds = {"min_x": 50, "min_y": 50, "max_x": 1200, "max_y": 900}

        result_x, result_y = resolver._avoid_overlap(100, 100, elem, positioned, bounds)
        # Result should not overlap with any of the blockers
        elem_right = result_x + 120
        elem_bottom = result_y + 80
        for other in positioned.values():
            overlaps = (
                result_x < other.x + other.width
                and elem_right > other.x
                and result_y < other.y + other.height
                and elem_bottom > other.y
            )
            assert not overlaps, f"Still overlaps with {other.id}"

    def test_overlap_with_none_coords_skipped(self):
        """Positioned elements with None coords are ignored in overlap check."""
        resolver = self._build_resolver()
        elem = make_element("new", width=120, height=80)
        positioned = {
            "ghost": make_element("ghost"),  # x=None, y=None
        }
        bounds = {"min_x": 50, "min_y": 50, "max_x": 1200, "max_y": 900}

        result = resolver._avoid_overlap(100, 100, elem, positioned, bounds)
        # Should stay at original since the only element has None coords
        assert result == (100, 100)

    def test_boundary_touching_not_overlap(self):
        """Elements that touch but don't overlap should not shift."""
        resolver = self._build_resolver()
        elem = make_element("new", width=120, height=80)
        # Place the existing element exactly after the new one ends
        positioned = {
            "adjacent": make_element("adjacent", x=220, y=100, width=120, height=80),
        }
        bounds = {"min_x": 50, "min_y": 50, "max_x": 1200, "max_y": 900}

        result = resolver._avoid_overlap(100, 100, elem, positioned, bounds)
        assert result == (100, 100)


# ===========================================================================
# 5. _position_boundary_events() — boundary event placement
# ===========================================================================


class TestPositionBoundaryEvents:
    """Tests for _position_boundary_events()."""

    def _build_resolver(self):
        return PositionResolver()

    def test_boundary_event_attached_via_property(self):
        """Boundary event uses attachedToRef from properties to find parent."""
        task = make_element(
            "task1", type="userTask", x=200, y=200, width=120, height=80
        )
        boundary = make_element(
            "boundary1",
            type="boundaryEvent",
            x=0,
            y=0,
            width=36,
            height=36,
            properties={"attachedToRef": "task1"},
        )
        model = BPMNModel(elements=[task, boundary])
        resolver = self._build_resolver()

        resolver._position_boundary_events(model)

        assert boundary.parent_id == "task1"
        # Positioned on bottom edge of task
        assert boundary.y == 80 - 18  # attached_height - event_height/2

    def test_boundary_event_x_offset(self):
        """Boundary event x starts at offset 20 from the left of the parent."""
        task = make_element(
            "task1", type="userTask", x=200, y=200, width=120, height=80
        )
        boundary = make_element(
            "b1",
            type="boundaryEvent",
            width=36,
            height=36,
            properties={"attachedToRef": "task1"},
        )
        model = BPMNModel(elements=[task, boundary])
        resolver = self._build_resolver()

        resolver._position_boundary_events(model)

        assert boundary.x == 20

    def test_multiple_boundary_events_spaced(self):
        """Multiple boundary events on same task are spaced horizontally."""
        task = make_element(
            "task1", type="userTask", x=200, y=200, width=120, height=80
        )
        b1 = make_element(
            "b1",
            type="boundaryEvent",
            width=36,
            height=36,
            properties={"attachedToRef": "task1"},
        )
        b2 = make_element(
            "b2",
            type="boundaryEvent",
            width=36,
            height=36,
            properties={"attachedToRef": "task1"},
        )
        model = BPMNModel(elements=[task, b1, b2])
        resolver = self._build_resolver()

        resolver._position_boundary_events(model)

        # Second boundary event should be 50px to the right of the first
        assert b1.x == 20
        assert b2.x == 70  # 20 + 1*50

    def test_boundary_event_no_attached_ref_skipped(self):
        """Boundary event without attachedToRef and no ID pattern match keeps coords."""
        boundary = make_element(
            "orphanBoundary", type="boundaryEvent", x=999, y=999, width=36, height=36
        )
        model = BPMNModel(elements=[boundary])
        resolver = self._build_resolver()

        resolver._position_boundary_events(model)

        # No parent found; x/y unchanged from what _position_boundary_events sees
        # (it won't modify coords if no attached element is found)
        assert boundary.parent_id is None

    def test_boundary_event_id_pattern_fallback(self):
        """Boundary event without attachedToRef falls back to ID pattern matching."""
        task = make_element("myTask", type="task", x=100, y=100, width=120, height=80)
        # The boundary event id contains the parent task id
        boundary = make_element(
            "myTaskBoundary", type="boundaryEvent", width=36, height=36
        )
        model = BPMNModel(elements=[task, boundary])
        resolver = self._build_resolver()

        resolver._position_boundary_events(model)

        assert boundary.parent_id == "myTask"


# ===========================================================================
# 6. Edge cases
# ===========================================================================


class TestEdgeCasesNoneCoordinates:
    """Edge cases around elements with None coordinates."""

    def test_all_elements_none_coords_get_positions(self):
        """All elements with None x/y get positions after resolve."""
        elements = [
            make_element("a", type="startEvent"),
            make_element("b", type="task"),
            make_element("c", type="endEvent"),
        ]
        flows = [
            make_flow("f1", "a", "b"),
            make_flow("f2", "b", "c"),
        ]
        model = BPMNModel(elements=elements, flows=flows)
        resolved = PositionResolver().resolve(model)

        for elem in resolved.elements:
            assert elem.x is not None
            assert elem.y is not None

    def test_mixed_none_and_set_coords(self):
        """Elements with set coords are preserved; None-coord elements get positions."""
        elements = [
            make_element("withDI", x=200, y=300, width=120, height=80),
            make_element("noDI"),
        ]
        flows = [make_flow("f1", "withDI", "noDI")]
        model = BPMNModel(elements=elements, flows=flows)
        resolved = PositionResolver().resolve(model)

        di_elem = resolved.get_element_by_id("withDI")
        no_di_elem = resolved.get_element_by_id("noDI")
        assert di_elem.x == 200
        assert di_elem.y == 300
        assert no_di_elem.x is not None
        assert no_di_elem.y is not None

    def test_element_with_x_only(self):
        """Element with x=100 but y=None is treated as no-DI (both required).

        _use_di_coordinates requires both x and y to be non-None, so
        x=100 alone does not qualify as having DI.  The layout engine
        or fallback may reassign x.  The key guarantee is that after
        resolve, both x and y are non-None.
        """
        elements = [make_element("half", x=100)]
        model = BPMNModel(elements=elements)
        resolved = PositionResolver().resolve(model)

        elem = resolved.get_element_by_id("half")
        assert elem.x is not None
        assert elem.y is not None


class TestEdgeCasesCircularReferences:
    """Edge cases around circular flow references."""

    def test_circular_flow_does_not_hang(self):
        """Circular flows (A->B->A) must not cause infinite loops."""
        elements = [
            make_element("a"),
            make_element("b"),
        ]
        flows = [
            make_flow("f1", "a", "b"),
            make_flow("f2", "b", "a"),
        ]
        model = BPMNModel(elements=elements, flows=flows)
        # Should complete in reasonable time
        resolved = PositionResolver().resolve(model)

        for elem in resolved.elements:
            assert elem.x is not None
            assert elem.y is not None

    def test_self_loop_flow(self):
        """An element flowing to itself should not crash."""
        elements = [make_element("loop")]
        flows = [make_flow("f1", "loop", "loop")]
        model = BPMNModel(elements=elements, flows=flows)
        resolved = PositionResolver().resolve(model)

        elem = resolved.get_element_by_id("loop")
        assert elem.x is not None
        assert elem.y is not None

    def test_three_way_cycle(self):
        """A->B->C->A cycle resolves without infinite loop."""
        elements = [
            make_element("a"),
            make_element("b"),
            make_element("c"),
        ]
        flows = [
            make_flow("f1", "a", "b"),
            make_flow("f2", "b", "c"),
            make_flow("f3", "c", "a"),
        ]
        model = BPMNModel(elements=elements, flows=flows)
        resolved = PositionResolver().resolve(model)

        for elem in resolved.elements:
            assert elem.x is not None and elem.y is not None


# ===========================================================================
# 7. Additional internal method tests
# ===========================================================================


class TestGetDiBounds:
    """Tests for _get_di_bounds()."""

    def test_default_bounds_when_no_coords(self):
        """With no DI coordinates anywhere, returns sensible defaults."""
        model = BPMNModel(elements=[make_element("t1")])
        resolver = PositionResolver()
        bounds = resolver._get_di_bounds(model)
        assert bounds == {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}

    def test_bounds_from_elements(self):
        """Bounds are calculated from elements with coords."""
        model = BPMNModel(
            elements=[
                make_element("a", x=100, y=200, width=120, height=80),
                make_element("b", x=500, y=400, width=120, height=80),
            ]
        )
        resolver = PositionResolver()
        bounds = resolver._get_di_bounds(model)
        assert bounds["min_x"] == 100
        assert bounds["min_y"] == 200
        assert bounds["max_x"] == 620  # 500 + 120
        assert bounds["max_y"] == 480  # 400 + 80

    def test_bounds_include_pools(self):
        """Pool coordinates contribute to the bounding box."""
        pool = make_pool("p1", x=0, y=0, width=1000, height=500)
        model = BPMNModel(pools=[pool])
        resolver = PositionResolver()
        bounds = resolver._get_di_bounds(model)
        assert bounds["min_x"] == 0
        assert bounds["max_x"] == 1000
        assert bounds["max_y"] == 500

    def test_bounds_include_lanes(self):
        """Lane coordinates contribute to the bounding box."""
        lane = make_lane("l1", x=40, y=50, width=560, height=200)
        model = BPMNModel(lanes=[lane])
        resolver = PositionResolver()
        bounds = resolver._get_di_bounds(model)
        assert bounds["min_x"] == 40
        assert bounds["max_y"] == 250  # 50 + 200


class TestFindConnectedElements:
    """Tests for _find_connected_elements()."""

    def test_elements_in_flows_are_connected(self):
        """Elements referenced by flows are marked connected."""
        a = make_element("a")
        b = make_element("b")
        c = make_element("c")
        flows = [make_flow("f1", "a", "b")]
        resolver = PositionResolver()

        connected = resolver._find_connected_elements([a, b, c], flows)
        assert "a" in connected
        assert "b" in connected
        assert "c" not in connected

    def test_subprocess_internals_connected(self):
        """Elements inside a connected subprocess are also connected."""
        subprocess = make_element("sub1", properties={"_is_subprocess": True})
        internal = make_element("int1", subprocess_id="sub1")
        flows = [make_flow("f1", "external", "sub1")]
        # Note: 'external' is not in elements list, but sub1 is the target
        resolver = PositionResolver()

        connected = resolver._find_connected_elements([subprocess, internal], flows)
        assert "sub1" in connected
        assert "int1" in connected

    def test_no_flows_returns_empty(self):
        """With no flows, only subprocess internals can be connected."""
        a = make_element("a")
        resolver = PositionResolver()
        connected = resolver._find_connected_elements([a], [])
        assert len(connected) == 0


class TestPlaceDisconnectedElements:
    """Tests for _place_disconnected_elements()."""

    def test_data_objects_in_sidebar(self):
        """Data objects are placed in left sidebar."""
        resolver = PositionResolver()
        data = make_element("d1", type="dataObject", width=40, height=50)
        bounds = {"min_x": 100, "min_y": 50, "max_x": 800, "max_y": 600}

        resolver._place_disconnected_elements([data], bounds)

        # Sidebar x should be left of min_x
        assert data.x < bounds["min_x"]
        assert data.y == bounds["min_y"]

    def test_non_data_disconnected_below_diagram(self):
        """Non-data disconnected elements are placed below the diagram."""
        resolver = PositionResolver()
        task = make_element("orphan", type="task", width=120, height=80)
        bounds = {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}

        resolver._place_disconnected_elements([task], bounds)

        assert task.x == bounds["min_x"]
        assert task.y == bounds["max_y"] + 50

    def test_empty_list_no_crash(self):
        """Empty disconnected list should be a no-op."""
        resolver = PositionResolver()
        bounds = {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}
        resolver._place_disconnected_elements([], bounds)  # no error


class TestAssignDimensions:
    """Tests for _assign_dimensions()."""

    def test_start_event_gets_36x36(self):
        """startEvent gets 36x36 dimensions."""
        resolver = PositionResolver()
        elem = make_element("s", type="startEvent")
        resolver._assign_dimensions(elem)
        assert elem.width == 36
        assert elem.height == 36

    def test_task_gets_120x80(self):
        """task gets 120x80 dimensions."""
        resolver = PositionResolver()
        elem = make_element("t", type="task")
        resolver._assign_dimensions(elem)
        assert elem.width == 120
        assert elem.height == 80

    def test_subprocess_gets_200x150(self):
        """subProcess gets 200x150 dimensions."""
        resolver = PositionResolver()
        elem = make_element("sp", type="subProcess")
        resolver._assign_dimensions(elem)
        assert elem.width == 200
        assert elem.height == 150

    def test_existing_dimensions_preserved(self):
        """Element with existing dimensions keeps them."""
        resolver = PositionResolver()
        elem = make_element("t", type="task", width=999, height=888)
        resolver._assign_dimensions(elem)
        assert elem.width == 999
        assert elem.height == 888

    def test_unknown_type_gets_default(self):
        """An unknown element type gets 120x80 default."""
        resolver = PositionResolver()
        elem = make_element("u", type="unknownType")
        resolver._assign_dimensions(elem)
        assert elem.width == 120
        assert elem.height == 80


class TestAssignFallbackPositions:
    """Tests for _assign_fallback_positions()."""

    def test_only_none_elements_get_fallback(self):
        """Elements with existing x are not overwritten."""
        resolver = PositionResolver()
        a = make_element("a", x=100, y=100, width=120, height=80)
        b = make_element("b", width=120, height=80)  # no coords
        bounds = {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}

        resolver._assign_fallback_positions([a, b], bounds)
        assert a.x == 100  # unchanged
        assert b.x is not None  # assigned

    def test_fallback_y_below_max_y(self):
        """Fallback Y is set below the max_y boundary."""
        resolver = PositionResolver()
        elem = make_element("e", width=120, height=80)
        bounds = {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}

        resolver._assign_fallback_positions([elem], bounds)
        assert elem.y == 700  # max_y + 100


class TestUseDiCoordinates:
    """Tests for _use_di_coordinates()."""

    def test_both_set_returns_true(self):
        resolver = PositionResolver()
        elem = make_element("t", x=10, y=20)
        assert resolver._use_di_coordinates(elem) is True

    def test_x_only_returns_false(self):
        resolver = PositionResolver()
        elem = make_element("t", x=10)
        assert resolver._use_di_coordinates(elem) is False

    def test_neither_set_returns_false(self):
        resolver = PositionResolver()
        elem = make_element("t")
        assert resolver._use_di_coordinates(elem) is False


class TestResolvePoolPositions:
    """Tests for _resolve_pool_positions()."""

    def test_no_pools_no_op(self):
        """Model with no pools should not raise."""
        resolver = PositionResolver()
        model = BPMNModel()
        resolver._resolve_pool_positions(model)
        # No crash

    def test_all_pools_positioned_skipped(self):
        """If all pools already have positions, nothing changes."""
        pool = make_pool("p1", x=50, y=50, width=600, height=200)
        model = BPMNModel(pools=[pool])
        resolver = PositionResolver()
        resolver._resolve_pool_positions(model)
        assert model.pools[0].x == 50
        assert model.pools[0].y == 50

    def test_unpositioned_pools_get_defaults(self):
        """Pools without positions get default coords."""
        pool = make_pool("p1")
        model = BPMNModel(pools=[pool])
        resolver = PositionResolver()
        resolver._resolve_pool_positions(model)
        assert pool.x == 50.0
        assert pool.y == 50.0
        assert pool.width == 600
        assert pool.height == 200

    def test_unpositioned_pool_below_positioned(self):
        """An unpositioned pool is placed below an existing positioned pool."""
        p1 = make_pool("p1", x=50, y=50, width=800, height=300)
        p2 = make_pool("p2")  # no coords
        model = BPMNModel(pools=[p1, p2])
        resolver = PositionResolver()
        resolver._resolve_pool_positions(model)

        assert p2.x == 50  # same x as p1
        assert p2.y == 400  # 50 + 300 + 50 gap


class TestAdjustSubprocessInternalPositions:
    """Tests for _adjust_subprocess_internal_positions()."""

    def test_internal_element_coords_made_relative(self):
        """Internal elements get coords relative to their subprocess."""
        sub = make_element(
            "sub1",
            type="subProcess",
            x=200,
            y=200,
            width=300,
            height=250,
            properties={"_is_subprocess": True},
        )
        internal = make_element(
            "int1", x=250, y=260, width=80, height=60, subprocess_id="sub1"
        )
        model = BPMNModel(elements=[sub, internal])
        resolver = PositionResolver()

        resolver._adjust_subprocess_internal_positions(model)

        # Relative coords: x = 250-200 = 50, y = 260-200-26 = 34
        assert internal.x == 50
        assert internal.y == 34

    def test_no_subprocesses_no_op(self):
        """If there are no subprocesses, nothing happens."""
        model = BPMNModel(elements=[make_element("t1", x=100, y=100)])
        resolver = PositionResolver()
        resolver._adjust_subprocess_internal_positions(model)
        assert model.elements[0].x == 100


class TestResolvePositionsConvenienceFunction:
    """Tests for the module-level resolve_positions() function."""

    def test_returns_model_with_positions(self):
        """resolve_positions creates a PositionResolver and resolves."""
        model = BPMNModel(
            elements=[
                make_element("s", type="startEvent"),
                make_element("e", type="endEvent"),
            ],
            flows=[make_flow("f1", "s", "e")],
        )
        resolved = resolve_positions(model, direction="LR")
        for elem in resolved.elements:
            assert elem.x is not None
            assert elem.y is not None

    def test_preserve_mode(self):
        """resolve_positions with use_layout='preserve' still assigns fallback."""
        model = BPMNModel(elements=[make_element("t1")])
        resolved = resolve_positions(model, use_layout="preserve")
        t = resolved.get_element_by_id("t1")
        assert t.x is not None
        assert t.y is not None


class TestPreserveLanePositions:
    """Tests for _preserve_lane_positions()."""

    def test_absolute_coords_converted_to_relative(self):
        """Element absolute coords become lane-relative in preserve mode."""
        pool = make_pool("pool1", x=50, y=50, width=800, height=400)
        lane = make_lane(
            "lane1", parent_pool_id="pool1", x=90, y=50, width=760, height=400
        )
        elem = make_element("t1", parent_id="lane1", x=200, y=150, width=120, height=80)
        model = BPMNModel(
            elements=[elem],
            pools=[pool],
            lanes=[lane],
            has_di_coordinates=True,
        )
        resolver = PositionResolver(use_layout="preserve")
        resolver._preserve_lane_positions(model)

        # Lane coords relative to pool
        assert lane.x == 40  # 90 - 50
        assert lane.y == 0  # 50 - 50

        # Element coords relative to lane (absolute lane coords: 90, 50)
        assert elem.x == 110  # 200 - 90
        assert elem.y == 100  # 150 - 50

    def test_laneless_pool_elements_relative_to_pool(self):
        """Elements in pool without lanes get pool-relative coords."""
        pool = make_pool("pool1", x=100, y=100, width=600, height=300)
        elem = make_element("t1", parent_id="pool1", x=250, y=200, width=120, height=80)
        model = BPMNModel(
            elements=[elem],
            pools=[pool],
            lanes=[],
            has_di_coordinates=True,
        )
        resolver = PositionResolver(use_layout="preserve")
        resolver._preserve_lane_positions(model)

        assert elem.x == 150  # 250 - 100
        assert elem.y == 100  # 200 - 100
