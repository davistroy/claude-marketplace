"""BPMN 2.0 XML parser."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from lxml import etree

from .models import BPMNElement, BPMNFlow, Pool, Lane, BPMNModel
from .constants import (
    BPMN_NAMESPACES,
    ALL_ELEMENT_TYPES,
    FLOW_TYPES,
    ELEMENT_DIMENSIONS,
)
from .exceptions import BPMNParseError


class BPMNParser:
    """Parser for BPMN 2.0 XML files."""

    def __init__(self):
        """Initialize parser with BPMN namespaces."""
        self.namespaces = BPMN_NAMESPACES
        self._di_shapes: Dict[str, Dict] = {}
        self._di_edges: Dict[str, List[Tuple[float, float]]] = {}

    def parse(self, source: Union[str, Path]) -> BPMNModel:
        """Parse a BPMN file or XML string.

        Args:
            source: File path or XML string

        Returns:
            Parsed BPMNModel

        Raises:
            BPMNParseError: If parsing fails
        """
        try:
            if isinstance(source, Path) or (
                isinstance(source, str) and not source.strip().startswith("<")
            ):
                # It's a file path
                tree = etree.parse(str(source))
                root = tree.getroot()
            else:
                # It's an XML string
                root = etree.fromstring(source.encode() if isinstance(source, str) else source)
        except etree.XMLSyntaxError as e:
            raise BPMNParseError(f"Invalid XML: {e}") from e
        except FileNotFoundError as e:
            raise BPMNParseError(f"File not found: {e}") from e
        except Exception as e:
            raise BPMNParseError(f"Failed to parse BPMN: {e}") from e

        # Detect namespace prefix used in the document
        self._detect_namespaces(root)

        # Parse DI information first
        self._parse_di(root)

        # Parse model
        model = BPMNModel()
        model.has_di_coordinates = bool(self._di_shapes)

        # Parse process
        self._parse_process(root, model)

        # Parse collaboration (pools and lanes)
        self._parse_collaboration(root, model)

        return model

    def _detect_namespaces(self, root: etree._Element) -> None:
        """Detect and update namespace mappings from root element."""
        nsmap = root.nsmap
        # Check for common BPMN namespace variations
        for prefix, uri in nsmap.items():
            # Handle Python 3.14+ / lxml compatibility - ensure strings
            if not isinstance(uri, str):
                continue
            if prefix is None:
                # Default namespace
                if "BPMN" in uri or "bpmn" in uri.lower():
                    self.namespaces["bpmn"] = uri
            elif isinstance(prefix, str):
                if "bpmn" in prefix.lower() and "di" not in prefix.lower():
                    self.namespaces["bpmn"] = uri
                elif prefix == "bpmndi" or "bpmndi" in prefix.lower():
                    self.namespaces["bpmndi"] = uri
                elif prefix == "dc":
                    self.namespaces["dc"] = uri
                elif prefix == "di":
                    self.namespaces["di"] = uri

    def _parse_di(self, root: etree._Element) -> None:
        """Parse BPMN Diagram Interchange information."""
        self._di_shapes = {}
        self._di_edges = {}

        # Find BPMNDiagram element
        di_diagram = root.find(".//bpmndi:BPMNDiagram", self.namespaces)
        if di_diagram is None:
            # Try without namespace
            di_diagram = root.find(".//{*}BPMNDiagram")
        if di_diagram is None:
            return

        # Find BPMNPlane
        plane = di_diagram.find(".//bpmndi:BPMNPlane", self.namespaces)
        if plane is None:
            plane = di_diagram.find(".//{*}BPMNPlane")
        if plane is None:
            return

        # Parse shapes
        shapes = plane.findall(".//bpmndi:BPMNShape", self.namespaces)
        if not shapes:
            shapes = plane.findall(".//{*}BPMNShape")

        for shape in shapes:
            bpmn_element = shape.get("bpmnElement")
            if bpmn_element:
                bounds = shape.find(".//dc:Bounds", self.namespaces)
                if bounds is None:
                    bounds = shape.find(".//{*}Bounds")
                if bounds is not None:
                    self._di_shapes[bpmn_element] = {
                        "x": float(bounds.get("x", 0)),
                        "y": float(bounds.get("y", 0)),
                        "width": float(bounds.get("width", 0)),
                        "height": float(bounds.get("height", 0)),
                    }

        # Parse edges
        edges = plane.findall(".//bpmndi:BPMNEdge", self.namespaces)
        if not edges:
            edges = plane.findall(".//{*}BPMNEdge")

        for edge in edges:
            bpmn_element = edge.get("bpmnElement")
            if bpmn_element:
                waypoints = []
                points = edge.findall(".//di:waypoint", self.namespaces)
                if not points:
                    points = edge.findall(".//{*}waypoint")
                for point in points:
                    x = float(point.get("x", 0))
                    y = float(point.get("y", 0))
                    waypoints.append((x, y))
                if waypoints:
                    self._di_edges[bpmn_element] = waypoints

    def _parse_process(self, root: etree._Element, model: BPMNModel) -> None:
        """Parse process elements and flows."""
        # Find process element
        process = root.find(".//bpmn:process", self.namespaces)
        if process is None:
            process = root.find(".//{*}process")
        if process is None:
            # Try finding process in collaboration
            process = root.find(".//bpmn:collaboration//bpmn:process", self.namespaces)
            if process is None:
                process = root.find(".//{*}collaboration//{*}process")

        if process is not None:
            model.process_id = process.get("id")
            model.process_name = process.get("name")
            self._parse_process_contents(process, model)

        # Also check for processes referenced by participants
        for participant in root.iter():
            # Skip comments and other non-element nodes
            if not isinstance(participant.tag, str):
                continue
            if participant.tag.endswith("participant"):
                process_ref = participant.get("processRef")
                if process_ref:
                    referenced_process = root.find(
                        f".//*[@id='{process_ref}']"
                    )
                    if referenced_process is not None and referenced_process not in [process]:
                        self._parse_process_contents(referenced_process, model)

    def _parse_process_contents(
        self, process: etree._Element, model: BPMNModel
    ) -> None:
        """Parse contents of a process element."""
        # Parse elements
        for child in process:
            # Skip comments and other non-element nodes
            if not isinstance(child.tag, str):
                continue
            tag = self._local_name(child.tag)

            if tag in ALL_ELEMENT_TYPES:
                element = self._parse_element(child, tag)
                model.elements.append(element)

            elif tag in FLOW_TYPES:
                flow = self._parse_flow(child, tag)
                if flow:
                    model.flows.append(flow)

            elif tag == "laneSet":
                self._parse_lane_set(child, model)

            elif tag == "subProcess":
                # Parse subprocess as element
                element = self._parse_element(child, tag)
                model.elements.append(element)
                # Also parse its contents
                self._parse_process_contents(child, model)

    def _parse_element(self, elem: etree._Element, elem_type: str) -> BPMNElement:
        """Parse a BPMN element."""
        elem_id = elem.get("id", "")
        elem_name = elem.get("name")

        # Get DI coordinates if available
        di_info = self._di_shapes.get(elem_id, {})
        x = di_info.get("x")
        y = di_info.get("y")
        width = di_info.get("width")
        height = di_info.get("height")

        # If no DI dimensions, use defaults
        if width is None or height is None:
            default_dims = ELEMENT_DIMENSIONS.get(elem_type, (120, 80))
            width = width or default_dims[0]
            height = height or default_dims[1]

        # Parse element-specific properties
        properties = self._parse_element_properties(elem, elem_type)

        return BPMNElement(
            id=elem_id,
            type=elem_type,
            name=elem_name,
            x=x,
            y=y,
            width=width,
            height=height,
            properties=properties,
        )

    def _parse_element_properties(
        self, elem: etree._Element, elem_type: str
    ) -> Dict:
        """Parse element-specific properties."""
        properties = {}

        # Event definitions
        for child in elem:
            child_tag = self._local_name(child.tag)
            if child_tag.endswith("EventDefinition"):
                properties["eventDefinition"] = child_tag.replace(
                    "EventDefinition", ""
                )

        # Gateway properties
        if "Gateway" in elem_type:
            default_flow = elem.get("default")
            if default_flow:
                properties["defaultFlow"] = default_flow

        # Task properties
        if "Task" in elem_type or elem_type == "task":
            # Check for loop characteristics
            loop = elem.find(".//bpmn:multiInstanceLoopCharacteristics", self.namespaces)
            if loop is None:
                loop = elem.find(".//{*}multiInstanceLoopCharacteristics")
            if loop is not None:
                properties["isMultiInstance"] = True
                properties["isSequential"] = loop.get("isSequential", "false") == "true"

            loop = elem.find(".//bpmn:standardLoopCharacteristics", self.namespaces)
            if loop is None:
                loop = elem.find(".//{*}standardLoopCharacteristics")
            if loop is not None:
                properties["isLoop"] = True

        return properties

    def _parse_flow(self, elem: etree._Element, flow_type: str) -> Optional[BPMNFlow]:
        """Parse a flow element."""
        flow_id = elem.get("id", "")
        source_ref = elem.get("sourceRef", "")
        target_ref = elem.get("targetRef", "")

        if not source_ref or not target_ref:
            return None

        flow_name = elem.get("name")

        # Check for condition
        condition = None
        cond_expr = elem.find(".//bpmn:conditionExpression", self.namespaces)
        if cond_expr is None:
            cond_expr = elem.find(".//{*}conditionExpression")
        if cond_expr is not None:
            condition = cond_expr.text

        # Get waypoints from DI
        waypoints = self._di_edges.get(flow_id, [])

        return BPMNFlow(
            id=flow_id,
            type=flow_type,
            source_ref=source_ref,
            target_ref=target_ref,
            name=flow_name,
            condition=condition,
            is_default=False,  # Will be set later based on gateway default
            waypoints=waypoints,
        )

    def _parse_collaboration(self, root: etree._Element, model: BPMNModel) -> None:
        """Parse collaboration (pools and message flows)."""
        collaboration = root.find(".//bpmn:collaboration", self.namespaces)
        if collaboration is None:
            collaboration = root.find(".//{*}collaboration")
        if collaboration is None:
            return

        # Parse participants (pools)
        participants = collaboration.findall(".//bpmn:participant", self.namespaces)
        if not participants:
            participants = collaboration.findall(".//{*}participant")

        for participant in participants:
            pool = self._parse_pool(participant)
            model.pools.append(pool)

        # Parse message flows
        message_flows = collaboration.findall(".//bpmn:messageFlow", self.namespaces)
        if not message_flows:
            message_flows = collaboration.findall(".//{*}messageFlow")

        for mf in message_flows:
            flow = self._parse_flow(mf, "messageFlow")
            if flow:
                model.flows.append(flow)

    def _parse_pool(self, participant: etree._Element) -> Pool:
        """Parse a participant (pool) element."""
        pool_id = participant.get("id", "")
        pool_name = participant.get("name")
        process_ref = participant.get("processRef")

        # Get DI coordinates
        di_info = self._di_shapes.get(pool_id, {})

        return Pool(
            id=pool_id,
            name=pool_name,
            process_ref=process_ref,
            x=di_info.get("x"),
            y=di_info.get("y"),
            width=di_info.get("width"),
            height=di_info.get("height"),
        )

    def _parse_lane_set(self, lane_set: etree._Element, model: BPMNModel) -> None:
        """Parse lane set element."""
        lanes = lane_set.findall(".//bpmn:lane", self.namespaces)
        if not lanes:
            lanes = lane_set.findall(".//{*}lane")

        for lane_elem in lanes:
            lane = self._parse_lane(lane_elem)
            model.lanes.append(lane)

            # Update element parent IDs based on lane flowNodeRefs
            for element in model.elements:
                if element.id in lane.element_refs:
                    element.parent_id = lane.id

    def _parse_lane(self, lane_elem: etree._Element) -> Lane:
        """Parse a lane element."""
        lane_id = lane_elem.get("id", "")
        lane_name = lane_elem.get("name")

        # Get DI coordinates
        di_info = self._di_shapes.get(lane_id, {})

        # Get flow node references
        element_refs = []
        flow_node_refs = lane_elem.findall(".//bpmn:flowNodeRef", self.namespaces)
        if not flow_node_refs:
            flow_node_refs = lane_elem.findall(".//{*}flowNodeRef")
        for ref in flow_node_refs:
            if ref.text:
                element_refs.append(ref.text)

        return Lane(
            id=lane_id,
            name=lane_name,
            x=di_info.get("x"),
            y=di_info.get("y"),
            width=di_info.get("width"),
            height=di_info.get("height"),
            element_refs=element_refs,
        )

    def _local_name(self, tag) -> str:
        """Get local name from a potentially namespaced tag."""
        # Handle Python 3.14+ / lxml compatibility - ensure string
        if not isinstance(tag, str):
            tag = str(tag) if tag is not None else ""
        if "}" in tag:
            return tag.split("}")[1]
        return tag

    def _mark_default_flows(self, model: BPMNModel) -> None:
        """Mark flows as default based on gateway default attribute."""
        for element in model.elements:
            default_flow_id = element.properties.get("defaultFlow")
            if default_flow_id:
                flow = model.get_flow_by_id(default_flow_id)
                if flow:
                    flow.is_default = True


def parse_bpmn(source: Union[str, Path]) -> BPMNModel:
    """Parse a BPMN file or XML string.

    Convenience function for simple parsing.

    Args:
        source: File path or XML string

    Returns:
        Parsed BPMNModel
    """
    parser = BPMNParser()
    model = parser.parse(source)
    parser._mark_default_flows(model)
    return model
