"""Recovery strategies for handling errors gracefully."""

from typing import Dict, Tuple
import logging

from .models import BPMNModel, BPMNElement, BPMNFlow
from .constants import ELEMENT_DIMENSIONS
from .styles import STYLE_MAP

logger = logging.getLogger(__name__)


class RecoveryStrategy:
    """Handle errors gracefully with fallbacks."""

    def __init__(self):
        self.recovered_count = 0

    def recover_missing_coordinates(self, element: BPMNElement, index: int = 0) -> None:
        """Fall back to simple grid layout for missing DI.

        Args:
            element: Element with missing coordinates
            index: Element index for grid positioning
        """
        if element.x is None:
            element.x = 100 + (index % 5) * 150
            self.recovered_count += 1
            logger.debug(f"Assigned default x={element.x} to {element.id}")

        if element.y is None:
            element.y = 100 + (index // 5) * 100
            logger.debug(f"Assigned default y={element.y} to {element.id}")

        if element.width is None or element.height is None:
            dims = ELEMENT_DIMENSIONS.get(element.type, (120, 80))
            element.width = element.width or dims[0]
            element.height = element.height or dims[1]
            logger.debug(f"Assigned default dimensions to {element.id}")

    def recover_invalid_parent(self, element: BPMNElement, valid_parents: set) -> None:
        """Place element at diagram root if parent invalid.

        Args:
            element: Element with invalid parent
            valid_parents: Set of valid parent IDs
        """
        if element.parent_id and element.parent_id not in valid_parents:
            logger.warning(
                f"Invalid parent '{element.parent_id}' for element '{element.id}', "
                f"placing at root"
            )
            element.parent_id = None
            self.recovered_count += 1

    def recover_unknown_element_type(self, element: BPMNElement) -> str:
        """Return generic task style for unknown types.

        Args:
            element: Element with unknown type

        Returns:
            Fallback style string
        """
        if element.type not in STYLE_MAP:
            logger.warning(
                f"Unknown element type '{element.type}' for element '{element.id}', "
                f"using generic task style"
            )
            self.recovered_count += 1
            return STYLE_MAP["task"]
        return STYLE_MAP[element.type]

    def recover_invalid_flow(self, flow: BPMNFlow, element_ids: set) -> bool:
        """Check if flow can be recovered.

        Args:
            flow: Flow to check
            element_ids: Valid element IDs

        Returns:
            True if flow is valid, False if should be skipped
        """
        if flow.source_ref not in element_ids:
            logger.warning(
                f"Skipping flow '{flow.id}': invalid source '{flow.source_ref}'"
            )
            self.recovered_count += 1
            return False

        if flow.target_ref not in element_ids:
            logger.warning(
                f"Skipping flow '{flow.id}': invalid target '{flow.target_ref}'"
            )
            self.recovered_count += 1
            return False

        return True

    def recover_graphviz_failure(
        self, model: BPMNModel
    ) -> Dict[str, Tuple[float, float]]:
        """Use simple grid layout if Graphviz fails.

        Args:
            model: BPMN model to position

        Returns:
            Dictionary mapping element IDs to (x, y) positions
        """
        logger.warning("Graphviz layout failed, falling back to grid layout")
        self.recovered_count += 1

        positions = {}
        elements_per_row = 5
        x_spacing = 150
        y_spacing = 100
        margin = 100

        for i, element in enumerate(model.elements):
            row = i // elements_per_row
            col = i % elements_per_row
            positions[element.id] = (margin + col * x_spacing, margin + row * y_spacing)

        return positions

    def get_recovery_count(self) -> int:
        """Get number of recoveries performed.

        Returns:
            Number of recovery actions taken
        """
        return self.recovered_count


def recover_model(model: BPMNModel) -> Tuple[BPMNModel, int]:
    """Apply all recovery strategies to a model.

    Args:
        model: BPMN model to recover

    Returns:
        Tuple of (recovered model, recovery count)
    """
    strategy = RecoveryStrategy()
    element_ids = {e.id for e in model.elements}
    valid_parents = (
        element_ids | {p.id for p in model.pools} | {lane.id for lane in model.lanes}
    )

    # Recover elements
    for i, element in enumerate(model.elements):
        strategy.recover_missing_coordinates(element, i)
        strategy.recover_invalid_parent(element, valid_parents)

    # Filter invalid flows
    valid_flows = [
        flow for flow in model.flows if strategy.recover_invalid_flow(flow, element_ids)
    ]
    model.flows = valid_flows

    return model, strategy.get_recovery_count()
