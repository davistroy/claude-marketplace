"""Boundary event and subprocess positioning for BPMN elements."""

from typing import Dict, List

from .models import BPMNModel, BPMNElement


class BoundaryPositioner:
    """Position boundary events and adjust subprocess internals.

    Handles:
    - Positioning boundary events relative to their attached elements
    - Converting subprocess internal element coordinates to relative positions
    - Assigning pool parents for elements in laneless pools
    """

    def position_boundary_events(self, model: BPMNModel) -> None:
        """Position boundary events relative to their attached elements.

        Boundary events are placed on the bottom edge of the element they're
        attached to (typically a subprocess or task).

        In Draw.io, boundary events have:
        1. parent set to the attached element
        2. Coordinates relative to the parent element

        Args:
            model: BPMN model with elements (modified in place)
        """
        elem_lookup = {e.id: e for e in model.elements}
        attached_boundary_counts: Dict[str, int] = {}

        for element in model.elements:
            if element.type != "boundaryEvent":
                continue

            attached_id = self._find_attached_element_id(element, elem_lookup)

            if attached_id and attached_id in elem_lookup:
                self._position_single_boundary(
                    element,
                    elem_lookup[attached_id],
                    attached_id,
                    attached_boundary_counts,
                )

    def adjust_subprocess_internal_positions(self, model: BPMNModel) -> None:
        """Convert subprocess internal element coordinates to relative positions.

        In Draw.io, when an element has a parent, its coordinates are relative
        to the parent container. This converts absolute coordinates to
        subprocess-relative coordinates.

        Args:
            model: BPMN model (modified in place)
        """
        subprocess_lookup = self._build_subprocess_lookup(model.elements)
        if not subprocess_lookup:
            return

        for element in model.elements:
            subprocess_id = element.subprocess_id or element.properties.get(
                "subprocess_id"
            )
            if subprocess_id and subprocess_id in subprocess_lookup:
                self._make_coords_relative(element, subprocess_lookup[subprocess_id])

    def assign_pool_parents_for_laneless_pools(self, model: BPMNModel) -> None:
        """Assign pool as parent for elements in pools without lanes.

        When a pool has no lanes, elements should be direct children of the pool.

        Args:
            model: BPMN model (modified in place)
        """
        if not model.pools:
            return

        laneless_pools = self._find_laneless_pools(model)
        if not laneless_pools:
            return

        for pool in laneless_pools:
            if not pool.process_ref:
                continue
            self._assign_elements_to_pool(pool, model.elements, laneless_pools)

    # --- Private helpers ---

    def _find_attached_element_id(
        self,
        boundary: BPMNElement,
        elem_lookup: Dict[str, BPMNElement],
    ) -> str | None:
        """Find the element a boundary event is attached to.

        First checks the attachedToRef property, then falls back to
        ID pattern matching.

        Args:
            boundary: Boundary event element
            elem_lookup: All elements keyed by ID

        Returns:
            ID of the attached element, or None
        """
        attached_id = boundary.properties.get("attachedToRef")
        if attached_id:
            return attached_id

        attachable_types = (
            "subProcess",
            "task",
            "userTask",
            "serviceTask",
            "scriptTask",
            "callActivity",
        )
        for other_id, other in elem_lookup.items():
            if other.type not in attachable_types:
                continue
            if (
                other_id in boundary.id
                or boundary.id.replace("Boundary", "") in other_id
            ):
                return other_id

        return None

    def _position_single_boundary(
        self,
        boundary: BPMNElement,
        attached: BPMNElement,
        attached_id: str,
        boundary_counts: Dict[str, int],
    ) -> None:
        """Position a single boundary event on the bottom edge of its parent.

        Args:
            boundary: Boundary event element (modified in place)
            attached: Element the boundary is attached to
            attached_id: ID of the attached element
            boundary_counts: Tracks how many boundaries per element (modified)
        """
        boundary.parent_id = attached_id

        boundary_index = boundary_counts.get(attached_id, 0)
        boundary_counts[attached_id] = boundary_index + 1

        event_height = boundary.height or 36
        attached_height = attached.height or 80

        spacing = 50
        x_offset = 20 + (boundary_index * spacing)

        boundary.x = x_offset
        boundary.y = attached_height - (event_height / 2)

    def _build_subprocess_lookup(
        self, elements: List[BPMNElement]
    ) -> Dict[str, BPMNElement]:
        """Build a lookup of subprocess elements.

        Args:
            elements: All model elements

        Returns:
            Dict mapping subprocess ID to subprocess element
        """
        return {e.id: e for e in elements if e.properties.get("_is_subprocess")}

    def _make_coords_relative(
        self, element: BPMNElement, subprocess: BPMNElement
    ) -> None:
        """Convert element coordinates from absolute to subprocess-relative.

        Args:
            element: Internal element (modified in place)
            subprocess: Containing subprocess
        """
        if not (
            element.x is not None
            and element.y is not None
            and subprocess.x is not None
            and subprocess.y is not None
        ):
            return

        header_offset = 26  # Standard collapsible container header height
        element.x = element.x - subprocess.x
        element.y = element.y - subprocess.y - header_offset

        max_x = (subprocess.width or 200) - (element.width or 80)
        max_y = (subprocess.height or 150) - header_offset - (element.height or 60)
        element.x = max(0, min(element.x, max_x))
        element.y = max(0, min(element.y, max_y))

    def _find_laneless_pools(self, model: BPMNModel) -> list:
        """Find pools that have no lanes.

        Args:
            model: BPMN model

        Returns:
            List of pools without lanes
        """
        pools_with_lanes = set()
        for lane in model.lanes:
            if lane.parent_pool_id:
                pools_with_lanes.add(lane.parent_pool_id)

        return [p for p in model.pools if p.id not in pools_with_lanes]

    def _assign_elements_to_pool(
        self,
        pool,
        elements: List[BPMNElement],
        laneless_pools: list,
    ) -> None:
        """Assign unparented elements to a laneless pool.

        Args:
            pool: Pool to assign elements to
            elements: All model elements
            laneless_pools: All pools without lanes
        """
        for element in elements:
            if element.parent_id:
                continue
            if element.subprocess_id or element.properties.get("subprocess_id"):
                continue
            if len(laneless_pools) == 1:
                element.parent_id = pool.id
