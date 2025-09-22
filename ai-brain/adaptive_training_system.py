#!/usr/bin/env python3
"""
Adaptive Training System for Progressive AI Intent Recognition

This system continuously learns from user interactions and improves intent recognition
through multiple training approaches:
1. Real-time feedback learning
2. Pattern mining from successful interactions
3. Semantic similarity learning
4. Context-aware intent classification
5. Active learning with uncertainty sampling
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import sqlite3
import hashlib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import pickle
import os

logger = logging.getLogger(__name__)

@dataclass
class TrainingExample:
    """A training example for intent recognition"""
    text: str
    intent: str
    confidence: float
    user_feedback: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    source: str = "user_interaction"  # user_interaction, synthetic, imported
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class IntentPattern:
    """Enhanced intent pattern with learning capabilities"""
    pattern: str
    intent: str
    confidence_base: float
    success_count: int = 0
    failure_count: int = 0
    last_used: datetime = None
    created_at: datetime = None
    pattern_type: str = "regex"  # regex, semantic, keyword, hybrid
    semantic_embedding: Optional[List[float]] = None
    context_requirements: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def adjusted_confidence(self) -> float:
        """Confidence adjusted by success rate and recency"""
        base_confidence = self.confidence_base * self.success_rate if self.success_rate > 0 else self.confidence_base * 0.5
        
        # Boost confidence for recently successful patterns
        if self.last_used and self.success_count > 0:
            days_since_use = (datetime.now() - self.last_used).days
            recency_boost = max(0, 1 - (days_since_use / 30))  # Decay over 30 days
            base_confidence *= (1 + recency_boost * 0.2)
        
        return min(1.0, base_confidence)

class SemanticIntentMatcher:
    """Semantic-based intent matching using embeddings"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        self.intent_embeddings = {}
        self.training_texts = []
        self.training_intents = []
        self.is_trained = False
    
    def add_training_example(self, text: str, intent: str):
        """Add a training example"""
        self.training_texts.append(text.lower())
        self.training_intents.append(intent)
        self.is_trained = False
    
    def train(self):
        """Train the semantic matcher"""
        if len(self.training_texts) < 2:
            return
        
        try:
            # Fit vectorizer on training texts
            text_vectors = self.vectorizer.fit_transform(self.training_texts)
            
            # Create intent embeddings by averaging vectors for each intent
            intent_vectors = defaultdict(list)
            for i, intent in enumerate(self.training_intents):
                intent_vectors[intent].append(text_vectors[i].toarray()[0])
            
            # Average vectors for each intent
            for intent, vectors in intent_vectors.items():
                self.intent_embeddings[intent] = np.mean(vectors, axis=0)
            
            self.is_trained = True
            logger.info(f"Trained semantic matcher with {len(self.training_texts)} examples for {len(self.intent_embeddings)} intents")
            
        except Exception as e:
            logger.error(f"Error training semantic matcher: {e}")
    
    def predict_intent(self, text: str) -> List[Tuple[str, float]]:
        """Predict intent with confidence scores"""
        if not self.is_trained or not self.intent_embeddings:
            return []
        
        try:
            # Vectorize input text
            text_vector = self.vectorizer.transform([text.lower()]).toarray()[0]
            
            # Calculate similarities with all intent embeddings
            similarities = []
            for intent, embedding in self.intent_embeddings.items():
                similarity = cosine_similarity([text_vector], [embedding])[0][0]
                similarities.append((intent, similarity))
            
            # Sort by similarity and return top matches
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:3]  # Top 3 matches
            
        except Exception as e:
            logger.error(f"Error predicting intent: {e}")
            return []

class AdaptiveTrainingSystem:
    """Main adaptive training system"""
    
    def __init__(self, db_path: str = "/tmp/adaptive_training.db"):
        self.db_path = db_path
        self.semantic_matcher = SemanticIntentMatcher()
        self.training_examples = []
        self.intent_patterns = {}
        self.uncertainty_threshold = 0.6  # Threshold for active learning
        self.min_examples_for_training = 5
        self.last_training_time = None
        self.training_interval = timedelta(hours=1)  # Retrain every hour
        
        # Initialize database
        self._init_database()
        self._load_training_data()
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Training examples table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_examples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    user_feedback TEXT,
                    context TEXT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL
                )
            ''')
            
            # Intent patterns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intent_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    confidence_base REAL NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    created_at TEXT NOT NULL,
                    pattern_type TEXT NOT NULL,
                    semantic_embedding TEXT,
                    context_requirements TEXT
                )
            ''')
            
            # Training sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS training_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start TEXT NOT NULL,
                    session_end TEXT,
                    examples_processed INTEGER DEFAULT 0,
                    patterns_created INTEGER DEFAULT 0,
                    patterns_updated INTEGER DEFAULT 0,
                    accuracy_improvement REAL DEFAULT 0.0,
                    notes TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _load_training_data(self):
        """Load existing training data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load training examples
            cursor.execute('SELECT * FROM training_examples ORDER BY timestamp DESC LIMIT 1000')
            for row in cursor.fetchall():
                example = TrainingExample(
                    text=row[1],
                    intent=row[2],
                    confidence=row[3],
                    user_feedback=row[4],
                    context=json.loads(row[5]) if row[5] else None,
                    timestamp=datetime.fromisoformat(row[6]),
                    source=row[7]
                )
                self.training_examples.append(example)
                self.semantic_matcher.add_training_example(example.text, example.intent)
            
            # Load intent patterns
            cursor.execute('SELECT * FROM intent_patterns')
            for row in cursor.fetchall():
                pattern = IntentPattern(
                    pattern=row[1],
                    intent=row[2],
                    confidence_base=row[3],
                    success_count=row[4],
                    failure_count=row[5],
                    last_used=datetime.fromisoformat(row[6]) if row[6] else None,
                    created_at=datetime.fromisoformat(row[7]),
                    pattern_type=row[8],
                    semantic_embedding=json.loads(row[9]) if row[9] else None,
                    context_requirements=json.loads(row[10]) if row[10] else None
                )
                pattern_key = f"{pattern.intent}:{hashlib.md5(pattern.pattern.encode()).hexdigest()[:8]}"
                self.intent_patterns[pattern_key] = pattern
            
            conn.close()
            
            logger.info(f"Loaded {len(self.training_examples)} training examples and {len(self.intent_patterns)} patterns")
            
            # Train semantic matcher if we have enough examples
            if len(self.training_examples) >= self.min_examples_for_training:
                self.semantic_matcher.train()
            
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
    
    async def add_training_example(self, text: str, intent: str, confidence: float, 
                                 user_feedback: Optional[str] = None, 
                                 context: Optional[Dict[str, Any]] = None,
                                 source: str = "user_interaction") -> bool:
        """Add a new training example"""
        try:
            example = TrainingExample(
                text=text,
                intent=intent,
                confidence=confidence,
                user_feedback=user_feedback,
                context=context,
                source=source
            )
            
            self.training_examples.append(example)
            self.semantic_matcher.add_training_example(text, intent)
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO training_examples 
                (text, intent, confidence, user_feedback, context, timestamp, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                example.text,
                example.intent,
                example.confidence,
                example.user_feedback,
                json.dumps(example.context) if example.context else None,
                example.timestamp.isoformat(),
                example.source
            ))
            conn.commit()
            conn.close()
            
            # Trigger retraining if needed
            await self._check_and_retrain()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding training example: {e}")
            return False
    
    async def _check_and_retrain(self):
        """Check if retraining is needed and trigger it"""
        now = datetime.now()
        
        # Check if enough time has passed since last training
        if (self.last_training_time is None or 
            now - self.last_training_time > self.training_interval):
            
            # Check if we have enough new examples
            recent_examples = [
                ex for ex in self.training_examples 
                if self.last_training_time is None or ex.timestamp > self.last_training_time
            ]
            
            if len(recent_examples) >= self.min_examples_for_training:
                await self.retrain_system()
    
    async def retrain_system(self) -> Dict[str, Any]:
        """Retrain the entire system with accumulated examples"""
        session_start = datetime.now()
        patterns_created = 0
        patterns_updated = 0
        
        try:
            logger.info("Starting adaptive training session...")
            
            # Train semantic matcher
            self.semantic_matcher.train()
            
            # Mine new patterns from successful examples
            new_patterns = await self._mine_patterns_from_examples()
            patterns_created = len(new_patterns)
            
            # Update existing patterns based on feedback
            patterns_updated = await self._update_patterns_from_feedback()
            
            # Optimize pattern set
            await self._optimize_pattern_set()
            
            # Record training session
            session_end = datetime.now()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO training_sessions 
                (session_start, session_end, examples_processed, patterns_created, patterns_updated)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session_start.isoformat(),
                session_end.isoformat(),
                len(self.training_examples),
                patterns_created,
                patterns_updated
            ))
            conn.commit()
            conn.close()
            
            self.last_training_time = session_end
            
            result = {
                "success": True,
                "session_duration": (session_end - session_start).total_seconds(),
                "examples_processed": len(self.training_examples),
                "patterns_created": patterns_created,
                "patterns_updated": patterns_updated,
                "total_patterns": len(self.intent_patterns)
            }
            
            logger.info(f"Training session completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error during retraining: {e}")
            return {"success": False, "error": str(e)}
    
    async def _mine_patterns_from_examples(self) -> List[IntentPattern]:
        """Mine new patterns from successful training examples"""
        new_patterns = []
        
        try:
            # Group examples by intent
            intent_examples = defaultdict(list)
            for example in self.training_examples:
                if example.confidence > 0.7:  # Only use high-confidence examples
                    intent_examples[example.intent].append(example)
            
            # Mine patterns for each intent
            for intent, examples in intent_examples.items():
                if len(examples) < 3:  # Need at least 3 examples
                    continue
                
                # Extract common keywords and phrases
                texts = [ex.text.lower() for ex in examples]
                
                # Find common n-grams
                common_patterns = self._extract_common_patterns(texts)
                
                for pattern_text, frequency in common_patterns:
                    if frequency >= 2:  # Pattern appears in at least 2 examples
                        pattern = IntentPattern(
                            pattern=pattern_text,
                            intent=intent,
                            confidence_base=min(0.9, 0.5 + (frequency * 0.1)),
                            pattern_type="mined",
                            success_count=frequency
                        )
                        
                        pattern_key = f"{intent}:{hashlib.md5(pattern_text.encode()).hexdigest()[:8]}"
                        if pattern_key not in self.intent_patterns:
                            self.intent_patterns[pattern_key] = pattern
                            new_patterns.append(pattern)
                            
                            # Save to database
                            await self._save_pattern_to_db(pattern)
            
            return new_patterns
            
        except Exception as e:
            logger.error(f"Error mining patterns: {e}")
            return []
    
    def _extract_common_patterns(self, texts: List[str]) -> List[Tuple[str, int]]:
        """Extract common patterns from a list of texts"""
        patterns = Counter()
        
        for text in texts:
            # Extract keywords (words longer than 3 characters)
            words = re.findall(r'\b\w{4,}\b', text)
            for word in words:
                patterns[word] += 1
            
            # Extract 2-grams and 3-grams
            words_list = text.split()
            for i in range(len(words_list) - 1):
                bigram = ' '.join(words_list[i:i+2])
                patterns[bigram] += 1
                
                if i < len(words_list) - 2:
                    trigram = ' '.join(words_list[i:i+3])
                    patterns[trigram] += 1
        
        # Return patterns that appear in multiple texts
        return [(pattern, count) for pattern, count in patterns.most_common(20) if count > 1]
    
    async def _update_patterns_from_feedback(self) -> int:
        """Update existing patterns based on user feedback"""
        updated_count = 0
        
        try:
            # Process feedback from training examples
            for example in self.training_examples:
                if example.user_feedback:
                    # Find patterns that matched this example
                    matching_patterns = await self._find_matching_patterns(example.text)
                    
                    for pattern_key, confidence in matching_patterns:
                        pattern = self.intent_patterns.get(pattern_key)
                        if pattern:
                            # Update pattern based on feedback
                            if "correct" in example.user_feedback.lower() or "good" in example.user_feedback.lower():
                                pattern.success_count += 1
                            elif "wrong" in example.user_feedback.lower() or "incorrect" in example.user_feedback.lower():
                                pattern.failure_count += 1
                            
                            pattern.last_used = example.timestamp
                            updated_count += 1
                            
                            # Update in database
                            await self._update_pattern_in_db(pattern_key, pattern)
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating patterns from feedback: {e}")
            return 0
    
    async def _find_matching_patterns(self, text: str) -> List[Tuple[str, float]]:
        """Find patterns that match the given text"""
        matches = []
        
        for pattern_key, pattern in self.intent_patterns.items():
            try:
                if pattern.pattern_type == "regex":
                    if re.search(pattern.pattern, text, re.IGNORECASE):
                        matches.append((pattern_key, pattern.adjusted_confidence))
                elif pattern.pattern_type in ["mined", "keyword"]:
                    if pattern.pattern.lower() in text.lower():
                        matches.append((pattern_key, pattern.adjusted_confidence))
            except Exception as e:
                logger.warning(f"Error matching pattern {pattern_key}: {e}")
        
        return matches
    
    async def _optimize_pattern_set(self):
        """Optimize the pattern set by removing poor performers"""
        patterns_to_remove = []
        
        for pattern_key, pattern in self.intent_patterns.items():
            total_uses = pattern.success_count + pattern.failure_count
            
            # Remove patterns with poor success rate and enough usage
            if total_uses >= 10 and pattern.success_rate < 0.3:
                patterns_to_remove.append(pattern_key)
            
            # Remove very old unused patterns
            elif (pattern.last_used is None and 
                  (datetime.now() - pattern.created_at).days > 90):
                patterns_to_remove.append(pattern_key)
        
        # Remove poor patterns
        for pattern_key in patterns_to_remove:
            del self.intent_patterns[pattern_key]
            await self._remove_pattern_from_db(pattern_key)
        
        if patterns_to_remove:
            logger.info(f"Removed {len(patterns_to_remove)} poor-performing patterns")
    
    async def predict_intent(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Predict intent using all available methods"""
        predictions = []
        
        # 1. Pattern-based matching
        pattern_matches = await self._find_matching_patterns(text)
        for pattern_key, confidence in pattern_matches:
            pattern = self.intent_patterns[pattern_key]
            predictions.append({
                "intent": pattern.intent,
                "confidence": confidence,
                "method": "pattern",
                "pattern_key": pattern_key
            })
        
        # 2. Semantic matching
        if self.semantic_matcher.is_trained:
            semantic_matches = self.semantic_matcher.predict_intent(text)
            for intent, similarity in semantic_matches:
                predictions.append({
                    "intent": intent,
                    "confidence": similarity,
                    "method": "semantic"
                })
        
        # 3. Combine and rank predictions
        intent_scores = defaultdict(list)
        for pred in predictions:
            intent_scores[pred["intent"]].append(pred["confidence"])
        
        # Calculate final scores (average of all methods)
        final_predictions = []
        for intent, scores in intent_scores.items():
            avg_confidence = sum(scores) / len(scores)
            max_confidence = max(scores)
            final_predictions.append({
                "intent": intent,
                "confidence": avg_confidence,
                "max_confidence": max_confidence,
                "method_count": len(scores)
            })
        
        # Sort by confidence
        final_predictions.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Determine if we need active learning
        needs_feedback = (
            not final_predictions or 
            final_predictions[0]["confidence"] < self.uncertainty_threshold
        )
        
        return {
            "predictions": final_predictions[:3],  # Top 3
            "best_intent": final_predictions[0]["intent"] if final_predictions else "unknown",
            "confidence": final_predictions[0]["confidence"] if final_predictions else 0.0,
            "needs_feedback": needs_feedback,
            "uncertainty_score": 1.0 - (final_predictions[0]["confidence"] if final_predictions else 0.0)
        }
    
    async def _save_pattern_to_db(self, pattern: IntentPattern):
        """Save pattern to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO intent_patterns 
                (pattern, intent, confidence_base, success_count, failure_count, 
                 last_used, created_at, pattern_type, semantic_embedding, context_requirements)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern,
                pattern.intent,
                pattern.confidence_base,
                pattern.success_count,
                pattern.failure_count,
                pattern.last_used.isoformat() if pattern.last_used else None,
                pattern.created_at.isoformat(),
                pattern.pattern_type,
                json.dumps(pattern.semantic_embedding) if pattern.semantic_embedding else None,
                json.dumps(pattern.context_requirements) if pattern.context_requirements else None
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving pattern to database: {e}")
    
    async def _update_pattern_in_db(self, pattern_key: str, pattern: IntentPattern):
        """Update pattern in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE intent_patterns 
                SET success_count = ?, failure_count = ?, last_used = ?
                WHERE pattern = ? AND intent = ?
            ''', (
                pattern.success_count,
                pattern.failure_count,
                pattern.last_used.isoformat() if pattern.last_used else None,
                pattern.pattern,
                pattern.intent
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating pattern in database: {e}")
    
    async def _remove_pattern_from_db(self, pattern_key: str):
        """Remove pattern from database"""
        try:
            pattern = self.intent_patterns.get(pattern_key)
            if pattern:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM intent_patterns 
                    WHERE pattern = ? AND intent = ?
                ''', (pattern.pattern, pattern.intent))
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Error removing pattern from database: {e}")
    
    async def get_training_statistics(self) -> Dict[str, Any]:
        """Get comprehensive training statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get training session stats
            cursor.execute('''
                SELECT COUNT(*), AVG(examples_processed), AVG(patterns_created), AVG(patterns_updated)
                FROM training_sessions
            ''')
            session_stats = cursor.fetchone()
            
            # Get intent distribution
            cursor.execute('''
                SELECT intent, COUNT(*) as count
                FROM training_examples
                GROUP BY intent
                ORDER BY count DESC
            ''')
            intent_distribution = dict(cursor.fetchall())
            
            # Get pattern performance
            pattern_stats = {}
            for pattern_key, pattern in self.intent_patterns.items():
                if pattern.intent not in pattern_stats:
                    pattern_stats[pattern.intent] = {
                        "count": 0,
                        "avg_success_rate": 0,
                        "total_uses": 0
                    }
                
                pattern_stats[pattern.intent]["count"] += 1
                pattern_stats[pattern.intent]["avg_success_rate"] += pattern.success_rate
                pattern_stats[pattern.intent]["total_uses"] += pattern.success_count + pattern.failure_count
            
            # Calculate averages
            for intent_stat in pattern_stats.values():
                if intent_stat["count"] > 0:
                    intent_stat["avg_success_rate"] /= intent_stat["count"]
            
            conn.close()
            
            return {
                "total_examples": len(self.training_examples),
                "total_patterns": len(self.intent_patterns),
                "training_sessions": session_stats[0] if session_stats[0] else 0,
                "avg_examples_per_session": session_stats[1] if session_stats[1] else 0,
                "avg_patterns_created_per_session": session_stats[2] if session_stats[2] else 0,
                "avg_patterns_updated_per_session": session_stats[3] if session_stats[3] else 0,
                "intent_distribution": intent_distribution,
                "pattern_performance": pattern_stats,
                "semantic_matcher_trained": self.semantic_matcher.is_trained,
                "last_training": self.last_training_time.isoformat() if self.last_training_time else None
            }
            
        except Exception as e:
            logger.error(f"Error getting training statistics: {e}")
            return {"error": str(e)}

# Integration function for the main conversation handler
async def integrate_adaptive_training(conversation_handler):
    """Integrate adaptive training system with the conversation handler"""
    
    # Initialize adaptive training system
    training_system = AdaptiveTrainingSystem()
    
    # Add method to conversation handler for training integration
    async def enhanced_process_message(self, message: str, user_id: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced message processing with adaptive training"""
        
        # Get intent prediction from training system
        intent_prediction = await training_system.predict_intent(message)
        
        # Process message normally
        result = await self.original_process_message(message, user_id, conversation_id)
        
        # Add training data if we have a successful interpretation
        if result.get("success") and intent_prediction.get("best_intent") != "unknown":
            await training_system.add_training_example(
                text=message,
                intent=intent_prediction["best_intent"],
                confidence=intent_prediction["confidence"],
                context={"user_id": user_id, "conversation_id": conversation_id}
            )
        
        # Add training suggestions to result
        result["training_info"] = {
            "predicted_intent": intent_prediction["best_intent"],
            "confidence": intent_prediction["confidence"],
            "needs_feedback": intent_prediction["needs_feedback"],
            "uncertainty_score": intent_prediction["uncertainty_score"]
        }
        
        return result
    
    # Store original method and replace with enhanced version
    conversation_handler.original_process_message = conversation_handler.process_message
    conversation_handler.process_message = enhanced_process_message.__get__(conversation_handler, type(conversation_handler))
    
    # Add training system methods to conversation handler
    conversation_handler.training_system = training_system
    conversation_handler.get_training_statistics = training_system.get_training_statistics
    conversation_handler.retrain_system = training_system.retrain_system
    
    return training_system