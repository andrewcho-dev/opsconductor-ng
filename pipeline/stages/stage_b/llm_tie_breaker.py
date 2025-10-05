"""
LLM Tie-Breaker - Phase 4 Module 2/2

Uses LLM to break ties when deterministic scoring is ambiguous.
This is the ONLY place where LLM makes tool selection decisions.

When to Use:
    - Top-2 candidates have scores within 8% of each other
    - Deterministic scorer cannot confidently choose
    - Need nuanced understanding of user intent

Design Principles:
1. Compact prompt (minimize tokens)
2. Structured JSON response for parsing
3. FAIL HARD if LLM is unavailable or fails - NO FALLBACKS
4. Log all LLM decisions for telemetry
5. Include justification for explainability
"""

import json
import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TieBreakerResult:
    """Result of LLM tie-breaking"""
    chosen_candidate: Dict  # The winning candidate
    justification: str
    llm_choice: str  # "A" or "B"
    llm_response_raw: Optional[str] = None  # Raw LLM response for debugging


class LLMTieBreaker:
    """
    Uses LLM to break ties between equally-scored candidates.
    
    This is the ONLY place where LLM makes tool selection decisions.
    All other decisions are deterministic and explainable.
    """
    
    # Compact prompt template to minimize tokens
    TIEBREAKER_PROMPT = """You are helping select the best tool for a user query. Two tools are equally viable based on mathematical scoring. Please choose the better option and explain why.

USER QUERY: {query}

OPTION A: {tool1_name}.{pattern1_name}
- Time: {time1_ms}ms
- Cost: ${cost1:.3f}
- Accuracy: {accuracy1:.2f}/1.0
- Completeness: {completeness1:.2f}/1.0
- Complexity: {complexity1:.2f}/1.0
- Limitations: {limitations1}

OPTION B: {tool2_name}.{pattern2_name}
- Time: {time2_ms}ms
- Cost: ${cost2:.3f}
- Accuracy: {accuracy2:.2f}/1.0
- Completeness: {completeness2:.2f}/1.0
- Complexity: {complexity2:.2f}/1.0
- Limitations: {limitations2}

Respond in JSON format:
{{"choice": "A" or "B", "justification": "Brief explanation (1-2 sentences)"}}"""
    
    def __init__(self, llm_client: Optional[Any] = None):
        """
        Initialize LLM tie-breaker.
        
        Args:
            llm_client: LLM client for tie-breaking. If None, break_tie() will raise RuntimeError.
        """
        self.llm_client = llm_client
    
    async def break_tie(
        self,
        query: str,
        candidate1: Dict,
        candidate2: Dict,
        timeout_ms: int = 3000
    ) -> TieBreakerResult:
        """
        Use LLM to choose between two equally-scored candidates.
        
        Args:
            query: Original user query
            candidate1: First candidate dict (from DeterministicScorer)
            candidate2: Second candidate dict
            timeout_ms: LLM timeout in milliseconds
        
        Returns:
            TieBreakerResult with chosen candidate and justification
        
        Raises:
            RuntimeError: If LLM client is not available or LLM call fails
        """
        # FAIL HARD if no LLM client
        if self.llm_client is None:
            raise RuntimeError("LLM client is required for tie-breaking but was not provided")
        
        # Build prompt
        prompt = self._build_prompt(query, candidate1, candidate2)
        
        # Call LLM with timeout
        response = await self._call_llm(prompt, timeout_ms)
        
        # Parse response
        choice, justification = self._parse_response(response)
        
        # Select winner
        chosen = candidate1 if choice == "A" else candidate2
        
        logger.info(
            f"LLM tie-breaker chose {choice}: {chosen['tool_name']}.{chosen['pattern_name']} "
            f"- {justification}"
        )
        
        return TieBreakerResult(
            chosen_candidate=chosen,
            justification=justification,
            llm_choice=choice,
            llm_response_raw=response
        )
    
    def _build_prompt(
        self,
        query: str,
        candidate1: Dict,
        candidate2: Dict
    ) -> str:
        """
        Build compact prompt for LLM.
        
        Args:
            query: User query
            candidate1: First candidate
            candidate2: Second candidate
        
        Returns:
            Formatted prompt string
        """
        # Extract features from candidates
        raw1 = candidate1.get('raw_features', {})
        raw2 = candidate2.get('raw_features', {})
        
        return self.TIEBREAKER_PROMPT.format(
            query=query,
            tool1_name=candidate1.get('tool_name', 'unknown'),
            pattern1_name=candidate1.get('pattern_name', 'unknown'),
            time1_ms=raw1.get('time_ms', 0),
            cost1=raw1.get('cost', 0.0),
            accuracy1=raw1.get('accuracy', 0.5),
            completeness1=raw1.get('completeness', 0.5),
            complexity1=raw1.get('complexity', 0.5),
            limitations1=raw1.get('limitations', 'None'),
            tool2_name=candidate2.get('tool_name', 'unknown'),
            pattern2_name=candidate2.get('pattern_name', 'unknown'),
            time2_ms=raw2.get('time_ms', 0),
            cost2=raw2.get('cost', 0.0),
            accuracy2=raw2.get('accuracy', 0.5),
            completeness2=raw2.get('completeness', 0.5),
            complexity2=raw2.get('complexity', 0.5),
            limitations2=raw2.get('limitations', 'None')
        )
    
    async def _call_llm(self, prompt: str, timeout_ms: int) -> str:
        """
        Call LLM with timeout.
        
        Args:
            prompt: Formatted prompt
            timeout_ms: Timeout in milliseconds
        
        Returns:
            LLM response string
        """
        # Check if llm_client has async chat method
        if hasattr(self.llm_client, 'chat'):
            response = await self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout_ms / 1000.0  # Convert to seconds
            )
            return response.get('content', '')
        
        # Fallback: try synchronous call
        elif hasattr(self.llm_client, 'generate'):
            response = self.llm_client.generate(prompt)
            return response
        
        else:
            raise ValueError("LLM client does not have chat() or generate() method")
    
    def _parse_response(self, response: str) -> Tuple[str, str]:
        """
        Parse LLM JSON response.
        
        Expected format:
        {"choice": "A" or "B", "justification": "..."}
        
        Args:
            response: Raw LLM response
        
        Returns:
            (choice, justification) tuple
        
        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to extract JSON from response
            # LLM might wrap JSON in markdown code blocks
            response_clean = response.strip()
            
            # Remove markdown code blocks if present
            if response_clean.startswith("```"):
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1])
            
            # Parse JSON
            data = json.loads(response_clean)
            
            choice = data.get('choice', '').upper()
            justification = data.get('justification', '')
            
            # Validate choice
            if choice not in ['A', 'B']:
                raise ValueError(f"Invalid choice: {choice}")
            
            if not justification:
                raise ValueError("Missing justification")
            
            return choice, justification
        
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}\nResponse: {response}")
            raise ValueError(f"Invalid LLM response format: {e}")