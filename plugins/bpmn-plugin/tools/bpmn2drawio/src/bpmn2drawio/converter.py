"""Main conversion orchestrator."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from .parser import parse_bpmn
from .generator import DrawioGenerator, GenerationResult
from .models import BPMNModel
from .position_resolver import resolve_positions
from .themes import get_theme, BPMNTheme
from .config import load_brand_config, merge_theme_with_config


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
        layout: str = "graphviz",
        theme: Optional[str] = None,
        config: Optional[str] = None,
        direction: str = "LR",
    ):
        """Initialize converter.

        Args:
            layout: Layout algorithm ("graphviz" or "preserve")
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
            config_theme = load_brand_config(config)
            bpmn_theme = merge_theme_with_config(bpmn_theme, {})
            # Use config theme if provided
            bpmn_theme = config_theme

        self.generator = DrawioGenerator(theme=bpmn_theme)

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

            # Check for DI coordinates
            if not model.has_di_coordinates and self.layout == "preserve":
                warnings.append(
                    "No DI coordinates found, but layout='preserve' was specified. "
                    "Elements will be positioned at (0,0)."
                )

            # Resolve positions (calculate layout for elements without DI)
            model = resolve_positions(
                model,
                direction=self.direction,
                use_layout=self.layout,
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
            use_layout=self.layout,
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
