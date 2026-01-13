"""Layout engine for BPMN diagrams using Graphviz."""

from typing import Dict, List, Tuple, Optional
import networkx as nx

from .models import BPMNElement, BPMNFlow
from .constants import ELEMENT_DIMENSIONS, LayoutConstants
from .exceptions import LayoutError


class LayoutEngine:
    """Calculate element positions using Graphviz."""

    def __init__(self, direction: str = "LR"):
        """Initialize layout engine.

        Args:
            direction: Flow direction - LR (left-right), TB (top-bottom),
                      RL (right-left), BT (bottom-top)
        """
        self.direction = direction
        self._rankdir_map = {
            "LR": "LR",
            "TB": "TB",
            "RL": "RL",
            "BT": "BT",
        }

    def calculate_layout(
        self,
        elements: List[BPMNElement],
        flows: List[BPMNFlow],
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate positions using Graphviz dot algorithm.

        Args:
            elements: List of BPMN elements
            flows: List of BPMN flows

        Returns:
            Dictionary mapping element ID to (x, y) position
        """
        if not elements:
            return {}

        # Build graph
        graph = self._build_graph(elements, flows)

        # Apply Graphviz layout
        try:
            positions = self._apply_graphviz_layout(graph, elements)
        except Exception as e:
            # Fall back to simple grid layout
            positions = self._simple_grid_layout(elements)

        # Scale and transform positions
        return self._scale_positions(positions, elements)

    def _build_graph(
        self,
        elements: List[BPMNElement],
        flows: List[BPMNFlow],
    ) -> nx.DiGraph:
        """Build NetworkX graph from BPMN elements.

        Args:
            elements: List of BPMN elements
            flows: List of BPMN flows

        Returns:
            NetworkX directed graph
        """
        graph = nx.DiGraph()

        # Add nodes
        element_ids = {e.id for e in elements}
        for element in elements:
            graph.add_node(element.id)

        # Add edges
        for flow in flows:
            if flow.source_ref in element_ids and flow.target_ref in element_ids:
                graph.add_edge(flow.source_ref, flow.target_ref)

        return graph

    def _apply_graphviz_layout(
        self,
        graph: nx.DiGraph,
        elements: List[BPMNElement],
    ) -> Dict[str, Tuple[float, float]]:
        """Apply Graphviz layout algorithm.

        Args:
            graph: NetworkX graph
            elements: List of BPMN elements for dimension info

        Returns:
            Dictionary mapping element ID to (x, y) position
        """
        try:
            import pygraphviz as pgv
        except ImportError:
            raise LayoutError("pygraphviz is required for automatic layout")

        # Create pygraphviz graph
        A = pgv.AGraph(directed=True, strict=True)

        # Set graph attributes
        A.graph_attr["rankdir"] = self._rankdir_map.get(self.direction, "LR")
        A.graph_attr["nodesep"] = str(LayoutConstants.GRAPHVIZ_NODESEP)
        A.graph_attr["ranksep"] = str(LayoutConstants.GRAPHVIZ_RANKSEP)
        A.graph_attr["splines"] = "ortho"

        # Create element dimension lookup
        elem_dims = {e.id: self._get_element_dimensions(e) for e in elements}

        # Add nodes with dimensions
        for node in graph.nodes():
            width, height = elem_dims.get(node, (120, 80))
            # Convert to inches for Graphviz
            A.add_node(
                node,
                width=str(width / 72),  # Convert points to inches
                height=str(height / 72),
                shape="box",
            )

        # Add edges
        for source, target in graph.edges():
            A.add_edge(source, target)

        # Run layout
        A.layout(prog="dot")

        # Extract positions
        positions = {}
        for node in A.nodes():
            pos = node.attr["pos"]
            if pos:
                x, y = map(float, pos.split(","))
                positions[str(node)] = (x, y)

        return positions

    def _simple_grid_layout(
        self,
        elements: List[BPMNElement],
    ) -> Dict[str, Tuple[float, float]]:
        """Simple grid-based fallback layout.

        Args:
            elements: List of BPMN elements

        Returns:
            Dictionary mapping element ID to (x, y) position
        """
        positions = {}
        x = LayoutConstants.DIAGRAM_MARGIN
        y = LayoutConstants.DIAGRAM_MARGIN
        row_height = 0

        for i, element in enumerate(elements):
            width, height = self._get_element_dimensions(element)

            # Place element
            positions[element.id] = (x, y)

            # Update position for next element
            x += width + LayoutConstants.NODE_HORIZONTAL_GAP
            row_height = max(row_height, height)

            # Start new row every 5 elements
            if (i + 1) % 5 == 0:
                x = LayoutConstants.DIAGRAM_MARGIN
                y += row_height + LayoutConstants.NODE_VERTICAL_GAP
                row_height = 0

        return positions

    def _scale_positions(
        self,
        positions: Dict[str, Tuple[float, float]],
        elements: List[BPMNElement],
    ) -> Dict[str, Tuple[float, float]]:
        """Scale and transform coordinates for Draw.io.

        Graphviz uses Y increasing upward, Draw.io uses Y increasing downward.
        We flip the Y axis during transformation.

        Args:
            positions: Raw positions from layout
            elements: List of elements for dimension info

        Returns:
            Scaled positions
        """
        if not positions:
            return {}

        # Find bounds
        min_x = min(p[0] for p in positions.values())
        max_y = max(p[1] for p in positions.values())

        # Normalize to start at margin, flipping Y axis
        scaled = {}
        for elem_id, (x, y) in positions.items():
            scaled_x = (x - min_x) * LayoutConstants.SCALE_X + LayoutConstants.DIAGRAM_MARGIN
            # Flip Y: subtract from max to invert coordinate system
            scaled_y = (max_y - y) * LayoutConstants.SCALE_Y + LayoutConstants.DIAGRAM_MARGIN
            scaled[elem_id] = (scaled_x, scaled_y)

        return scaled

    def _get_element_dimensions(
        self,
        element: BPMNElement,
    ) -> Tuple[float, float]:
        """Get dimensions for an element.

        Args:
            element: BPMN element

        Returns:
            (width, height) tuple
        """
        if element.width is not None and element.height is not None:
            return (element.width, element.height)
        return ELEMENT_DIMENSIONS.get(element.type, (120, 80))
