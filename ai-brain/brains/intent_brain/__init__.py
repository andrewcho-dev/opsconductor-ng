"""
Intent Brain Module

This module contains the Intent Brain implementation for the multi-brain AI architecture.
The Intent Brain is responsible for understanding WHAT the user wants - their business intent
and desired outcomes.
"""

from .intent_brain import IntentBrain
from .four_w_analyzer import FourWAnalyzer

__all__ = ['IntentBrain', 'FourWAnalyzer']