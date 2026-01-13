"""Custom exceptions for the BPMN to Draw.io converter."""


class BPMN2DrawioError(Exception):
    """Base exception for all converter errors."""

    pass


class BPMNParseError(BPMN2DrawioError):
    """Raised when BPMN XML cannot be parsed."""

    pass


class InvalidBPMNError(BPMN2DrawioError):
    """Raised when BPMN is structurally invalid."""

    pass


class LayoutError(BPMN2DrawioError):
    """Raised when layout calculation fails."""

    pass


class StyleError(BPMN2DrawioError):
    """Raised when style configuration is invalid."""

    pass


class OutputError(BPMN2DrawioError):
    """Raised when output cannot be written."""

    pass


class ConfigurationError(BPMN2DrawioError):
    """Raised when configuration file is invalid."""

    pass
