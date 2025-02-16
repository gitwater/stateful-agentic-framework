from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import sys, os
import threading
import queue
import logging
import time
from session import SessionState, AgenticFrameworkConfig

# from socratic_agent import *
# from persona_agent import PesonaAgent

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format="",
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'socraticalpaca'
Session(app)

last_client_id = 0
session_states = {}  # Maps client_id to SessionState
chat_count = 0

persona_config_path = None
persona_config = None

def process_session(session_state):
    """
    Long running thread for a given session. It watches the session's user_input_queue.
    When new input is enqueued (even if the agent is busy processing a previous input),
    it will process them sequentially.
    """
    logging.info("Before init session")
    session_state.init_session()
    logging.info("Entering Agent main loop")
    while True:
        # This call blocks until new user input is available.
        # Non blocking queue get
        try:
            user_input = session_state.user_input_queue.get(block=False)
        except queue.Empty:
            user_input = None
        # Process the input (this call may take a while).
        success = session_state.agent.interactions(user_input)
        if not success:
            # You can add error handling here if needed.
            app.logger.error(f"Error processing input for client {session_state.client_id}")
        # After processing, the agent is assumed to have pushed messages onto its internal queues.
        # (No need to signal the HTTP thread; /active-message will poll for new messages.)
        # Mark the task as done (if you are using task_done() in your queue logic).
        if user_input is not None:
            session_state.user_input_queue.task_done()
        # Sleep for a slit second to avoid busy waiting.
        # (You can adjust this value based on your needs.)
        time.sleep(0.1)

@app.route('/')
def index():
    global last_client_id
    global persona_config_path
    global persona_config

    if persona_config is None:
        persona_config = AgenticFrameworkConfig(persona_config_path)

    last_client_id += 1
    session['client_id'] = last_client_id

    # Create a new session state for this client.
    # Note: We now assume that the SessionState (and its agent) will be used exclusively
    # in the dedicated thread created below.
    session_state = SessionState(last_client_id, persona_config_path)
    # Create a thread-safe queue for user input.
    session_states[last_client_id] = session_state

    # Start a dedicated worker thread for this session.
    t = threading.Thread(target=process_session, args=(session_state,), daemon=True)
    t.start()

    # Render the index page. (Uncomment the template you wish to use.)
    return render_template('index_hud.html', agent_name=persona_config.config['persona']['name'])

@app.route('/active-message')
def active_message():
    client_id = int(session['client_id'])
    session_state = session_states.get(client_id)

    if not session_state:
        return jsonify([])

    # Instead of calling interactions() here, we simply return any messages that the
    # dedicated thread has pushed into the agent's message queues.
    user_messages = session_state.pop_user_messages()
    deliberation_messages = session_state.pop_agent_dialog_messages()
    user_messages.extend(deliberation_messages)

    return jsonify(user_messages)

@app.route('/chat', methods=['POST'])
def chat():
    global chat_count
    client_id = int(session['client_id'])
    session_state = session_states.get(client_id)

    if not session_state:
        return jsonify({'status': 'error', 'message': 'Invalid session.'}), 400

    user_input = request.form['user_input']
    chat_count += 1
    app.logger.info(f"Client {client_id} input #{chat_count}: {user_input}")

    # Instead of processing the input immediately, we enqueue it.
    session_state.user_input_queue.put(user_input)

    # Return immediately; the dedicated thread will process the input.
    return jsonify({'status': 'queued'})

if __name__ == '__main__':
    os.environ["CHROMA_DISABLE_TELEMETRY"] = "true"

    # Usage check for the persona config path.
    if len(sys.argv) < 2:
        logging.info("Usage: python src/webapp.py <config_path>")
        sys.exit(1)
    persona_config_path = sys.argv[1]
    if not os.path.exists(persona_config_path):
        logging.info(f"Invalid config path: {persona_config_path}")
        sys.exit(1)

    # Start the Flask app.
    # Note: threaded=False ensures that our dedicated threads (for each session) are used
    # for the agent interactions while Flask handles HTTP requests in its own way.
    app.run(port=8000, debug=False, threaded=False)
