"""Position resolver for BPMN elements."""

from typing import Optional, List, Dict, Tuple, Set
from copy import deepcopy

from .models import BPMNModel, BPMNElement
from .layout import LayoutEngine
from .constants import ELEMENT_DIMENSIONS, DATA_TYPES
from .boundary_positioner import BoundaryPositioner
from .lane_organizer import LaneOrganizer


class PositionResolver:
    """Resolve element positions from DI or layout engine."""

    def __init__(
        self,
        layout_engine: Optional[LayoutEngine] = None,
        use_layout: str = "graphviz",
    ):
        """Initialize position resolver.

        Args:
            layout_engine: Layout engine to use for calculating positions
            use_layout: Layout mode - "graphviz" or "preserve"
        """
        self.layout_engine = layout_engine or LayoutEngine()
        self.use_layout = use_layout
        self._boundary_positioner = BoundaryPositioner()
        self._lane_organizer = LaneOrganizer(use_layout=use_layout)

    def resolve(self, model: BPMNModel) -> BPMNModel:
        """Ensure all elements have positions.

        Creates a copy of the model with resolved positions.

        Args:
            model: BPMN model

        Returns:
            New BPMNModel with all positions resolved
        """
        # Create a deep copy to avoid modifying the original
        resolved_model = deepcopy(model)

        # First resolve pool positions (needed for element placement context)
        self._resolve_pool_positions(resolved_model)

        # Assign dimensions to all elements first
        for element in resolved_model.elements:
            self._assign_dimensions(element)

        # Get diagram bounds from elements with DI coordinates
        bounds = self._get_di_bounds(resolved_model)

        # Separate elements by whether they have DI coordinates
        with_di = []
        needs_layout = []
        for element in resolved_model.elements:
            if self._use_di_coordinates(element):
                with_di.append(element)
            else:
                needs_layout.append(element)

        # Only calculate layout if we have elements needing it
        if needs_layout and self.use_layout == "graphviz":
            self._layout_elements(needs_layout, with_di, resolved_model, bounds)

        # Ensure all elements have some position (final fallback)
        self._assign_fallback_positions(resolved_model.elements, bounds)

        # Delegate to BoundaryPositioner
        self._boundary_positioner.position_boundary_events(resolved_model)
        self._boundary_positioner.adjust_subprocess_internal_positions(resolved_model)
        self._boundary_positioner.assign_pool_parents_for_laneless_pools(resolved_model)

        # Delegate to LaneOrganizer
        if resolved_model.lanes:
            self._lane_organizer.organize(resolved_model)

        return resolved_model

    def _layout_elements(
        self,
        needs_layout: List[BPMNElement],
        with_di: List[BPMNElement],
        model: BPMNModel,
        bounds: Dict[str, float],
    ) -> None:
        """Layout elements that lack DI coordinates.

        Args:
            needs_layout: Elements needing position calculation
            with_di: Elements with existing DI coordinates
            model: BPMN model
            bounds: Diagram bounds
        """
        connected_ids = self._find_connected_elements(needs_layout, model.flows)

        connected_elements = [e for e in needs_layout if e.id in connected_ids]
        disconnected_elements = [e for e in needs_layout if e.id not in connected_ids]

        if not with_di and connected_elements:
            positions = self.layout_engine.calculate_layout(model.elements, model.flows)
            self._apply_layout_positions(model.elements, positions)
        elif connected_elements:
            self._place_connected_elements(
                connected_elements, with_di, model.flows, bounds
            )

        self._place_disconnected_elements(disconnected_elements, bounds)

    def _apply_layout_positions(
        self,
        elements: List[BPMNElement],
        positions: Dict[str, tuple],
    ) -> None:
        """Apply calculated layout positions to elements missing coordinates.

        Args:
            elements: All model elements (modified in place)
            positions: Mapping of element ID to (x, y) position
        """
        for element in elements:
            if element.id not in positions:
                continue
            x, y = positions[element.id]
            if element.x is None:
                element.x = x
            if element.y is None:
                element.y = y

    def _resolve_pool_positions(self, model: BPMNModel) -> None:
        """Resolve positions for pools without DI coordinates.

        Args:
            model: BPMN model (modified in place)
        """
        if not model.pools:
            return

        pools_with_pos = [p for p in model.pools if p.x is not None and p.y is not None]
        pools_without_pos = [p for p in model.pools if p.x is None or p.y is None]

        if not pools_without_pos:
            return

        if pools_with_pos:
            min_x = min(p.x for p in pools_with_pos)
            max_y = max((p.y or 0) + (p.height or 200) for p in pools_with_pos)
            typical_width = max(p.width or 600 for p in pools_with_pos)

            for pool in pools_without_pos:
                pool.x = min_x
                pool.y = max_y + 50
                pool.width = pool.width or typical_width
                pool.height = pool.height or 200
                max_y = pool.y + pool.height
        else:
            y = 50.0
            for pool in pools_without_pos:
                pool.x = 50.0
                pool.y = y
                pool.width = pool.width or 600
                pool.height = pool.height or 200
                y += pool.height + 50

    def _get_di_bounds(self, model: BPMNModel) -> Dict[str, float]:
        """Get bounding box of all elements with DI coordinates.

        Args:
            model: BPMN model

        Returns:
            Dictionary with min_x, min_y, max_x, max_y
        """
        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for element in model.elements:
            if element.x is not None and element.y is not None:
                min_x = min(min_x, element.x)
                min_y = min(min_y, element.y)
                max_x = max(max_x, element.x + (element.width or 120))
                max_y = max(max_y, element.y + (element.height or 80))

        for pool in model.pools:
            if pool.x is not None and pool.y is not None:
                min_x = min(min_x, pool.x)
                min_y = min(min_y, pool.y)
                max_x = max(max_x, pool.x + (pool.width or 600))
                max_y = max(max_y, pool.y + (pool.height or 200))

        for lane in model.lanes:
            if lane.x is not None and lane.y is not None:
                min_x = min(min_x, lane.x)
                min_y = min(min_y, lane.y)
                max_x = max(max_x, lane.x + (lane.width or 560))
                max_y = max(max_y, lane.y + (lane.height or 200))

        if min_x == float("inf"):
            return {"min_x": 50, "min_y": 50, "max_x": 800, "max_y": 600}

        return {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y,
        }

    def _find_connected_elements(
        self,
        elements: List[BPMNElement],
        flows: list,
    ) -> Set[str]:
        """Find elements that are connected to flows, including subprocess internals.

        Args:
            elements: Elements to check
            flows: All flows in model

        Returns:
            Set of element IDs that participate in flows or are subprocess internals
        """
        element_ids = {e.id for e in elements}
        connected = set()

        for flow in flows:
            if flow.source_ref in element_ids:
                connected.add(flow.source_ref)
            if flow.target_ref in element_ids:
                connected.add(flow.target_ref)

        subprocess_ids = set()
        for e in elements:
            if e.properties.get("_is_subprocess"):
                subprocess_ids.add(e.id)

        for e in elements:
            subprocess_id = e.subprocess_id or e.properties.get("subprocess_id")
            if subprocess_id:
                if subprocess_id in connected or subprocess_id in subprocess_ids:
                    connected.add(e.id)
                    connected.add(subprocess_id)

        return connected

    def _place_connected_elements(
        self,
        elements: List[BPMNElement],
        elements_with_di: List[BPMNElement],
        flows: list,
        bounds: Dict[str, float],
    ) -> None:
        """Position elements without DI relative to connected elements with DI.

        Args:
            elements: Elements without DI that need positioning
            elements_with_di: Elements that have DI coordinates
            flows: All flows in model
            bounds: Diagram bounds
        """
        if not elements:
            return

        di_elements = {e.id: e for e in elements_with_di}
        positioned = set()
        unpositioned = list(elements)

        max_iterations = len(elements) * 2
        iteration = 0

        while unpositioned and iteration < max_iterations:
            iteration += 1
            for element in list(unpositioned):
                pos = self._find_position_from_neighbors(
                    element, flows, di_elements, positioned, bounds
                )
                if pos:
                    element.x, element.y = pos
                    positioned.add(element.id)
                    di_elements[element.id] = element
                    unpositioned.remove(element)

        if unpositioned:
            x = bounds["min_x"]
            y = bounds["max_y"] + 50
            for element in unpositioned:
                element.x = x
                element.y = y
                x += (element.width or 120) + 30
                if x > bounds["max_x"]:
                    x = bounds["min_x"]
                    y += 100

    def _find_position_from_neighbors(
        self,
        element: BPMNElement,
        flows: list,
        positioned_elements: Dict[str, BPMNElement],
        already_positioned: Set[str],
        bounds: Dict[str, float],
    ) -> Optional[Tuple[float, float]]:
        """Try to find position based on connected neighbors.

        Args:
            element: Element to position
            flows: All flows
            positioned_elements: Elements with known positions
            already_positioned: IDs of elements we've already positioned this round
            bounds: Diagram bounds

        Returns:
            (x, y) position or None if no positioned neighbor found
        """
        incoming_neighbors = []
        outgoing_neighbors = []

        for flow in flows:
            if flow.target_ref == element.id and flow.source_ref in positioned_elements:
                incoming_neighbors.append(positioned_elements[flow.source_ref])
            if flow.source_ref == element.id and flow.target_ref in positioned_elements:
                outgoing_neighbors.append(positioned_elements[flow.target_ref])

        if incoming_neighbors:
            source = incoming_neighbors[0]
            if source.x is not None and source.y is not None:
                new_x = source.x + (source.width or 120) + 60
                new_y = source.y

                if new_x > bounds["max_x"] - (element.width or 120):
                    new_x = bounds["min_x"] + 100
                    new_y = source.y + (source.height or 80) + 60

                new_x, new_y = self._avoid_overlap(
                    new_x, new_y, element, positioned_elements, bounds
                )
                return (new_x, new_y)

        if outgoing_neighbors:
            target = outgoing_neighbors[0]
            if target.x is not None and target.y is not None:
                new_x = target.x - (element.width or 120) - 60
                new_y = target.y

                if new_x < bounds["min_x"]:
                    new_x = bounds["min_x"] + 100
                    new_y = target.y - (element.height or 80) - 60

                new_x, new_y = self._avoid_overlap(
                    new_x, new_y, element, positioned_elements, bounds
                )
                return (new_x, new_y)

        return None

    def _avoid_overlap(
        self,
        x: float,
        y: float,
        element: BPMNElement,
        positioned_elements: Dict[str, BPMNElement],
        bounds: Dict[str, float],
    ) -> Tuple[float, float]:
        """Adjust position to avoid overlap with existing elements.

        Args:
            x, y: Initial position
            element: Element being positioned
            positioned_elements: Already positioned elements
            bounds: Diagram bounds

        Returns:
            Adjusted (x, y) position
        """
        elem_width = element.width or 120
        elem_height = element.height or 80
        offset_step = 100

        for attempt in range(10):
            has_overlap = False
            for other_id, other in positioned_elements.items():
                if other.x is None or other.y is None:
                    continue

                other_width = other.width or 120
                other_height = other.height or 80

                if (
                    x < other.x + other_width
                    and x + elem_width > other.x
                    and y < other.y + other_height
                    and y + elem_height > other.y
                ):
                    has_overlap = True
                    break

            if not has_overlap:
                return (x, y)

            y += offset_step

            if y > bounds["max_y"] + 200:
                x += offset_step
                y = bounds["min_y"]

        return (x, y)

    def _place_disconnected_elements(
        self,
        elements: List[BPMNElement],
        bounds: Dict[str, float],
    ) -> None:
        """Place disconnected elements (data objects, etc.) in a sidebar.

        Args:
            elements: Disconnected elements
            bounds: Diagram bounds from DI elements
        """
        if not elements:
            return

        data_elements = [e for e in elements if e.type in DATA_TYPES]
        other_elements = [e for e in elements if e.type not in DATA_TYPES]

        sidebar_x = max(0, bounds["min_x"] - 100)
        y = bounds["min_y"]

        for element in data_elements:
            element.x = sidebar_x
            element.y = y
            y += (element.height or 50) + 20

        x = bounds["min_x"]
        y = bounds["max_y"] + 50

        for element in other_elements:
            element.x = x
            element.y = y
            x += (element.width or 120) + 30

            if x > bounds["max_x"]:
                x = bounds["min_x"]
                y += 100

    def _use_di_coordinates(self, element: BPMNElement) -> bool:
        """Check if DI coordinates should be used.

        Args:
            element: BPMN element

        Returns:
            True if element has valid DI coordinates
        """
        return element.x is not None and element.y is not None

    def _assign_dimensions(self, element: BPMNElement) -> None:
        """Assign default dimensions based on element type.

        Args:
            element: BPMN element (modified in place)
        """
        if element.width is None or element.height is None:
            default_dims = ELEMENT_DIMENSIONS.get(element.type, (120, 80))
            if element.width is None:
                element.width = float(default_dims[0])
            if element.height is None:
                element.height = float(default_dims[1])

    def _assign_fallback_positions(
        self,
        elements: List[BPMNElement],
        bounds: Dict[str, float],
    ) -> None:
        """Assign fallback positions to elements without any.

        Places elements below the existing diagram bounds.

        Args:
            elements: List of BPMN elements (modified in place)
            bounds: Diagram bounds
        """
        x = bounds["min_x"]
        y = bounds["max_y"] + 100

        for element in elements:
            if element.x is None:
                element.x = x
                x += (element.width or 120) + 30

                if x > bounds["max_x"]:
                    x = bounds["min_x"]
                    y += 100

            if element.y is None:
                element.y = y

    # --- Backward-compatible delegate methods ---
    # These maintain the old internal API so existing tests that call
    # resolver._position_boundary_events(model) still work.

    def _position_boundary_events(self, model: BPMNModel) -> None:
        """Delegate to BoundaryPositioner.position_boundary_events()."""
        self._boundary_positioner.position_boundary_events(model)

    def _adjust_subprocess_internal_positions(self, model: BPMNModel) -> None:
        """Delegate to BoundaryPositioner.adjust_subprocess_internal_positions()."""
        self._boundary_positioner.adjust_subprocess_internal_positions(model)

    def _assign_pool_parents_for_laneless_pools(self, model: BPMNModel) -> None:
        """Delegate to BoundaryPositioner.assign_pool_parents_for_laneless_pools()."""
        self._boundary_positioner.assign_pool_parents_for_laneless_pools(model)

    def _organize_by_lanes(self, model: BPMNModel) -> None:
        """Delegate to LaneOrganizer.organize()."""
        self._lane_organizer.organize(model)

    def _preserve_lane_positions(self, model: BPMNModel) -> None:
        """Delegate to LaneOrganizer._preserve_lane_positions()."""
        self._lane_organizer._preserve_lane_positions(model)


def resolve_positions(
    model: BPMNModel,
    direction: str = "LR",
    use_layout: str = "graphviz",
) -> BPMNModel:
    """Resolve positions for all elements in a model.

    Convenience function for position resolution.

    Args:
        model: BPMN model
        direction: Flow direction for layout
        use_layout: Layout mode

    Returns:
        Model with resolved positions
    """
    layout_engine = LayoutEngine(direction=direction)
    resolver = PositionResolver(layout_engine=layout_engine, use_layout=use_layout)
    return resolver.resolve(model)
