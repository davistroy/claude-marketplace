"""Validation system for BPMN models."""

from dataclasses import dataclass
from typing import List, Optional, Set

from .models import BPMNModel, BPMNElement


@dataclass
class ValidationWarning:
    """Validation warning or error."""

    level: str  # "error", "warning", "info"
    element_id: Optional[str]
    message: str


class ModelValidator:
    """Validate BPMN model before generation."""

    def validate(self, model: BPMNModel) -> List[ValidationWarning]:
        """Run all validation rules.

        Args:
            model: BPMN model to validate

        Returns:
            List of validation warnings
        """
        warnings = []

        warnings.extend(self._check_start_end_events(model))
        warnings.extend(self._check_valid_references(model))
        warnings.extend(self._check_connected_graph(model))
        warnings.extend(self._check_overlapping_elements(model))
        warnings.extend(self._check_missing_labels(model))

        return warnings

    def _check_start_end_events(self, model: BPMNModel) -> List[ValidationWarning]:
        """Ensure at least one start and end event."""
        warnings = []

        start_events = [e for e in model.elements if e.type == "startEvent"]
        end_events = [e for e in model.elements if e.type == "endEvent"]

        if not start_events:
            warnings.append(
                ValidationWarning(
                    level="warning",
                    element_id=None,
                    message="Process has no start event",
                )
            )

        if not end_events:
            warnings.append(
                ValidationWarning(
                    level="warning", element_id=None, message="Process has no end event"
                )
            )

        return warnings

    def _check_valid_references(self, model: BPMNModel) -> List[ValidationWarning]:
        """Verify sourceRef/targetRef point to existing elements."""
        warnings = []
        element_ids = {e.id for e in model.elements}

        for flow in model.flows:
            if flow.source_ref not in element_ids:
                warnings.append(
                    ValidationWarning(
                        level="error",
                        element_id=flow.id,
                        message=f"Flow '{flow.id}' has invalid source reference: '{flow.source_ref}'",
                    )
                )

            if flow.target_ref not in element_ids:
                warnings.append(
                    ValidationWarning(
                        level="error",
                        element_id=flow.id,
                        message=f"Flow '{flow.id}' has invalid target reference: '{flow.target_ref}'",
                    )
                )

        return warnings

    def _check_connected_graph(self, model: BPMNModel) -> List[ValidationWarning]:
        """Check all elements reachable from start."""
        warnings = []

        if not model.elements:
            return warnings

        # Build adjacency map
        adjacency: dict = {e.id: set() for e in model.elements}
        for flow in model.flows:
            if flow.source_ref in adjacency and flow.target_ref in adjacency:
                adjacency[flow.source_ref].add(flow.target_ref)
                # Also check reverse connectivity for bidirectional traversal
                adjacency[flow.target_ref].add(flow.source_ref)

        # Find start events
        start_events = [e for e in model.elements if e.type == "startEvent"]
        if not start_events:
            return warnings

        # BFS from start events
        visited: Set[str] = set()
        queue = [e.id for e in start_events]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            queue.extend(adjacency.get(current, set()) - visited)

        # Check for unreachable elements
        all_ids = {e.id for e in model.elements}
        unreachable = all_ids - visited

        for elem_id in unreachable:
            warnings.append(
                ValidationWarning(
                    level="info",
                    element_id=elem_id,
                    message=f"Element '{elem_id}' is not connected to the main flow",
                )
            )

        return warnings

    def _check_overlapping_elements(self, model: BPMNModel) -> List[ValidationWarning]:
        """Detect overlapping element positions."""
        warnings = []

        # Only check elements with coordinates
        positioned_elements = [
            e
            for e in model.elements
            if e.x is not None
            and e.y is not None
            and e.width is not None
            and e.height is not None
        ]

        for i, elem1 in enumerate(positioned_elements):
            for elem2 in positioned_elements[i + 1 :]:
                if self._elements_overlap(elem1, elem2):
                    warnings.append(
                        ValidationWarning(
                            level="warning",
                            element_id=elem1.id,
                            message=f"Element '{elem1.id}' overlaps with '{elem2.id}'",
                        )
                    )

        return warnings

    def _elements_overlap(self, e1: BPMNElement, e2: BPMNElement) -> bool:
        """Check if two elements overlap."""
        # Use bounding box intersection
        e1_right = e1.x + e1.width
        e1_bottom = e1.y + e1.height
        e2_right = e2.x + e2.width
        e2_bottom = e2.y + e2.height

        # Check for no overlap conditions
        if e1.x >= e2_right or e2.x >= e1_right:
            return False
        if e1.y >= e2_bottom or e2.y >= e1_bottom:
            return False

        return True

    def _check_missing_labels(self, model: BPMNModel) -> List[ValidationWarning]:
        """Warn about elements without labels."""
        warnings = []

        # Only check tasks and gateways - events without names are common
        labeled_types = {
            "task",
            "userTask",
            "serviceTask",
            "scriptTask",
            "sendTask",
            "receiveTask",
            "businessRuleTask",
            "manualTask",
            "callActivity",
        }

        for elem in model.elements:
            if elem.type in labeled_types and not elem.name:
                warnings.append(
                    ValidationWarning(
                        level="info",
                        element_id=elem.id,
                        message=f"Element '{elem.id}' has no label",
                    )
                )

        return warnings


def validate_model(model: BPMNModel) -> List[ValidationWarning]:
    """Validate a BPMN model.

    Args:
        model: BPMN model to validate

    Returns:
        List of validation warnings
    """
    validator = ModelValidator()
    return validator.validate(model)
