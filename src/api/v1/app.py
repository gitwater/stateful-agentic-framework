from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import sys
import yaml
import uuid
from typing import Dict, Any, Optional, List

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import route modules
from src.api.v1.routes import agents, sessions, health

# Initialize FastAPI app
app = FastAPI(
    title="Stateful Agentic Framework API",
    description="API for managing and interacting with agentic frameworks",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )

# Create necessary directories on startup
@app.on_event("startup")
async def startup_event():
    # Create tmp/configs directory if it doesn't exist
    config_dir = os.path.join(os.getcwd(), 'tmp', 'configs')
    os.makedirs(config_dir, exist_ok=True)
    
    # Set environment variables
    os.environ["CHROMA_DISABLE_TELEMETRY"] = "true"
    
    logger.info("API started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.v1.app:app", host="127.0.0.1", port=4331, reload=False) 