from socratic_agent import SocraticAgent
from single_agent import SingleAgent
from persona_state import PersonaStateManager
from sql_database.core import SQLDatabase
from memory import AgentMemory
import json
from pprint import pprint

class PersonaAgent:

    def __init__(self, session, persona_config, model=None):
        self.session = session
        self.persona_config = persona_config
        self.sql_db = SQLDatabase(persona_config.config)
        self.socratic_agent = SocraticAgent(session, self)
        self.single_agent = SingleAgent(session, self)
        self.state_manager = PersonaStateManager(persona_config.config, self.sql_db)

        if self.persona_config.config['framework_settings']['reasoning_agent'] == "socratic":
            self.agent = self.socratic_agent
        else:
            self.agent = self.single_agent

        self.current_user_input = None
        self.memory_system = AgentMemory(persona_config.config, self)

    def get_conversation_memory(self):
        user_input = ""
        if self.current_user_input != None:
            user_input = self.current_user_input
        memory = self.memory_system.get_memory(user_input)
        return memory


    def put_conversation_history(self, role, message):
        if role not in ['user', 'agent']:
            breakpoint()

        self.memory_system.store_utterance(role, message)

    def get_response(self, messages, json_response=False):
        return self.single_agent.get_response(messages, json_response)

    def get_embeddings(self, input_text):
        return self.single_agent.get_embeddings(input_text)

    # A recurrent fucntion to convert a data object from a JSON object to a string
    # by iterating over keys and recalling the function to convert dicts and lists
    def data_obj_json_to_string(self, data_obj, indent="    "):
        data_obj_str = f""
        if type(data_obj) == list:
            for value in data_obj:
                if type(value) == dict:
                    data_obj_str += f"{indent}-\n{self.data_obj_json_to_string(value, indent+'  ')}"
                elif type(value) == list:
                    data_obj_str += f"{indent}-\n{self.data_obj_json_to_string(value, indent+'  ')}"
                else:
                    data_obj_str += f"{indent}- {value}\n"
        else:
            for (key, value) in data_obj.items():
                if type(value) == dict:
                    data_obj_str += f"{indent}{key}:\n{self.data_obj_json_to_string(value, indent+'  ')}"
                elif type(value) == list:
                    data_obj_str += f"{indent}{key}:\n{self.data_obj_json_to_string(value, indent+'  ')}"
                else:
                    data_obj_str += f"{indent}{key}: {value}\n"
        return data_obj_str


    def get_conversation_history(self):
        conversation_history_list = self.db.get_conversation_history()
        conversation_history = "START Conversation History\n"
        for message in conversation_history_list:
            conversation_history += f"{message['created_at']}: {message['role']}: {message['content']}\n\n"
        conversation_history += "END Conversation History\n"
        message = {
            "role": "assistant",
            "content": conversation_history
        }
        return message

    # Get the framework messages for the persona
    # Persona
    #
    def get_framework_messages(self, messages, state_data_json_response=False):
        persona_config = self.persona_config.config['persona']
        persona_state_obj = self.state_manager.get_state_obj()
        # Persona
        persona_info = f"""
You are {persona_config['name']}, a {persona_config['description']}.
Your purpose is {persona_config['purpose']}.
"""

        # Framework States
        framework_states = ""
         # Current State
        current_state = f"Current State: {persona_state_obj.name}"

        states_config = self.persona_config.config['states']
        state_list = []
        for (state_name, state_config) in states_config.items():
            # State
            state_list.append(state_name)
            framework_states += f"- State: {state_name}:\n"
            framework_states += f"    Purpose: {state_config['purpose']}\n"
            #framework_states += f"    Action Description: {state_config['action_description']}\n"
            # If current state is the state being processed, then use the current state data
            state_data = self.sql_db.db_states.get_persona_state_data(state_name)
            for (goal_name, goal_config) in state_config['goals'].items():
                framework_states += f"    Goals:\n"
                framework_states += f"        * {goal_name}: {goal_config['goal']}\n"
                if current_state == state_name:
                    framework_states += f"          Goal Successful Data Criteria: When all data fields have values that are adequate to the state and goal.\n"
                    framework_states += f"          Goal Successful When: {goal_config['success']}\n"
                    framework_states += f"          Goal Success Action: When this goal is complete, transition to the next best state according to the current context.\n"
                data_config = goal_config['data']
                if state_data == None:
                    framework_states += f"          Goal Data: {json.dumps(data_config)}\n"
                else:
                    new_data = {}
                    # Merge state_data and data_config into new_data.
                    # if the value of a state_data key is None, then use the value from data_config
                    for (key, value) in data_config.items():
                        if 'data' not in state_data['goals'][goal_name].keys():
                            breakpoint()
                        if state_data['goals'][goal_name]['data'][key] == None:
                            new_data[key] = value
                        else:
                            new_data[key] = state_data['goals'][goal_name]['data'][key]
                    framework_states += f"          Goal Data: {json.dumps(new_data)}\n"
            framework_states += "\n"
        framework_states += "States are considered complete when all of their goals success criteria are met."

        # Framework Goals
        framework_goals = ""
        for (name, goal) in self.persona_config.config['goals']['framework'].items():
            framework_goals += f"- {name}: {goal}\n"

        # Memory Context
        memory_context = self.get_conversation_memory()


        # Output Format Text
        output_format_text = ""
        if state_data_json_response == True:

            output_format_text = f"""
The response should be provided in the following JSON format:
{{
    "current_state": "{current_state}",
    "next_state": f"<Determine if the current state should change and place it here, otherwise stay in the same state: Valid states = {', '.join(state_list)}>",
    'agent_response": "<Generate the response to the user input in markdown here and esure that it contains a follow up question to keep the conversation going.>",
    "data": {persona_state_obj.data_schema_json}
}}
Ensure that the JSON response is loadable by json.loads(). Ensure that newlines are represented as '\\n' in the JSON response.
"""

        # Markdown Format Requirements
        markdown_format_requirements = """
Markdown Format Requirements:
- Generate Markdown for any JSON values that are intended to be displayed to the user.
- DO NOT use headers.
- Apply **bold** for titles and keywords; use *italics* for emphasis. Do not make entire sentences bold or italic.
- Present lists with bullet points or numbers depending on sequence importance.
- Use tables to structure comparative or detailed data.
- Ensure that newlines are represented as two for additional space'\\n\\n'
- Place questions on its own line
- Apply the formatting style that best enhances the clarity and engagement of the content.

DO NOT generate JSON values using HTML or XML.
"""
        # Framework Message
        framework_message = f"""
{persona_info}

Available States and their details:
{framework_states}
Global Framework Goals:
{framework_goals}
{memory_context}

{current_state}

{markdown_format_requirements}

{output_format_text}
"""
        messages.append({
            "role": "system",
            "content": framework_message
        })

        return messages

    def process_user_input(self, user_input):
        self.current_user_input = user_input
        self.put_conversation_history('user', user_input)


    def interaction_get_starting_conversation(self):
        messages = []
        messages = self.get_framework_messages(messages)

        messages.append({
            "role": "system",
            "content": f"The user has just begun a conversation with you, generate a response approrate for the starting point of the conversation based on the current state, its data, and goals (both framework and current state)."
        })

        json_format_dict = {
            'agent_greeting_response': "<Welcome the user, describe the current state they are in, and then assess and generate summary of their progress for the current state. This value must be formatted in Markdown.>",
            'agent_question_response': "<Ask the user only one question relevant to the current state to keep the conversation going. This value must be formatted in Markdown. Ensure the question is on a newline if sentences come before it.>",
        }

        system_content = f"""
The response should be provided in the following JSON format:
{json.dumps(json_format_dict)}

Please ensure that all variables in the JSON response format have valid values.
Ensure that the JSON response is loadable by json.loads(). Ensure that newlines are represented as '\\n' in the JSON response.
"""

        messages.append({
            "role": "system",
            "content": system_content
        })

        response = self.get_response(messages, json_response=True)

        agent_response = f"""
{response['agent_greeting_response']}
{response['agent_question_response']}
"""
        self.session.send_user_message(agent_response)
        # self.session.send_user_message(response['agent_greeting'])
        # self.session.send_user_message(response['current_context'])
        # self.session.send_user_message(response['next_steps'])
        # self.session.send_user_message(response['agent_question'])
        self.put_conversation_history('agent', response['agent_question_response'])

        #self.persona_config['data_objects']['framework']['user_state'] = response['user_state']
        self.session.init_complete = True

        return True

    # Processes the interactions with the User
    def interactions(self, user_input=None):
        if user_input != None:
            self.process_user_input(user_input)
        elif self.session.init_complete == False:
            self.interaction_get_starting_conversation()

        return self.agent.interactions(user_input)
