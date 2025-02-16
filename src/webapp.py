from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import sys, os
from subprocess import TimeoutExpired
from session import SessionState

#from socratic_agent import *
#from persona_agent import PesonaAgent
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
#logging.basicConfig(level=logging.ERROR)


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'socraticalpaca'
Session(app)

last_client_id = 0
session_states = {}
chat_count = 0

request_locks = {}

persona_config_path = None

@app.route('/')
def index():
    global last_client_id
    global persona_config_path
    last_client_id += 1
    session['client_id'] = last_client_id
    session_states[last_client_id] = SessionState(last_client_id, persona_config_path)
    #return render_template('index.html')
    #return render_template('index_debug.html', agent_name=session_states[last_client_id].agent.persona_config.config['persona']['name'])
    #return render_template('index_debug_2.html', agent_name=session_states[last_client_id].agent.persona_config.config['persona']['name'])
    return render_template('index_hud.html', agent_name=session_states[last_client_id].agent.persona_config.config['persona']['name'])


@app.route('/active-message')
def active_message():

    global last_client_id, session_states, request_locks, persona_config_path

    client_id = int(session['client_id'])
    #if client_id not in request_locks:
    #    request_locks[client_id] = threading.Lock()

    #request_lock = request_locks[client_id]
    # print(f"{client_id}: Request locked? 1: {request_lock.locked()}")
    # print(f"Lock aquire 1: {request_lock.acquire()}")
    # print(f"{client_id}: Request locked? 2: {request_lock.locked()}")
    # print(f"Lock aquire 2: {request_lock.acquire()}")
    # print(f"Lock aquire 3: {request_lock.acquire()}")
    #request_lock.aquire()
    user_messages = []
    if True == True: #request_lock.acquire(blocking=False) == True:
        #print(f"{client_id}: Request lock after : {request_lock.locked()}")
        if client_id > last_client_id:
            print("current session id", client_id)
            print("last_client_id", last_client_id)
            last_client_id = client_id
            session_states[last_client_id] = SessionState(last_client_id, persona_config_path)

        session_state = session_states[client_id]
        success = session_state.agent.interactions()
        if success:
            user_messages = session_state.pop_user_messages()
            deliberation_messages = session_state.pop_agent_dialog_messages()
            user_messages.extend(deliberation_messages)
        else:
            breakpoint()
        #request_lock.release()
    else:
        print(f"{client_id}: Request lock: interaction in progress")

    return jsonify(user_messages)

@app.route('/chat', methods=['POST'])
def chat():
    global session_states
    global chat_count
    client_id = int(session['client_id'])
    session_state = session_states[client_id]

    user_input = request.form['user_input']
    chat_count += 1
    print(f"--------------> User input: {user_input}: {chat_count}")
    success = session_state.agent.interactions(user_input)
    if success:
        user_messages = session_state.pop_user_messages()
        return jsonify(user_messages)

    return jsonify([])
    # if session_state.question is None:
    #     session_state.question = user_input
    #     session_state.socrates.set_question(session_state.question)
    #     session_state.theaetetus.set_question(session_state.question)
    #     session_state.plato.set_question(session_state.question)
    #     response = generate_response(user_input, mode="question")

    # if session_state.wait_tony:
    #     feedback = user_input
    #     session_state.socrates.add_feedback(session_state.all_questions_to_tony, feedback)
    #     session_state.theaetetus.add_feedback(session_state.all_questions_to_tony, feedback)
    #     session_state.plato.add_feedback(session_state.all_questions_to_tony, feedback)
    #     session_state.all_questions_to_tony = ""
    #     session_state.wait_tony = False
    #     response = generate_response(user_input, mode="feedback")
    return jsonify([{'role': 'system','response': response}])


# def generate_response(user_input, mode="question"):
#     if mode == "question":
#         return f"You just said: {user_input}\n\nA conversation among (Socrates, Theaetetus, and Plato) will begin shortly..."
#     elif mode == "feedback":
#         return f"Received your feedback: {user_input}"
#     return "Connecting..."


if __name__ == '__main__':
    # Print a usage message if the user does not provide any arguments
    if len(sys.argv) < 2:
        print("Usage: python src/webapp.py <config_path>")
        sys.exit(1)
    # Get the first argument which is a config file path
    persona_config_path = sys.argv[1]
    # Verify the config path is vaid and exists
    if not os.path.exists(persona_config_path):
        print(f"Invalid config path: {persona_config_path}")
        sys.exit(1)


    app.run(port=8000, debug=False, threaded=False)
