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

        try:
            command = session_state.command_queue.get(block=False)
        except queue.Empty:
            command = None
        if command != None:
            if command == "refresh":
                session_state.agent.refresh()
        time.sleep(0.1)

def get_session_state(create_if_missing=False, disable_conversation_init=False):
    global persona_config_path, auth

    session_state = None
    client_id = session.get('client_id')
    if client_id == None:
        if create_if_missing == True:
            client_id = auth.get_next_client_id()
            session['client_id'] = client_id
            logging.info(f"webapp: New client_id: {client_id}")
        else:
            return None


    if client_id in session_states.keys():
        session_state = session_states[client_id]
        if session_state.client_id != client_id:
            # Log the user out if the client_id is invalid.
            logging.info(f"webapp: Session client_id doesn't match SessionState client_id, clearing session: {client_id} != {session_state.client_id}")
            session.clear()
            return None
        # If username doesn't match the session state, clear the session
        if session['user']['username'] != session_state.username:
            logging.info(f"webapp: Session username doesn't match SessionState username, clearing session: {session['user']['username']} != {session_state.username}")
            session.clear()
            return None
        # logging.info(f"webapp: Using existing SessionState: client_id = {client_id}, username = {session['user']['username']}")
    elif create_if_missing == True:
        session_state = SessionState(client_id, persona_config_path, session['user']['username'], disable_conversation_init)
        session_states[client_id] = session_state
        logging.info(f"webapp: Created new SessionState: client_id = {client_id}, username = {session['user']['username']}")
        # Start the dedicated agent thread only for a new session.
        t = threading.Thread(target=process_session, args=(session_state,), daemon=True)
        t.start()

    return session_state

@app.route('/')
def index():
    # If the user is not logged in, render the login/registration form.
    if 'user' not in session:
        return render_template('index_hud.html', logged_in=False)

    session_state = get_session_state(create_if_missing=True)
    session_state.command_queue.put("refresh")

    # Get additional agent info from persona_config.
    persona = persona_config.config.get('persona', {})
    agent_purpose = persona.get('purpose', '')
    agent_description = persona.get('description', '')
    agent_additional = persona.get('additional', '')

    return render_template(
        'index_hud.html',
        logged_in=True,
        agent_name=persona.get('name', 'Agent'),
        username=session['user']['username'],
        agent_purpose=agent_purpose,
        agent_description=agent_description,
        agent_additional=agent_additional
    )


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

    session_state = get_session_state(True, True)

    if not session_state:
        session.clear()
        return redirect(url_for('login'))
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

    # If the current working directory is not the root of the project,
    # print an error message and exit.
    if not os.path.exists('src/webapp.py'):
        logging.info("Please run the script from the root directory of the project.")
        sys.exit(1)

    persona_config = AgenticFrameworkConfig(persona_config_path)
    auth = Authentication(persona_config.config)

    app.run(port=8000, debug=False, threaded=False)
