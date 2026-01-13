"""Tests for Draw.io XML generator."""

import pytest
from pathlib import Path
from xml.etree import ElementTree as ET

from bpmn2drawio.parser import parse_bpmn
from bpmn2drawio.generator import DrawioGenerator
from bpmn2drawio.models import BPMNModel, BPMNElement, BPMNFlow


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestEmptyModel:
    """Tests for generating empty model."""

    def test_generate_empty_model(self):
        """Test generating XML for empty model."""
        model = BPMNModel()
        generator = DrawioGenerator()

        result = generator.generate_result(model)

        assert result.element_count == 0
        assert result.flow_count == 0
        assert result.xml_string.startswith('<?xml')

    def test_empty_model_has_base_cells(self):
        """Test that empty model has base cells (id=0, id=1)."""
        model = BPMNModel()
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        # Find mxGraphModel/root
        graph_model = root.find(".//mxGraphModel")
        assert graph_model is not None

        xml_root = graph_model.find("root")
        assert xml_root is not None

        cells = xml_root.findall("mxCell")
        cell_ids = [c.get("id") for c in cells]

        assert "0" in cell_ids
        assert "1" in cell_ids


class TestMinimalProcess:
    """Tests for generating minimal process."""

    def test_generate_minimal_process(self):
        """Test generating minimal process."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        generator = DrawioGenerator()

        result = generator.generate_result(model)

        assert result.element_count == 3
        assert result.flow_count == 2

    def test_minimal_contains_elements(self):
        """Test that generated XML contains Start, Task, End cells."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        # Find all mxCells with vertex="1"
        vertices = root.findall(".//mxCell[@vertex='1']")
        assert len(vertices) == 3

        # Check element names
        values = [v.get("value") for v in vertices]
        assert "Start" in values
        assert "Do Something" in values
        assert "End" in values

    def test_minimal_contains_edges(self):
        """Test that generated XML contains edges."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        # Find all mxCells with edge="1"
        edges = root.findall(".//mxCell[@edge='1']")
        assert len(edges) == 2


class TestVertexStyles:
    """Tests for vertex styles."""

    def test_start_event_style(self):
        """Test start event has correct style."""
        model = BPMNModel(
            elements=[BPMNElement(id="start1", type="startEvent", name="Start")]
        )
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        vertex = root.find(".//mxCell[@vertex='1']")
        style = vertex.get("style")

        assert "ellipse" in style
        assert "fillColor=#d5e8d4" in style
        assert "strokeColor=#82b366" in style

    def test_end_event_style(self):
        """Test end event has correct style."""
        model = BPMNModel(
            elements=[BPMNElement(id="end1", type="endEvent", name="End")]
        )
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        vertex = root.find(".//mxCell[@vertex='1']")
        style = vertex.get("style")

        assert "ellipse" in style
        assert "fillColor=#f8cecc" in style
        assert "strokeWidth=3" in style

    def test_task_style(self):
        """Test task has correct style."""
        model = BPMNModel(
            elements=[BPMNElement(id="task1", type="task", name="Task")]
        )
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        vertex = root.find(".//mxCell[@vertex='1']")
        style = vertex.get("style")

        assert "rounded=1" in style
        assert "fillColor=#dae8fc" in style

    def test_gateway_style(self):
        """Test gateway has correct style."""
        model = BPMNModel(
            elements=[BPMNElement(id="gw1", type="exclusiveGateway", name="Decision")]
        )
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        vertex = root.find(".//mxCell[@vertex='1']")
        style = vertex.get("style")

        assert "rhombus" in style
        assert "fillColor=#fff2cc" in style


class TestEdgeConnections:
    """Tests for edge connections."""

    def test_edge_source_target(self):
        """Test edges have correct source and target."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        edges = root.findall(".//mxCell[@edge='1']")

        # All edges should have source and target
        for edge in edges:
            assert edge.get("source") is not None
            assert edge.get("target") is not None

    def test_edge_style(self):
        """Test edges have correct style."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        edge = root.find(".//mxCell[@edge='1']")
        style = edge.get("style")

        assert "orthogonalEdgeStyle" in style
        assert "endArrow=block" in style


class TestGeometry:
    """Tests for element geometry."""

    def test_vertex_geometry(self):
        """Test vertices have geometry."""
        model = BPMNModel(
            elements=[
                BPMNElement(id="task1", type="task", x=100, y=200, width=120, height=80)
            ]
        )
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        vertex = root.find(".//mxCell[@vertex='1']")
        geometry = vertex.find("mxGeometry")

        assert geometry is not None
        assert geometry.get("x") == "100"
        assert geometry.get("y") == "200"
        assert geometry.get("width") == "120"
        assert geometry.get("height") == "80"

    def test_default_dimensions(self):
        """Test default dimensions are used when not specified."""
        model = BPMNModel(
            elements=[BPMNElement(id="start1", type="startEvent")]
        )
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        vertex = root.find(".//mxCell[@vertex='1']")
        geometry = vertex.find("mxGeometry")

        # Start events should have 36x36 dimensions
        assert geometry.get("width") == "36"
        assert geometry.get("height") == "36"


class TestOutputFile:
    """Tests for file output."""

    def test_generate_to_file(self, tmp_path):
        """Test generating to file."""
        model = parse_bpmn(FIXTURES_DIR / "minimal.bpmn")
        generator = DrawioGenerator()

        output_file = tmp_path / "output.drawio"
        result = generator.generate(model, str(output_file))

        assert output_file.exists()
        assert result.element_count == 3

        # Verify file content is valid XML
        content = output_file.read_text()
        root = ET.fromstring(content.encode())
        assert root.tag == "mxfile"


class TestDICoordinates:
    """Tests for DI coordinate handling."""

    def test_di_coordinates_preserved(self):
        """Test that DI coordinates are preserved in output."""
        model = parse_bpmn(FIXTURES_DIR / "with_di.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        vertices = root.findall(".//mxCell[@vertex='1']")

        # Find the task (should have x=200)
        task_vertex = None
        for v in vertices:
            if v.get("value") == "Do Something":
                task_vertex = v
                break

        assert task_vertex is not None
        geometry = task_vertex.find("mxGeometry")
        assert geometry.get("x") == "200.0"
        assert geometry.get("y") == "78.0"
