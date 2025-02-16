import random
#from socratic_agent import SocraticAgent
from persona_agent import PersonaAgent
from user import User
from cli import CLI
from pprint import pprint
import json
from types import SimpleNamespace
import yaml

class AgenticFrameworkConfig:
    def __init__(self, config_path):
        self.config_file_path = config_path
        self.config = self.load_yaml_file(config_path)

    def load_yaml_file(self, filepath):
        """
        Load a YAML file and return its contents as a Python dictionary.

        Parameters:
            filepath (str): The path to the YAML file.

        Returns:
            dict: The YAML file content as a Python dictionary.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
            yaml.YAMLError: If an error occurs while parsing the YAML file.
        """
        with open(filepath, 'r', encoding='utf-8') as file:
            try:
                data = yaml.safe_load(file)
                if data is None:
                    data = {}
                return data
            except yaml.YAMLError as exc:
                print(f"Error parsing YAML file: {exc}")
                raise

        return data

    @property
    def persona(self):
        return self.config['persona']

    def framework_llm_config(self, agent_type=None, socratic_persona=None):
        framework = self.config['framework_settings']
        if agent_type is None:
            if framework['reasoning_agent'] == 'single':
                return framework['reasoning_agents_config']['single']
            if framework['reasoning_agent'] == 'socratic':
                if socratic_persona is None:
                    breakpoint()
                return framework['reasoning_agents_config']['socratic'][socratic_persona]
        elif agent_type == 'single':
            return framework['reasoning_agents_config']['single']
        elif agent_type == 'socratic':
            if socratic_persona is None:
                breakpoint()
            return framework['reasoning_agents_config']['socratic'][socratic_persona]
        return None

    def framework_llm_openai_config(self, agent_type=None, socratic_persona=None):
        agent_config = self.framework_agent_config(agent_type, socratic_persona)
        return agent_config['openai_config']

    def state_output_formats(self):
        # Iterate over each state and build a string of the output formats
        state_output_formats = ""
        for state_name, state_config in self.config['states'].items():
            if 'output_format' not in state_config:
                continue
            if state_output_formats == "":
                state_output_formats = "State Output Formats:\n"
            state_output_formats += f"{state_name}: <states.{state_name}.output_format>\n{state_config['output_format']}\n\n"

        return state_output_formats

class SessionState:
    def __init__(self, client_id, persona_config_path):
        self.client_id = client_id
        self.user_input = None
        self.agent_msgs = []
        self.agent_dialog_msgs = []
        # Init will assess the current state of the User to decide where to start
        self.init_complete = False
        self.agent_session = None
        # Load a JSON file from the path provided
        persona_config = AgenticFrameworkConfig(persona_config_path)

        self.agent = PersonaAgent(self, persona_config )

    def load_config(filename):
        with open(filename, 'r') as file:
            return json.load(file, object_hook=lambda d: SimpleNamespace(**d))

    def send_user_message(self, message):
        agent_msg = {'role': 'Agent', 'response': message}
        self.agent_msgs.append(agent_msg)

    def pop_user_messages(self):
        messages = self.agent_msgs
        self.agent_msgs = []
        return messages

    def send_agent_dialog_message(self, agent_role, message):
        agent_msg = {'role': 'debug-agent', 'response': f"{agent_role}: {message}"}
        self.agent_dialog_msgs.append(agent_msg)

    def send_debug_message(self, message):
        agent_msg = {'role': 'debug-agent', 'response': f"{message}"}
        self.agent_dialog_msgs.append(agent_msg)

    def send_hud_message(self, message):
        agent_msg = {'role': 'hud', 'response': f"{message}"}
        self.agent_dialog_msgs.append(agent_msg)

    def pop_agent_dialog_messages(self):
        messages = self.agent_dialog_msgs
        self.agent_dialog_msgs = []
        return messages
