"""Layout engine for BPMN diagrams using Graphviz."""

import logging
from typing import Dict, List, Tuple, Optional
import networkx as nx

from .models import BPMNElement, BPMNFlow
from .constants import ELEMENT_DIMENSIONS, LayoutConstants
from .exceptions import LayoutError

logger = logging.getLogger(__name__)


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
        except (ImportError, AttributeError, RuntimeError, OSError, LayoutError):
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

        # Add edges with validation logging
        for flow in flows:
            source_exists = flow.source_ref in element_ids
            target_exists = flow.target_ref in element_ids

            if source_exists and target_exists:
                graph.add_edge(flow.source_ref, flow.target_ref)
            else:
                # Log skipped flows for debugging layout issues
                missing = []
                if not source_exists:
                    missing.append(f"source={flow.source_ref}")
                if not target_exists:
                    missing.append(f"target={flow.target_ref}")
                logger.debug(
                    "Skipped flow %s: missing %s",
                    flow.id,
                    ", ".join(missing)
                )

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

        # Add fallback positions for elements not positioned by graphviz
        # (disconnected elements, etc.)
        fallback_x = LayoutConstants.DIAGRAM_MARGIN
        fallback_y = LayoutConstants.DIAGRAM_MARGIN
        if positions:
            # Place below existing positions
            max_y = max(p[1] for p in positions.values())
            fallback_y = max_y + LayoutConstants.RANK_SEPARATION

        for element in elements:
            if element.id not in positions:
                positions[element.id] = (fallback_x, fallback_y)
                width, height = self._get_element_dimensions(element)
                fallback_x += width + LayoutConstants.NODE_HORIZONTAL_GAP
                logger.debug(
                    "Assigned fallback position for element %s at (%s, %s)",
                    element.id,
                    fallback_x,
                    fallback_y
                )

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

        Uses BFS with re-queuing when a longer path is found to ensure
        nodes receive the maximum rank (longest path from any source).
        Handles cyclic graphs by limiting iterations.

        Args:
            graph: NetworkX directed graph

        Returns:
            Dictionary mapping node ID to rank (0 = source level)
        """
        ranks = {}
        num_nodes = graph.number_of_nodes()

        if num_nodes == 0:
            return ranks

        # Find source nodes (no incoming edges)
        sources = [n for n in graph.nodes() if graph.in_degree(n) == 0]

        # If no sources (cyclic graph), use all nodes as potential sources
        if not sources:
            sources = list(graph.nodes())

        # Initialize source ranks
        for source in sources:
            ranks[source] = 0

        # BFS with re-queuing when rank improves
        # Limit iterations to prevent infinite loops in cyclic graphs
        queue = [(s, 0) for s in sources]
        max_iterations = num_nodes * num_nodes  # O(n^2) worst case for DAG
        iterations = 0

        while queue and iterations < max_iterations:
            iterations += 1
            node, rank = queue.pop(0)

            # Skip if we already found a longer path to this node
            current_rank = ranks.get(node, -1)
            if rank < current_rank:
                continue

            # Update rank if this path is longer
            if rank > current_rank:
                ranks[node] = rank

            # Process successors - re-queue if rank would improve
            # Cap rank to prevent unbounded growth in cycles
            max_rank = num_nodes - 1
            for succ in graph.successors(node):
                new_rank = min(rank + 1, max_rank)
                succ_current = ranks.get(succ, -1)
                if new_rank > succ_current:
                    ranks[succ] = new_rank
                    # Re-queue to propagate improved rank to downstream nodes
                    queue.append((succ, new_rank))

        if iterations >= max_iterations:
            logger.warning(
                "Rank assignment reached iteration limit (%d), graph may have cycles",
                max_iterations
            )

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
