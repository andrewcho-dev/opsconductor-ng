"""
LLM Engine for OpsConductor
GPU-accelerated communication with Ollama and text generation
"""
import asyncio
import time
import torch
import structlog
from typing import Dict, List, Optional, Any
import ollama
import json

logger = structlog.get_logger()

class LLMEngine:
    """LLM engine for text generation and reasoning"""
    
    def __init__(self, ollama_host: str, default_model: str):
        self.ollama_host = ollama_host
        self.default_model = default_model
        self.client = None
        self.available_models = []
        
        # Initialize GPU monitoring
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"LLM Engine using device: {self.device}")
        
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            logger.info(f"GPU memory available: {gpu_memory:.2f} GB")
            logger.info(f"CUDA version: {torch.version.cuda}")
        else:
            logger.warning("No GPU available, using CPU for LLM operations")
        
    async def initialize(self) -> bool:
        """Initialize the LLM engine"""
        try:
            # Configure Ollama client
            self.client = ollama.Client(host=self.ollama_host)
            
            # Test connection and get available models
            self.available_models = await self.get_available_models()
            
            # Ensure default model is available
            if self.default_model not in self.available_models:
                logger.warning(f"Default model '{self.default_model}' not available. Attempting to pull...")
                success = await self.pull_model(self.default_model)
                if not success:
                    logger.error(f"Failed to pull default model '{self.default_model}'")
                    return False
            
            logger.info(f"LLM engine initialized with {len(self.available_models)} models")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize LLM engine", error=str(e))
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            if not self.client:
                return []
            
            models_response = self.client.list()
            models = [model['name'] for model in models_response.get('models', [])]
            self.available_models = models
            return models
            
        except Exception as e:
            logger.error("Failed to get available models", error=str(e))
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull/download a model"""
        try:
            if not self.client:
                return False
            
            logger.info(f"Pulling model: {model_name}")
            self.client.pull(model_name)
            
            # Refresh available models list
            await self.get_available_models()
            
            return model_name in self.available_models
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}", error=str(e))
            return False
    
    async def chat(self, message: str, context: Optional[str] = None, 
                   system_prompt: Optional[str] = None, model: Optional[str] = None,
                   parsed_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Chat with the LLM"""
        try:
            start_time = time.time()
            model_to_use = model or self.default_model
            
            if model_to_use not in self.available_models:
                raise Exception(f"Model '{model_to_use}' not available")
            
            # Build the conversation
            messages = []
            
            # Add system prompt
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            else:
                # Default system prompt for OpsConductor
                messages.append({
                    "role": "system",
                    "content": """You are OpsConductor AI, an IT operations automation assistant. 
                    You help with system administration, automation, troubleshooting, and IT operations.
                    Be helpful, accurate, and concise in your responses."""
                })
            
            # Add context if provided
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Relevant context:\n{context}"
                })
            
            # Add parsed data context if available
            if parsed_data:
                context_parts = []
                if parsed_data.get("operation"):
                    context_parts.append(f"Detected operation: {parsed_data['operation']}")
                if parsed_data.get("target_process"):
                    context_parts.append(f"Target process: {parsed_data['target_process']}")
                if parsed_data.get("target_group"):
                    context_parts.append(f"Target group: {parsed_data['target_group']}")
                
                if context_parts:
                    messages.append({
                        "role": "system",
                        "content": f"Parsed request details:\n" + "\n".join(context_parts)
                    })
            
            # Add user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Generate response
            response = self.client.chat(
                model=model_to_use,
                messages=messages
            )
            
            processing_time = time.time() - start_time
            response_text = response['message']['content']
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(response_text, message)
            
            return {
                "response": response_text,
                "model_used": model_to_use,
                "confidence": confidence,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error("Chat generation failed", error=str(e))
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "model_used": model_to_use,
                "confidence": 0.1,
                "processing_time": time.time() - start_time
            }
    
    async def generate(self, prompt: str, context: Optional[str] = None,
                      model: Optional[str] = None, max_tokens: Optional[int] = None,
                      temperature: Optional[float] = None) -> Dict[str, Any]:
        """Generate text from prompt"""
        try:
            start_time = time.time()
            model_to_use = model or self.default_model
            
            if model_to_use not in self.available_models:
                raise Exception(f"Model '{model_to_use}' not available")
            
            # Build full prompt
            full_prompt = prompt
            if context:
                full_prompt = f"Context:\n{context}\n\nPrompt:\n{prompt}"
            
            # Generate response
            response = self.client.generate(
                model=model_to_use,
                prompt=full_prompt
            )
            
            processing_time = time.time() - start_time
            generated_text = response['response']
            
            # Estimate token count (rough approximation)
            tokens_generated = len(generated_text.split())
            
            return {
                "generated_text": generated_text,
                "model_used": model_to_use,
                "tokens_generated": tokens_generated,
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error("Text generation failed", error=str(e))
            raise
    
    async def summarize(self, text: str, max_length: int = 200,
                       model: Optional[str] = None) -> Dict[str, Any]:
        """Summarize text"""
        try:
            model_to_use = model or self.default_model
            
            prompt = f"""Please summarize the following text in approximately {max_length} characters or less. 
            Focus on the key points and main ideas:

            {text}

            Summary:"""
            
            response = await self.generate(prompt, model=model_to_use)
            
            return {
                "summary": response["generated_text"].strip(),
                "model_used": model_to_use
            }
            
        except Exception as e:
            logger.error("Summarization failed", error=str(e))
            raise
    
    async def analyze(self, text: str, analysis_type: str = "sentiment",
                     model: Optional[str] = None) -> Dict[str, Any]:
        """Analyze text for sentiment, intent, etc."""
        try:
            model_to_use = model or self.default_model
            
            if analysis_type == "sentiment":
                prompt = f"""Analyze the sentiment of the following text. 
                Respond with a JSON object containing 'sentiment' (positive/negative/neutral) and 'score' (0-1):

                {text}

                Analysis:"""
            
            elif analysis_type == "intent":
                prompt = f"""Analyze the intent of the following text in the context of IT operations. 
                Respond with a JSON object containing 'intent' (automation/question/support/other) and 'confidence' (0-1):

                {text}

                Analysis:"""
            
            elif analysis_type == "complexity":
                prompt = f"""Analyze the complexity of the following text/request. 
                Respond with a JSON object containing 'complexity' (low/medium/high) and 'factors' (list of complexity factors):

                {text}

                Analysis:"""
            
            else:
                raise Exception(f"Unsupported analysis type: {analysis_type}")
            
            response = await self.generate(prompt, model=model_to_use)
            
            # Try to parse JSON response
            try:
                result = json.loads(response["generated_text"].strip())
                confidence = result.get("confidence", result.get("score", 0.5))
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                result = {"raw_response": response["generated_text"]}
                confidence = 0.3
            
            return {
                "result": result,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error("Text analysis failed", error=str(e))
            raise
    
    def _calculate_confidence(self, response: str, original_message: str) -> float:
        """Calculate confidence score for response quality"""
        try:
            # Simple heuristics for confidence calculation
            confidence = 0.5  # Base confidence
            
            # Length-based confidence
            if len(response) > 20:
                confidence += 0.2
            
            # Check for specific IT/automation terms
            it_terms = ["server", "service", "process", "automation", "script", "command", 
                       "system", "network", "database", "application", "workflow"]
            
            response_lower = response.lower()
            term_matches = sum(1 for term in it_terms if term in response_lower)
            confidence += min(term_matches * 0.05, 0.2)
            
            # Check for uncertainty indicators
            uncertainty_terms = ["i'm not sure", "i don't know", "maybe", "possibly", "might"]
            if any(term in response_lower for term in uncertainty_terms):
                confidence -= 0.2
            
            # Ensure confidence is between 0 and 1
            return max(0.1, min(1.0, confidence))
            
        except Exception:
            return 0.5
    
    def get_gpu_status(self) -> Dict[str, Any]:
        """Get current GPU status and memory usage"""
        try:
            if not torch.cuda.is_available():
                return {
                    "gpu_available": False,
                    "device": "cpu",
                    "message": "No GPU available"
                }
            
            device_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            device_name = torch.cuda.get_device_name(current_device)
            
            # Get memory info
            memory_allocated = torch.cuda.memory_allocated(current_device) / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved(current_device) / 1024**3   # GB
            memory_total = torch.cuda.get_device_properties(current_device).total_memory / 1024**3  # GB
            
            return {
                "gpu_available": True,
                "device": f"cuda:{current_device}",
                "device_name": device_name,
                "device_count": device_count,
                "memory_allocated_gb": round(memory_allocated, 2),
                "memory_reserved_gb": round(memory_reserved, 2),
                "memory_total_gb": round(memory_total, 2),
                "memory_free_gb": round(memory_total - memory_reserved, 2),
                "cuda_version": torch.version.cuda
            }
            
        except Exception as e:
            logger.error(f"Failed to get GPU status: {e}")
            return {
                "gpu_available": False,
                "device": "cpu",
                "error": str(e)
            }