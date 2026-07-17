"""Main conversion orchestrator."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from .config import load_brand_config
from .generator import DrawioGenerator, GenerationResult
from .models import BPMNModel
from .parser import parse_bpmn
from .position_resolver import resolve_positions
from .themes import get_theme


@dataclass
class ConversionResult:
    """Result of BPMN to Draw.io conversion."""

    success: bool
    element_count: int
    flow_count: int
    warnings: list
    output_path: Optional[str] = None
    error: Optional[str] = None


class Converter:
    """Main conversion orchestrator."""

    def __init__(
        self,
        layout: str = "auto",
        theme: Optional[str] = None,
        config: Optional[str] = None,
        direction: str = "LR",
    ):
        """Initialize converter.

        Args:
            layout: Layout algorithm ("auto", "graphviz" or "preserve").
                "auto" preserves BPMN DI coordinates when the file provides
                them and falls back to graphviz layout otherwise.
            theme: Color theme name
            config: Path to brand configuration file
            direction: Flow direction (LR, TB, RL, BT)
        """
        self.layout = layout
        self.theme_name = theme
        self.config = config
        self.direction = direction

        # Build the actual theme object
        bpmn_theme = get_theme(theme or "default")
        if config:
            bpmn_theme = load_brand_config(config)

        self.generator = DrawioGenerator(theme=bpmn_theme)

    def _effective_layout(self, model: BPMNModel) -> str:
        """Resolve the concrete layout mode for a parsed model.

        "auto" becomes "preserve" only when the model carries *complete* DI
        coordinates (every element positioned); otherwise "graphviz". Gating on
        complete-rather-than-any DI keeps partial-DI files on a full graphviz
        layout instead of stranding the DI-less elements at the origin (#143).

        Args:
            model: Parsed BPMN model

        Returns:
            Either "preserve" or "graphviz"
        """
        if self.layout == "auto":
            return "preserve" if model.has_complete_di_coordinates else "graphviz"
        return self.layout

    def convert(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
    ) -> ConversionResult:
        """Convert BPMN file to Draw.io format.

        Args:
            input_path: Path to input BPMN file
            output_path: Path to output Draw.io file

        Returns:
            ConversionResult with statistics and status
        """
        warnings = []

        try:
            # Parse BPMN
            model = parse_bpmn(input_path)

            # Resolve the concrete layout mode (handles "auto")
            effective_layout = self._effective_layout(model)

            # Check for DI coordinates
            if not model.has_di_coordinates and effective_layout == "preserve":
                warnings.append(
                    "No DI coordinates found, but layout='preserve' was specified. "
                    "Elements will be positioned at (0,0)."
                )

            # Resolve positions (calculate layout for elements without DI)
            model = resolve_positions(
                model,
                direction=self.direction,
                use_layout=effective_layout,
            )

            # Generate Draw.io XML
            result = self.generator.generate(model, str(output_path))

            return ConversionResult(
                success=True,
                element_count=result.element_count,
                flow_count=result.flow_count,
                warnings=warnings,
                output_path=str(output_path),
            )

        except Exception as e:
            return ConversionResult(
                success=False,
                element_count=0,
                flow_count=0,
                warnings=warnings,
                error=str(e),
            )

    def convert_string(self, bpmn_xml: str) -> str:
        """Convert BPMN XML string to Draw.io XML string.

        Args:
            bpmn_xml: BPMN XML string

        Returns:
            Draw.io XML string
        """
        model = parse_bpmn(bpmn_xml)
        model = resolve_positions(
            model,
            direction=self.direction,
            use_layout=self._effective_layout(model),
        )
        return self.generator.generate_string(model)

    def convert_model(self, model: BPMNModel) -> GenerationResult:
        """Convert parsed BPMN model to Draw.io.

        Args:
            model: Parsed BPMN model

        Returns:
            GenerationResult with XML and statistics
        """
        return self.generator.generate_result(model)
