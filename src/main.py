import uvicorn
from api.webhook import app
from core.database import Database
from core.config import settings

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await Database.connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await Database.close_db()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
