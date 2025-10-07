"""
Stage AB - Combined Understanding & Selection

This module merges the functionality of Stage A (Classifier) and Stage B (Selector)
into a single, more reliable stage that eliminates the fragile handoff between stages.
"""

from .combined_selector import CombinedSelector

__all__ = ["CombinedSelector"]