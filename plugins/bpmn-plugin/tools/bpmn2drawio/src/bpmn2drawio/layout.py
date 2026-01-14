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
        used_graphviz = False
        try:
            positions = self._apply_graphviz_layout(graph, elements)
            used_graphviz = True
        except Exception:
            # Fall back to flow-based layout that respects direction and branching
            positions = self._flow_based_layout(graph, elements)

        # Scale and transform positions
        # For Graphviz: flip Y (uses Y increasing upward) and scale (returns inches)
        # For fallback: don't flip (already correct) and don't scale (already pixels)
        return self._scale_positions(
            positions,
            elements,
            flip_y=used_graphviz,
            apply_scale=used_graphviz,
        )

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

    def _flow_based_layout(
        self,
        graph: nx.DiGraph,
        elements: List[BPMNElement],
    ) -> Dict[str, Tuple[float, float]]:
        """Flow-based layout that respects direction and handles branching.

        Uses topological sorting to assign ranks/levels to elements,
        then positions elements based on their rank with proper spacing
        for branches.

        Args:
            graph: NetworkX directed graph
            elements: List of BPMN elements

        Returns:
            Dictionary mapping element ID to (x, y) position
        """
        if not graph.nodes():
            return self._simple_grid_layout(elements)

        # Create element lookup
        elem_lookup = {e.id: e for e in elements}

        # Assign ranks using longest path from sources
        ranks = self._assign_ranks(graph)

        # Group elements by rank
        rank_groups: Dict[int, List[str]] = {}
        for node_id, rank in ranks.items():
            if rank not in rank_groups:
                rank_groups[rank] = []
            rank_groups[rank].append(node_id)

        # Calculate positions based on direction
        positions = {}
        is_horizontal = self.direction in ("LR", "RL")
        is_reversed = self.direction in ("RL", "BT")

        # Spacing constants
        rank_spacing = LayoutConstants.RANK_SEPARATION
        node_spacing = LayoutConstants.NODE_VERTICAL_GAP if is_horizontal else LayoutConstants.NODE_HORIZONTAL_GAP

        # Position each rank
        sorted_ranks = sorted(rank_groups.keys(), reverse=is_reversed)
        primary_pos = LayoutConstants.DIAGRAM_MARGIN

        for rank in sorted_ranks:
            nodes = rank_groups[rank]
            secondary_pos = LayoutConstants.DIAGRAM_MARGIN

            for node_id in nodes:
                if node_id not in elem_lookup:
                    continue

                elem = elem_lookup[node_id]
                width, height = self._get_element_dimensions(elem)

                if is_horizontal:
                    # LR/RL: primary is X, secondary is Y
                    x = primary_pos
                    y = secondary_pos
                    secondary_pos += height + node_spacing
                else:
                    # TB/BT: primary is Y, secondary is X
                    x = secondary_pos
                    y = primary_pos
                    secondary_pos += width + node_spacing

                positions[node_id] = (x, y)

            # Move to next rank
            if is_horizontal:
                max_width = max(
                    self._get_element_dimensions(elem_lookup[n])[0]
                    for n in nodes if n in elem_lookup
                )
                primary_pos += max_width + rank_spacing
            else:
                max_height = max(
                    self._get_element_dimensions(elem_lookup[n])[1]
                    for n in nodes if n in elem_lookup
                )
                primary_pos += max_height + rank_spacing

        # Add any elements not in the graph
        for elem in elements:
            if elem.id not in positions:
                positions[elem.id] = (primary_pos, LayoutConstants.DIAGRAM_MARGIN)
                primary_pos += self._get_element_dimensions(elem)[0] + LayoutConstants.NODE_HORIZONTAL_GAP

        return positions

    def _assign_ranks(self, graph: nx.DiGraph) -> Dict[str, int]:
        """Assign ranks to nodes based on longest path from sources.

        Args:
            graph: NetworkX directed graph

        Returns:
            Dictionary mapping node ID to rank (0 = source level)
        """
        ranks = {}

        # Find source nodes (no incoming edges)
        sources = [n for n in graph.nodes() if graph.in_degree(n) == 0]

        # If no sources, use all nodes
        if not sources:
            sources = list(graph.nodes())

        # BFS to assign ranks
        visited = set()
        queue = [(s, 0) for s in sources]

        while queue:
            node, rank = queue.pop(0)

            if node in visited:
                # Take the maximum rank for nodes reachable via multiple paths
                if rank > ranks.get(node, -1):
                    ranks[node] = rank
                continue

            visited.add(node)
            ranks[node] = max(ranks.get(node, 0), rank)

            # Add successors
            for succ in graph.successors(node):
                queue.append((succ, rank + 1))

        # Handle disconnected nodes
        for node in graph.nodes():
            if node not in ranks:
                ranks[node] = 0

        return ranks

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
        flip_y: bool = True,
        apply_scale: bool = True,
    ) -> Dict[str, Tuple[float, float]]:
        """Scale and transform coordinates for Draw.io.

        Graphviz uses Y increasing upward, Draw.io uses Y increasing downward.
        We flip the Y axis during transformation for Graphviz output.
        For fallback layout, Y is already correct and already in pixels.

        Args:
            positions: Raw positions from layout
            elements: List of elements for dimension info
            flip_y: Whether to flip Y axis (True for Graphviz, False for fallback)
            apply_scale: Whether to apply SCALE_X/Y multipliers (True for Graphviz
                        which returns inches, False for fallback which returns pixels)

        Returns:
            Scaled positions
        """
        if not positions:
            return {}

        # Find bounds
        min_x = min(p[0] for p in positions.values())
        min_y = min(p[1] for p in positions.values())
        max_y = max(p[1] for p in positions.values())

        # Scale factors (1.0 for fallback layout which already uses pixels)
        scale_x = LayoutConstants.SCALE_X if apply_scale else 1.0
        scale_y = LayoutConstants.SCALE_Y if apply_scale else 1.0

        # Normalize to start at margin
        scaled = {}
        for elem_id, (x, y) in positions.items():
            scaled_x = (x - min_x) * scale_x + LayoutConstants.DIAGRAM_MARGIN
            if flip_y:
                # Flip Y: subtract from max to invert coordinate system (for Graphviz)
                scaled_y = (max_y - y) * scale_y + LayoutConstants.DIAGRAM_MARGIN
            else:
                # Keep Y as-is, just normalize to margin (for fallback layout)
                scaled_y = (y - min_y) * scale_y + LayoutConstants.DIAGRAM_MARGIN
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
