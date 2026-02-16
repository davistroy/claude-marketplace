"""Edge routing logic for BPMN flows."""

from typing import Dict, List, Optional, Tuple

from .models import BPMNElement, BPMNFlow


class EdgeRouter:
    """Calculate edge routes between elements."""

    def __init__(self, elements: List[BPMNElement]):
        """Initialize router with element positions.

        Args:
            elements: List of BPMN elements
        """
        self.elements = {e.id: e for e in elements}

    def route(
        self,
        source_id: str,
        target_id: str,
        existing_waypoints: Optional[List[Tuple[float, float]]] = None,
    ) -> List[Tuple[float, float]]:
        """Calculate waypoints for edge.

        Args:
            source_id: Source element ID
            target_id: Target element ID
            existing_waypoints: Existing waypoints from DI

        Returns:
            List of waypoint coordinates
        """
        if existing_waypoints:
            return existing_waypoints

        source = self.elements.get(source_id)
        target = self.elements.get(target_id)

        if not source or not target:
            return []

        return self._orthogonal_route(source, target)

    def _get_connection_point(
        self,
        element: BPMNElement,
        direction: str,
    ) -> Tuple[float, float]:
        """Get connection point on element edge.

        Args:
            element: BPMN element
            direction: Connection direction (left, right, top, bottom)

        Returns:
            (x, y) connection point
        """
        x = element.x or 0
        y = element.y or 0
        width = element.width or 120
        height = element.height or 80

        center_x = x + width / 2
        center_y = y + height / 2

        if direction == "left":
            return (x, center_y)
        elif direction == "right":
            return (x + width, center_y)
        elif direction == "top":
            return (center_x, y)
        elif direction == "bottom":
            return (center_x, y + height)
        else:
            return (center_x, center_y)

    def _orthogonal_route(
        self,
        source: BPMNElement,
        target: BPMNElement,
    ) -> List[Tuple[float, float]]:
        """Calculate L-shaped or Z-shaped route.

        Args:
            source: Source element
            target: Target element

        Returns:
            List of waypoint coordinates
        """
        waypoints = []

        # Get element centers
        src_x = (source.x or 0) + (source.width or 120) / 2
        src_y = (source.y or 0) + (source.height or 80) / 2
        tgt_x = (target.x or 0) + (target.width or 120) / 2
        tgt_y = (target.y or 0) + (target.height or 80) / 2

        # Determine connection points based on relative positions
        if tgt_x > src_x:
            # Target is to the right
            src_point = self._get_connection_point(source, "right")
            tgt_point = self._get_connection_point(target, "left")
        elif tgt_x < src_x:
            # Target is to the left
            src_point = self._get_connection_point(source, "left")
            tgt_point = self._get_connection_point(target, "right")
        elif tgt_y > src_y:
            # Target is below
            src_point = self._get_connection_point(source, "bottom")
            tgt_point = self._get_connection_point(target, "top")
        else:
            # Target is above
            src_point = self._get_connection_point(source, "top")
            tgt_point = self._get_connection_point(target, "bottom")

        waypoints.append(src_point)

        # Add intermediate point for orthogonal routing if needed
        if (
            abs(src_point[0] - tgt_point[0]) > 10
            and abs(src_point[1] - tgt_point[1]) > 10
        ):
            # Create L-shaped route
            mid_x = (src_point[0] + tgt_point[0]) / 2
            waypoints.append((mid_x, src_point[1]))
            waypoints.append((mid_x, tgt_point[1]))

        waypoints.append(tgt_point)

        return waypoints


def calculate_edge_routes(
    elements: List[BPMNElement],
    flows: List[BPMNFlow],
) -> Dict[str, List[Tuple[float, float]]]:
    """Calculate routes for all flows.

    Args:
        elements: List of elements
        flows: List of flows

    Returns:
        Dictionary mapping flow ID to waypoints
    """
    router = EdgeRouter(elements)
    routes = {}

    for flow in flows:
        waypoints = router.route(
            flow.source_ref,
            flow.target_ref,
            flow.waypoints if flow.has_waypoints() else None,
        )
        routes[flow.id] = waypoints

    return routes
