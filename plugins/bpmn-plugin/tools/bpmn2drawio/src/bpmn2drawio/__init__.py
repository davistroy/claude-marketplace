"""BPMN to Draw.io Converter.

A Python library and CLI tool for converting BPMN 2.0 XML files
to Draw.io diagram format.
"""

from .converter import ConversionResult, Converter
from .exceptions import (
    BPMN2DrawioError,
    BPMNParseError,
    ConfigurationError,
    InvalidBPMNError,
    LayoutError,
    OutputError,
    StyleError,
)
from .generator import DrawioGenerator, GenerationResult
from .layout import LayoutEngine
from .models import BPMNElement, BPMNFlow, BPMNModel, Lane, Pool
from .parser import BPMNParser, parse_bpmn
from .position_resolver import PositionResolver, resolve_positions
from .recovery import RecoveryStrategy, recover_model
from .validation import ModelValidator, ValidationWarning, validate_model

__version__ = "1.0.0"
__all__ = [
    "BPMNElement",
    "BPMNFlow",
    "Pool",
    "Lane",
    "BPMNModel",
    "parse_bpmn",
    "BPMNParser",
    "DrawioGenerator",
    "GenerationResult",
    "Converter",
    "ConversionResult",
    "LayoutEngine",
    "PositionResolver",
    "resolve_positions",
    "BPMNParseError",
    "InvalidBPMNError",
    "BPMN2DrawioError",
    "LayoutError",
    "StyleError",
    "OutputError",
    "ConfigurationError",
    "ValidationWarning",
    "ModelValidator",
    "validate_model",
    "RecoveryStrategy",
    "recover_model",
]
