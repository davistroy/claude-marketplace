"""Visual Explainer - Transform text into AI-generated explanatory images."""

__version__ = "0.1.0"

# Re-export key classes for convenient access
from .models import (
    Concept,
    ConceptAnalysis,
    EvaluationResult,
    EvaluationVerdict,
    GenerationMetadata,
    ImagePrompt,
    ImageResult,
)

__all__ = [
    "__version__",
    # Models
    "Concept",
    "ConceptAnalysis",
    "EvaluationResult",
    "EvaluationVerdict",
    "GenerationMetadata",
    "ImagePrompt",
    "ImageResult",
]
