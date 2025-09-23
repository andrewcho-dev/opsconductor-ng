"""
Intent Brain Module

This module contains the Intent Brain implementation for the multi-brain AI architecture.
The Intent Brain is responsible for understanding WHAT the user wants - their business intent
and desired outcomes.
"""

from .intent_brain import IntentBrain
from .itil_classifier import ITILOperationsClassifier
from .business_intent_analyzer import BusinessIntentAnalyzer

__all__ = ['IntentBrain', 'ITILOperationsClassifier', 'BusinessIntentAnalyzer']