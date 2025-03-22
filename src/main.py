import uvicorn
import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import app
from src.api.v1.app import app

def main():
    """
    Main entry point for the API server.
    """
    # Set environment variables
    os.environ["CHROMA_DISABLE_TELEMETRY"] = "true"
    
    # Create tmp/configs directory if it doesn't exist
    config_dir = os.path.join(os.getcwd(), 'tmp', 'configs')
    os.makedirs(config_dir, exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 4331))
    
    # Start the server
    logger.info(f"Starting API server on port {port}")
    uvicorn.run(
        "src.api.v1.app:app",
        host="0.0.0.0",  # Use 0.0.0.0 for Docker compatibility
        port=port,
        reload=False,    # Set to True for development
        workers=1,       # Adjust based on your needs
    )

if __name__ == "__main__":
    main() 