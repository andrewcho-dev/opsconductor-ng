"""
OpsConductor AI Brain - Modern Learning API Router

This module provides REST API endpoints for machine learning and pattern recognition,
using the modernized learning engine with vector store integration.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from shared.learning_engine import LearningOrchestrator
from integrations.vector_client import OpsConductorVectorStore

logger = logging.getLogger(__name__)

# Initialize learning orchestrator with vector client
vector_client = OpsConductorVectorStore()
learning_orchestrator = LearningOrchestrator(vector_client)

# Create router
learning_router = APIRouter(prefix="/ai/learning", tags=["AI Learning"])

# Request/Response Models
class ExecutionRecord(BaseModel):
    user_id: str = Field(..., description="User who executed the automation")
    automation_type: str = Field(..., description="Type of automation executed")
    execution_data: Dict[str, Any] = Field(..., description="Execution details and parameters")
    success: bool = Field(..., description="Whether execution was successful")
    execution_time: float = Field(..., description="Time taken for execution")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")

class FailurePredictionRequest(BaseModel):
    system_type: str = Field(..., description="Type of system to predict failures for")
    current_metrics: Dict[str, Any] = Field(..., description="Current system metrics")
    prediction_horizon: int = Field(24, description="Hours ahead to predict")

class TrainingRequest(BaseModel):
    force_retrain: bool = Field(False, description="Force retraining of all models")
    specific_models: Optional[List[str]] = Field(None, description="Specific models to train")

class PredictionValidation(BaseModel):
    actual_outcome: str = Field(..., description="Actual outcome that occurred")
    notes: Optional[str] = Field(None, description="Additional notes about the validation")

@learning_router.post("/record")
async def record_execution(record: ExecutionRecord):
    """Record automation execution for learning (replaces /ai/learning/record-execution)"""
    try:
        # Store execution pattern in vector store
        await learning_orchestrator.pattern_learner.learn_from_execution(
            user_id=record.user_id,
            automation_type=record.automation_type,
            execution_data=record.execution_data,
            success=record.success,
            execution_time=record.execution_time,
            error_message=record.error_message
        )
        
        return {
            "success": True,
            "message": "Execution recorded successfully",
            "user_id": record.user_id,
            "automation_type": record.automation_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to record execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.post("/predictions")
async def predict_failure(request: FailurePredictionRequest):
    """Predict system failures (replaces /ai/learning/predict-failure)"""
    try:
        # Use learning orchestrator to predict failures
        prediction = await learning_orchestrator.predict_system_failure(
            system_type=request.system_type,
            current_metrics=request.current_metrics,
            prediction_horizon=request.prediction_horizon
        )
        
        return {
            "success": True,
            "system_type": request.system_type,
            "prediction_horizon": request.prediction_horizon,
            "prediction": prediction,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to predict failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/patterns/{user_id}")
async def get_user_patterns(user_id: str, limit: int = 50):
    """Get user behavior patterns (replaces /ai/learning/patterns/{user_id})"""
    try:
        # Search for user patterns in vector store
        patterns = await learning_orchestrator.pattern_learner.get_user_patterns(
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "patterns": patterns,
            "count": len(patterns),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get user patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/predictions/history")
async def get_prediction_history(limit: int = 100):
    """Get prediction history with accuracy metrics (replaces /ai/learning/predictions/history)"""
    try:
        # Get prediction history from learning orchestrator
        history = await learning_orchestrator.get_prediction_history(limit=limit)
        
        # Calculate overall accuracy
        validated_predictions = [p for p in history if p.get("actual_outcome") is not None]
        overall_accuracy = 0.0
        if validated_predictions:
            correct_predictions = sum(1 for p in validated_predictions 
                                    if p["predicted_outcome"] == p["actual_outcome"])
            overall_accuracy = correct_predictions / len(validated_predictions)
        
        return {
            "success": True,
            "predictions": history,
            "count": len(history),
            "validated_count": len(validated_predictions),
            "overall_accuracy": overall_accuracy,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get prediction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.post("/predictions/{prediction_id}/validate")
async def validate_prediction(prediction_id: str, validation: PredictionValidation):
    """Validate a prediction with actual outcome (replaces /ai/learning/validate-prediction/{prediction_id})"""
    try:
        # Validate prediction through learning orchestrator
        result = await learning_orchestrator.validate_prediction(
            prediction_id=prediction_id,
            actual_outcome=validation.actual_outcome,
            notes=validation.notes
        )
        
        return {
            "success": True,
            "message": "Prediction validated successfully",
            "prediction_id": prediction_id,
            "actual_outcome": validation.actual_outcome,
            "accuracy": result.get("accuracy", 0.0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to validate prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.post("/train")
async def train_models(background_tasks: BackgroundTasks, request: TrainingRequest):
    """Train or retrain ML models (replaces /ai/learning/train-models)"""
    try:
        # Run training in background
        if request.specific_models:
            background_tasks.add_task(
                learning_orchestrator.train_specific_models,
                request.specific_models,
                request.force_retrain
            )
        else:
            background_tasks.add_task(
                learning_orchestrator.train_all_models,
                request.force_retrain
            )
        
        return {
            "success": True,
            "message": "Model training started in background",
            "force_retrain": request.force_retrain,
            "specific_models": request.specific_models,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/statistics")
async def get_learning_statistics():
    """Get learning engine statistics (replaces /ai/learning/stats)"""
    try:
        stats = await learning_orchestrator.get_learning_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/anomalies")
async def get_active_anomalies(limit: int = 50, severity: Optional[str] = None):
    """Get active anomalies detected by learning system"""
    try:
        anomalies = await learning_orchestrator.get_active_anomalies(
            limit=limit,
            severity_filter=severity
        )
        
        return {
            "success": True,
            "anomalies": anomalies,
            "count": len(anomalies),
            "severity_filter": severity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get active anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/system-health")
async def get_system_health_insights():
    """Get system health insights from learning analysis"""
    try:
        health_insights = await learning_orchestrator.get_system_health_insights()
        
        return {
            "success": True,
            "health_insights": health_insights,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/models")
async def get_model_information():
    """Get information about trained models (replaces /ai/learning/model-info)"""
    try:
        model_info = await learning_orchestrator.get_model_information()
        
        return {
            "success": True,
            "model_info": model_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get model information: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.delete("/reset")
async def reset_learning_data(confirm: bool = False):
    """Reset all learning data (replaces /ai/learning/reset-learning-data)"""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must set confirm=true to reset learning data"
        )
    
    try:
        # Reset learning data through orchestrator
        await learning_orchestrator.reset_all_learning_data()
        
        return {
            "success": True,
            "message": "All learning data has been reset",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset learning data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/feedback/summary")
async def get_feedback_summary():
    """Get summary of user feedback and learning improvements"""
    try:
        summary = await learning_orchestrator.feedback_processor.get_feedback_summary()
        
        return {
            "success": True,
            "feedback_summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get feedback summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.post("/feedback")
async def submit_feedback(
    user_id: str,
    automation_id: str,
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5"),
    feedback_text: Optional[str] = None,
    improvement_suggestions: Optional[List[str]] = None
):
    """Submit user feedback for learning improvement"""
    try:
        # Process feedback through learning orchestrator
        result = await learning_orchestrator.feedback_processor.process_user_feedback(
            user_id=user_id,
            automation_id=automation_id,
            rating=rating,
            feedback_text=feedback_text,
            improvement_suggestions=improvement_suggestions or []
        )
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "user_id": user_id,
            "automation_id": automation_id,
            "processing_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))