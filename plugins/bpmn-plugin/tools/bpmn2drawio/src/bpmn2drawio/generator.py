"""Draw.io XML generator."""

from typing import Dict, Optional
from xml.etree import ElementTree as ET
from dataclasses import dataclass

from .models import BPMNModel, BPMNElement, BPMNFlow
from .styles import get_element_style, get_edge_style
from .constants import ELEMENT_DIMENSIONS, GATEWAY_TYPES, TASK_TYPES, EVENT_TYPES
from .markers import create_gateway_marker
from .icons import create_task_icon, create_event_icon
from .swimlanes import create_pool_cell, create_lane_cell, SwimlaneSizer
from .themes import BPMNTheme


@dataclass
class GenerationResult:
    """Result of Draw.io generation."""

    xml_string: str
    element_count: int
    flow_count: int


class DrawioGenerator:
    """Generates Draw.io XML from BPMN intermediate model."""

    def __init__(self, theme: Optional[BPMNTheme] = None):
        """Initialize the generator.

        Args:
            theme: Optional color theme for the diagram
        """
        self._cell_counter = 2  # Start after base cells 0 and 1
        self._element_cell_ids: Dict[str, str] = {}
        self._theme = theme

    def generate(self, model: BPMNModel, output_path: str) -> GenerationResult:
        """Generate Draw.io file from BPMN model.

        Args:
            model: Parsed BPMN model
            output_path: Path to output file

        Returns:
            GenerationResult with statistics
        """
        result = self.generate_result(model)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.xml_string)

        return result

    def generate_string(self, model: BPMNModel) -> str:
        """Generate Draw.io XML as string.

        Args:
            model: Parsed BPMN model

        Returns:
            Draw.io XML string
        """
        return self.generate_result(model).xml_string

    def generate_result(self, model: BPMNModel) -> GenerationResult:
        """Generate Draw.io XML and return result with statistics.

        Args:
            model: Parsed BPMN model

        Returns:
            GenerationResult with XML and statistics
        """
        # Reset state
        self._cell_counter = 2
        self._element_cell_ids = {}

        # Create document structure
        mxfile = self._create_mxfile()
        diagram = ET.SubElement(mxfile, "diagram")
        diagram.set("id", "diagram_1")
        diagram.set("name", model.process_name or "BPMN Diagram")

        graph_model = self._create_graph_model()
        diagram.append(graph_model)

        root = graph_model.find("root")

        # Generate pools and lanes first (they are parents of elements)
        pool_cell_ids = {}
        lane_cell_ids = {}
        sizer = SwimlaneSizer()

        for pool in model.pools:
            # Calculate pool size if not set
            pool_elements = [e for e in model.elements if e.parent_id == pool.id]
            pool_lanes = [l for l in model.lanes if l.parent_pool_id == pool.id]
            if not pool.width or not pool.height:
                pool.width, pool.height = sizer.calculate_pool_size(
                    pool, pool_elements, pool_lanes
                )

            cell_id = str(self._cell_counter)
            self._cell_counter += 1
            pool_cell = create_pool_cell(pool, cell_id)
            root.append(pool_cell)
            pool_cell_ids[pool.id] = cell_id

        for lane in model.lanes:
            parent_pool_cell_id = pool_cell_ids.get(lane.parent_pool_id, "1")
            cell_id = str(self._cell_counter)
            self._cell_counter += 1
            lane_cell = create_lane_cell(lane, cell_id, parent_pool_cell_id)
            root.append(lane_cell)
            lane_cell_ids[lane.id] = cell_id

        # Store lane/pool cell IDs for element parent lookup
        self._pool_cell_ids = pool_cell_ids
        self._lane_cell_ids = lane_cell_ids

        # Generate vertices for elements and their markers/icons
        for element in model.elements:
            vertex = self._create_vertex(element)
            root.append(vertex)
            cell_id = vertex.get("id")
            self._element_cell_ids[element.id] = cell_id

            # Add gateway markers
            if element.type in GATEWAY_TYPES:
                marker_result = create_gateway_marker(
                    element, cell_id, self._cell_counter
                )
                if marker_result:
                    marker_cell, self._cell_counter = marker_result
                    root.append(marker_cell)

            # Add task icons
            if element.type in TASK_TYPES:
                icon_result = create_task_icon(
                    element, cell_id, self._cell_counter
                )
                if icon_result:
                    icon_cell, self._cell_counter = icon_result
                    root.append(icon_cell)

            # Add event icons
            if element.type in EVENT_TYPES:
                icon_result = create_event_icon(
                    element, cell_id, self._cell_counter
                )
                if icon_result:
                    icon_cell, self._cell_counter = icon_result
                    root.append(icon_cell)

        # Generate edges for flows
        for flow in model.flows:
            edge = self._create_edge(flow)
            if edge is not None:
                root.append(edge)

        # Generate XML string
        xml_string = self._element_to_string(mxfile)

        return GenerationResult(
            xml_string=xml_string,
            element_count=len(model.elements),
            flow_count=len(model.flows),
        )

    def _create_mxfile(self) -> ET.Element:
        """Create root mxfile element."""
        mxfile = ET.Element("mxfile")
        mxfile.set("host", "bpmn2drawio")
        mxfile.set("modified", "2024-01-01T00:00:00.000Z")
        mxfile.set("agent", "bpmn2drawio converter")
        mxfile.set("version", "1.0.0")
        mxfile.set("type", "device")
        return mxfile

    def _create_graph_model(self) -> ET.Element:
        """Create mxGraphModel with default attributes."""
        graph_model = ET.Element("mxGraphModel")
        graph_model.set("dx", "0")
        graph_model.set("dy", "0")
        graph_model.set("grid", "1")
        graph_model.set("gridSize", "10")
        graph_model.set("guides", "1")
        graph_model.set("tooltips", "1")
        graph_model.set("connect", "1")
        graph_model.set("arrows", "1")
        graph_model.set("fold", "1")
        graph_model.set("page", "1")
        graph_model.set("pageScale", "1")
        graph_model.set("pageWidth", "1169")
        graph_model.set("pageHeight", "827")
        graph_model.set("math", "0")
        graph_model.set("shadow", "0")

        # Create root element with base cells
        root = ET.SubElement(graph_model, "root")

        # Cell 0 - root cell
        cell0 = ET.SubElement(root, "mxCell")
        cell0.set("id", "0")

        # Cell 1 - default parent
        cell1 = ET.SubElement(root, "mxCell")
        cell1.set("id", "1")
        cell1.set("parent", "0")

        return graph_model

    def _create_vertex(self, element: BPMNElement) -> ET.Element:
        """Create mxCell for a shape.

        Args:
            element: BPMN element

        Returns:
            mxCell element
        """
        cell_id = str(self._cell_counter)
        self._cell_counter += 1

        cell = ET.Element("mxCell")
        cell.set("id", cell_id)
        cell.set("value", element.name or "")
        # Use theme-based style if theme provided, otherwise fallback to default
        if self._theme:
            cell.set("style", self._theme.style_for(element.type))
        else:
            cell.set("style", get_element_style(element.type))
        cell.set("vertex", "1")

        # Resolve parent cell ID
        parent_cell_id = "1"
        if element.parent_id:
            # Check if parent is a lane
            if hasattr(self, '_lane_cell_ids') and element.parent_id in self._lane_cell_ids:
                parent_cell_id = self._lane_cell_ids[element.parent_id]
            # Check if parent is a pool
            elif hasattr(self, '_pool_cell_ids') and element.parent_id in self._pool_cell_ids:
                parent_cell_id = self._pool_cell_ids[element.parent_id]
            else:
                parent_cell_id = element.parent_id

        cell.set("parent", parent_cell_id)

        # Add geometry
        geometry = ET.SubElement(cell, "mxGeometry")

        # Use coordinates from element or defaults
        x = element.x if element.x is not None else 0
        y = element.y if element.y is not None else 0

        # Get dimensions
        if element.width is not None and element.height is not None:
            width = element.width
            height = element.height
        else:
            default_dims = ELEMENT_DIMENSIONS.get(element.type, (120, 80))
            width = default_dims[0]
            height = default_dims[1]

        geometry.set("x", str(x))
        geometry.set("y", str(y))
        geometry.set("width", str(width))
        geometry.set("height", str(height))
        geometry.set("as", "geometry")

        return cell

    def _create_edge(self, flow: BPMNFlow) -> Optional[ET.Element]:
        """Create mxCell for a connector.

        Args:
            flow: BPMN flow

        Returns:
            mxCell element or None if source/target not found
        """
        source_cell = self._element_cell_ids.get(flow.source_ref)
        target_cell = self._element_cell_ids.get(flow.target_ref)

        if not source_cell or not target_cell:
            return None

        cell_id = str(self._cell_counter)
        self._cell_counter += 1

        cell = ET.Element("mxCell")
        cell.set("id", cell_id)
        cell.set("value", flow.name or "")
        cell.set("style", get_edge_style(
            flow.type,
            is_default=flow.is_default,
            has_condition=flow.condition is not None
        ))
        cell.set("edge", "1")
        cell.set("parent", "1")
        cell.set("source", source_cell)
        cell.set("target", target_cell)

        # Add geometry with waypoints if available
        geometry = ET.SubElement(cell, "mxGeometry")
        geometry.set("relative", "1")
        geometry.set("as", "geometry")

        if flow.waypoints:
            array = ET.SubElement(geometry, "Array")
            array.set("as", "points")
            # Skip first and last waypoints (they're at source/target)
            for wp in flow.waypoints[1:-1]:
                point = ET.SubElement(array, "mxPoint")
                point.set("x", str(wp[0]))
                point.set("y", str(wp[1]))

        return cell

    def _element_to_string(self, element: ET.Element) -> str:
        """Convert element to formatted XML string.

        Args:
            element: XML element

        Returns:
            Formatted XML string
        """
        # Create XML declaration manually
        xml_decl = '<?xml version="1.0" encoding="UTF-8"?>\n'

        # Convert element to string
        xml_string = ET.tostring(element, encoding="unicode")

        return xml_decl + xml_string
