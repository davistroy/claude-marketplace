"""BPMN to Draw.io Converter.

A Python library and CLI tool for converting BPMN 2.0 XML files
to Draw.io diagram format.
"""

from .models import BPMNElement, BPMNFlow, Pool, Lane, BPMNModel
from .parser import parse_bpmn, BPMNParser
from .generator import DrawioGenerator, GenerationResult
from .converter import Converter, ConversionResult
from .layout import LayoutEngine
from .position_resolver import PositionResolver, resolve_positions
from .exceptions import (
    BPMNParseError, InvalidBPMNError, BPMN2DrawioError,
    LayoutError, StyleError, OutputError, ConfigurationError
)
from .validation import ValidationWarning, ModelValidator, validate_model
from .recovery import RecoveryStrategy, recover_model

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
