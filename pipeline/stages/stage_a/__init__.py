"""
Stage A: Classifier
NEWIDEA.MD Pipeline - Intent Classification and Entity Extraction

This stage is responsible for:
1. Intent classification - Understanding what the user wants to do
2. Entity extraction - Identifying key entities (services, hosts, commands, etc.)
3. Confidence scoring - Assessing confidence in the classification
4. Risk assessment - Initial risk evaluation
5. Decision v1 output - Structured output for Stage B

Stage A is the entry point of the NEWIDEA.MD pipeline and converts
natural language requests into structured Decision v1 format.
"""

from .classifier import StageAClassifier
from .intent_classifier import IntentClassifier
from .entity_extractor import EntityExtractor
from .confidence_scorer import ConfidenceScorer
from .risk_assessor import RiskAssessor

__all__ = [
    "StageAClassifier",
    "IntentClassifier", 
    "EntityExtractor",
    "ConfidenceScorer",
    "RiskAssessor"
]

# Stage A version
STAGE_A_VERSION = "1.0.0"