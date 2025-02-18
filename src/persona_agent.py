from socratic_agent import SocraticAgent
from single_agent import SingleAgent
from persona_state import PersonaStateManager
from sql_database.core import SQLDatabase
from memory import AgentMemory
import json
from pprint import pprint
import sys
import logging

class PersonaAgent:

    def __init__(self, session, persona_config):
        self.session = session
        self.persona_config = persona_config
        self.sql_db = SQLDatabase(self.session.username, persona_config.config['persona']['name'])
        self.state_manager = PersonaStateManager(persona_config.config, self.sql_db)

        if self.persona_config.config['framework_settings']['reasoning_agent'] == "socratic":
            self.agent = SocraticAgent(session, self)
        else:
            self.single_agent = SingleAgent(session, self)
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

        if type(message) == bool:
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


    # Generates a string where each new line has a prefix of indent
    def pstring(self, key, value, indent=""):
        key = key+": "
        prompt_text = f"{indent}{key}"
        count = 1
        for line in value.split("\n"):
            if count > 1:
                prompt_text += f"{indent}{' ' * len(key)}"
            prompt_text += f"{line}\n"
            count += 1

        if prompt_text[-1] != '\n':
            prompt_text += "\n"
        return prompt_text

    # Get the framework messages for the persona
    # Persona
    #
    def get_framework_messages(self, messages, state_data_json_response=False):
        persona_config = self.persona_config.config['persona']
        persona_state_obj = self.state_manager.get_state_obj()
        # Persona
        persona_info = f"""You are {persona_config['name']}.
You are described as {persona_config['description']}.
Your purpose is {persona_config['purpose']}.
"""

        # Framework States
        framework_states = "Available States and their details:\n"
         # Current State
        current_state = persona_state_obj.name

        states_config = self.persona_config.config['states']
        state_list = []
        indent = "  "
        for (state_name, state_config) in states_config.items():
            if 'visibility' in state_config.keys() and state_config['visibility'] == 'state_only' and current_state != state_name:
                continue
            # State
            state_list.append(state_name)
            framework_states += self.pstring("State", state_name, indent)
            indent += "  "
            framework_states += self.pstring("Purpose", state_config['purpose'], indent)
            # If current state is the state being processed, then use the current state data
            state_data = self.sql_db.db_states.get_persona_state_data(state_name)
            framework_states += self.pstring("Goals", "", indent)
            for (goal_name, goal_config) in state_config['goals'].items():
                indent += "  "
                framework_states += self.pstring("Goal", goal_name, indent)
                indent += "  "
                framework_states += self.pstring("Description", goal_config['goal'], indent)
                if current_state == state_name:
                    framework_states += self.pstring("Goal Sucess Criteria", "When all data fields have values that satisfy the goals intent.", indent)
                data_config = goal_config['data']
                if state_data == None:
                    framework_states += self.pstring("Goal Data", json.dumps(data_config), indent)
                else:
                    new_data = {}
                    # Merge state_data and data_config into new_data.
                    # if the value of a state_data key is None, then use the value from data_config
                    for (key, value) in data_config.items():
                        if goal_name not in state_data['goals'].keys():
                            state_data['goals'][goal_name] = {'data': {}}
                        if 'data' not in state_data['goals'][goal_name].keys():
                            breakpoint()
                        if key not in state_data['goals'][goal_name]['data'].keys():
                            state_data['goals'][goal_name]['data'][key] = None
                        if state_data['goals'][goal_name]['data'][key] == None:
                            new_data[key] = value
                        else:
                            new_data[key] = state_data['goals'][goal_name]['data'][key]
                    framework_states += self.pstring("Goal Data", json.dumps(new_data), indent)
                indent = indent[:-4]
            # state_data_output_format
            # if 'output_format' in state_config.keys():
            #     framework_states += self.pstring("State Data Output Format", "", indent)
            #     framework_states += self.pstring("", state_config['output_format'], indent)

            indent += "  "
            framework_states += self.pstring(f"State Transition Criteria", "Only transition to another state when all of the {state_name}'s goals and their success criteria have been met.", indent)
            indent = indent[:-4]
        framework_states += "States are considered complete only when all of their goals success criteria are met."
        framework_states += "However, if asked, please display state outputs as configured by the outputs_format."

        # Framework Goals
        framework_goals = ""
        count = 1
        for (name, goal) in self.persona_config.config['goals']['framework'].items():
            if count == 1: framework_goals = "Global Framework Goals:\n"
            framework_goals += self.pstring(name, goal, "  ")
            count += 1

        # Memory Context
        memory_context = self.get_conversation_memory()
        #memory_context = ""

        # Output Format Text
        output_format_text = ""
        if state_data_json_response == True:

            output_format_text = f"""
The response should be provided in the following JSON format:
{{
    "current_state": "{current_state}",
    "next_state": f"<Determine if the current state should change and place it here, otherwise stay in the same state: Valid states = {', '.join(state_list)}: Format with Markdown using the Markdown and Response Instructions.>",
    'agent_response": "<Place your response here and esure that it contains a follow up question to keep the conversation going. Format with Markdown using the Markdown and Response Instructions.>",
    "data": {persona_state_obj.data_schema_json}
}}
Ensure that the JSON response is loadable by json.loads(). Ensure that newlines are represented as '\\n' in the JSON response.
Please rewrite the user's answers using a refined, professional tone suitable for formal documentation.
"""
        # Markdown Format Requirements
        response_and_markdown_format_requirements = """
Markdown Formatting Instructions:
  - Only format using Markdown when JSON values indicate it.
  - Do not use headers larger than 4 #'s
  - Apply **bold** for titles and keywords; use *italics* for emphasis. Do not make entire sentences bold or italic.
  - Present lists with bullet points or numbers depending on sequence importance.
  - Use tables to structure comparative or detailed data.
  - Apply the formatting style that best enhances the clarity and engagement of the content.

Other Response Instructions:
  - Never format JSON values using HTML or XML.
  - Always separate questions with a newline if they are part of a paragraph.
  - Use the data in each of the states to help answer the existing state's goals and avoid asking the user questions if it does not need to.
  - If the user asks to switch to a different state, then switch to that state and perform the actions they asked or ask questions if needed.
"""
        # Framework Message
        framework_message = f"""{persona_info}
{framework_states}
{framework_goals}
{memory_context}
Current State: {current_state}
{response_and_markdown_format_requirements}
{output_format_text}
"""
        messages.append({
            "role": "system",
            "content": framework_message
        })

        self.session.send_debug_message("---------------------------------------------------------------------")
        self.session.send_debug_message("Framework Messages\n\n")
        for message in messages:
            self.session.send_debug_message(message['content'])

        return messages

    def process_user_input(self, user_input):
        self.current_user_input = user_input
        self.put_conversation_history('user', user_input)


    def interaction_get_response(self, system_message, json_format_dict=None):
        messages = []
        prompt_messages = []
        framework_messages = self.get_framework_messages(messages)
        messages.extend(framework_messages)

        prompt_messages.append({
            "role": "system",
            "content": system_message
        })

        if json_format_dict != None:
            json_response_content = f"""
The response should be provided in the following JSON format:
{json.dumps(json_format_dict, indent=4)}

Please ensure that all variables in the JSON response format have valid values.
Ensure that the JSON response is loadable by json.loads(). Ensure that newlines are represented as '\\n' in the JSON response.
"""

        prompt_messages.append({
            "role": "system",
            "content": json_response_content
        })

        for message in prompt_messages:
            self.session.send_debug_message(message['content'])
        self.session.send_debug_message("---------------------------------------------------------------------")

        messages = framework_messages
        messages.extend(prompt_messages)

        response = self.get_response(messages, json_response=True)
        self.session.send_debug_message(f"Get Response:\n{json.dumps(response, indent=4)}")

        return response

    def interaction_get_starting_conversation(self):

        start_conv_prompt = """The user has just begun a conversation with you, generate a response approrate for the
starting point of the conversation based on the current state, its data, and goals (both framework and current state)."""

        json_format_dict = {
            'agent_greeting_response': "<Place a welcome message here that describes the current state they are in, a summary of their progress. Do not ask questions here. Format with Markdown using the Markdown and Response Instructions.>",
            'agent_question_response': "<Place a question here relevant to the current state to keep the conversation going. Format with Markdown using the Markdown and Response Instructions.>",
        }

        response = self.interaction_get_response(start_conv_prompt, json_format_dict)

        agent_response = f"""
{response['agent_greeting_response']}\n
{response['agent_question_response']}
"""
        self.session.send_user_message(agent_response)
        self.session.conversation_started = True

        # Render the HUD content and send it to the user
        self.interaction_update_hud_content()

        return response['agent_question_response']

    def interaction_update_hud_content(self):
        hud_prompt_message = f"""Generate the HUD content replacing <variables> with the state data
Only replace the text between the <variable> with the state data and the state output format.

HUD Content Template:
{self.persona_config.config['hud']['content_markdown']}

Instructions:
* Replace <var1.var2> variable tags with real content from the state data.
* If real content from the state is not available, insert the string 'TBD' in place of the content.
"""

        hud_prompt_message += self.persona_config.state_output_formats()

        json_format_dict = {
            'hud_content': "<Generate HUD content <variables> using state data. Format with Markdown using the Markdown and Response Instructions.>",
        }

        response = self.interaction_get_response(hud_prompt_message, json_format_dict)

        self.session.send_hud_message(response['hud_content'])

        return True

    # Refresh the conversation by sending the HUD content to the user
    # and the last 10 utterances in the conversation history
    def refresh(self):
        self.interaction_update_hud_content()
        conversation_history = self.sql_db.db_stm.retreive_utterances()
        # iterate in reverse order to get the last 10 utterances
        conversation_history = conversation_history[::-1]
        for message in conversation_history:
            if message['speaker'] == 'user':
                self.session.send_as_user_message(message['utterance'])
            else:
                self.session.send_user_message(message['utterance'])


    # Processes the interactions with the User
    def interactions(self, user_input=None):
        update_hud = False
        agent_response = None
        if user_input != None:
            self.process_user_input(user_input)
            update_hud = True

        if self.session.conversation_started == False and self.session.disable_conversation_init == False:
            agent_response = self.interaction_get_starting_conversation()
        else:
            agent_response = self.agent.interactions(user_input)

        if update_hud:
            self.interaction_update_hud_content()

        if agent_response != None:
            self.put_conversation_history('agent', agent_response)

        return True
