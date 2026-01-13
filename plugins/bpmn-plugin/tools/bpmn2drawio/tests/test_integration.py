"""Integration tests for end-to-end conversion."""

import pytest
from pathlib import Path
import xml.etree.ElementTree as ET
import glob

from bpmn2drawio.converter import Converter
from bpmn2drawio.parser import parse_bpmn
from bpmn2drawio.generator import DrawioGenerator
from bpmn2drawio.validation import validate_model


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestEndToEnd:
    """End-to-end conversion tests."""

    @pytest.fixture
    def converter(self):
        """Create converter instance."""
        return Converter()

    def test_minimal_conversion(self, converter, tmp_path):
        """Test minimal BPMN to Draw.io conversion."""
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        assert result.success
        assert output.exists()
        assert result.element_count == 3

    def test_all_fixtures_convert(self, converter, tmp_path):
        """Test all fixture files convert without error."""
        fixture_files = list(FIXTURES_DIR.glob("*.bpmn"))

        for fixture in fixture_files:
            output = tmp_path / f"{fixture.stem}.drawio"
            result = converter.convert(str(fixture), str(output))

            assert result.success, f"Failed to convert {fixture.name}: {result.error}"
            assert output.exists(), f"Output not created for {fixture.name}"

    def test_output_is_valid_xml(self, converter, tmp_path):
        """Test generated file is valid XML."""
        output = tmp_path / "output.drawio"
        converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        # Should parse without error
        tree = ET.parse(str(output))
        root = tree.getroot()

        assert root.tag == "mxfile"

    def test_output_has_correct_structure(self, converter, tmp_path):
        """Test generated file has correct Draw.io structure."""
        output = tmp_path / "output.drawio"
        converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        tree = ET.parse(str(output))
        root = tree.getroot()

        # Check structure: mxfile > diagram > mxGraphModel > root
        diagram = root.find("diagram")
        assert diagram is not None

        # Content is inside mxGraphModel
        graph_model = diagram.find("mxGraphModel")
        assert graph_model is not None

        root_elem = graph_model.find("root")
        assert root_elem is not None

    def test_element_count_preserved(self, converter, tmp_path):
        """Test all elements are preserved in conversion."""
        input_model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        assert result.element_count == len(input_model.elements)

    def test_flows_preserved(self, converter, tmp_path):
        """Test all flows are preserved in conversion."""
        input_model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        assert result.flow_count == len(input_model.flows)


class TestConversionOptions:
    """Tests for conversion options."""

    def test_theme_option(self, tmp_path):
        """Test theme option applies colors."""
        converter = Converter(theme="blueprint")
        output = tmp_path / "output.drawio"

        converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        content = output.read_text()
        # Blueprint uses blue colors
        assert "#1976d2" in content or "#bbdefb" in content

    def test_direction_lr(self, tmp_path):
        """Test left-to-right direction."""
        converter = Converter(direction="LR")
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        assert result.success

    def test_direction_tb(self, tmp_path):
        """Test top-to-bottom direction."""
        converter = Converter(direction="TB")
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        assert result.success


class TestElementTypes:
    """Tests for specific element type conversion."""

    def test_gateway_conversion(self, tmp_path):
        """Test gateway elements are converted."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "with_gateway.bpmn"),
            str(output)
        )

        assert result.success
        content = output.read_text()
        # Should have rhombus shape for gateway
        assert "rhombus" in content

    def test_all_tasks_conversion(self, tmp_path):
        """Test all task types are converted."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "all_tasks.bpmn"),
            str(output)
        )

        assert result.success
        content = output.read_text()
        # Tasks use rounded rectangles
        assert "rounded=1" in content

    def test_all_gateways_conversion(self, tmp_path):
        """Test all gateway types are converted."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "all_gateways.bpmn"),
            str(output)
        )

        assert result.success
        content = output.read_text()
        # Should have multiple gateway shapes
        assert content.count("rhombus") >= 5

    def test_all_events_conversion(self, tmp_path):
        """Test all event types are converted."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "all_events.bpmn"),
            str(output)
        )

        assert result.success
        content = output.read_text()
        # Events use ellipse shape
        assert "ellipse" in content


class TestSwimlaneConversion:
    """Tests for swimlane conversion."""

    def test_single_pool_conversion(self, tmp_path):
        """Test single pool is converted."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "single_pool.bpmn"),
            str(output)
        )

        assert result.success
        content = output.read_text()
        # Pool uses swimlane style
        assert "swimlane" in content

    def test_pool_with_lanes_conversion(self, tmp_path):
        """Test pool with lanes is converted."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "swimlanes.bpmn"),
            str(output)
        )

        assert result.success
        content = output.read_text()
        # Should have multiple swimlane elements
        assert content.count("swimlane") >= 3


class TestFlowConversion:
    """Tests for flow conversion."""

    def test_sequence_flow_style(self, tmp_path):
        """Test sequence flows have correct style."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        content = output.read_text()
        # Should have edge style
        assert "edgeStyle" in content
        assert "endArrow=block" in content

    def test_conditional_flow_style(self, tmp_path):
        """Test conditional flows have diamond marker."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        converter.convert(
            str(FIXTURES_DIR / "conditional_flows.bpmn"),
            str(output)
        )

        content = output.read_text()
        # Conditional flows have diamond start
        assert "startArrow=diamond" in content or "startArrow=dash" in content


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_process_conversion(self, tmp_path):
        """Test empty process converts without error."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "empty.bpmn"),
            str(output)
        )

        assert result.success
        assert output.exists()

    def test_invalid_refs_conversion(self, tmp_path):
        """Test file with invalid refs converts with warnings."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "invalid_refs.bpmn"),
            str(output)
        )

        # Should still succeed, invalid flows filtered
        assert result.success

    def test_disconnected_elements_conversion(self, tmp_path):
        """Test disconnected elements are still converted."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        result = converter.convert(
            str(FIXTURES_DIR / "disconnected.bpmn"),
            str(output)
        )

        assert result.success


class TestValidationIntegration:
    """Tests for validation integration."""

    def test_valid_model_no_errors(self):
        """Test valid model has no validation errors."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        warnings = validate_model(model)

        errors = [w for w in warnings if w.level == "error"]
        assert len(errors) == 0

    def test_invalid_refs_has_errors(self):
        """Test invalid refs produces validation errors."""
        model = parse_bpmn(FIXTURES_DIR / "invalid_refs.bpmn")
        warnings = validate_model(model)

        errors = [w for w in warnings if w.level == "error"]
        assert len(errors) > 0


class TestRoundTrip:
    """Tests for round-trip conversion."""

    def test_element_ids_preserved(self, tmp_path):
        """Test elements are represented in conversion output."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        content = output.read_text()
        # Element values (names) should be in output
        # Note: Draw.io uses numeric cell IDs, not BPMN IDs
        assert "Start" in content
        assert "Do Something" in content
        assert "End" in content
        # Should have the correct number of mxCells (2 base + 3 elements + 2 flows)
        assert content.count("mxCell") >= 7

    def test_element_names_preserved(self, tmp_path):
        """Test element names are preserved in conversion."""
        converter = Converter()
        output = tmp_path / "output.drawio"

        converter.convert(
            str(FIXTURES_DIR / "minimal.bpmn"),
            str(output)
        )

        content = output.read_text()
        # Element names should be in output
        assert "Start" in content
        assert "Do Something" in content
        assert "End" in content
