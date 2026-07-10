"""Tests for converter module."""

from pathlib import Path

from bpmn2drawio.converter import Converter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestConverterBasic:
    """Basic converter tests."""

    def test_convert_minimal(self, tmp_path):
        """Test converting minimal BPMN file."""
        converter = Converter()
        output_file = tmp_path / "output.drawio"

        result = converter.convert(FIXTURES_DIR / "minimal.bpmn", output_file)

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

        assert "<?xml" in drawio_xml
        assert "mxfile" in drawio_xml
        assert "Begin" in drawio_xml
        assert "Finish" in drawio_xml

    def test_convert_nonexistent_file(self, tmp_path):
        """Test converting nonexistent file."""
        converter = Converter()
        output_file = tmp_path / "output.drawio"

        result = converter.convert("/nonexistent/file.bpmn", output_file)

        assert not result.success
        assert result.error is not None


class TestConverterOptions:
    """Tests for converter options."""

    def test_converter_with_options(self, tmp_path):
        """Test converter with various options."""
        converter = Converter(layout="preserve", theme="default", direction="LR")
        output_file = tmp_path / "output.drawio"

        result = converter.convert(FIXTURES_DIR / "minimal.bpmn", output_file)

        # Should succeed but may have warnings
        assert result.success

    def test_preserve_layout_warning(self, tmp_path):
        """Test warning when preserve layout with no DI."""
        converter = Converter(layout="preserve")
        output_file = tmp_path / "output.drawio"

        result = converter.convert(
            FIXTURES_DIR / "minimal.bpmn",  # Has no DI
            output_file,
        )

        # Should have warning about missing DI
        assert any("DI" in w for w in result.warnings)


class TestEndToEnd:
    """End-to-end conversion tests."""

    def test_minimal_to_drawio(self, tmp_path):
        """Test full conversion pipeline."""
        converter = Converter()
        output_file = tmp_path / "minimal.drawio"

        result = converter.convert(FIXTURES_DIR / "minimal.bpmn", output_file)

        assert result.success
        assert output_file.exists()

        # Verify output is valid XML
        content = output_file.read_text()
        assert content.startswith("<?xml")
        assert "<mxfile" in content
        assert "</mxfile>" in content

    def test_with_di_to_drawio(self, tmp_path):
        """Test conversion with DI coordinates."""
        converter = Converter()
        output_file = tmp_path / "with_di.drawio"

        result = converter.convert(FIXTURES_DIR / "with_di.bpmn", output_file)

        assert result.success
        assert len(result.warnings) == 0  # Should have no warnings

    def test_gateway_to_drawio(self, tmp_path):
        """Test conversion with gateways."""
        converter = Converter()
        output_file = tmp_path / "gateway.drawio"

        result = converter.convert(FIXTURES_DIR / "with_gateway.bpmn", output_file)

        assert result.success
        assert result.element_count == 6  # start, gateway, yes task, no task, merge gateway, end


class TestAutoLayoutMode:
    """Tests for the 'auto' layout mode (the default)."""

    def test_default_layout_is_auto(self):
        """A freshly constructed converter defaults to 'auto' layout."""
        assert Converter().layout == "auto"

    def test_effective_layout_prefers_preserve_with_di(self):
        """'auto' resolves to 'preserve' when the model carries DI coordinates."""
        from bpmn2drawio.parser import parse_bpmn

        converter = Converter()  # layout="auto"
        model = parse_bpmn(FIXTURES_DIR / "with_di.bpmn")

        assert model.has_di_coordinates
        assert converter._effective_layout(model) == "preserve"

    def test_effective_layout_falls_back_to_graphviz_without_di(self):
        """'auto' resolves to 'graphviz' when the model has no DI coordinates."""
        from bpmn2drawio.parser import parse_bpmn

        converter = Converter()  # layout="auto"
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")

        assert not model.has_di_coordinates
        assert converter._effective_layout(model) == "graphviz"

    def test_explicit_layout_is_not_overridden(self):
        """An explicit layout choice is used verbatim regardless of DI."""
        from bpmn2drawio.parser import parse_bpmn

        converter = Converter(layout="graphviz")
        di_model = parse_bpmn(FIXTURES_DIR / "with_di.bpmn")
        no_di_model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")

        assert converter._effective_layout(di_model) == "graphviz"
        assert converter._effective_layout(no_di_model) == "graphviz"

    def test_auto_with_di_emits_no_warning(self, tmp_path):
        """Auto mode on a DI file does not warn about missing coordinates."""
        converter = Converter()  # auto
        output_file = tmp_path / "out.drawio"

        result = converter.convert(FIXTURES_DIR / "with_di.bpmn", output_file)

        assert result.success
        assert result.warnings == []

    def test_auto_without_di_emits_no_warning(self, tmp_path):
        """Auto mode on a non-DI file uses graphviz and does not warn."""
        converter = Converter()  # auto
        output_file = tmp_path / "out.drawio"

        result = converter.convert(FIXTURES_DIR / "minimal.bpmn", output_file)

        assert result.success
        # The (0,0) preserve warning must not appear in auto mode.
        assert not any("(0,0)" in w for w in result.warnings)

    def test_auto_preserves_di_coordinates(self, tmp_path):
        """Auto mode keeps the original DI layout for a swimlane file."""
        from xml.etree import ElementTree as ET

        converter = Converter()  # auto -> preserve
        output_file = tmp_path / "geo.drawio"

        result = converter.convert(FIXTURES_DIR / "geometric_lanes.bpmn", output_file)
        assert result.success

        root = ET.fromstring(output_file.read_text(encoding="utf-8").encode())
        shapes = [c for c in root.findall(".//mxCell[@vertex='1']") if c.get("value")]

        # Sibling shapes inside lanes must not collapse onto the same point.
        def geom(cell):
            g = cell.find("mxGeometry")
            return (float(g.get("x")), float(g.get("y")))

        work = [geom(c) for c in shapes if c.get("value") in {"Start", "Do Work", "End"}]
        assert len(work) == 3
        assert len(set(work)) == 3  # distinct positions preserved
