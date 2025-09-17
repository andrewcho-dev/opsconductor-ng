"""
Learning Engine API Endpoints
FastAPI routes for AI learning, predictions, and recommendations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from learning_engine import learning_engine

logger = logging.getLogger(__name__)

# Create router
learning_router = APIRouter(prefix="/ai/learning", tags=["AI Learning"])

# Pydantic models for API
class ExecutionRecord(BaseModel):
    user_id: str
    operation_type: str
    target_info: Dict[str, Any]
    duration: float
    success: bool
    error_message: Optional[str] = None
    system_metrics: Optional[Dict[str, float]] = None

class PredictionRequest(BaseModel):
    operation_type: str
    target_info: Dict[str, Any]
    user_id: str

class TrainingRequest(BaseModel):
    force_retrain: bool = False

@learning_router.post("/record-execution")
async def record_execution(execution: ExecutionRecord):
    """Record a job execution for learning"""
    try:
        await learning_engine.record_execution(
            user_id=execution.user_id,
            operation_type=execution.operation_type,
            target_info=execution.target_info,
            duration=execution.duration,
            success=execution.success,
            error_message=execution.error_message,
            system_metrics=execution.system_metrics
        )
        
        return {
            "success": True,
            "message": "Execution recorded successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to record execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.post("/predict-failure")
async def predict_failure(request: PredictionRequest):
    """Get failure risk prediction for an operation"""
    try:
        prediction = await learning_engine.predict_failure_risk(
            operation_type=request.operation_type,
            target_info=request.target_info,
            user_id=request.user_id
        )
        
        return {
            "success": True,
            "prediction": prediction.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to predict failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/recommendations/{user_id}")
async def get_user_recommendations(user_id: str):
    """Get personalized recommendations for a user"""
    try:
        recommendations = await learning_engine.get_user_recommendations(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/system-health")
async def get_system_health():
    """Get system health insights and anomalies"""
    try:
        health_insights = await learning_engine.get_system_health_insights()
        
        return {
            "success": True,
            "health_insights": health_insights,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/stats")
async def get_learning_stats():
    """Get learning engine statistics"""
    try:
        stats = await learning_engine.get_learning_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get learning stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.post("/train-models")
async def train_models(background_tasks: BackgroundTasks, request: TrainingRequest):
    """Train or retrain ML models"""
    try:
        # Run training in background
        background_tasks.add_task(learning_engine.train_models)
        
        return {
            "success": True,
            "message": "Model training started in background",
            "force_retrain": request.force_retrain
        }
        
    except Exception as e:
        logger.error(f"Failed to start model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/anomalies")
async def get_active_anomalies(limit: int = 50):
    """Get active anomalies"""
    try:
        import sqlite3
        anomalies = []
        
        with sqlite3.connect(learning_engine.db_path) as conn:
            cursor = conn.execute("""
                SELECT anomaly_type, severity, description, affected_systems, 
                       detection_time, confidence
                FROM anomalies 
                WHERE resolved = FALSE 
                ORDER BY detection_time DESC
                LIMIT ?
            """, (limit,))
            
            for row in cursor.fetchall():
                import json
                anomalies.append({
                    "type": row[0],
                    "severity": row[1],
                    "description": row[2],
                    "affected_systems": json.loads(row[3]),
                    "detection_time": row[4],
                    "confidence": row[5]
                })
        
        return {
            "success": True,
            "anomalies": anomalies,
            "count": len(anomalies)
        }
        
    except Exception as e:
        logger.error(f"Failed to get anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/patterns/{user_id}")
async def get_user_patterns(user_id: str):
    """Get user behavior patterns"""
    try:
        import sqlite3
        patterns = []
        
        with sqlite3.connect(learning_engine.db_path) as conn:
            cursor = conn.execute("""
                SELECT pattern_type, pattern_data, confidence, last_updated
                FROM user_patterns 
                WHERE user_id = ?
                ORDER BY last_updated DESC
            """, (user_id,))
            
            for row in cursor.fetchall():
                import json
                pattern_data = json.loads(row[1])
                patterns.append({
                    "pattern_type": row[0],
                    "pattern_data": pattern_data,
                    "confidence": row[2],
                    "last_updated": row[3]
                })
        
        return {
            "success": True,
            "user_id": user_id,
            "patterns": patterns,
            "count": len(patterns)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/predictions/history")
async def get_prediction_history(limit: int = 100):
    """Get prediction history with accuracy metrics"""
    try:
        import sqlite3
        predictions = []
        
        with sqlite3.connect(learning_engine.db_path) as conn:
            cursor = conn.execute("""
                SELECT prediction_type, target_system, predicted_outcome, 
                       confidence, actual_outcome, prediction_time, 
                       validation_time, accuracy
                FROM predictions 
                ORDER BY prediction_time DESC
                LIMIT ?
            """, (limit,))
            
            for row in cursor.fetchall():
                predictions.append({
                    "prediction_type": row[0],
                    "target_system": row[1],
                    "predicted_outcome": row[2],
                    "confidence": row[3],
                    "actual_outcome": row[4],
                    "prediction_time": row[5],
                    "validation_time": row[6],
                    "accuracy": row[7]
                })
        
        # Calculate overall accuracy
        validated_predictions = [p for p in predictions if p["actual_outcome"] is not None]
        overall_accuracy = 0.0
        if validated_predictions:
            correct_predictions = sum(1 for p in validated_predictions 
                                    if p["predicted_outcome"] == p["actual_outcome"])
            overall_accuracy = correct_predictions / len(validated_predictions)
        
        return {
            "success": True,
            "predictions": predictions,
            "count": len(predictions),
            "validated_count": len(validated_predictions),
            "overall_accuracy": overall_accuracy
        }
        
    except Exception as e:
        logger.error(f"Failed to get prediction history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.post("/validate-prediction/{prediction_id}")
async def validate_prediction(prediction_id: int, actual_outcome: str):
    """Validate a prediction with actual outcome"""
    try:
        import sqlite3
        
        with sqlite3.connect(learning_engine.db_path) as conn:
            # Update prediction with actual outcome
            cursor = conn.execute("""
                UPDATE predictions 
                SET actual_outcome = ?, validation_time = CURRENT_TIMESTAMP,
                    accuracy = CASE 
                        WHEN predicted_outcome = ? THEN 1.0 
                        ELSE 0.0 
                    END
                WHERE id = ?
            """, (actual_outcome, actual_outcome, prediction_id))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Prediction not found")
        
        return {
            "success": True,
            "message": "Prediction validated successfully",
            "prediction_id": prediction_id,
            "actual_outcome": actual_outcome
        }
        
    except Exception as e:
        logger.error(f"Failed to validate prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.delete("/reset-learning-data")
async def reset_learning_data(confirm: bool = False):
    """Reset all learning data (use with caution)"""
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must set confirm=true to reset learning data"
        )
    
    try:
        import sqlite3
        
        with sqlite3.connect(learning_engine.db_path) as conn:
            # Clear all learning tables
            conn.executescript("""
                DELETE FROM execution_logs;
                DELETE FROM user_patterns;
                DELETE FROM predictions;
                DELETE FROM anomalies;
                DELETE FROM system_metrics;
            """)
        
        # Clear in-memory caches
        learning_engine.execution_history.clear()
        learning_engine.user_patterns.clear()
        learning_engine.system_metrics.clear()
        learning_engine.pattern_cache.clear()
        
        return {
            "success": True,
            "message": "All learning data has been reset"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset learning data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@learning_router.get("/model-info")
async def get_model_info():
    """Get information about trained models"""
    try:
        model_info = {
            "available_models": list(learning_engine.models.keys()),
            "model_details": {}
        }
        
        for model_name, model in learning_engine.models.items():
            if hasattr(model, 'get_params'):
                # Scikit-learn model
                model_info["model_details"][model_name] = {
                    "type": type(model).__name__,
                    "parameters": model.get_params()
                }
            elif isinstance(model, dict):
                # Custom model (like performance optimizer)
                model_info["model_details"][model_name] = {
                    "type": "custom",
                    "keys": list(model.keys())
                }
            else:
                model_info["model_details"][model_name] = {
                    "type": type(model).__name__,
                    "info": "Model details not available"
                }
        
        return {
            "success": True,
            "model_info": model_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))