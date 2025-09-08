#!/usr/bin/env python3
"""
New Service Template - OpsConductor Microservice
Replace 'new-service' with your actual service name throughout this file
"""

import os
import sys
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

# Add shared module to path
sys.path.append('/home/opsconductor')

from shared.database import get_db_cursor, check_database_health, cleanup_database_pool
from shared.errors import DatabaseError, ValidationError, NotFoundError, AuthError
from fastapi import FastAPI, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="New Service",
    description="Template for new OpsConductor microservice",
    version="1.0.0"
)

security = HTTPBearer()

# Database connection handled by shared module

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")

# Pydantic models
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

# Database connection handled by shared module

# Authentication
async def verify_token(token: str = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")

# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        health_status = await check_database_health()
        return {"status": "healthy" if health_status else "unhealthy", "service": "new-service"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "service": "new-service", "error": str(e)}

# CRUD endpoints
@app.get("/items", response_model=List[ItemResponse])
async def get_items(user: dict = Depends(verify_token)):
    """Get all items"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, name, description, created_at, updated_at 
                FROM items 
                ORDER BY created_at DESC
            """)
            items = cursor.fetchall()
        return items
    except Exception as e:
        logger.error(f"Error fetching items: {e}")
        raise DatabaseError("Failed to fetch items")

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: int, user: dict = Depends(verify_token)):
    """Get item by ID"""
    try:
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("""
                SELECT id, name, description, created_at, updated_at 
                FROM items 
                WHERE id = %s
            """, (item_id,))
            item = cursor.fetchone()
        
        if not item:
            raise NotFoundError("Item not found")
        
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching item {item_id}: {e}")
        raise DatabaseError("Failed to fetch item")

@app.post("/items", response_model=ItemResponse)
async def create_item(item: ItemCreate, user: dict = Depends(verify_token)):
    """Create new item"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO items (name, description, created_at, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, name, description, created_at, updated_at
            """, (item.name, item.description))
            new_item = cursor.fetchone()
        
        logger.info(f"Created item: {new_item['id']}")
        return new_item
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise DatabaseError("Failed to create item")

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: ItemUpdate, user: dict = Depends(verify_token)):
    """Update item"""
    try:
        with get_db_cursor() as cursor:
            # Build dynamic update query
            update_fields = []
            values = []
            
            if item.name is not None:
                update_fields.append("name = %s")
                values.append(item.name)
            
            if item.description is not None:
                update_fields.append("description = %s")
                values.append(item.description)
            
            if not update_fields:
                raise ValidationError("No fields to update")
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(item_id)
            
            cursor.execute(f"""
                UPDATE items 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, name, description, created_at, updated_at
            """, values)
            
            updated_item = cursor.fetchone()
        
        if not updated_item:
            raise NotFoundError("Item not found")
        
        logger.info(f"Updated item: {item_id}")
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {e}")
        raise DatabaseError("Failed to update item")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int, user: dict = Depends(verify_token)):
    """Delete item"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
            if cursor.rowcount == 0:
                raise NotFoundError("Item not found")
        
        logger.info(f"Deleted item: {item_id}")
        return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {e}")
        raise DatabaseError("Failed to delete item")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3010"))
    uvicorn.run(app, host="0.0.0.0", port=port)