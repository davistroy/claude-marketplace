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

    def _find_element(self, parent, ns_xpath: str, wildcard_xpath: str):
        """Find element with namespace fallback."""
        result = parent.find(ns_xpath, self.namespaces)
        return result if result is not None else parent.find(wildcard_xpath)

    def _findall_elements(self, parent, ns_xpath: str, wildcard_xpath: str):
        """Find all elements with namespace fallback."""
        results = parent.findall(ns_xpath, self.namespaces)
        return results if results else parent.findall(wildcard_xpath)

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

        # Assign lane parents now that all elements are parsed
        self._assign_lane_parents(model)

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
        di_diagram = self._find_element(root, ".//bpmndi:BPMNDiagram", ".//{*}BPMNDiagram")
        if di_diagram is None:
            return

        # Find BPMNPlane
        plane = self._find_element(di_diagram, ".//bpmndi:BPMNPlane", ".//{*}BPMNPlane")
        if plane is None:
            return

        # Parse shapes
        shapes = self._findall_elements(plane, ".//bpmndi:BPMNShape", ".//{*}BPMNShape")

        for shape in shapes:
            bpmn_element = shape.get("bpmnElement")
            if bpmn_element:
                bounds = self._find_element(shape, ".//dc:Bounds", ".//{*}Bounds")
                if bounds is not None:
                    self._di_shapes[bpmn_element] = {
                        "x": float(bounds.get("x", 0)),
                        "y": float(bounds.get("y", 0)),
                        "width": float(bounds.get("width", 0)),
                        "height": float(bounds.get("height", 0)),
                    }

        # Parse edges
        edges = self._findall_elements(plane, ".//bpmndi:BPMNEdge", ".//{*}BPMNEdge")

        for edge in edges:
            bpmn_element = edge.get("bpmnElement")
            if bpmn_element:
                waypoints = []
                points = self._findall_elements(edge, ".//di:waypoint", ".//{*}waypoint")
                for point in points:
                    x = float(point.get("x", 0))
                    y = float(point.get("y", 0))
                    waypoints.append((x, y))
                if waypoints:
                    self._di_edges[bpmn_element] = waypoints

    def _parse_process(self, root: etree._Element, model: BPMNModel) -> None:
        """Parse process elements and flows."""
        # Find process element
        process = self._find_element(root, ".//bpmn:process", ".//{*}process")
        if process is None:
            # Try finding process in collaboration
            process = self._find_element(
                root, ".//bpmn:collaboration//bpmn:process", ".//{*}collaboration//{*}process"
            )

        if process is not None:
            model.process_id = process.get("id")
            model.process_name = process.get("name")
            self._parse_process_contents(process, model, process.get("id"))

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
                        self._parse_process_contents(referenced_process, model, process_ref)

    def _parse_process_contents(
        self, process: etree._Element, model: BPMNModel, process_id: Optional[str] = None
    ) -> None:
        """Parse contents of a process element.

        Args:
            process: Process XML element
            model: BPMN model to populate
            process_id: ID of the containing process (for tracking element ownership)
        """
        # Parse elements
        for child in process:
            # Skip comments and other non-element nodes
            if not isinstance(child.tag, str):
                continue
            tag = self._local_name(child.tag)

            # Handle subProcess FIRST (before generic ALL_ELEMENT_TYPES check)
            # because subProcess is in TASK_TYPES but needs special handling
            if tag == "subProcess":
                # Parse subprocess as element
                element = self._parse_element(child, tag)
                element.properties["_is_subprocess"] = True  # Mark as subprocess container
                if process_id:
                    element.properties["_process_id"] = process_id
                model.elements.append(element)
                # Parse subprocess contents with parent relationship
                self._parse_subprocess_contents(child, model, element.id, process_id)

            elif tag in ALL_ELEMENT_TYPES:
                element = self._parse_element(child, tag)
                # Track which process this element came from
                if process_id:
                    element.properties["_process_id"] = process_id
                model.elements.append(element)

            elif tag in FLOW_TYPES:
                flow = self._parse_flow(child, tag)
                if flow:
                    model.flows.append(flow)

            elif tag == "laneSet":
                self._parse_lane_set(child, model, process_id)

    def _parse_subprocess_contents(
        self,
        subprocess_elem: etree._Element,
        model: BPMNModel,
        subprocess_id: str,
        process_id: Optional[str] = None,
    ) -> None:
        """Parse contents of a subprocess, setting parent relationships.

        Args:
            subprocess_elem: Subprocess XML element
            model: BPMN model to populate
            subprocess_id: ID of the containing subprocess
            process_id: ID of the parent process
        """
        for child in subprocess_elem:
            if not isinstance(child.tag, str):
                continue
            tag = self._local_name(child.tag)

            # Handle nested subprocesses FIRST (before generic ALL_ELEMENT_TYPES check)
            # because subProcess is in TASK_TYPES but needs special handling
            if tag == "subProcess":
                nested = self._parse_element(child, tag)
                nested.subprocess_id = subprocess_id  # Parent is outer subprocess
                nested.properties["_is_subprocess"] = True
                if process_id:
                    nested.properties["_process_id"] = process_id
                model.elements.append(nested)
                # Recursively parse nested subprocess contents
                self._parse_subprocess_contents(child, model, nested.id, process_id)

            # Handle flow nodes (tasks, events, gateways)
            elif tag in ALL_ELEMENT_TYPES or tag in (
                "task",
                "userTask",
                "serviceTask",
                "sendTask",
                "receiveTask",
                "manualTask",
                "businessRuleTask",
                "scriptTask",
                "callActivity",
                "startEvent",
                "endEvent",
                "intermediateCatchEvent",
                "intermediateThrowEvent",
                "boundaryEvent",
                "exclusiveGateway",
                "parallelGateway",
                "inclusiveGateway",
                "eventBasedGateway",
                "complexGateway",
            ):
                element = self._parse_element(child, tag)
                element.subprocess_id = subprocess_id  # Set subprocess parent!
                if process_id:
                    element.properties["_process_id"] = process_id
                model.elements.append(element)

            # Handle sequence flows within subprocess
            elif tag == "sequenceFlow":
                flow = self._parse_flow(child, tag)
                if flow:
                    model.flows.append(flow)

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

        # For boundary events, capture the attachedToRef
        if elem_type == "boundaryEvent":
            attached_to = elem.get("attachedToRef")
            if attached_to:
                properties["attachedToRef"] = attached_to

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
            loop = self._find_element(
                elem, ".//bpmn:multiInstanceLoopCharacteristics", ".//{*}multiInstanceLoopCharacteristics"
            )
            if loop is not None:
                properties["isMultiInstance"] = True
                properties["isSequential"] = loop.get("isSequential", "false") == "true"

            loop = self._find_element(
                elem, ".//bpmn:standardLoopCharacteristics", ".//{*}standardLoopCharacteristics"
            )
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
        cond_expr = self._find_element(elem, ".//bpmn:conditionExpression", ".//{*}conditionExpression")
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
        collaboration = self._find_element(root, ".//bpmn:collaboration", ".//{*}collaboration")
        if collaboration is None:
            return

        # Parse participants (pools)
        participants = self._findall_elements(
            collaboration, ".//bpmn:participant", ".//{*}participant"
        )

        # Build process_id to pool mapping
        process_to_pool: Dict[str, Pool] = {}

        for participant in participants:
            pool = self._parse_pool(participant)
            model.pools.append(pool)

            if pool.process_ref:
                process_to_pool[pool.process_ref] = pool

        # Associate lanes with their correct pools based on process_id
        for lane in model.lanes:
            if not lane.parent_pool_id and lane.process_id:
                if lane.process_id in process_to_pool:
                    lane.parent_pool_id = process_to_pool[lane.process_id].id

        # Associate elements with pools when they don't have lane parents
        # This handles pools without lanes (like external system pools)
        for element in model.elements:
            if element.parent_id:
                continue  # Already has a parent (lane)

            # Find which process this element belongs to using the stored _process_id
            elem_process_id = element.properties.get("_process_id")
            if elem_process_id and elem_process_id in process_to_pool:
                pool = process_to_pool[elem_process_id]
                # Check if pool has lanes
                lanes_for_pool = [l for l in model.lanes if l.parent_pool_id == pool.id]
                if not lanes_for_pool:
                    # Pool has no lanes - element should be direct child of pool
                    element.parent_id = pool.id

        # Parse message flows
        message_flows = self._findall_elements(
            collaboration, ".//bpmn:messageFlow", ".//{*}messageFlow"
        )

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

    def _parse_lane_set(
        self, lane_set: etree._Element, model: BPMNModel, process_id: Optional[str] = None
    ) -> None:
        """Parse lane set element.

        Note: Lanes are parsed to capture their element_refs, but parent_id
        assignment is deferred to _assign_lane_parents() since elements may
        not be parsed yet when laneSet is encountered.

        Args:
            lane_set: Lane set XML element
            model: BPMN model to populate
            process_id: ID of the process containing this lane set
        """
        lanes = self._findall_elements(lane_set, ".//bpmn:lane", ".//{*}lane")

        for lane_elem in lanes:
            lane = self._parse_lane(lane_elem, process_id)
            model.lanes.append(lane)

    def _assign_lane_parents(self, model: BPMNModel) -> None:
        """Assign parent_id to elements based on lane membership.

        Must be called after all elements and lanes are parsed.

        Args:
            model: BPMN model with elements and lanes
        """
        # Build lane element_refs lookup
        for lane in model.lanes:
            for element in model.elements:
                if element.id in lane.element_refs:
                    element.parent_id = lane.id

    def _parse_lane(
        self, lane_elem: etree._Element, process_id: Optional[str] = None
    ) -> Lane:
        """Parse a lane element.

        Args:
            lane_elem: Lane XML element
            process_id: ID of the process containing this lane

        Returns:
            Parsed Lane object
        """
        lane_id = lane_elem.get("id", "")
        lane_name = lane_elem.get("name")

        # Get DI coordinates
        di_info = self._di_shapes.get(lane_id, {})

        # Get flow node references
        element_refs = []
        flow_node_refs = self._findall_elements(
            lane_elem, ".//bpmn:flowNodeRef", ".//{*}flowNodeRef"
        )
        for ref in flow_node_refs:
            if ref.text:
                element_refs.append(ref.text)

        return Lane(
            id=lane_id,
            name=lane_name,
            process_id=process_id,
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
