"""
Preference Detector - Phase 3 Module 1/2

Detects user preferences from query text and maps to PreferenceMode.
This module analyzes natural language queries for preference signals like:
- Speed: "quick", "fast", "rapid", "immediate"
- Accuracy: "accurate", "precise", "exact", "verify"
- Thoroughness: "thorough", "complete", "comprehensive", "detailed"
- Cost: "cheap", "free", "cost-effective"
- Complexity: "simple", "basic", "straightforward"

Design Principles:
1. Keyword-based detection (simple, fast, explainable)
2. Explicit mode override support (from UI or API)
3. Balanced default (when no signals detected)
4. Case-insensitive matching
"""

from typing import Optional
import re
from .deterministic_scorer import PreferenceMode


class PreferenceDetector:
    """
    Detects user preferences from query text.
    
    Uses keyword matching to identify preference signals and maps them
    to PreferenceMode enum values.
    
    Example:
        detector = PreferenceDetector()
        mode = detector.detect_preference("Give me a quick count of Linux assets")
        # Returns: PreferenceMode.FAST
    """
    
    # Mode keywords (ordered by priority - more specific first)
    FAST_KEYWORDS = [
        "quick", "quickly", "fast", "rapid", "rapidly", "immediate", "immediately",
        "asap", "hurry", "urgent", "urgently", "speed", "speedy", "swift", "swiftly"
    ]
    
    ACCURATE_KEYWORDS = [
        "accurate", "accurately", "precise", "precisely", "exact", "exactly",
        "verify", "verified", "double-check", "double check", "confirm", "validated",
        "reliable", "reliably", "correct", "correctly"
    ]
    
    THOROUGH_KEYWORDS = [
        "thorough", "thoroughly", "complete", "completely", "comprehensive",
        "comprehensively", "detailed", "in detail", "all", "every", "exhaustive",
        "exhaustively", "full", "fully", "entire", "entirely"
    ]
    
    CHEAP_KEYWORDS = [
        "cheap", "cheaply", "free", "cost-effective", "economical", "economically",
        "inexpensive", "inexpensively", "low cost", "low-cost", "budget", "affordable"
    ]
    
    SIMPLE_KEYWORDS = [
        "simple", "simply", "basic", "basically", "straightforward", "easy",
        "easily", "minimal", "minimally", "lightweight"
    ]
    
    def __init__(self):
        """Initialize preference detector."""
        # Compile regex patterns for efficiency
        self._fast_pattern = self._compile_pattern(self.FAST_KEYWORDS)
        self._accurate_pattern = self._compile_pattern(self.ACCURATE_KEYWORDS)
        self._thorough_pattern = self._compile_pattern(self.THOROUGH_KEYWORDS)
        self._cheap_pattern = self._compile_pattern(self.CHEAP_KEYWORDS)
        self._simple_pattern = self._compile_pattern(self.SIMPLE_KEYWORDS)
    
    def _compile_pattern(self, keywords: list[str]) -> re.Pattern:
        """
        Compile keyword list into regex pattern.
        
        Uses word boundaries to avoid partial matches (e.g., "fast" shouldn't match "breakfast").
        
        Args:
            keywords: List of keywords to match
            
        Returns:
            Compiled regex pattern
        """
        # Escape special regex characters and join with OR
        escaped = [re.escape(kw) for kw in keywords]
        pattern = r'\b(' + '|'.join(escaped) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    
    def detect_preference(
        self,
        query: str,
        explicit_mode: Optional[str] = None
    ) -> PreferenceMode:
        """
        Detect user preference from query text.
        
        Priority:
        1. Explicit mode (if provided) - highest priority
        2. Keyword detection (if found)
        3. Balanced default (fallback)
        
        Args:
            query: User query text
            explicit_mode: Override mode ("fast", "accurate", "thorough", "cheap", "simple", "balanced")
            
        Returns:
            PreferenceMode enum value
            
        Examples:
            >>> detector = PreferenceDetector()
            >>> detector.detect_preference("Give me a quick count")
            PreferenceMode.FAST
            
            >>> detector.detect_preference("I need accurate data")
            PreferenceMode.ACCURATE
            
            >>> detector.detect_preference("Show me all details")
            PreferenceMode.THOROUGH
            
            >>> detector.detect_preference("Count assets", explicit_mode="fast")
            PreferenceMode.FAST
        """
        # Priority 1: Explicit mode override
        if explicit_mode:
            return self._parse_explicit_mode(explicit_mode)
        
        # Priority 2: Keyword detection
        query_lower = query.lower()
        
        # Count matches for each mode
        matches = {
            PreferenceMode.FAST: len(self._fast_pattern.findall(query_lower)),
            PreferenceMode.ACCURATE: len(self._accurate_pattern.findall(query_lower)),
            PreferenceMode.THOROUGH: len(self._thorough_pattern.findall(query_lower)),
            PreferenceMode.CHEAP: len(self._cheap_pattern.findall(query_lower)),
            PreferenceMode.SIMPLE: len(self._simple_pattern.findall(query_lower)),
        }
        
        # Find mode with most matches
        max_matches = max(matches.values())
        
        if max_matches > 0:
            # Return mode with most keyword matches
            for mode, count in matches.items():
                if count == max_matches:
                    return mode
        
        # Priority 3: Balanced default
        return PreferenceMode.BALANCED
    
    def _parse_explicit_mode(self, mode_str: str) -> PreferenceMode:
        """
        Parse explicit mode string to PreferenceMode enum.
        
        Args:
            mode_str: Mode string (case-insensitive)
            
        Returns:
            PreferenceMode enum value
            
        Raises:
            ValueError: If mode string is invalid
        """
        mode_lower = mode_str.lower().strip()
        
        mode_map = {
            "fast": PreferenceMode.FAST,
            "accurate": PreferenceMode.ACCURATE,
            "thorough": PreferenceMode.THOROUGH,
            "cheap": PreferenceMode.CHEAP,
            "simple": PreferenceMode.SIMPLE,
            "balanced": PreferenceMode.BALANCED,
        }
        
        if mode_lower not in mode_map:
            raise ValueError(
                f"Invalid preference mode: '{mode_str}'. "
                f"Must be one of: {list(mode_map.keys())}"
            )
        
        return mode_map[mode_lower]
    
    def detect_preference_with_confidence(
        self,
        query: str,
        explicit_mode: Optional[str] = None
    ) -> tuple[PreferenceMode, float]:
        """
        Detect preference with confidence score.
        
        Confidence is based on:
        - Explicit mode: 1.0 (highest confidence)
        - Keyword matches: 0.7 + (0.1 × num_matches) up to 1.0
        - Default: 0.5 (balanced fallback)
        
        Args:
            query: User query text
            explicit_mode: Override mode
            
        Returns:
            Tuple of (PreferenceMode, confidence_score)
            
        Examples:
            >>> detector = PreferenceDetector()
            >>> mode, conf = detector.detect_preference_with_confidence("quick fast count")
            >>> mode
            PreferenceMode.FAST
            >>> conf >= 0.8
            True
        """
        # Explicit mode has highest confidence
        if explicit_mode:
            mode = self._parse_explicit_mode(explicit_mode)
            return mode, 1.0
        
        # Keyword detection
        query_lower = query.lower()
        
        matches = {
            PreferenceMode.FAST: len(self._fast_pattern.findall(query_lower)),
            PreferenceMode.ACCURATE: len(self._accurate_pattern.findall(query_lower)),
            PreferenceMode.THOROUGH: len(self._thorough_pattern.findall(query_lower)),
            PreferenceMode.CHEAP: len(self._cheap_pattern.findall(query_lower)),
            PreferenceMode.SIMPLE: len(self._simple_pattern.findall(query_lower)),
        }
        
        max_matches = max(matches.values())
        
        if max_matches > 0:
            # Find mode with most matches
            for mode, count in matches.items():
                if count == max_matches:
                    # Confidence: 0.7 base + 0.1 per match (capped at 1.0)
                    confidence = min(1.0, 0.7 + (0.1 * count))
                    return mode, confidence
        
        # Default: balanced with medium confidence
        return PreferenceMode.BALANCED, 0.5