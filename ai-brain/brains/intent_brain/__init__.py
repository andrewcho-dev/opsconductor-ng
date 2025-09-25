"""
Intent Brain Module

This module contains the Intent Brain implementation for the simplified AI architecture.
The Intent Brain is responsible for understanding WHAT the user wants - their business intent
and desired outcomes.
"""

from .intent_brain import IntentBrain
from .intent_analyzer import IntentAnalyzer

__all__ = ['IntentBrain', 'IntentAnalyzer']