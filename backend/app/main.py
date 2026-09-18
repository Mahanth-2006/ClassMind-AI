from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.classroom import router as classroom_router

# Create FastAPI application
app = FastAPI(
    title="ClassMind AI Backend",
    description="Backend API for the Intelligent Online Classroom Engagement and Learning Assessment System",
    version="1.0.0",
)

app.include_router(health_router)
app.include_router(classroom_router)
