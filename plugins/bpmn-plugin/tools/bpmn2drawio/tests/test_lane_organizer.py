"""Tests for LaneOrganizer class.

Tests the extracted lane organization, height calculation, element positioning,
and DI-preserve coordinate conversion logic.
"""

from bpmn2drawio.models import BPMNElement, BPMNModel, Pool, Lane
from bpmn2drawio.lane_organizer import LaneOrganizer
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
# 1. organize() — main entry point
# ===========================================================================


class TestOrganize:
    """Tests for LaneOrganizer.organize()."""

    def test_no_lanes_no_op(self):
        """Model without lanes is a no-op."""
        organizer = LaneOrganizer()
        model = BPMNModel(elements=[make_element("t1", x=100, y=100)])

        organizer.organize(model)

        assert model.elements[0].x == 100
        assert model.elements[0].y == 100

    def test_elements_grouped_into_correct_lanes(self):
        """Elements with parent_id matching a lane.id are grouped correctly."""
        pool = make_pool("pool1", process_ref="proc1")
        lane_a = make_lane("laneA", parent_pool_id="pool1")
        lane_b = make_lane("laneB", parent_pool_id="pool1")
        elements = [
            make_element("t1", parent_id="laneA", x=100, y=100, width=120, height=80),
            make_element("t2", parent_id="laneB", x=300, y=300, width=120, height=80),
        ]
        model = BPMNModel(
            elements=elements, flows=[], pools=[pool], lanes=[lane_a, lane_b]
        )

        LaneOrganizer().organize(model)

        assert model.lanes[0].x is not None
        assert model.lanes[1].x is not None

    def test_empty_lane_gets_minimum_height(self):
        """A lane with no elements gets 120px minimum height."""
        pool = make_pool("pool1", process_ref="proc1")
        lane = make_lane("laneA", parent_pool_id="pool1")
        model = BPMNModel(elements=[], flows=[], pools=[pool], lanes=[lane])

        LaneOrganizer().organize(model)

        assert model.lanes[0].height >= 120

    def test_lane_height_grows_with_tall_elements(self):
        """Lane height accommodates the tallest element plus padding."""
        pool = make_pool("pool1", process_ref="proc1")
        lane = make_lane("laneA", parent_pool_id="pool1")
        elements = [
            make_element("big", parent_id="laneA", x=50, y=50, width=200, height=200),
        ]
        model = BPMNModel(elements=elements, flows=[], pools=[pool], lanes=[lane])

        LaneOrganizer().organize(model)

        assert model.lanes[0].height >= 200

    def test_lane_x_equals_pool_header_width(self):
        """Lane x should equal LayoutConstants.POOL_HEADER_WIDTH."""
        pool = make_pool("pool1", process_ref="proc1")
        lane = make_lane("laneA", parent_pool_id="pool1")
        elements = [
            make_element("t1", parent_id="laneA", x=100, y=100, width=120, height=80),
        ]
        model = BPMNModel(elements=elements, flows=[], pools=[pool], lanes=[lane])

        LaneOrganizer().organize(model)

        assert model.lanes[0].x == LayoutConstants.POOL_HEADER_WIDTH

    def test_multiple_lanes_sequential_y(self):
        """Lanes in the same pool get sequential Y positions starting at 0."""
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

        LaneOrganizer().organize(model)

        y_positions = [lane.y for lane in model.lanes]
        assert y_positions[0] == 0
        for i in range(1, len(y_positions)):
            assert y_positions[i] > y_positions[i - 1]

    def test_pool_dimensions_updated(self):
        """Pool dimensions are set after organize."""
        pool = make_pool("pool1", process_ref="proc1")
        lane = make_lane("laneA", parent_pool_id="pool1")
        elements = [
            make_element("t1", parent_id="laneA", x=100, y=100, width=120, height=80),
        ]
        model = BPMNModel(elements=elements, flows=[], pools=[pool], lanes=[lane])

        LaneOrganizer().organize(model)

        assert pool.x is not None
        assert pool.y is not None
        assert pool.width is not None
        assert pool.height is not None
        assert pool.height >= 150  # minimum pool height


# ===========================================================================
# 2. Internal helper methods
# ===========================================================================


class TestCalculateHorizontalExtent:
    """Tests for _calculate_horizontal_extent()."""

    def test_returns_defaults_with_no_coords(self):
        """No positioned elements returns defaults (50, 800)."""
        organizer = LaneOrganizer()
        result = organizer._calculate_horizontal_extent([make_element("t1")])
        assert result == (50.0, 800.0)

    def test_calculates_from_element_positions(self):
        """Extent calculated from element x + width."""
        organizer = LaneOrganizer()
        elements = [
            make_element("a", x=100, width=120),
            make_element("b", x=500, width=120),
        ]
        min_x, max_x = organizer._calculate_horizontal_extent(elements)
        assert min_x == 100
        assert max_x == 620  # 500 + 120


class TestCalculateLaneHeights:
    """Tests for _calculate_lane_heights()."""

    def test_empty_lane_gets_minimum(self):
        """Empty lane gets 120 min height."""
        organizer = LaneOrganizer()
        heights = organizer._calculate_lane_heights({"lane1": []})
        assert heights["lane1"] == 120.0

    def test_tall_element_increases_height(self):
        """Lane with a tall element gets taller than minimum."""
        organizer = LaneOrganizer()
        elements = [make_element("big", height=200)]
        heights = organizer._calculate_lane_heights({"lane1": elements})
        assert heights["lane1"] >= 200

    def test_multiple_lanes_independent(self):
        """Each lane gets its own height calculation."""
        organizer = LaneOrganizer()
        lane_elements = {
            "lane1": [make_element("small", height=40)],
            "lane2": [make_element("big", height=300)],
        }
        heights = organizer._calculate_lane_heights(lane_elements)
        assert heights["lane1"] < heights["lane2"]


class TestGroupLanesByPool:
    """Tests for _group_lanes_by_pool()."""

    def test_lanes_grouped_correctly(self):
        """Lanes are grouped by their parent_pool_id."""
        organizer = LaneOrganizer()
        lanes = [
            make_lane("l1", parent_pool_id="pool1"),
            make_lane("l2", parent_pool_id="pool1"),
            make_lane("l3", parent_pool_id="pool2"),
        ]
        result = organizer._group_lanes_by_pool(lanes)
        assert len(result["pool1"]) == 2
        assert len(result["pool2"]) == 1

    def test_lane_without_pool_uses_default(self):
        """Lane without parent_pool_id goes into 'default' group."""
        organizer = LaneOrganizer()
        lanes = [make_lane("l1")]  # parent_pool_id=""
        result = organizer._group_lanes_by_pool(lanes)
        assert "default" in result


class TestCalculateLaneYPositions:
    """Tests for _calculate_lane_y_positions()."""

    def test_lanes_stacked_from_zero(self):
        """Lanes start at y=0 and stack vertically."""
        organizer = LaneOrganizer()
        lane_a = make_lane("lA", parent_pool_id="pool1")
        lane_b = make_lane("lB", parent_pool_id="pool1")
        pool_lanes = {"pool1": [lane_a, lane_b]}
        lane_heights = {"lA": 120.0, "lB": 150.0}

        y_positions, pool_heights = organizer._calculate_lane_y_positions(
            pool_lanes, lane_heights
        )

        assert y_positions["lA"] == 0.0
        assert y_positions["lB"] == 120.0
        assert pool_heights["pool1"] == 270.0


# ===========================================================================
# 3. _preserve_lane_positions() — DI coordinate preservation
# ===========================================================================


class TestPreserveLanePositions:
    """Tests for DI coordinate preservation mode."""

    def test_absolute_coords_converted_to_relative(self):
        """Absolute DI coords become lane-relative in preserve mode."""
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

        organizer = LaneOrganizer(use_layout="preserve")
        organizer._preserve_lane_positions(model)

        # Lane relative to pool
        assert lane.x == 40  # 90 - 50
        assert lane.y == 0  # 50 - 50

        # Element relative to lane (absolute lane was at 90, 50)
        assert elem.x == 110  # 200 - 90
        assert elem.y == 100  # 150 - 50

    def test_laneless_pool_elements_made_relative(self):
        """Elements in laneless pools get pool-relative coords."""
        pool = make_pool("pool1", x=100, y=100, width=600, height=300)
        elem = make_element("t1", parent_id="pool1", x=250, y=200, width=120, height=80)
        model = BPMNModel(
            elements=[elem],
            pools=[pool],
            lanes=[],
            has_di_coordinates=True,
        )

        organizer = LaneOrganizer(use_layout="preserve")
        organizer._preserve_lane_positions(model)

        assert elem.x == 150  # 250 - 100
        assert elem.y == 100  # 200 - 100

    def test_should_preserve_di_false_in_graphviz_mode(self):
        """Preserve check returns False when use_layout is graphviz."""
        organizer = LaneOrganizer(use_layout="graphviz")
        model = BPMNModel(
            has_di_coordinates=True,
            lanes=[make_lane("l1", x=0, y=0, width=100, height=100)],
        )
        assert organizer._should_preserve_di(model) is False

    def test_should_preserve_di_false_without_di(self):
        """Preserve check returns False when model has no DI coordinates."""
        organizer = LaneOrganizer(use_layout="preserve")
        model = BPMNModel(
            has_di_coordinates=False,
            lanes=[make_lane("l1", x=0, y=0, width=100, height=100)],
        )
        assert organizer._should_preserve_di(model) is False

    def test_should_preserve_di_false_with_incomplete_lanes(self):
        """Preserve check returns False when lanes lack dimension data."""
        organizer = LaneOrganizer(use_layout="preserve")
        model = BPMNModel(
            has_di_coordinates=True,
            lanes=[
                make_lane("l1", x=0, y=0)  # no width/height
            ],
        )
        assert organizer._should_preserve_di(model) is False

    def test_should_preserve_di_true_when_all_conditions_met(self):
        """Preserve check returns True with preserve mode, DI, and complete lanes."""
        organizer = LaneOrganizer(use_layout="preserve")
        model = BPMNModel(
            has_di_coordinates=True,
            lanes=[make_lane("l1", x=0, y=0, width=100, height=100)],
        )
        assert organizer._should_preserve_di(model) is True


# ===========================================================================
# 4. Laneless pool element positioning
# ===========================================================================


class TestPositionLanelessPoolElements:
    """Tests for _position_laneless_pool_elements()."""

    def test_elements_positioned_relative_to_pool(self):
        """Elements in a laneless pool get pool-relative X and centered Y."""
        pool = make_pool("pool1", x=50.0, y=50.0, width=600, height=200)
        elem = make_element("t1", parent_id="pool1", x=200, y=100, width=120, height=80)
        model = BPMNModel(elements=[elem], pools=[pool], lanes=[])

        organizer = LaneOrganizer()
        organizer._position_laneless_pool_elements(model, min_x=100.0)

        # X adjusted: x - min_x + padding + header_width
        expected_x = (
            200 - 100 + LayoutConstants.LANE_PADDING + LayoutConstants.POOL_HEADER_WIDTH
        )
        assert elem.x == expected_x

        # Y centered in pool
        expected_y = 200 / 2 - 80 / 2
        assert elem.y == expected_y

    def test_pool_with_lanes_skipped(self):
        """Pool with lanes does not reposition elements."""
        pool = make_pool("pool1", x=50.0, y=50.0, width=600, height=200)
        lane = make_lane("lane1", parent_pool_id="pool1")
        elem = make_element("t1", parent_id="pool1", x=200, y=100, width=120, height=80)
        model = BPMNModel(elements=[elem], pools=[pool], lanes=[lane])

        organizer = LaneOrganizer()
        organizer._position_laneless_pool_elements(model, min_x=100.0)

        # Should be unchanged since pool has lanes
        assert elem.x == 200
        assert elem.y == 100
