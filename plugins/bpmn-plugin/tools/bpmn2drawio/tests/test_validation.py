"""Tests for validation system."""

from pathlib import Path

from bpmn2drawio.validation import ModelValidator, ValidationWarning, validate_model
from bpmn2drawio.models import BPMNModel, BPMNElement, BPMNFlow
from bpmn2drawio.parser import parse_bpmn


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestValidationWarning:
    """Tests for ValidationWarning dataclass."""

    def test_warning_creation(self):
        """Test creating a validation warning."""
        warning = ValidationWarning(
            level="error", element_id="Task_1", message="Invalid element"
        )

        assert warning.level == "error"
        assert warning.element_id == "Task_1"
        assert warning.message == "Invalid element"


class TestStartEndEventValidation:
    """Tests for start/end event validation."""

    def test_valid_process(self):
        """Test process with start and end events."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Start_1", type="startEvent"),
                BPMNElement(id="Task_1", type="task"),
                BPMNElement(id="End_1", type="endEvent"),
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_start_end_events(model)

        # Should have no warnings about missing events
        assert not any("start event" in w.message.lower() for w in warnings)
        assert not any("end event" in w.message.lower() for w in warnings)

    def test_missing_start_event(self):
        """Test process without start event."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Task_1", type="task"),
                BPMNElement(id="End_1", type="endEvent"),
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_start_end_events(model)

        assert len(warnings) == 1
        assert "start event" in warnings[0].message.lower()

    def test_missing_end_event(self):
        """Test process without end event."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Start_1", type="startEvent"),
                BPMNElement(id="Task_1", type="task"),
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_start_end_events(model)

        assert len(warnings) == 1
        assert "end event" in warnings[0].message.lower()


class TestReferenceValidation:
    """Tests for flow reference validation."""

    def test_valid_references(self):
        """Test flows with valid references."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Start_1", type="startEvent"),
                BPMNElement(id="Task_1", type="task"),
            ],
            flows=[
                BPMNFlow(
                    id="Flow_1",
                    type="sequenceFlow",
                    source_ref="Start_1",
                    target_ref="Task_1",
                ),
            ],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_valid_references(model)

        assert len(warnings) == 0

    def test_invalid_source_reference(self):
        """Test flow with invalid source reference."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Task_1", type="task"),
            ],
            flows=[
                BPMNFlow(
                    id="Flow_1",
                    type="sequenceFlow",
                    source_ref="NonExistent",
                    target_ref="Task_1",
                ),
            ],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_valid_references(model)

        assert len(warnings) == 1
        assert warnings[0].level == "error"
        assert "invalid source" in warnings[0].message.lower()

    def test_invalid_target_reference(self):
        """Test flow with invalid target reference."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Task_1", type="task"),
            ],
            flows=[
                BPMNFlow(
                    id="Flow_1",
                    type="sequenceFlow",
                    source_ref="Task_1",
                    target_ref="NonExistent",
                ),
            ],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_valid_references(model)

        assert len(warnings) == 1
        assert warnings[0].level == "error"
        assert "invalid target" in warnings[0].message.lower()


class TestConnectedGraphValidation:
    """Tests for connected graph validation."""

    def test_connected_graph(self):
        """Test fully connected process."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Start_1", type="startEvent"),
                BPMNElement(id="Task_1", type="task"),
                BPMNElement(id="End_1", type="endEvent"),
            ],
            flows=[
                BPMNFlow(
                    id="Flow_1",
                    type="sequenceFlow",
                    source_ref="Start_1",
                    target_ref="Task_1",
                ),
                BPMNFlow(
                    id="Flow_2",
                    type="sequenceFlow",
                    source_ref="Task_1",
                    target_ref="End_1",
                ),
            ],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_connected_graph(model)

        assert len(warnings) == 0

    def test_disconnected_element(self):
        """Test process with disconnected element."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Start_1", type="startEvent"),
                BPMNElement(id="Task_1", type="task"),
                BPMNElement(id="End_1", type="endEvent"),
                BPMNElement(id="Orphan", type="task"),  # Not connected
            ],
            flows=[
                BPMNFlow(
                    id="Flow_1",
                    type="sequenceFlow",
                    source_ref="Start_1",
                    target_ref="Task_1",
                ),
                BPMNFlow(
                    id="Flow_2",
                    type="sequenceFlow",
                    source_ref="Task_1",
                    target_ref="End_1",
                ),
            ],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_connected_graph(model)

        assert len(warnings) == 1
        assert "Orphan" in warnings[0].message


class TestOverlappingValidation:
    """Tests for overlapping element detection."""

    def test_no_overlapping(self):
        """Test elements without overlap."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="E1", type="task", x=0, y=0, width=100, height=80),
                BPMNElement(id="E2", type="task", x=200, y=0, width=100, height=80),
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=True,
        )

        validator = ModelValidator()
        warnings = validator._check_overlapping_elements(model)

        assert len(warnings) == 0

    def test_overlapping_elements(self):
        """Test overlapping elements detected."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="E1", type="task", x=0, y=0, width=100, height=80),
                BPMNElement(id="E2", type="task", x=50, y=40, width=100, height=80),
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=True,
        )

        validator = ModelValidator()
        warnings = validator._check_overlapping_elements(model)

        assert len(warnings) == 1
        assert warnings[0].level == "warning"
        assert "overlaps" in warnings[0].message.lower()


class TestMissingLabelValidation:
    """Tests for missing label detection."""

    def test_task_with_label(self):
        """Test task with label."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Task_1", type="task", name="My Task"),
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_missing_labels(model)

        assert len(warnings) == 0

    def test_task_without_label(self):
        """Test task without label."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Task_1", type="userTask", name=None),
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_missing_labels(model)

        assert len(warnings) == 1
        assert warnings[0].level == "info"
        assert "no label" in warnings[0].message.lower()

    def test_event_without_label_ok(self):
        """Test events without labels don't generate warnings."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="Start_1", type="startEvent", name=None),
            ],
            flows=[],
            pools=[],
            lanes=[],
            has_di_coordinates=False,
        )

        validator = ModelValidator()
        warnings = validator._check_missing_labels(model)

        assert len(warnings) == 0


class TestValidateModelFunction:
    """Tests for validate_model convenience function."""

    def test_validate_minimal_file(self):
        """Test validating minimal BPMN file."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        warnings = validate_model(model)

        # Minimal should be valid with no errors
        errors = [w for w in warnings if w.level == "error"]
        assert len(errors) == 0

    def test_validate_invalid_refs_file(self):
        """Test validating file with invalid references."""
        model = parse_bpmn(FIXTURES_DIR / "invalid_refs.bpmn")
        warnings = validate_model(model)

        errors = [w for w in warnings if w.level == "error"]
        assert len(errors) == 2  # Two invalid flows

    def test_validate_disconnected_file(self):
        """Test validating file with disconnected elements."""
        model = parse_bpmn(FIXTURES_DIR / "disconnected.bpmn")
        warnings = validate_model(model)

        info_warnings = [w for w in warnings if w.level == "info"]
        # Should have warnings about disconnected elements
        assert len(info_warnings) >= 2
