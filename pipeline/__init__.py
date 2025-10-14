"""
NEWIDEA.MD Pipeline Architecture
4-Stage Pipeline for AI-Driven Operations

Architecture:
User Request → Stage A (Classifier) → Stage B (Selector) → Stage C (Planner) → [Stage D (Answerer)] → Execution

This is a CLEAN BREAK from the old AI Brain architecture.
No backward compatibility, no fallback mechanisms.
"""

__version__ = "1.1.0"
__architecture__ = "4-stage-pipeline"

# Pipeline stages
STAGE_A_CLASSIFIER = "classifier"
STAGE_B_SELECTOR = "selector" 
STAGE_C_PLANNER = "planner"
STAGE_D_ANSWERER = "answerer"

# Pipeline flow
PIPELINE_STAGES = [
    STAGE_A_CLASSIFIER,
    STAGE_B_SELECTOR,
    STAGE_C_PLANNER,
    STAGE_D_ANSWERER
]

# Decision types
DECISION_ACTION = "action"
DECISION_INFO = "info"