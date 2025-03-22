from flask import Flask, request, jsonify
import sys, os
import threading
import queue
import logging
import time
import json
import uuid
import yaml
from flask_cors import CORS
from session import SessionState, AgenticFrameworkConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# TODO: Initialize database connection
# db = Database()

def extract_agent_metadata(config_yaml):
    """
    Extracts metadata (name, description, purpose) from the agent config.
    
    Args:
        config_yaml: The YAML configuration string
        
    Returns:
        dict: Dictionary with name, description, and purpose fields
    """
    try:
        config = yaml.safe_load(config_yaml)
        return {
            "name": config.get("name", "Unnamed Agent"),
            "description": config.get("description", ""),
            "purpose": config.get("purpose", "")
        }
    except Exception as e:
        logger.error(f"Error parsing agent config: {e}")
        return {
            "name": "Unnamed Agent",
            "description": "",
            "purpose": ""
        }

# Global variables for agent management
agent_sessions = {}  # Maps "{user_id}:{agent_id}" to SessionState objects

def get_session_key(user_id, agent_id):
    """Helper function to create a combined session key"""
    return f"{user_id}:{agent_id}"

def parse_session_key(session_key):
    """Helper function to parse user_id and agent_id from a session key"""
    parts = session_key.split(':', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None

def process_session(session_state):
    """
    Worker thread for each agent session.
    """
    logger.info(f"Initializing session for agent {session_state.client_id}")
    session_state.init_session()
    logger.info(f"Entering Agent main loop for agent {session_state.client_id}")
    
    while True:
        try:
            user_input = session_state.user_input_queue.get(block=False)
        except queue.Empty:
            user_input = None
            
        success = session_state.agent.interactions(user_input)
        if not success:
            logger.error(f"Error processing input for agent {session_state.client_id}")
        if user_input is not None:
            session_state.user_input_queue.task_done()

        try:
            command = session_state.command_queue.get(block=False)
        except queue.Empty:
            command = None
        if command is not None:
            if command == "refresh":
                session_state.agent.refresh()
        time.sleep(0.1)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/api/engage', methods=['POST'])
def engage_agent():
    """
    Engage with an agent based on the provided configuration.
    
    Expected POST data:
    - user_id: ID of the frontend user
    - agent_id: ID of the specific agent to engage with
    - config: (Optional) YAML configuration for the agent. If not provided, will be loaded from the database.
    
    Returns:
    - session_id: ID of the engaged session
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    user_id = data.get('user_id')
    username = data.get('username')
    agent_id = data.get('agent_id')
    agent_config = data.get('config')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    if not agent_id:
        return jsonify({"error": "agent_id is required"}), 400
    
    # Create the combined session key
    session_key = get_session_key(user_id, agent_id)
    
    # Check if this agent is already engaged by this user
    if session_key in agent_sessions:
        # Agent already engaged by this user, return the existing agent_id
        logger.info(f"Agent {agent_id} already engaged by user {user_id}, resuming session")
        session_state = agent_sessions[session_key]
        session_state.command_queue.put("refresh")
        return jsonify({
            "session_id": session_key
        })
    
    # If no config was provided, try to load it from the database
    if not agent_config:
        agent_data = db_get_agent(user_id, agent_id)
        if not agent_data or not agent_data.get("config"):
            return jsonify({"error": "Agent not found or has no configuration"}), 404
        agent_config = agent_data.get("config")
    
    # Initialize the session with the config
    session_state = SessionState(session_key, None, username, False, config_str=agent_config)
    agent_sessions[session_key] = session_state
    
    # Start a thread for this agent session
    thread = threading.Thread(
        target=process_session,
        args=(session_state,),
        daemon=True
    )
    thread.start()
    
    # Refresh the agent state
    session_state.command_queue.put("refresh")
    
    return jsonify({
        "session_id": session_key
    })

@app.route('/api/session/<session_key>/messages', methods=['GET'])
def get_agent_messages(session_key):
    """
    Get active messages for a specific session.
    
    Returns:
    - messages: Array of messages from the agent
    """
    session_state = agent_sessions.get(session_key)
    
    if not session_state:
        return jsonify({"error": "No active session found"}), 404
    
    # Collect messages from the agent thread
    user_messages = session_state.pop_user_messages()
    deliberation_messages = session_state.pop_agent_dialog_messages()
    
    # Combine messages if needed
    all_messages = user_messages + deliberation_messages
    
    return jsonify({
        "messages": all_messages
    })

@app.route('/api/session/<session_key>/send', methods=['POST'])
def send_message(session_key):
    """
    Send a message to a specific session.
    
    Expected POST data:
    - message: Text message to send to the agent
    
    Returns:
    - status: Status of the operation
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    message = data.get('message')
    
    if not message:
        return jsonify({"error": "message is required"}), 400
    
    session_state = agent_sessions.get(session_key)
    
    if not session_state:
        return jsonify({"error": "No active session found"}), 404
    
    # Queue the message for processing
    session_state.user_input_queue.put(message)
    
    return jsonify({"status": "queued"})

@app.route('/api/session/<session_key>', methods=['DELETE'])
def end_agent_session(session_key):
    """
    End a session.
    
    Returns:
    - status: Status of the operation
    """
    session_state = agent_sessions.pop(session_key, None)
    
    if not session_state:
        return jsonify({"error": "No active session found"}), 404
    
    # Clean up the config file
    config_path = os.path.join(os.getcwd(), 'tmp', 'configs', f"{session_key}.yaml")
    if os.path.exists(config_path):
        os.remove(config_path)
    
    return jsonify({
        "status": "agent session ended"
    })

@app.route('/api/user/<user_id>/agents', methods=['GET'])
def get_user_agents(user_id):
    """
    Get all active agent sessions for a specific user.
    
    Returns:
    - agents: Array of agent IDs
    """
    user_agents = []
    
    user_prefix = f"{user_id}:"
    for session_key, session_state in agent_sessions.items():
        if session_key.startswith(user_prefix):
            # Extract agent_id from the session key
            _, agent_id = parse_session_key(session_key)
            if agent_id:
                user_agents.append(agent_id)
    
    return jsonify({"agents": user_agents})

@app.route('/api/agents', methods=['POST'])
def create_agent():
    """
    Create a new agent for a user.
    
    Expected POST data:
    - user_id: ID of the user who will own the agent
    - config: YAML configuration for the agent
    - agent_id: (Optional) ID for the agent, will be generated if not provided
    
    Returns:
    - agent_id: ID of the created agent
    - name: Name of the agent extracted from the config
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    user_id = data.get('user_id')
    agent_config = data.get('config')
    agent_id = data.get('agent_id', str(uuid.uuid4()))
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    if not agent_config:
        return jsonify({"error": "config is required"}), 400
    
    # Extract metadata to verify the config contains necessary information
    metadata = extract_agent_metadata(agent_config)
    if not metadata.get("name"):
        return jsonify({"error": "Agent config must contain a name"}), 400
    
    # TODO: Placeholder for database call to create agent
    # success = db.agents.create(user_id=user_id, agent_id=agent_id, config=agent_config)
    success = True  # Placeholder for database operation result
    
    if not success:
        return jsonify({"error": "Failed to create agent"}), 500
    
    return jsonify({
        "agent_id": agent_id,
        "name": metadata["name"],
        "description": metadata["description"],
        "purpose": metadata["purpose"]
    })

@app.route('/api/agents/<agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """
    Update an existing agent's configuration.
    
    Expected PUT data:
    - user_id: ID of the user who owns the agent
    - config: New YAML configuration for the agent
    
    Returns:
    - agent_id: ID of the updated agent
    - name: Updated name of the agent
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    user_id = data.get('user_id')
    agent_config = data.get('config')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    if not agent_config:
        return jsonify({"error": "config is required"}), 400
    
    # Check if the agent exists
    # TODO: Placeholder for database call to check if agent exists
    # agent = db.agents.get(user_id=user_id, agent_id=agent_id)
    agent = None  # Placeholder for database operation result
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # Extract metadata to verify the config contains necessary information
    metadata = extract_agent_metadata(agent_config)
    if not metadata.get("name"):
        return jsonify({"error": "Agent config must contain a name"}), 400
    
    # TODO: Placeholder for database call to update agent
    # success = db.agents.update(user_id=user_id, agent_id=agent_id, config=agent_config)
    success = True  # Placeholder for database operation result
    
    if not success:
        return jsonify({"error": "Failed to update agent"}), 500
    
    # If the agent is currently active in a session, tell it to refresh
    session_key = get_session_key(user_id, agent_id)
    if session_key in agent_sessions:
        session_state = agent_sessions[session_key]
        session_state.command_queue.put("refresh")
    
    return jsonify({
        "agent_id": agent_id,
        "name": metadata["name"],
        "description": metadata["description"],
        "purpose": metadata["purpose"]
    })

@app.route('/api/agents/<agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """
    Delete an agent.
    
    Expected query parameters:
    - user_id: ID of the user who owns the agent
    
    Returns:
    - status: Status of the operation
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id query parameter is required"}), 400
    
    # Check if the agent exists
    # TODO: Placeholder for database call to check if agent exists
    # agent = db.agents.get(user_id=user_id, agent_id=agent_id)
    agent = None  # Placeholder for database operation result
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # TODO: Placeholder for database call to delete agent
    # success = db.agents.delete(user_id=user_id, agent_id=agent_id)
    success = True  # Placeholder for database operation result
    
    if not success:
        return jsonify({"error": "Failed to delete agent"}), 500
    
    # If the agent is currently in a session, end the session
    session_key = get_session_key(user_id, agent_id)
    if session_key in agent_sessions:
        session_state = agent_sessions.pop(session_key, None)
        if session_state:
            logger.info(f"Terminating session for agent {agent_id}")
            # Any cleanup needed for the session would go here
    
    return jsonify({
        "status": "agent deleted"
    })

@app.route('/api/agents', methods=['GET'])
def list_agents():
    """
    List all agents owned by a user.
    
    Expected query parameters:
    - user_id: ID of the user whose agents to list
    
    Returns:
    - agents: Array of agent metadata (id, name, description, purpose)
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id query parameter is required"}), 400
    
    # TODO: Placeholder for database call to list user's agents
    # agents = db.agents.list(user_id=user_id)
    agents = []  # Placeholder for database operation result
    
    # Extract the required fields for each agent
    agents_list = []
    for agent in agents:
        # In the actual implementation, you would extract metadata from agent.config
        # For now, we'll just create empty placeholders
        agents_list.append({
            "agent_id": agent.get("agent_id", ""),
            "name": agent.get("name", "Unnamed Agent"),
            "description": agent.get("description", ""),
            "purpose": agent.get("purpose", "")
        })
    
    return jsonify({
        "agents": agents_list
    })

@app.route('/api/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """
    Get details of a specific agent.
    
    Expected query parameters:
    - user_id: ID of the user who owns the agent
    
    Returns:
    - agent: Agent details including metadata and config
    """
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id query parameter is required"}), 400
    
    # TODO: Placeholder for database call to get agent
    # agent = db.agents.get(user_id=user_id, agent_id=agent_id)
    agent = None  # Placeholder for database operation result
    
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    
    # In the actual implementation, extract metadata from agent.config
    # For now, we'll just create empty placeholders
    metadata = {
        "name": "Placeholder Agent",
        "description": "Placeholder description",
        "purpose": "Placeholder purpose"
    }
    
    return jsonify({
        "agent_id": agent_id,
        "user_id": user_id,
        "name": metadata.get("name"),
        "description": metadata.get("description"),
        "purpose": metadata.get("purpose"),
        "config": "placeholder_config_yaml"  # In real implementation, this would be agent.config
    })

if __name__ == '__main__':
    os.environ["CHROMA_DISABLE_TELEMETRY"] = "true"
    
    # Create tmp/configs directory if it doesn't exist
    config_dir = os.path.join(os.getcwd(), 'tmp', 'configs')
    os.makedirs(config_dir, exist_ok=True)
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=4331, debug=False, threaded=True) 