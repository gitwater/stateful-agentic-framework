from fastapi import APIRouter, Depends
from src.api.v1.models import StatusResponse

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

@router.get("/", response_model=StatusResponse)
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"} 