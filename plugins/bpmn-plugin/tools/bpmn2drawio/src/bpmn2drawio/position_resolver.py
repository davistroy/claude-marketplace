"""Position resolver for BPMN elements."""

from typing import Optional
from copy import deepcopy

from .models import BPMNModel, BPMNElement
from .layout import LayoutEngine
from .constants import ELEMENT_DIMENSIONS


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

        # Check if we need layout calculation
        needs_layout = []
        for element in resolved_model.elements:
            # Assign dimensions if missing
            self._assign_dimensions(element)

            # Check if position is missing
            if not self._use_di_coordinates(element):
                needs_layout.append(element)

        # Calculate layout for elements without positions
        if needs_layout and self.use_layout == "graphviz":
            positions = self.layout_engine.calculate_layout(
                resolved_model.elements,
                resolved_model.flows,
            )

            # Apply calculated positions
            for element in resolved_model.elements:
                if element.id in positions:
                    x, y = positions[element.id]
                    if element.x is None:
                        element.x = x
                    if element.y is None:
                        element.y = y

        # Ensure all elements have some position
        self._assign_fallback_positions(resolved_model.elements)

        return resolved_model

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

    def _assign_fallback_positions(self, elements: list) -> None:
        """Assign fallback positions to elements without any.

        Args:
            elements: List of BPMN elements (modified in place)
        """
        x = 50.0
        y = 50.0

        for element in elements:
            if element.x is None:
                element.x = x
                x += element.width + 60
            if element.y is None:
                element.y = y


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
