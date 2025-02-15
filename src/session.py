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

    def pop_agent_dialog_messages(self):
        messages = self.agent_dialog_msgs
        self.agent_dialog_msgs = []
        return messages
