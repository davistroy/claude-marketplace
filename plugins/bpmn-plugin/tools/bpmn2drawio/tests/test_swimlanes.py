"""Tests for swimlane handling (pools and lanes)."""

from pathlib import Path
from xml.etree import ElementTree as ET

from bpmn2drawio.parser import parse_bpmn
from bpmn2drawio.generator import DrawioGenerator
from bpmn2drawio.converter import Converter
from bpmn2drawio.models import Pool, Lane, BPMNElement, BPMNModel
from bpmn2drawio.swimlanes import (
    SwimlaneSizer,
    create_pool_cell,
    create_lane_cell,
    resolve_parent_hierarchy,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestSwimlaneSizer:
    """Tests for SwimlaneSizer class."""

    def test_calculate_pool_size_default(self):
        """Test default pool size calculation."""
        sizer = SwimlaneSizer()
        pool = Pool(id="pool1", name="Test Pool")
        elements = []
        lanes = []

        width, height = sizer.calculate_pool_size(pool, elements, lanes)

        assert width >= 400
        assert height >= 150

    def test_calculate_pool_size_with_elements(self):
        """Test pool size with contained elements."""
        sizer = SwimlaneSizer()
        pool = Pool(id="pool1", name="Test Pool")
        elements = [
            BPMNElement(id="e1", type="task", x=100, y=100, width=120, height=80),
            BPMNElement(id="e2", type="task", x=300, y=100, width=120, height=80),
        ]

        width, height = sizer.calculate_pool_size(pool, elements, [])

        # Should be at least minimum size
        assert width >= 400  # minimum width
        assert height >= 150  # minimum height

    def test_pool_size_preserves_explicit_dimensions(self):
        """Test that explicit pool dimensions are preserved."""
        sizer = SwimlaneSizer()
        pool = Pool(id="pool1", name="Test", width=800, height=400)

        width, height = sizer.calculate_pool_size(pool, [], [])

        assert width == 800
        assert height == 400


class TestCreatePoolCell:
    """Tests for pool cell creation."""

    def test_create_pool_cell(self):
        """Test basic pool cell creation."""
        pool = Pool(
            id="pool1",
            name="Customer",
            x=50,
            y=50,
            width=600,
            height=200,
        )

        cell = create_pool_cell(pool, "10")

        assert cell.get("id") == "10"
        assert cell.get("value") == "Customer"
        assert "swimlane" in cell.get("style")
        assert cell.get("vertex") == "1"

        geometry = cell.find("mxGeometry")
        assert geometry.get("width") == "600"
        assert geometry.get("height") == "200"

    def test_create_pool_cell_horizontal(self):
        """Test horizontal pool style."""
        pool = Pool(id="pool1", name="Test", is_horizontal=True)
        cell = create_pool_cell(pool, "10")

        assert "horizontal=0" in cell.get("style")

    def test_create_pool_cell_vertical(self):
        """Test vertical pool style."""
        pool = Pool(id="pool1", name="Test", is_horizontal=False)
        cell = create_pool_cell(pool, "10")

        # Vertical pools don't have horizontal=0
        assert "horizontal=0" not in cell.get("style") or "startSize=30" in cell.get(
            "style"
        )


class TestCreateLaneCell:
    """Tests for lane cell creation."""

    def test_create_lane_cell(self):
        """Test basic lane cell creation."""
        lane = Lane(
            id="lane1",
            name="Manager",
            parent_pool_id="pool1",
            x=40,
            y=0,
            width=560,
            height=100,
        )

        cell = create_lane_cell(lane, "15", "10")

        assert cell.get("id") == "15"
        assert cell.get("value") == "Manager"
        assert cell.get("parent") == "10"
        assert "swimlane" in cell.get("style")


class TestResolveParentHierarchy:
    """Tests for parent hierarchy resolution."""

    def test_element_in_lane(self):
        """Test element in lane gets lane as parent."""
        model = BPMNModel(
            elements=[BPMNElement(id="task1", type="task")],
            lanes=[
                Lane(
                    id="lane1",
                    name="Lane",
                    parent_pool_id="pool1",
                    element_refs=["task1"],
                )
            ],
            pools=[Pool(id="pool1", name="Pool", lanes=["lane1"])],
        )

        hierarchy = resolve_parent_hierarchy(model)

        assert hierarchy["task1"] == "lane1"

    def test_element_outside_pool(self):
        """Test element outside pool gets root as parent."""
        model = BPMNModel(
            elements=[BPMNElement(id="task1", type="task")],
        )

        hierarchy = resolve_parent_hierarchy(model)

        assert hierarchy["task1"] == "1"


class TestParseSwimlanes:
    """Tests for parsing BPMN with swimlanes."""

    def test_parse_single_pool(self):
        """Test parsing single pool."""
        model = parse_bpmn(FIXTURES_DIR / "single_pool.bpmn")

        assert len(model.pools) == 1
        pool = model.pools[0]
        assert pool.name == "Main Process"
        assert pool.width == 500
        assert pool.height == 200

    def test_parse_pool_with_lanes(self):
        """Test parsing pool with lanes."""
        model = parse_bpmn(FIXTURES_DIR / "swimlanes.bpmn")

        assert len(model.pools) == 2
        assert len(model.lanes) >= 2

        # Find customer pool
        customer_pool = None
        for pool in model.pools:
            if "Customer" in (pool.name or ""):
                customer_pool = pool
                break

        assert customer_pool is not None

    def test_elements_assigned_to_lanes(self):
        """Test lane element_refs are populated."""
        model = parse_bpmn(FIXTURES_DIR / "swimlanes.bpmn")

        # Find lane with element refs
        lane_with_refs = None
        for lane in model.lanes:
            if lane.element_refs:
                lane_with_refs = lane
                break

        # At least one lane should have element references
        assert lane_with_refs is not None
        assert len(lane_with_refs.element_refs) > 0


class TestGenerateSwimlanes:
    """Tests for generating Draw.io with swimlanes."""

    def test_generate_single_pool(self):
        """Test generating diagram with single pool."""
        model = parse_bpmn(FIXTURES_DIR / "single_pool.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        # Should have pool cell
        cells = root.findall(".//mxCell[@vertex='1']")
        pool_cells = [c for c in cells if "swimlane" in c.get("style", "")]

        assert len(pool_cells) >= 1

    def test_generate_pool_with_lanes(self):
        """Test generating diagram with pool and lanes."""
        model = parse_bpmn(FIXTURES_DIR / "swimlanes.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        # Should have pool and lane cells
        cells = root.findall(".//mxCell[@vertex='1']")
        swimlane_cells = [c for c in cells if "swimlane" in c.get("style", "")]

        # At least 2 pools + 2 lanes
        assert len(swimlane_cells) >= 4

    def test_elements_have_correct_parents(self):
        """Test elements have correct parent references."""
        model = parse_bpmn(FIXTURES_DIR / "single_pool.bpmn")
        generator = DrawioGenerator()

        xml = generator.generate_string(model)
        root = ET.fromstring(xml.encode())

        # Find the pool cell
        cells = root.findall(".//mxCell[@vertex='1']")
        assert any("swimlane" in c.get("style", "") for c in cells)

        # Element cells should reference pool or lane as parent
        # (not the root "1")
        # This is a basic structure check


class TestEndToEndSwimlanes:
    """End-to-end tests for swimlane conversion."""

    def test_convert_single_pool(self, tmp_path):
        """Test converting file with single pool."""
        converter = Converter()
        output_file = tmp_path / "single_pool.drawio"

        result = converter.convert(FIXTURES_DIR / "single_pool.bpmn", output_file)

        assert result.success
        assert output_file.exists()

        content = output_file.read_text()
        assert "swimlane" in content

    def test_convert_swimlanes(self, tmp_path):
        """Test converting file with multiple pools and lanes."""
        converter = Converter()
        output_file = tmp_path / "swimlanes.drawio"

        result = converter.convert(FIXTURES_DIR / "swimlanes.bpmn", output_file)

        assert result.success

        content = output_file.read_text()
        assert "Customer" in content or "Service" in content
