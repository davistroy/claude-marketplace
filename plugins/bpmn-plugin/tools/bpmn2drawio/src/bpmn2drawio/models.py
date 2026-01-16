"""Data models for BPMN elements and structures."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class BPMNElement:
    """Represents a BPMN element (task, event, gateway, etc.)."""

    id: str
    type: str  # e.g., "userTask", "exclusiveGateway", "startEvent"
    name: Optional[str] = None
    x: Optional[float] = None  # From BPMN DI, None if missing
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    parent_id: Optional[str] = None  # Lane or subprocess container
    subprocess_id: Optional[str] = None  # ID of containing subprocess if this is an internal element
    properties: Dict[str, Any] = field(default_factory=dict)

    def has_coordinates(self) -> bool:
        """Check if element has DI coordinates."""
        return self.x is not None and self.y is not None

    def has_dimensions(self) -> bool:
        """Check if element has dimensions."""
        return self.width is not None and self.height is not None

    def center(self) -> Optional[Tuple[float, float]]:
        """Get center point of element if coordinates and dimensions are available."""
        if self.has_coordinates() and self.has_dimensions():
            return (self.x + self.width / 2, self.y + self.height / 2)
        return None


@dataclass
class BPMNFlow:
    """Represents a flow connection (sequence, message, association)."""

    id: str
    type: str  # "sequenceFlow", "messageFlow", "association"
    source_ref: str
    target_ref: str
    name: Optional[str] = None
    condition: Optional[str] = None
    is_default: bool = False
    waypoints: List[Tuple[float, float]] = field(default_factory=list)

    def has_waypoints(self) -> bool:
        """Check if flow has DI waypoints."""
        return len(self.waypoints) > 0


@dataclass
class Pool:
    """Represents a BPMN pool (participant)."""

    id: str
    name: Optional[str] = None
    process_ref: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    lanes: List[str] = field(default_factory=list)  # Lane IDs
    is_horizontal: bool = True

    def has_coordinates(self) -> bool:
        """Check if pool has DI coordinates."""
        return self.x is not None and self.y is not None


@dataclass
class Lane:
    """Represents a lane within a pool."""

    id: str
    name: Optional[str] = None
    parent_pool_id: str = ""
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    element_refs: List[str] = field(default_factory=list)  # Elements in this lane

    def has_coordinates(self) -> bool:
        """Check if lane has DI coordinates."""
        return self.x is not None and self.y is not None


@dataclass
class BPMNModel:
    """Complete parsed BPMN model."""

    elements: List[BPMNElement] = field(default_factory=list)
    flows: List[BPMNFlow] = field(default_factory=list)
    pools: List[Pool] = field(default_factory=list)
    lanes: List[Lane] = field(default_factory=list)
    has_di_coordinates: bool = False
    process_id: Optional[str] = None
    process_name: Optional[str] = None

    def get_element_by_id(self, element_id: str) -> Optional[BPMNElement]:
        """Get element by ID."""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None

    def get_flow_by_id(self, flow_id: str) -> Optional[BPMNFlow]:
        """Get flow by ID."""
        for flow in self.flows:
            if flow.id == flow_id:
                return flow
        return None

    def get_pool_by_id(self, pool_id: str) -> Optional[Pool]:
        """Get pool by ID."""
        for pool in self.pools:
            if pool.id == pool_id:
                return pool
        return None

    def get_lane_by_id(self, lane_id: str) -> Optional[Lane]:
        """Get lane by ID."""
        for lane in self.lanes:
            if lane.id == lane_id:
                return lane
        return None

    def get_elements_in_lane(self, lane_id: str) -> List[BPMNElement]:
        """Get all elements in a specific lane."""
        return [e for e in self.elements if e.parent_id == lane_id]

    def get_start_events(self) -> List[BPMNElement]:
        """Get all start events."""
        return [e for e in self.elements if e.type == "startEvent"]

    def get_end_events(self) -> List[BPMNElement]:
        """Get all end events."""
        return [e for e in self.elements if e.type == "endEvent"]

    def get_outgoing_flows(self, element_id: str) -> List[BPMNFlow]:
        """Get all flows originating from an element."""
        return [f for f in self.flows if f.source_ref == element_id]

    def get_incoming_flows(self, element_id: str) -> List[BPMNFlow]:
        """Get all flows targeting an element."""
        return [f for f in self.flows if f.target_ref == element_id]
