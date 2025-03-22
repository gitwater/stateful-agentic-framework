import os
import sys
import uvicorn

# Ensure the current directory is in the Python path
current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, current_dir)

# Add src directory to the Python path directly
# This allows imports like "import persona_agent" to work
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

def start_api():
    """Start the API server."""
    print("Starting the Stateful Agentic Framework API...")
    
    # Set environment variables
    os.environ["CHROMA_DISABLE_TELEMETRY"] = "true"
    
    # Run the FastAPI app
    uvicorn.run("src.api.v1.app:app", host="127.0.0.1", port=4331, reload=False)

if __name__ == "__main__":
    start_api() 