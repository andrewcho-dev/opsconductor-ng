"""
Simple Intent Analyzer - Understanding what the user wants

This module uses LLM intelligence to understand user intent in plain language.
No complex frameworks, no JSON parsing, no unnecessary complexity.
Just: What does the user want?
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """Simple intent analyzer that understands what the user wants."""
    
    def __init__(self, llm_engine=None):
        """Initialize the intent analyzer with LLM engine."""
        self.llm_engine = llm_engine
    
    async def understand_user_intent(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Use LLM to understand what the user wants in plain language.
        
        Args:
            user_message: The user's request
            context: Optional context information
            
        Returns:
            Plain language description of what the user wants
        """
        if not self.llm_engine:
            raise Exception("LLM engine required for intent understanding")
        
        # Build context string if provided
        context_str = ""
        if context:
            context_str = f"\nContext: {context}"
        
        prompt = f"""You are an expert at understanding what people want when they make requests.

Your job is simple: Read the user's request and explain clearly what they want.

Be specific and practical. Focus on the actual outcome they're looking for.

User request: "{user_message}"{context_str}

What does this user want?"""

        try:
            response = await self.llm_engine.generate(prompt=prompt)
            intent = response.get("generated_text", "").strip()
            
            if not intent:
                raise Exception("LLM returned empty response")
            
            logger.info(f"🧠 User intent understood: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"🧠 Intent understanding FAILED: {e}")
            raise Exception(f"Failed to understand user intent: {e}")
    
    async def needs_clarification(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> tuple[bool, list[str]]:
        """
        Determine if we need to ask clarifying questions to understand what the user wants.
        
        Args:
            user_message: The user's request
            context: Optional context information
            
        Returns:
            Tuple of (needs_clarification: bool, questions: list[str])
        """
        if not self.llm_engine:
            raise Exception("LLM engine required for clarification analysis")
        
        # Build context string if provided
        context_str = ""
        if context:
            context_str = f"\nContext: {context}"
        
        prompt = f"""You are an expert at understanding user requests and determining when clarification is needed.

Look at this user request and determine: Can we understand what they want, or do we need to ask questions?

IMPORTANT: Only ask for clarification if it's IMPOSSIBLE to proceed without more information.
- "every day" is clear enough (don't ask for exact times)
- "critical disk space" is clear enough (don't ask for exact percentages)  
- "windows machines" is clear enough (don't ask for specific hostnames)
- "send alerts" is clear enough (don't ask for exact notification methods)

User request: "{user_message}"{context_str}

Can you understand what this user wants? If yes, respond with "CLEAR".
If you need clarification, respond with "UNCLEAR" followed by 1-2 specific questions that are absolutely necessary."""

        try:
            response = await self.llm_engine.generate(prompt=prompt)
            response_text = response.get("generated_text", "").strip()
            
            if response_text.startswith("CLEAR"):
                logger.info("🧠 User intent is clear - no clarification needed")
                return False, []
            elif response_text.startswith("UNCLEAR"):
                # Extract questions from the response
                lines = response_text.split('\n')
                questions = []
                for line in lines[1:]:  # Skip the "UNCLEAR" line
                    line = line.strip()
                    if line and not line.startswith("UNCLEAR"):
                        # Clean up question formatting
                        if line.startswith('-') or line.startswith('*'):
                            line = line[1:].strip()
                        if line.endswith('?'):
                            questions.append(line)
                        elif line:
                            questions.append(line + "?")
                
                # Limit to 2 questions max
                questions = questions[:2]
                logger.info(f"🧠 Clarification needed - questions: {questions}")
                return True, questions
            else:
                # If response doesn't start with CLEAR or UNCLEAR, assume it's clear
                logger.info("🧠 Ambiguous response, assuming intent is clear")
                return False, []
                
        except Exception as e:
            logger.error(f"🧠 Clarification analysis FAILED: {e}")
            # If we can't determine, assume it's clear and proceed
            logger.info("🧠 Clarification analysis failed, assuming intent is clear")
            return False, []