"""Tests for task and event icon definitions and creation functions."""

from bpmn2drawio.models import BPMNElement
from bpmn2drawio.icons import (
    TASK_ICONS,
    EVENT_ICONS,
    create_task_icon,
    create_event_icon,
    get_task_icon_style,
    get_event_icon_style,
)


class TestTaskIconDefinitions:
    """Tests for TASK_ICONS dictionary completeness and structure."""

    EXPECTED_TASK_TYPES = [
        "userTask",
        "serviceTask",
        "scriptTask",
        "sendTask",
        "receiveTask",
        "businessRuleTask",
        "manualTask",
    ]

    def test_all_expected_task_types_have_icons(self):
        """All standard BPMN task types have icon mappings."""
        for task_type in self.EXPECTED_TASK_TYPES:
            assert task_type in TASK_ICONS, f"Missing icon for {task_type}"

    def test_task_icon_entries_have_required_keys(self):
        """Each task icon entry has style, size, and offset."""
        for task_type, icon_def in TASK_ICONS.items():
            assert "style" in icon_def, f"{task_type} missing 'style'"
            assert "size" in icon_def, f"{task_type} missing 'size'"
            assert "offset" in icon_def, f"{task_type} missing 'offset'"

    def test_task_icon_styles_are_nonempty_strings(self):
        """All task icon style values are non-empty strings."""
        for task_type, icon_def in TASK_ICONS.items():
            style = icon_def["style"]
            assert isinstance(style, str), f"{task_type} style is not a string"
            assert len(style) > 0, f"{task_type} style is empty"

    def test_task_icon_sizes_are_positive_tuples(self):
        """All task icon sizes are 2-tuples of positive integers."""
        for task_type, icon_def in TASK_ICONS.items():
            size = icon_def["size"]
            assert isinstance(size, tuple), f"{task_type} size is not a tuple"
            assert len(size) == 2, f"{task_type} size is not a 2-tuple"
            assert size[0] > 0, f"{task_type} width <= 0"
            assert size[1] > 0, f"{task_type} height <= 0"

    def test_task_icon_offsets_are_tuples(self):
        """All task icon offsets are 2-tuples."""
        for task_type, icon_def in TASK_ICONS.items():
            offset = icon_def["offset"]
            assert isinstance(offset, tuple), f"{task_type} offset is not a tuple"
            assert len(offset) == 2, f"{task_type} offset is not a 2-tuple"

    def test_script_task_uses_purple_color(self):
        """Script task icon uses purple (#9673a6) matching its distinct style."""
        style = TASK_ICONS["scriptTask"]["style"]
        assert "#9673a6" in style

    def test_user_task_uses_blue_color(self):
        """User task icon uses blue (#6c8ebf)."""
        style = TASK_ICONS["userTask"]["style"]
        assert "#6c8ebf" in style

    def test_business_rule_task_uses_orange_color(self):
        """Business rule task icon uses orange (#d79b00)."""
        style = TASK_ICONS["businessRuleTask"]["style"]
        assert "#d79b00" in style


class TestEventIconDefinitions:
    """Tests for EVENT_ICONS dictionary completeness and structure."""

    def test_event_icons_are_nonempty(self):
        """EVENT_ICONS contains entries."""
        assert len(EVENT_ICONS) > 0

    def test_event_icon_entries_have_required_keys(self):
        """Each event icon entry has style and size."""
        for key, icon_def in EVENT_ICONS.items():
            assert "style" in icon_def, f"{key} missing 'style'"
            assert "size" in icon_def, f"{key} missing 'size'"

    def test_event_icon_styles_are_nonempty_strings(self):
        """All event icon style values are non-empty strings."""
        for key, icon_def in EVENT_ICONS.items():
            style = icon_def["style"]
            assert isinstance(style, str), f"{key} style is not a string"
            assert len(style) > 0, f"{key} style is empty"

    def test_event_icon_sizes_are_positive_tuples(self):
        """All event icon sizes are 2-tuples of positive values."""
        for key, icon_def in EVENT_ICONS.items():
            size = icon_def["size"]
            assert isinstance(size, tuple), f"{key} size is not a tuple"
            assert len(size) == 2, f"{key} size is not a 2-tuple"
            assert size[0] > 0, f"{key} width <= 0"
            assert size[1] > 0, f"{key} height <= 0"

    def test_start_event_icons_use_green_color(self):
        """Start event icons use green (#82b366) stroke color."""
        start_keys = [k for k in EVENT_ICONS if k.startswith("startEvent_")]
        assert len(start_keys) > 0, "No startEvent icons found"
        for key in start_keys:
            assert "#82b366" in EVENT_ICONS[key]["style"], f"{key} missing green color"

    def test_end_event_icons_use_red_color(self):
        """End event icons use red (#b85450) stroke/fill color."""
        end_keys = [k for k in EVENT_ICONS if k.startswith("endEvent_")]
        assert len(end_keys) > 0, "No endEvent icons found"
        for key in end_keys:
            assert "#b85450" in EVENT_ICONS[key]["style"], f"{key} missing red color"

    def test_intermediate_catch_event_icons_use_yellow_color(self):
        """Intermediate catch event icons use yellow (#d6b656) stroke color."""
        catch_keys = [k for k in EVENT_ICONS if k.startswith("intermediateCatchEvent_")]
        assert len(catch_keys) > 0, "No intermediateCatchEvent icons found"
        for key in catch_keys:
            assert "#d6b656" in EVENT_ICONS[key]["style"], f"{key} missing yellow color"

    def test_same_event_type_different_definitions_have_different_icons(self):
        """Different event definitions for the same event type produce different icon keys."""
        # startEvent_message vs startEvent_timer should both exist with different styles
        msg_style = EVENT_ICONS["startEvent_message"]["style"]
        timer_style = EVENT_ICONS["startEvent_timer"]["style"]
        assert msg_style != timer_style

    def test_boundary_event_icons_exist(self):
        """Boundary event icons are defined."""
        boundary_keys = [k for k in EVENT_ICONS if k.startswith("boundaryEvent_")]
        assert len(boundary_keys) >= 5, (
            f"Expected at least 5 boundary event icons, got {len(boundary_keys)}"
        )

    def test_intermediate_throw_event_icons_exist(self):
        """Intermediate throw event icons are defined."""
        throw_keys = [k for k in EVENT_ICONS if k.startswith("intermediateThrowEvent_")]
        assert len(throw_keys) >= 3, (
            f"Expected at least 3 throw event icons, got {len(throw_keys)}"
        )


class TestCreateTaskIcon:
    """Tests for create_task_icon function."""

    def test_returns_cell_and_incremented_counter(self):
        """create_task_icon returns (mxCell, counter+1) for known task types."""
        element = BPMNElement(id="t1", type="userTask", width=120, height=80)
        result = create_task_icon(element, "parent_1", 100)

        assert result is not None
        cell, counter = result
        assert counter == 101

    def test_cell_is_valid_mxcell_element(self):
        """Returned cell is a proper mxCell XML element."""
        element = BPMNElement(id="t1", type="serviceTask", width=120, height=80)
        cell, _ = create_task_icon(element, "parent_1", 50)

        assert cell.tag == "mxCell"
        assert cell.get("vertex") == "1"
        assert cell.get("value") == ""
        assert cell.get("id") == "50"

    def test_cell_parent_matches_argument(self):
        """Cell parent attribute matches the given parent_cell_id."""
        element = BPMNElement(id="t1", type="userTask", width=120, height=80)
        cell, _ = create_task_icon(element, "my_parent", 10)

        assert cell.get("parent") == "my_parent"

    def test_cell_has_geometry_subelement(self):
        """Cell contains an mxGeometry child with proper attributes."""
        element = BPMNElement(id="t1", type="sendTask", width=120, height=80)
        cell, _ = create_task_icon(element, "parent_1", 10)

        geometry = cell.find("mxGeometry")
        assert geometry is not None
        assert geometry.get("as") == "geometry"
        assert float(geometry.get("width")) == 16
        assert float(geometry.get("height")) == 12  # sendTask has (16, 12) size

    def test_geometry_offset_matches_icon_definition(self):
        """Geometry x/y offset matches the offset in TASK_ICONS."""
        element = BPMNElement(id="t1", type="userTask", width=120, height=80)
        cell, _ = create_task_icon(element, "parent_1", 10)

        geometry = cell.find("mxGeometry")
        assert float(geometry.get("x")) == 5.0
        assert float(geometry.get("y")) == 5.0

    def test_returns_none_for_generic_task(self):
        """Generic 'task' type has no icon (returns None)."""
        element = BPMNElement(id="t1", type="task")
        result = create_task_icon(element, "parent_1", 10)
        assert result is None

    def test_returns_none_for_unknown_type(self):
        """Unknown element type returns None."""
        element = BPMNElement(id="t1", type="unknownTaskType")
        result = create_task_icon(element, "parent_1", 10)
        assert result is None

    def test_returns_none_for_gateway_type(self):
        """Non-task element types (gateway) return None."""
        element = BPMNElement(id="gw1", type="exclusiveGateway")
        result = create_task_icon(element, "parent_1", 10)
        assert result is None

    def test_all_task_types_produce_icons(self):
        """Every task type in TASK_ICONS successfully creates an icon cell."""
        for task_type in TASK_ICONS:
            element = BPMNElement(id="t1", type=task_type, width=120, height=80)
            result = create_task_icon(element, "parent_1", 10)
            assert result is not None, f"create_task_icon returned None for {task_type}"


class TestCreateEventIcon:
    """Tests for create_event_icon function."""

    def test_returns_cell_and_incremented_counter(self):
        """create_event_icon returns (mxCell, counter+1) for known event/definition combos."""
        element = BPMNElement(
            id="e1",
            type="startEvent",
            width=36,
            height=36,
            properties={"eventDefinition": "timer"},
        )
        result = create_event_icon(element, "parent_1", 200)

        assert result is not None
        cell, counter = result
        assert counter == 201

    def test_cell_is_valid_mxcell_element(self):
        """Returned cell is a proper mxCell XML element."""
        element = BPMNElement(
            id="e1",
            type="endEvent",
            width=36,
            height=36,
            properties={"eventDefinition": "message"},
        )
        cell, _ = create_event_icon(element, "parent_1", 50)

        assert cell.tag == "mxCell"
        assert cell.get("vertex") == "1"
        assert cell.get("value") == ""

    def test_event_icon_centered_in_event_circle(self):
        """Icon geometry is centered within the event's dimensions."""
        element = BPMNElement(
            id="e1",
            type="startEvent",
            width=36,
            height=36,
            properties={"eventDefinition": "timer"},
        )
        cell, _ = create_event_icon(element, "parent_1", 10)

        geometry = cell.find("mxGeometry")
        icon_width = float(geometry.get("width"))
        icon_height = float(geometry.get("height"))
        x = float(geometry.get("x"))
        y = float(geometry.get("y"))

        expected_x = (36 - icon_width) / 2
        expected_y = (36 - icon_height) / 2
        assert abs(x - expected_x) < 0.01
        assert abs(y - expected_y) < 0.01

    def test_returns_none_for_plain_event_no_definition(self):
        """Event without eventDefinition property returns None."""
        element = BPMNElement(
            id="e1",
            type="startEvent",
            width=36,
            height=36,
            properties={},
        )
        result = create_event_icon(element, "parent_1", 10)
        assert result is None

    def test_returns_none_for_empty_event_definition(self):
        """Event with empty string eventDefinition returns None."""
        element = BPMNElement(
            id="e1",
            type="startEvent",
            width=36,
            height=36,
            properties={"eventDefinition": ""},
        )
        result = create_event_icon(element, "parent_1", 10)
        assert result is None

    def test_returns_none_for_unknown_event_definition(self):
        """Event with unrecognized eventDefinition returns None."""
        element = BPMNElement(
            id="e1",
            type="startEvent",
            width=36,
            height=36,
            properties={"eventDefinition": "nonexistentDefinition"},
        )
        result = create_event_icon(element, "parent_1", 10)
        assert result is None

    def test_uses_default_event_dimensions_when_none(self):
        """When element width/height are None, defaults to 36x36 for centering."""
        element = BPMNElement(
            id="e1",
            type="startEvent",
            width=None,
            height=None,
            properties={"eventDefinition": "timer"},
        )
        result = create_event_icon(element, "parent_1", 10)
        assert result is not None

        cell, _ = result
        geometry = cell.find("mxGeometry")
        icon_width = float(geometry.get("width"))
        icon_height = float(geometry.get("height"))
        x = float(geometry.get("x"))
        y = float(geometry.get("y"))

        # Default event size is 36x36
        expected_x = (36 - icon_width) / 2
        expected_y = (36 - icon_height) / 2
        assert abs(x - expected_x) < 0.01
        assert abs(y - expected_y) < 0.01

    def test_boundary_event_timer_icon(self):
        """Boundary event with timer definition produces an icon."""
        element = BPMNElement(
            id="be1",
            type="boundaryEvent",
            width=36,
            height=36,
            properties={"eventDefinition": "timer"},
        )
        result = create_event_icon(element, "parent_1", 10)
        assert result is not None
        cell, _ = result
        assert "timer" in cell.get("style")

    def test_intermediate_throw_event_message_icon(self):
        """Intermediate throw event with message definition produces a filled icon."""
        element = BPMNElement(
            id="ite1",
            type="intermediateThrowEvent",
            width=36,
            height=36,
            properties={"eventDefinition": "message"},
        )
        result = create_event_icon(element, "parent_1", 10)
        assert result is not None
        cell, _ = result
        style = cell.get("style")
        assert "message" in style
        # Throw events have filled icons
        assert "fillColor=#d6b656" in style


class TestGetTaskIconStyle:
    """Tests for get_task_icon_style helper function."""

    def test_known_task_type_returns_style_string(self):
        """Known task type returns its style string."""
        style = get_task_icon_style("userTask")
        assert style is not None
        assert "user_task" in style

    def test_unknown_task_type_returns_none(self):
        """Unknown task type returns None."""
        style = get_task_icon_style("unknownType")
        assert style is None

    def test_generic_task_returns_none(self):
        """Generic 'task' type is not in TASK_ICONS so returns None."""
        style = get_task_icon_style("task")
        assert style is None

    def test_each_task_type_returns_distinct_or_consistent_style(self):
        """Each task type in TASK_ICONS returns a style via get_task_icon_style."""
        for task_type in TASK_ICONS:
            style = get_task_icon_style(task_type)
            assert style is not None, (
                f"get_task_icon_style returned None for {task_type}"
            )
            assert isinstance(style, str)


class TestGetEventIconStyle:
    """Tests for get_event_icon_style helper function."""

    def test_known_event_returns_style(self):
        """Known event type + definition returns a style string."""
        style = get_event_icon_style("startEvent", "timer")
        assert style is not None
        assert "timer" in style

    def test_unknown_event_returns_none(self):
        """Unknown event type returns None."""
        style = get_event_icon_style("unknownEvent", "timer")
        assert style is None

    def test_unknown_definition_returns_none(self):
        """Known event type with unknown definition returns None."""
        style = get_event_icon_style("startEvent", "nonexistent")
        assert style is None

    def test_all_event_icon_keys_produce_styles(self):
        """Every key in EVENT_ICONS produces a matching style via get_event_icon_style."""
        for key in EVENT_ICONS:
            parts = key.split("_", 1)
            event_type = parts[0]
            # Reconstruct: keys like "intermediateCatchEvent_timer" -> type="intermediateCatchEvent", def="timer"
            # But the split at first _ won't work for camelCase keys. Use the actual key parsing logic.
            # The key format is f"{element.type}_{event_def}" so we need to find the underscore
            # that separates event type from definition.
            # Event types: startEvent, endEvent, intermediateCatchEvent, intermediateThrowEvent, boundaryEvent
            # Find the last component after the event type prefix
            for prefix in [
                "intermediateCatchEvent",
                "intermediateThrowEvent",
                "boundaryEvent",
                "startEvent",
                "endEvent",
            ]:
                if key.startswith(prefix + "_"):
                    event_type = prefix
                    event_def = key[len(prefix) + 1 :]
                    break
            else:
                continue  # Skip if key format unrecognized

            style = get_event_icon_style(event_type, event_def)
            assert style is not None, (
                f"get_event_icon_style returned None for ({event_type}, {event_def})"
            )
