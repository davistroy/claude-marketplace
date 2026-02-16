"""Characterization tests for waypoint calculation and conversion."""

from bpmn2drawio.models import BPMNElement, BPMNFlow
from bpmn2drawio.waypoints import (
    convert_bpmn_waypoints,
    generate_waypoints,
    create_waypoint_array,
    position_edge_label,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _el(
    id: str, x: float, y: float, w: float = 120, h: float = 80, **kw
) -> BPMNElement:
    """Shorthand to build a BPMNElement with coordinates."""
    return BPMNElement(id=id, type=kw.get("type", "task"), x=x, y=y, width=w, height=h)


def _flow(name=None, **kw) -> BPMNFlow:
    """Shorthand to build a BPMNFlow."""
    return BPMNFlow(
        id=kw.get("id", "f1"),
        type=kw.get("type", "sequenceFlow"),
        source_ref=kw.get("source_ref", "s"),
        target_ref=kw.get("target_ref", "t"),
        name=name,
    )


# ===================================================================
# 1. Straight horizontal path between adjacent elements
# ===================================================================


class TestStraightHorizontalPath:
    """Elements at the same y, target to the right of source."""

    def test_horizontal_adjacent_waypoints(self):
        """Two tasks side by side, same row -- path should be horizontal."""
        source = _el("s", x=100, y=200, w=120, h=80)
        target = _el("t", x=300, y=200, w=120, h=80)

        wps = generate_waypoints(source, target)

        # Source center: (160, 240), Target center: (360, 240)
        # tgt_x(360) > src_x(160) + half_w(60) => exit right edge: (220, 240)
        # src_x(160) < tgt_x(360) - half_w(60) => enter left edge: (300, 240)
        # |220-300|=80 > 10, |240-240|=0 <= 10 => NO intermediate bend
        assert wps[0] == (220, 240)  # right edge of source
        assert wps[-1] == (300, 240)  # left edge of target
        assert len(wps) == 2  # straight line, no bends

    def test_horizontal_adjacent_left_to_right(self):
        """Verify horizontal path is purely along x axis."""
        source = _el("s", x=0, y=100, w=100, h=60)
        target = _el("t", x=200, y=100, w=100, h=60)

        wps = generate_waypoints(source, target)

        # src center: (50, 130), tgt center: (250, 130)
        # exit right: (100, 130), enter left: (200, 130)
        # |100-200|=100 > 10, |130-130|=0 <= 10 => no bend
        assert len(wps) == 2
        assert wps[0][1] == wps[1][1]  # same y => horizontal


# ===================================================================
# 2. Straight vertical path
# ===================================================================


class TestStraightVerticalPath:
    """Elements aligned vertically, target directly below or above."""

    def test_vertical_downward(self):
        """Target directly below source, same x center."""
        source = _el("s", x=200, y=100, w=120, h=80)
        target = _el("t", x=200, y=300, w=120, h=80)

        wps = generate_waypoints(source, target)

        # src center: (260, 140), tgt center: (260, 340)
        # tgt_x(260) == src_x(260) so NOT > src_x + 60 (320)
        # tgt_x(260) == src_x(260) so NOT < src_x - 60 (200)
        # tgt_y(340) > src_y(140) => exit bottom: (260, 180)
        # For target entry:
        # src_x(260) == tgt_x(260) so NOT > tgt_x + 60 (320)
        # src_x(260) == tgt_x(260) so NOT < tgt_x - 60 (200)
        # src_y(140) > tgt_y(340)? No. => enter top: (260, 300)
        # |260-260|=0 <= 10 => no bend
        assert len(wps) == 2
        assert wps[0] == (260, 180)  # bottom edge of source
        assert wps[1] == (260, 300)  # top edge of target

    def test_vertical_upward(self):
        """Target directly above source."""
        source = _el("s", x=200, y=300, w=120, h=80)
        target = _el("t", x=200, y=100, w=120, h=80)

        wps = generate_waypoints(source, target)

        # src center: (260, 340), tgt center: (260, 140)
        # tgt_y(140) < src_y(340) => exit top: (260, 300)
        # src_y(340) > tgt_y(140) => enter bottom: (260, 180)
        assert len(wps) == 2
        assert wps[0] == (260, 300)  # top of source
        assert wps[1] == (260, 180)  # bottom of target


# ===================================================================
# 3. Path with one bend (L-shape)
# ===================================================================


class TestLShapePath:
    """Source and target offset on both axes but close enough that
    one of the exit/entry deltas is <= 10, producing a single bend."""

    def test_l_shape_when_exit_entry_nearly_aligned_on_one_axis(self):
        """If |exit.x - entry.x| <= 10 OR |exit.y - entry.y| <= 10
        no intermediate points are added, giving 2 waypoints (start+end).
        An L-shape requires the exit and entry to already form the bend."""
        # Place elements so exit y ~= entry y but x differs moderately
        source = _el("s", x=100, y=200, w=120, h=80)
        target = _el("t", x=300, y=195, w=120, h=80)  # only 5px y offset

        wps = generate_waypoints(source, target)

        # src center: (160, 240), tgt center: (360, 235)
        # exit right: (220, 240), enter left: (300, 235)
        # |220-300|=80 > 10, |240-235|=5 <= 10 => NO intermediate
        assert len(wps) == 2
        # The two endpoints themselves form the L-shape connection
        assert wps[0] == (220, 240)
        assert wps[1] == (300, 235)


# ===================================================================
# 4. Path with two bends (Z-shape)
# ===================================================================


class TestZShapePath:
    """Source and target offset enough on both axes that the algorithm
    inserts two intermediate waypoints forming a Z/S path."""

    def test_z_shape_right_and_down(self):
        """Target to the right and significantly below."""
        source = _el("s", x=100, y=100, w=120, h=80)
        target = _el("t", x=400, y=300, w=120, h=80)

        wps = generate_waypoints(source, target)

        # src center: (160, 140), tgt center: (460, 340)
        # exit right: (220, 140), enter left: (400, 340)
        # |220-400|=180 > 10, |140-340|=200 > 10 => intermediate
        # mid_x = (220+400)/2 = 310
        # bend 1: (310, 140), bend 2: (310, 340)
        assert len(wps) == 4
        assert wps[0] == (220, 140)  # source exit (right)
        assert wps[1] == (310.0, 140)  # first bend
        assert wps[2] == (310.0, 340)  # second bend
        assert wps[3] == (400, 340)  # target entry (left)

    def test_z_shape_left_and_up(self):
        """Target to the left and above -- reverse Z."""
        source = _el("s", x=400, y=300, w=120, h=80)
        target = _el("t", x=100, y=100, w=120, h=80)

        wps = generate_waypoints(source, target)

        # src center: (460, 340), tgt center: (160, 140)
        # tgt_x(160) < src_x(460) - 60 => exit left: (400, 340)
        # src_x(460) > tgt_x(160) + 60 => enter right: (220, 140)
        # |400-220|=180 > 10, |340-140|=200 > 10 => intermediate
        # mid_x = (400+220)/2 = 310
        assert len(wps) == 4
        assert wps[0] == (400, 340)
        assert wps[1] == (310.0, 340)
        assert wps[2] == (310.0, 140)
        assert wps[3] == (220, 140)

    def test_z_shape_intermediate_count(self):
        """Confirm exactly two intermediate waypoints are added."""
        source = _el("s", x=50, y=50, w=100, h=60)
        target = _el("t", x=300, y=250, w=100, h=60)

        wps = generate_waypoints(source, target)

        # src center: (100, 80), tgt center: (350, 280)
        # exit right: (150, 80), enter left: (300, 280)
        # |150-300|=150 > 10, |80-280|=200 > 10 => add 2 intermediates
        assert len(wps) == 4
        mid_x = (150 + 300) / 2  # 225
        assert wps[1] == (mid_x, 80)
        assert wps[2] == (mid_x, 280)


# ===================================================================
# 5. Cross-lane paths (different parent_ids, large y gap)
# ===================================================================


class TestCrossLanePaths:
    """Elements in different lanes have large vertical offsets."""

    def test_cross_lane_vertical_offset(self):
        """Elements in lanes 200px apart, offset horizontally too."""
        source = _el("s", x=100, y=100, w=120, h=80)
        source.parent_id = "lane1"
        target = _el("t", x=400, y=400, w=120, h=80)
        target.parent_id = "lane2"

        wps = generate_waypoints(source, target)

        # src center: (160, 140), tgt center: (460, 440)
        # exit right: (220, 140), enter left: (400, 440)
        # |220-400|=180 > 10, |140-440|=300 > 10 => Z with 2 bends
        assert len(wps) == 4
        assert wps[0][1] == 140  # exits at source y
        assert wps[3][1] == 440  # enters at target y

    def test_cross_lane_same_column(self):
        """Elements in different lanes but same x column."""
        source = _el("s", x=200, y=50, w=120, h=80)
        source.parent_id = "lane1"
        target = _el("t", x=200, y=350, w=120, h=80)
        target.parent_id = "lane2"

        wps = generate_waypoints(source, target)

        # src center: (260, 90), tgt center: (260, 390)
        # exit bottom: (260, 130), enter top: (260, 350)
        # |260-260|=0 <= 10 => no intermediate
        assert len(wps) == 2
        assert wps[0] == (260, 130)
        assert wps[1] == (260, 350)


# ===================================================================
# 6. Self-loop paths (source == target)
# ===================================================================


class TestSelfLoopPath:
    """Edge connects an element back to itself."""

    def test_self_loop_returns_exit_and_entry_only(self):
        """Self-loop: source and target are the same element object."""
        element = _el("loop", x=200, y=200, w=120, h=80)

        wps = generate_waypoints(element, element)

        # src center: (260, 240), tgt center: (260, 240)
        # tgt_x(260) NOT > src_x(260) + 60 (320)
        # tgt_x(260) NOT < src_x(260) - 60 (200)
        # tgt_y(240) NOT > src_y(240) => exit top: (260, 200)
        # For target:
        # src_x(260) NOT > tgt_x(260) + 60
        # src_x(260) NOT < tgt_x(260) - 60
        # src_y(240) NOT > tgt_y(240) => enter top: (260, 200)
        # |260-260|=0 <= 10 => no intermediates
        assert len(wps) == 2
        # Both waypoints are the same point (top center)
        assert wps[0] == wps[1]
        assert wps[0] == (260, 200)

    def test_self_loop_direct_routing(self):
        """Self-loop with direct routing yields same center twice."""
        element = _el("loop", x=200, y=200, w=120, h=80)

        wps = generate_waypoints(element, element, routing_style="direct")

        assert len(wps) == 2
        assert wps[0] == (260, 240)  # center
        assert wps[1] == (260, 240)  # same center


# ===================================================================
# 7. Boundary coordinates (elements at pool edge / origin)
# ===================================================================


class TestBoundaryCoordinates:
    """Elements at extreme positions (origin, large offsets)."""

    def test_element_at_origin(self):
        """Element at (0, 0)."""
        source = _el("s", x=0, y=0, w=120, h=80)
        target = _el("t", x=300, y=0, w=120, h=80)

        wps = generate_waypoints(source, target)

        # src center: (60, 40), tgt center: (360, 40)
        # exit right: (120, 40), enter left: (300, 40)
        assert wps[0] == (120, 40)
        assert wps[-1] == (300, 40)

    def test_element_with_no_coordinates(self):
        """Elements with None coordinates use defaults (0, default dims)."""
        source = BPMNElement(id="s", type="task")
        target = BPMNElement(id="t", type="task")

        wps = generate_waypoints(source, target)

        # All None => x=0,y=0,w=120,h=80 defaults
        # src center: (60, 40), tgt center: (60, 40)
        # Same center => top exit, top entry, same point
        assert len(wps) == 2
        assert wps[0] == wps[1]

    def test_element_with_none_width_height(self):
        """Element with coordinates but None dimensions uses defaults."""
        source = BPMNElement(id="s", type="task", x=100, y=100)
        target = BPMNElement(id="t", type="task", x=400, y=100)

        wps = generate_waypoints(source, target)

        # Defaults: w=120, h=80
        # src center: (160, 140), tgt center: (460, 140)
        # exit right: (220, 140), enter left: (400, 140)
        assert wps[0] == (220, 140)
        assert wps[-1] == (400, 140)

    def test_element_large_coordinates(self):
        """Elements at very large offsets still compute correctly."""
        source = _el("s", x=5000, y=3000, w=120, h=80)
        target = _el("t", x=5500, y=3000, w=120, h=80)

        wps = generate_waypoints(source, target)

        assert wps[0] == (5120, 3040)
        assert wps[1] == (5500, 3040)


# ===================================================================
# 8. Elements with existing DI waypoints
# ===================================================================


class TestExistingDIWaypoints:
    """convert_bpmn_waypoints handles existing DI data."""

    def test_convert_string_coordinates(self):
        """DI waypoints are typically strings -- convert to float tuples."""
        di = [
            {"x": "100.5", "y": "200.5"},
            {"x": "300.0", "y": "200.5"},
        ]
        result = convert_bpmn_waypoints(di)

        assert result == [(100.5, 200.5), (300.0, 200.5)]

    def test_convert_numeric_coordinates(self):
        """Numeric dict values should also work."""
        di = [{"x": 100, "y": 200}, {"x": 300, "y": 200}]
        result = convert_bpmn_waypoints(di)

        assert result == [(100.0, 200.0), (300.0, 200.0)]

    def test_convert_missing_keys_default_to_zero(self):
        """Missing x or y keys fall back to 0."""
        di = [{"x": "100"}, {"y": "200"}, {}]
        result = convert_bpmn_waypoints(di)

        assert result == [(100.0, 0.0), (0.0, 200.0), (0.0, 0.0)]

    def test_convert_empty_list(self):
        """Empty DI waypoints should return empty list."""
        assert convert_bpmn_waypoints([]) == []

    def test_convert_single_waypoint(self):
        """Single waypoint converts normally."""
        result = convert_bpmn_waypoints([{"x": "42", "y": "99"}])
        assert result == [(42.0, 99.0)]


# ===================================================================
# 9. create_waypoint_array XML generation
# ===================================================================


class TestCreateWaypointArray:
    """Tests for the XML Array element builder."""

    def test_array_with_intermediates(self):
        """Intermediate points (skip first/last) become mxPoint elements."""
        wps = [(10, 20), (30, 40), (50, 60), (70, 80)]
        array = create_waypoint_array(wps)

        assert array is not None
        assert array.tag == "Array"
        assert array.get("as") == "points"
        points = array.findall("mxPoint")
        assert len(points) == 2
        assert points[0].get("x") == "30"
        assert points[0].get("y") == "40"
        assert points[1].get("x") == "50"
        assert points[1].get("y") == "60"

    def test_array_returns_none_for_two_points(self):
        """Two-point path has no intermediates -> None."""
        assert create_waypoint_array([(0, 0), (100, 100)]) is None

    def test_array_with_three_points(self):
        """Three points -> one intermediate."""
        array = create_waypoint_array([(0, 0), (50, 50), (100, 100)])
        assert array is not None
        points = array.findall("mxPoint")
        assert len(points) == 1
        assert points[0].get("x") == "50"

    def test_array_with_five_points(self):
        """Five points -> three intermediates."""
        wps = [(0, 0), (25, 25), (50, 50), (75, 75), (100, 100)]
        array = create_waypoint_array(wps)
        assert array is not None
        assert len(array.findall("mxPoint")) == 3


# ===================================================================
# 10. position_edge_label
# ===================================================================


class TestPositionEdgeLabel:
    """Tests for edge label positioning."""

    def test_unnamed_flow_returns_empty_dict(self):
        """Flow with no name returns empty position."""
        flow = _flow(name=None)
        assert position_edge_label(flow, [(0, 0), (100, 100)]) == {}

    def test_two_waypoints_midpoint(self):
        """Label at midpoint of two-point edge."""
        flow = _flow(name="Yes")
        pos = position_edge_label(flow, [(100, 200), (300, 400)])

        assert pos["x"] == 200.0
        assert pos["y"] == 300.0
        assert pos["offset_y"] == -10

    def test_three_waypoints_uses_middle(self):
        """Odd number -> picks middle waypoint directly."""
        flow = _flow(name="label")
        pos = position_edge_label(flow, [(0, 0), (50, 100), (100, 200)])

        # mid_idx = 3 // 2 = 1
        assert pos["x"] == 50
        assert pos["y"] == 100

    def test_four_waypoints_uses_index_two(self):
        """Even number -> mid_idx = 4 // 2 = 2."""
        flow = _flow(name="label")
        pos = position_edge_label(flow, [(0, 0), (25, 25), (50, 50), (75, 75)])

        assert pos["x"] == 50
        assert pos["y"] == 50

    def test_single_waypoint_returns_relative(self):
        """Fewer than 2 waypoints => relative position."""
        flow = _flow(name="edge")
        pos = position_edge_label(flow, [(42, 99)])

        assert pos == {"x": 0.5, "y": 0}


# ===================================================================
# 11. Direct routing style
# ===================================================================


class TestDirectRouting:
    """generate_waypoints with routing_style='direct'."""

    def test_direct_routing_returns_centers(self):
        """Direct routing gives source center -> target center."""
        source = _el("s", x=100, y=100, w=120, h=80)
        target = _el("t", x=400, y=300, w=120, h=80)

        wps = generate_waypoints(source, target, routing_style="direct")

        assert len(wps) == 2
        assert wps[0] == (160, 140)  # src center
        assert wps[1] == (460, 340)  # tgt center

    def test_direct_routing_same_position(self):
        """Direct routing with overlapping elements."""
        el = _el("s", x=100, y=100, w=120, h=80)
        wps = generate_waypoints(el, el, routing_style="direct")

        assert wps[0] == wps[1]


# ===================================================================
# 12. Edge cases and non-square elements
# ===================================================================


class TestEdgeCases:
    """Miscellaneous edge-case characterization."""

    def test_small_event_elements(self):
        """Start/End events are typically 36x36."""
        source = _el("s", x=100, y=100, w=36, h=36, type="startEvent")
        target = _el("t", x=300, y=100, w=36, h=36, type="endEvent")

        wps = generate_waypoints(source, target)

        # src center: (118, 118), tgt center: (318, 118)
        # exit right: (136, 118), enter left: (300, 118)
        assert wps[0] == (136, 118)
        assert wps[-1] == (300, 118)

    def test_gateway_diamond_dimensions(self):
        """Gateways are often 50x50."""
        source = _el("s", x=200, y=200, w=50, h=50, type="exclusiveGateway")
        target = _el("t", x=400, y=200, w=120, h=80, type="task")

        wps = generate_waypoints(source, target)

        # src center: (225, 225), tgt center: (460, 240)
        # exit right: (250, 225), enter left: (400, 240)
        # |250-400|=150 > 10, |225-240|=15 > 10 => Z-shape
        assert len(wps) == 4
        assert wps[0] == (250, 225)
        assert wps[3] == (400, 240)

    def test_target_left_of_source(self):
        """Target element is to the left of source."""
        source = _el("s", x=400, y=100, w=120, h=80)
        target = _el("t", x=100, y=100, w=120, h=80)

        wps = generate_waypoints(source, target)

        # src center: (460, 140), tgt center: (160, 140)
        # tgt_x(160) < src_x(460) - 60 => exit left: (400, 140)
        # src_x(460) > tgt_x(160) + 60 => enter right: (220, 140)
        # |400-220|=180 > 10, |140-140|=0 <= 10 => no bend
        assert len(wps) == 2
        assert wps[0] == (400, 140)
        assert wps[1] == (220, 140)
