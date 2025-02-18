from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
import sys, os
import threading
import queue
import logging
import time
from session import SessionState, AgenticFrameworkConfig
from auth import Authentication

# Set up logging.
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

# Global variables for session management.
last_client_id = 0
session_states = {}  # Maps client_id to SessionState
chat_count = 0

persona_config_path = None
persona_config = None
auth = None

def process_session(session_state):
    """
    Worker thread for each client session.
    """
    logging.info("Before init session")
    session_state.init_session()
    logging.info("Entering Agent main loop")
    while True:
        try:
            user_input = session_state.user_input_queue.get(block=False)
        except queue.Empty:
            user_input = None
        success = session_state.agent.interactions(user_input)
        if not success:
            app.logger.error(f"Error processing input for client {session_state.client_id}")
        if user_input is not None:
            session_state.user_input_queue.task_done()
        time.sleep(0.1)

@app.route('/')
def index():
    # If the user is not logged in, render the login/registration form.
    if 'user' not in session:
        return render_template('index_hud.html', logged_in=False)

    # Otherwise, set up the chat session.
    global last_client_id, persona_config_path
    last_client_id += 1
    session['client_id'] = last_client_id
    session_state = SessionState(last_client_id, persona_config_path)
    session_states[last_client_id] = session_state

    # Start the dedicated agent thread.
    t = threading.Thread(target=process_session, args=(session_state,), daemon=True)
    t.start()

    # Get additional agent info from persona_config.
    persona = persona_config.config.get('persona', {})
    agent_purpose = persona.get('purpose', '')
    agent_description = persona.get('description', '')
    agent_additional = persona.get('additional', '')

    return render_template('index_hud.html',
                           logged_in=True,
                           agent_name=persona.get('name', 'Agent'),
                           username=session['user']['username'],
                           agent_purpose=agent_purpose,
                           agent_description=agent_description,
                           agent_additional=agent_additional)

@app.route('/login', methods=['POST'])
def login():
    global auth
    username = request.form.get('username')
    password = request.form.get('password')
    token = auth.login(username, password)
    if token:
        # Store the user and token in session.
        session['user'] = {'username': username, 'token': token}
        return jsonify({'status': 'success', 'token': token})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/register', methods=['POST'])
def register():
    global auth
    username = request.form.get('username')
    password = request.form.get('password')
    success = auth.register(username, password)
    if success:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User already exists'}), 400

# Logout handler.
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/active-message')
def active_message():
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401

    client_id = int(session.get('client_id', 0))
    session_state = session_states.get(client_id)
    if not session_state:
        return jsonify([])
    # Collect messages from the dedicated agent thread.
    user_messages = session_state.pop_user_messages()
    deliberation_messages = session_state.pop_agent_dialog_messages()
    user_messages.extend(deliberation_messages)
    return jsonify(user_messages)

@app.route('/chat', methods=['POST'])
def chat():
    global chat_count
    if 'user' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401

    client_id = int(session.get('client_id', 0))
    session_state = session_states.get(client_id)
    if not session_state:
        return jsonify({'status': 'error', 'message': 'Invalid session.'}), 400

    user_input = request.form['user_input']
    chat_count += 1
    app.logger.info(f"Client {client_id} input #{chat_count}: {user_input}")

    # Enqueue the input to be processed by the dedicated thread.
    session_state.user_input_queue.put(user_input)
    return jsonify({'status': 'queued'})

if __name__ == '__main__':
    os.environ["CHROMA_DISABLE_TELEMETRY"] = "true"
    if len(sys.argv) < 2:
        logging.info("Usage: python src/webapp.py <config_path>")
        sys.exit(1)
    persona_config_path = sys.argv[1]
    if not os.path.exists(persona_config_path):
        logging.info(f"Invalid config path: {persona_config_path}")
        sys.exit(1)

    persona_config = AgenticFrameworkConfig(persona_config_path)
    auth = Authentication(persona_config.config)

    app.run(port=8000, debug=False, threaded=False)
