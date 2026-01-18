"""Theme system for BPMN diagrams."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class BPMNTheme:
    """Configurable color theme for BPMN diagrams."""

    # Event colors
    start_event_fill: str = "#d5e8d4"
    start_event_stroke: str = "#82b366"
    end_event_fill: str = "#f8cecc"
    end_event_stroke: str = "#b85450"
    intermediate_event_fill: str = "#fff2cc"
    intermediate_event_stroke: str = "#d6b656"

    # Task colors
    task_fill: str = "#dae8fc"
    task_stroke: str = "#6c8ebf"
    script_task_fill: str = "#e1d5e7"
    script_task_stroke: str = "#9673a6"
    business_rule_task_fill: str = "#ffe6cc"
    business_rule_task_stroke: str = "#d79b00"
    manual_task_fill: str = "#f5f5f5"
    manual_task_stroke: str = "#666666"

    # Gateway colors
    gateway_fill: str = "#fff2cc"
    gateway_stroke: str = "#d6b656"

    # Container colors
    pool_fill: str = "#f5f5f5"
    pool_stroke: str = "#666666"
    lane_fill: str = "#ffffff"
    lane_stroke: str = "#666666"

    # Flow colors
    sequence_flow_stroke: str = "#666666"
    message_flow_stroke: str = "#666666"

    # Text styling
    font_family: str = "Helvetica"
    font_size: int = 12
    font_color: str = "#333333"

    def style_for(self, element_type: str) -> str:
        """Generate complete style string for element type.

        Args:
            element_type: BPMN element type

        Returns:
            Draw.io style string
        """
        styles = {
            "startEvent": f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor={self.start_event_fill};strokeColor={self.start_event_stroke};perimeter=ellipsePerimeter;",
            "endEvent": f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor={self.end_event_fill};strokeColor={self.end_event_stroke};strokeWidth=3;perimeter=ellipsePerimeter;",
            "intermediateCatchEvent": f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor={self.intermediate_event_fill};strokeColor={self.intermediate_event_stroke};strokeWidth=2;perimeter=ellipsePerimeter;",
            "intermediateThrowEvent": f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor={self.intermediate_event_fill};strokeColor={self.intermediate_event_stroke};strokeWidth=2;perimeter=ellipsePerimeter;",
            "boundaryEvent": f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor={self.intermediate_event_fill};strokeColor={self.intermediate_event_stroke};strokeWidth=2;perimeter=ellipsePerimeter;",
            "task": f"rounded=1;whiteSpace=wrap;html=1;fillColor={self.task_fill};strokeColor={self.task_stroke};arcSize=10;",
            "userTask": f"rounded=1;whiteSpace=wrap;html=1;fillColor={self.task_fill};strokeColor={self.task_stroke};arcSize=10;",
            "serviceTask": f"rounded=1;whiteSpace=wrap;html=1;fillColor={self.task_fill};strokeColor={self.task_stroke};arcSize=10;",
            "scriptTask": f"rounded=1;whiteSpace=wrap;html=1;fillColor={self.script_task_fill};strokeColor={self.script_task_stroke};arcSize=10;",
            "businessRuleTask": f"rounded=1;whiteSpace=wrap;html=1;fillColor={self.business_rule_task_fill};strokeColor={self.business_rule_task_stroke};arcSize=10;",
            "manualTask": f"rounded=1;whiteSpace=wrap;html=1;fillColor={self.manual_task_fill};strokeColor={self.manual_task_stroke};arcSize=10;",
            "subProcess": f"rounded=1;whiteSpace=wrap;html=1;container=1;collapsible=1;childLayout=stackLayout;horizontalStack=0;resizeParent=1;resizeLast=0;dropTarget=1;fontStyle=1;swimlane=0;startSize=26;fillColor={self.task_fill};strokeColor={self.task_stroke};",
            "callActivity": f"rounded=1;whiteSpace=wrap;html=1;fillColor={self.task_fill};strokeColor={self.task_stroke};arcSize=10;strokeWidth=3;",
            "exclusiveGateway": f"rhombus;whiteSpace=wrap;html=1;fillColor={self.gateway_fill};strokeColor={self.gateway_stroke};perimeter=rhombusPerimeter;",
            "parallelGateway": f"rhombus;whiteSpace=wrap;html=1;fillColor={self.gateway_fill};strokeColor={self.gateway_stroke};perimeter=rhombusPerimeter;",
            "inclusiveGateway": f"rhombus;whiteSpace=wrap;html=1;fillColor={self.gateway_fill};strokeColor={self.gateway_stroke};perimeter=rhombusPerimeter;",
        }
        return styles.get(element_type, styles["task"])


# Predefined themes
THEMES: Dict[str, BPMNTheme] = {
    "default": BPMNTheme(),

    "blueprint": BPMNTheme(
        start_event_fill="#e3f2fd",
        start_event_stroke="#1976d2",
        end_event_fill="#e3f2fd",
        end_event_stroke="#1976d2",
        intermediate_event_fill="#e3f2fd",
        intermediate_event_stroke="#1976d2",
        task_fill="#bbdefb",
        task_stroke="#1976d2",
        script_task_fill="#bbdefb",
        script_task_stroke="#1976d2",
        business_rule_task_fill="#bbdefb",
        business_rule_task_stroke="#1976d2",
        manual_task_fill="#e3f2fd",
        manual_task_stroke="#1976d2",
        gateway_fill="#e3f2fd",
        gateway_stroke="#1976d2",
        pool_fill="#e3f2fd",
        pool_stroke="#1976d2",
        sequence_flow_stroke="#1976d2",
    ),

    "monochrome": BPMNTheme(
        start_event_fill="#ffffff",
        start_event_stroke="#333333",
        end_event_fill="#f5f5f5",
        end_event_stroke="#333333",
        intermediate_event_fill="#ffffff",
        intermediate_event_stroke="#333333",
        task_fill="#ffffff",
        task_stroke="#333333",
        script_task_fill="#ffffff",
        script_task_stroke="#333333",
        business_rule_task_fill="#ffffff",
        business_rule_task_stroke="#333333",
        manual_task_fill="#ffffff",
        manual_task_stroke="#333333",
        gateway_fill="#ffffff",
        gateway_stroke="#333333",
        pool_fill="#ffffff",
        pool_stroke="#333333",
        lane_fill="#ffffff",
        lane_stroke="#333333",
        sequence_flow_stroke="#333333",
        message_flow_stroke="#333333",
    ),

    "high_contrast": BPMNTheme(
        start_event_fill="#c8e6c9",
        start_event_stroke="#2e7d32",
        end_event_fill="#ffcdd2",
        end_event_stroke="#c62828",
        intermediate_event_fill="#fff9c4",
        intermediate_event_stroke="#f57f17",
        task_fill="#e3f2fd",
        task_stroke="#0d47a1",
        script_task_fill="#f3e5f5",
        script_task_stroke="#6a1b9a",
        business_rule_task_fill="#fff3e0",
        business_rule_task_stroke="#e65100",
        manual_task_fill="#eceff1",
        manual_task_stroke="#37474f",
        gateway_fill="#fff9c4",
        gateway_stroke="#f57f17",
        pool_fill="#eceff1",
        pool_stroke="#37474f",
    ),
}


def get_theme(name: str) -> BPMNTheme:
    """Get a theme by name.

    Args:
        name: Theme name

    Returns:
        BPMNTheme instance
    """
    return THEMES.get(name, THEMES["default"])
