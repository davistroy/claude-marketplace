"""Research Orchestrator - Parallel deep research across multiple LLM providers."""

from research_orchestrator.config import Depth, ResearchConfig
from research_orchestrator.models import ProviderResult, ResearchOutput
from research_orchestrator.orchestrator import ResearchOrchestrator

__version__ = "1.0.0"

__all__ = [
    "ResearchOrchestrator",
    "ResearchConfig",
    "ResearchOutput",
    "ProviderResult",
    "Depth",
]
