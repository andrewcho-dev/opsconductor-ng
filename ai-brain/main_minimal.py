from fastapi import FastAPI
import sys
sys.path.append('/app/shared')

app = FastAPI(
    title="OpsConductor AI Service - Minimal",
    description="Minimal version to test startup",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-service-minimal"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3005)