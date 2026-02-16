"""Tests for BoundaryPositioner class.

Tests the extracted boundary event positioning, subprocess coordinate
adjustment, and laneless pool parent assignment logic.
"""

from bpmn2drawio.models import BPMNElement, BPMNModel, Pool, Lane
from bpmn2drawio.boundary_positioner import BoundaryPositioner


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
    id, parent_pool_id="", name=None, x=None, y=None, width=None, height=None
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
    )


# ===========================================================================
# 1. position_boundary_events()
# ===========================================================================


class TestPositionBoundaryEvents:
    """Tests for BoundaryPositioner.position_boundary_events()."""

    def _positioner(self):
        return BoundaryPositioner()

    def test_boundary_attached_via_property(self):
        """Boundary event uses attachedToRef property to find parent."""
        task = make_element(
            "task1", type="userTask", x=200, y=200, width=120, height=80
        )
        boundary = make_element(
            "b1",
            type="boundaryEvent",
            x=0,
            y=0,
            width=36,
            height=36,
            properties={"attachedToRef": "task1"},
        )
        model = BPMNModel(elements=[task, boundary])

        self._positioner().position_boundary_events(model)

        assert boundary.parent_id == "task1"
        assert boundary.y == 80 - 18  # attached_height - event_height/2

    def test_boundary_x_starts_at_20(self):
        """First boundary event x starts at offset 20."""
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

        self._positioner().position_boundary_events(model)

        assert boundary.x == 20

    def test_multiple_boundaries_spaced_apart(self):
        """Multiple boundary events on the same task are spaced by 50px."""
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

        self._positioner().position_boundary_events(model)

        assert b1.x == 20
        assert b2.x == 70

    def test_no_attached_ref_skipped(self):
        """Boundary event without attachedToRef and no ID match keeps no parent."""
        boundary = make_element(
            "orphan", type="boundaryEvent", x=999, y=999, width=36, height=36
        )
        model = BPMNModel(elements=[boundary])

        self._positioner().position_boundary_events(model)

        assert boundary.parent_id is None

    def test_id_pattern_fallback(self):
        """Boundary event falls back to ID pattern matching."""
        task = make_element("myTask", type="task", x=100, y=100, width=120, height=80)
        boundary = make_element(
            "myTaskBoundary", type="boundaryEvent", width=36, height=36
        )
        model = BPMNModel(elements=[task, boundary])

        self._positioner().position_boundary_events(model)

        assert boundary.parent_id == "myTask"

    def test_non_boundary_events_ignored(self):
        """Non-boundary event elements are not modified."""
        task = make_element("task1", type="task", x=100, y=100, width=120, height=80)
        model = BPMNModel(elements=[task])

        self._positioner().position_boundary_events(model)

        assert task.parent_id is None
        assert task.x == 100
        assert task.y == 100

    def test_empty_model_no_crash(self):
        """Empty model should not raise."""
        model = BPMNModel()
        self._positioner().position_boundary_events(model)


# ===========================================================================
# 2. adjust_subprocess_internal_positions()
# ===========================================================================


class TestAdjustSubprocessInternalPositions:
    """Tests for BoundaryPositioner.adjust_subprocess_internal_positions()."""

    def _positioner(self):
        return BoundaryPositioner()

    def test_internal_coords_made_relative(self):
        """Internal element gets coordinates relative to subprocess."""
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

        self._positioner().adjust_subprocess_internal_positions(model)

        assert internal.x == 50  # 250 - 200
        assert internal.y == 34  # 260 - 200 - 26

    def test_no_subprocesses_no_op(self):
        """Without subprocesses nothing changes."""
        elem = make_element("t1", x=100, y=100)
        model = BPMNModel(elements=[elem])

        self._positioner().adjust_subprocess_internal_positions(model)

        assert elem.x == 100
        assert elem.y == 100

    def test_internal_clamped_to_subprocess_bounds(self):
        """Internal element coordinates are clamped within subprocess bounds."""
        sub = make_element(
            "sub1",
            type="subProcess",
            x=100,
            y=100,
            width=200,
            height=150,
            properties={"_is_subprocess": True},
        )
        # Element far outside subprocess
        internal = make_element(
            "int1", x=500, y=500, width=80, height=60, subprocess_id="sub1"
        )
        model = BPMNModel(elements=[sub, internal])

        self._positioner().adjust_subprocess_internal_positions(model)

        # Should be clamped to max valid position
        assert internal.x <= (200 - 80)  # subprocess width - element width
        assert internal.y <= (
            150 - 26 - 60
        )  # subprocess height - header - element height

    def test_subprocess_id_from_properties(self):
        """subprocess_id can also come from properties dict."""
        sub = make_element(
            "sub1",
            type="subProcess",
            x=100,
            y=100,
            width=200,
            height=150,
            properties={"_is_subprocess": True},
        )
        internal = make_element(
            "int1",
            x=150,
            y=150,
            width=80,
            height=60,
            properties={"subprocess_id": "sub1"},
        )
        model = BPMNModel(elements=[sub, internal])

        self._positioner().adjust_subprocess_internal_positions(model)

        assert internal.x == 50  # 150 - 100

    def test_none_coords_skipped(self):
        """Elements with None coords in subprocess context are not adjusted."""
        sub = make_element(
            "sub1",
            type="subProcess",
            x=100,
            y=100,
            width=200,
            height=150,
            properties={"_is_subprocess": True},
        )
        internal = make_element("int1", subprocess_id="sub1")  # x=None, y=None
        model = BPMNModel(elements=[sub, internal])

        self._positioner().adjust_subprocess_internal_positions(model)

        assert internal.x is None
        assert internal.y is None


# ===========================================================================
# 3. assign_pool_parents_for_laneless_pools()
# ===========================================================================


class TestAssignPoolParentsForLanelessPools:
    """Tests for BoundaryPositioner.assign_pool_parents_for_laneless_pools()."""

    def _positioner(self):
        return BoundaryPositioner()

    def test_single_laneless_pool_assigns_parent(self):
        """Elements in a single laneless pool get pool as parent."""
        pool = make_pool("pool1", process_ref="proc1")
        elements = [make_element("t1"), make_element("t2")]
        model = BPMNModel(elements=elements, pools=[pool])

        self._positioner().assign_pool_parents_for_laneless_pools(model)

        for elem in model.elements:
            assert elem.parent_id == "pool1"

    def test_no_pools_no_op(self):
        """Model without pools does nothing."""
        model = BPMNModel(elements=[make_element("t1")])

        self._positioner().assign_pool_parents_for_laneless_pools(model)

        assert model.elements[0].parent_id is None

    def test_pool_with_lanes_skipped(self):
        """Pools that have lanes are not considered laneless."""
        pool = make_pool("pool1", process_ref="proc1")
        lane = make_lane("lane1", parent_pool_id="pool1")
        elements = [make_element("t1")]
        model = BPMNModel(elements=elements, pools=[pool], lanes=[lane])

        self._positioner().assign_pool_parents_for_laneless_pools(model)

        # Element should NOT get pool1 as parent (it has lanes)
        assert model.elements[0].parent_id is None

    def test_existing_parent_preserved(self):
        """Elements with existing parent_id are not overwritten."""
        pool = make_pool("pool1", process_ref="proc1")
        elem = make_element("t1", parent_id="some_other_parent")
        model = BPMNModel(elements=[elem], pools=[pool])

        self._positioner().assign_pool_parents_for_laneless_pools(model)

        assert elem.parent_id == "some_other_parent"

    def test_subprocess_internals_skipped(self):
        """Elements inside subprocesses are not assigned to pool."""
        pool = make_pool("pool1", process_ref="proc1")
        elem = make_element("int1", subprocess_id="sub1")
        model = BPMNModel(elements=[elem], pools=[pool])

        self._positioner().assign_pool_parents_for_laneless_pools(model)

        assert elem.parent_id is None

    def test_pool_without_process_ref_skipped(self):
        """Laneless pool without process_ref does not assign parents."""
        pool = make_pool("pool1")  # No process_ref
        elem = make_element("t1")
        model = BPMNModel(elements=[elem], pools=[pool])

        self._positioner().assign_pool_parents_for_laneless_pools(model)

        assert elem.parent_id is None
