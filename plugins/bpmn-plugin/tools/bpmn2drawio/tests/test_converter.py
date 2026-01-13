"""Tests for converter module."""

import pytest
from pathlib import Path

from bpmn2drawio.converter import Converter


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestConverterBasic:
    """Basic converter tests."""

    def test_convert_minimal(self, tmp_path):
        """Test converting minimal BPMN file."""
        converter = Converter()
        output_file = tmp_path / "output.drawio"

        result = converter.convert(
            FIXTURES_DIR / "minimal.bpmn",
            output_file
        )

        assert result.success
        assert result.element_count == 3
        assert result.flow_count == 2
        assert output_file.exists()

    def test_convert_string(self):
        """Test converting BPMN string."""
        bpmn_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
          <bpmn:process id="Process_1">
            <bpmn:startEvent id="Start_1" name="Begin"/>
            <bpmn:endEvent id="End_1" name="Finish"/>
            <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="End_1"/>
          </bpmn:process>
        </bpmn:definitions>
        """
        converter = Converter()
        drawio_xml = converter.convert_string(bpmn_xml)

        assert '<?xml' in drawio_xml
        assert 'mxfile' in drawio_xml
        assert 'Begin' in drawio_xml
        assert 'Finish' in drawio_xml

    def test_convert_nonexistent_file(self, tmp_path):
        """Test converting nonexistent file."""
        converter = Converter()
        output_file = tmp_path / "output.drawio"

        result = converter.convert(
            "/nonexistent/file.bpmn",
            output_file
        )

        assert not result.success
        assert result.error is not None


class TestConverterOptions:
    """Tests for converter options."""

    def test_converter_with_options(self, tmp_path):
        """Test converter with various options."""
        converter = Converter(
            layout="preserve",
            theme="default",
            direction="LR"
        )
        output_file = tmp_path / "output.drawio"

        result = converter.convert(
            FIXTURES_DIR / "minimal.bpmn",
            output_file
        )

        # Should succeed but may have warnings
        assert result.success

    def test_preserve_layout_warning(self, tmp_path):
        """Test warning when preserve layout with no DI."""
        converter = Converter(layout="preserve")
        output_file = tmp_path / "output.drawio"

        result = converter.convert(
            FIXTURES_DIR / "minimal.bpmn",  # Has no DI
            output_file
        )

        # Should have warning about missing DI
        assert any("DI" in w for w in result.warnings)


class TestEndToEnd:
    """End-to-end conversion tests."""

    def test_minimal_to_drawio(self, tmp_path):
        """Test full conversion pipeline."""
        converter = Converter()
        output_file = tmp_path / "minimal.drawio"

        result = converter.convert(
            FIXTURES_DIR / "minimal.bpmn",
            output_file
        )

        assert result.success
        assert output_file.exists()

        # Verify output is valid XML
        content = output_file.read_text()
        assert content.startswith('<?xml')
        assert '<mxfile' in content
        assert '</mxfile>' in content

    def test_with_di_to_drawio(self, tmp_path):
        """Test conversion with DI coordinates."""
        converter = Converter()
        output_file = tmp_path / "with_di.drawio"

        result = converter.convert(
            FIXTURES_DIR / "with_di.bpmn",
            output_file
        )

        assert result.success
        assert len(result.warnings) == 0  # Should have no warnings

    def test_gateway_to_drawio(self, tmp_path):
        """Test conversion with gateways."""
        converter = Converter()
        output_file = tmp_path / "gateway.drawio"

        result = converter.convert(
            FIXTURES_DIR / "with_gateway.bpmn",
            output_file
        )

        assert result.success
        assert result.element_count == 6  # start, gateway, yes task, no task, merge gateway, end
