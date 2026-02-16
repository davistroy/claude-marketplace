"""Lane organization and coordinate calculation for BPMN elements."""

from typing import Dict, List

from .models import BPMNModel, BPMNElement, Lane
from .constants import LayoutConstants


class LaneOrganizer:
    """Organize elements into proper lane structure with correct positioning.

    Handles:
    - Grouping elements by their assigned lane
    - Calculating lane heights based on element content
    - Positioning lanes stacked vertically within pools
    - Adjusting element Y positions to fall within their lane
    - Resizing pools to fit all content
    - Converting absolute coordinates to lane-relative in preserve mode
    """

    def __init__(self, use_layout: str = "graphviz"):
        """Initialize lane organizer.

        Args:
            use_layout: Layout mode - "graphviz" or "preserve"
        """
        self.use_layout = use_layout

    def organize(self, model: BPMNModel) -> None:
        """Organize elements into proper lane structure.

        Main entry point. Groups elements by lane, calculates lane dimensions,
        positions lanes within pools, and adjusts element coordinates.

        Args:
            model: BPMN model to organize (modified in place)
        """
        if not model.lanes:
            return

        if self._should_preserve_di(model):
            self._preserve_lane_positions(model)
            return

        lane_elements = self._group_elements_by_lane(model)
        min_x, max_x = self._calculate_horizontal_extent(model.elements)
        lane_heights = self._calculate_lane_heights(lane_elements)
        pool_lanes = self._group_lanes_by_pool(model.lanes)

        lane_width = max_x - min_x + LayoutConstants.LANE_PADDING * 2
        lane_y_positions, pool_heights = self._calculate_lane_y_positions(
            pool_lanes, lane_heights
        )

        self._update_lane_dimensions(
            model.lanes, lane_y_positions, lane_heights, lane_width
        )
        self._adjust_element_positions(
            lane_elements, lane_y_positions, lane_heights, min_x
        )
        self._update_pool_dimensions(
            model, pool_heights, lane_width, lane_elements, min_x
        )
        self._position_laneless_pool_elements(model, min_x)

    # --- DI preserve mode ---

    def _should_preserve_di(self, model: BPMNModel) -> bool:
        """Check if DI coordinates should be preserved.

        Args:
            model: BPMN model

        Returns:
            True if preserve mode is active and all lanes have DI coordinates
        """
        if self.use_layout != "preserve" or not model.has_di_coordinates:
            return False

        return all(
            lane.x is not None
            and lane.y is not None
            and lane.width is not None
            and lane.height is not None
            for lane in model.lanes
        )

    def _preserve_lane_positions(self, model: BPMNModel) -> None:
        """Convert absolute DI coordinates to lane-relative coordinates.

        In BPMN DI, pools/lanes/elements all use absolute coordinates.
        In Draw.io, lanes are relative to pools, elements relative to lanes.

        Args:
            model: BPMN model with DI coordinates (modified in place)
        """
        lane_elements = self._group_elements_by_lane(model)

        for pool in model.pools:
            if pool.x is None or pool.y is None:
                continue
            self._convert_pool_lanes_to_relative(pool, model.lanes, lane_elements)

        self._convert_laneless_pool_elements(model)

    def _convert_pool_lanes_to_relative(
        self,
        pool,
        all_lanes: List[Lane],
        lane_elements: Dict[str, List[BPMNElement]],
    ) -> None:
        """Convert lane and element coords from absolute to pool-relative.

        Args:
            pool: Pool with absolute coordinates
            all_lanes: All model lanes
            lane_elements: Elements grouped by lane ID
        """
        pool_lanes = [ln for ln in all_lanes if ln.parent_pool_id == pool.id]

        for lane in pool_lanes:
            if lane.x is None or lane.y is None:
                continue

            lane_abs_x = lane.x
            lane_abs_y = lane.y

            lane.x = lane_abs_x - pool.x
            lane.y = lane_abs_y - pool.y

            for element in lane_elements.get(lane.id, []):
                if element.x is not None:
                    element.x = element.x - lane_abs_x
                if element.y is not None:
                    element.y = element.y - lane_abs_y

    def _convert_laneless_pool_elements(self, model: BPMNModel) -> None:
        """Convert elements in laneless pools to pool-relative coordinates.

        Args:
            model: BPMN model (modified in place)
        """
        for pool in model.pools:
            if pool.x is None or pool.y is None:
                continue

            pool_lanes = [ln for ln in model.lanes if ln.parent_pool_id == pool.id]
            if pool_lanes:
                continue

            for element in model.elements:
                if element.parent_id != pool.id:
                    continue
                if element.x is not None:
                    element.x = element.x - pool.x
                if element.y is not None:
                    element.y = element.y - pool.y

    # --- Layout mode helpers ---

    def _group_elements_by_lane(self, model: BPMNModel) -> Dict[str, List[BPMNElement]]:
        """Group elements by their parent lane.

        Args:
            model: BPMN model

        Returns:
            Dict mapping lane ID to list of elements in that lane
        """
        lane_elements: Dict[str, List[BPMNElement]] = {}
        for lane in model.lanes:
            lane_elements[lane.id] = []

        for element in model.elements:
            if element.parent_id and element.parent_id in lane_elements:
                lane_elements[element.parent_id].append(element)

        return lane_elements

    def _calculate_horizontal_extent(
        self, elements: List[BPMNElement]
    ) -> tuple[float, float]:
        """Calculate the horizontal extent (min_x, max_x) from all elements.

        Args:
            elements: All model elements

        Returns:
            Tuple of (min_x, max_x)
        """
        min_x = float("inf")
        max_x = float("-inf")

        for element in elements:
            if element.x is not None:
                min_x = min(min_x, element.x)
                max_x = max(max_x, element.x + (element.width or 120))

        if min_x == float("inf"):
            return 50.0, 800.0

        return min_x, max_x

    def _calculate_lane_heights(
        self, lane_elements: Dict[str, List[BPMNElement]]
    ) -> Dict[str, float]:
        """Calculate the height for each lane based on its elements.

        Args:
            lane_elements: Elements grouped by lane ID

        Returns:
            Dict mapping lane ID to calculated height
        """
        lane_min_height = 120.0
        lane_heights: Dict[str, float] = {}

        for lane_id, elements in lane_elements.items():
            if not elements:
                lane_heights[lane_id] = lane_min_height
                continue

            max_elem_height = max((e.height or 80) for e in elements)
            lane_heights[lane_id] = max(
                lane_min_height, max_elem_height + LayoutConstants.LANE_PADDING * 3
            )

        return lane_heights

    def _group_lanes_by_pool(self, lanes: List[Lane]) -> Dict[str, List[Lane]]:
        """Group lanes by their parent pool.

        Args:
            lanes: All model lanes

        Returns:
            Dict mapping pool ID to list of lanes
        """
        pool_lanes: Dict[str, List[Lane]] = {}
        for lane in lanes:
            pool_id = lane.parent_pool_id or "default"
            if pool_id not in pool_lanes:
                pool_lanes[pool_id] = []
            pool_lanes[pool_id].append(lane)
        return pool_lanes

    def _calculate_lane_y_positions(
        self,
        pool_lanes: Dict[str, List[Lane]],
        lane_heights: Dict[str, float],
    ) -> tuple[Dict[str, float], Dict[str, float]]:
        """Calculate Y positions for lanes within each pool.

        Lanes are stacked vertically starting at Y=0 within their pool.

        Args:
            pool_lanes: Lanes grouped by pool ID
            lane_heights: Heights for each lane

        Returns:
            Tuple of (lane_y_positions, pool_heights)
        """
        lane_y_positions: Dict[str, float] = {}
        pool_heights: Dict[str, float] = {}

        for pool_id, lanes in pool_lanes.items():
            current_y = 0.0
            for lane in lanes:
                if lane.id in lane_heights:
                    lane_y_positions[lane.id] = current_y
                    current_y += lane_heights[lane.id]
            pool_heights[pool_id] = current_y

        return lane_y_positions, pool_heights

    def _update_lane_dimensions(
        self,
        lanes: List[Lane],
        lane_y_positions: Dict[str, float],
        lane_heights: Dict[str, float],
        lane_width: float,
    ) -> None:
        """Update lane position and dimension attributes.

        Args:
            lanes: All model lanes (modified in place)
            lane_y_positions: Y position for each lane
            lane_heights: Height for each lane
            lane_width: Width for all lanes
        """
        lane_min_height = 120.0
        for lane in lanes:
            if lane.id in lane_y_positions:
                lane.x = LayoutConstants.POOL_HEADER_WIDTH
                lane.y = lane_y_positions[lane.id]
                lane.width = lane_width
                lane.height = lane_heights.get(lane.id, lane_min_height)

    def _adjust_element_positions(
        self,
        lane_elements: Dict[str, List[BPMNElement]],
        lane_y_positions: Dict[str, float],
        lane_heights: Dict[str, float],
        min_x: float,
    ) -> None:
        """Adjust element positions to be relative to their lane.

        In Draw.io, element coordinates are relative to their parent container.

        Args:
            lane_elements: Elements grouped by lane ID
            lane_y_positions: Y position for each lane
            lane_heights: Height for each lane
            min_x: Minimum X across all elements
        """
        padding = LayoutConstants.LANE_PADDING

        for lane_id, elements in lane_elements.items():
            if lane_id not in lane_y_positions:
                continue
            if not elements:
                continue

            lane_h = lane_heights[lane_id]
            self._position_elements_in_lane(elements, lane_h, min_x, padding)

    def _position_elements_in_lane(
        self,
        elements: List[BPMNElement],
        lane_h: float,
        min_x: float,
        padding: float,
    ) -> None:
        """Position a set of elements within a lane.

        Adjusts X to be lane-relative and scales Y to preserve relative
        positioning within the lane height.

        Args:
            elements: Elements to position (modified in place)
            lane_h: Height of the containing lane
            min_x: Minimum X across all elements (for offset calculation)
            padding: Lane padding value
        """
        y_values = [e.y for e in elements if e.y is not None]

        if y_values:
            self._scale_element_positions(elements, y_values, lane_h, min_x, padding)
        else:
            for element in elements:
                if element.x is not None:
                    element.x = element.x - min_x + padding

    def _scale_element_positions(
        self,
        elements: List[BPMNElement],
        y_values: List[float],
        lane_h: float,
        min_x: float,
        padding: float,
    ) -> None:
        """Scale element positions to fit within lane bounds.

        Args:
            elements: Elements to scale (modified in place)
            y_values: Non-None Y values from elements
            lane_h: Lane height
            min_x: Global minimum X
            padding: Lane padding
        """
        min_elem_y = min(y_values)
        max_elem_y = max(y_values)
        y_range = max_elem_y - min_elem_y
        max_elem_height = max((e.height or 80) for e in elements)

        for element in elements:
            if element.x is not None:
                element.x = element.x - min_x + padding

            if element.y is not None:
                if y_range > 0:
                    normalized = (element.y - min_elem_y) / y_range
                    usable_height = lane_h - padding * 2 - max_elem_height
                    element.y = padding + normalized * max(usable_height, 0)
                else:
                    elem_height = element.height or 80
                    element.y = (lane_h - elem_height) / 2

    def _update_pool_dimensions(
        self,
        model: BPMNModel,
        pool_heights: Dict[str, float],
        lane_width: float,
        lane_elements: Dict[str, List[BPMNElement]],
        min_x: float,
    ) -> None:
        """Update pool dimensions to fit their content.

        Pools are positioned vertically stacked with gaps.

        Args:
            model: BPMN model (pools modified in place)
            pool_heights: Calculated height for each pool
            lane_width: Width of lanes
            lane_elements: Elements grouped by lane ID
            min_x: Global minimum X
        """
        pool_header_width = LayoutConstants.POOL_HEADER_WIDTH
        lane_padding = LayoutConstants.LANE_PADDING
        current_pool_y = 50.0

        for pool in model.pools:
            pool.x = 50.0
            pool.y = current_pool_y
            pool.width = lane_width + pool_header_width if lane_width > 0 else 600

            pool.height = self._calculate_pool_height(
                pool, pool_heights, model.elements, lane_padding
            )
            pool.height = max(pool.height, 150)
            current_pool_y += pool.height + 50

    def _calculate_pool_height(
        self,
        pool,
        pool_heights: Dict[str, float],
        elements: List[BPMNElement],
        lane_padding: float,
    ) -> float:
        """Calculate the height for a single pool.

        Args:
            pool: Pool to calculate height for
            pool_heights: Pre-calculated heights from lane stacking
            elements: All model elements
            lane_padding: Padding constant

        Returns:
            Calculated pool height
        """
        if pool.id in pool_heights and pool_heights[pool.id] > 0:
            return pool_heights[pool.id]

        pool_elements = [e for e in elements if e.parent_id == pool.id]
        if pool_elements:
            max_elem_height = max((e.height or 80) for e in pool_elements)
            return max_elem_height + lane_padding * 3

        return 150.0

    def _position_laneless_pool_elements(self, model: BPMNModel, min_x: float) -> None:
        """Position elements in pools that have no lanes.

        Args:
            model: BPMN model (modified in place)
            min_x: Global minimum X
        """
        lane_padding = LayoutConstants.LANE_PADDING
        pool_header_width = LayoutConstants.POOL_HEADER_WIDTH

        for pool in model.pools:
            pool_lanes = [ln for ln in model.lanes if ln.parent_pool_id == pool.id]
            if pool_lanes:
                continue

            for element in model.elements:
                if element.parent_id != pool.id:
                    continue
                if element.x is not None:
                    element.x = element.x - min_x + lane_padding + pool_header_width
                if element.y is not None and pool.height:
                    element.y = pool.height / 2 - (element.height or 80) / 2
