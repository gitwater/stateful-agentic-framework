from agent import AgentCore
from pprint import pprint
import json


class SingleAgent(AgentCore):
    def __init__(self, session, persona_agent):
        llm_config = persona_agent.persona_config.framework_llm_config("single")
        super().__init__(persona_agent, llm_config)
        self.session = session
        self.system_role = f"""
You are {self.persona_agent.persona_config.config['persona']['name']}, a {self.persona_agent.persona_config.config['persona']['description']}.
Your purpose is {self.persona_agent.persona_config.config['persona']['purpose']}.
"""

    def get_response(self, messages, json_response=False):
        return super().get_response(messages, json_response)

    # def interaction_get_conversation_start_point(self):
    #     # Query the Agent for the initial steps
    #     response = self.socrates.get_conversation_starting_point()
    #     response = json.loads(response)
    #     # self.session.init_complete = True

    #     self.session.send_user_message(response['agent_greeting'])
    #     self.session.send_user_message(response['current_context'])
    #     self.session.send_user_message(response['next_steps'])
    #     self.session.send_user_message(response['agent_question'])
    #     #user_response_msg_list = [{'role': 'Agent', 'response': response['agent_question']}]
    #     self.persona_agent.put_conversation_history('agent', response['agent_question'])

    #     self.persona_config['data_objects']['framework']['user_state'] = response['user_state']
    #     self.session.init_complete = True

    #     return True

    def interaction_respond_to_user_input(self):

        # Take user input and process it through the State
        #
        messages = self.persona_agent.get_framework_messages([], state_data_json_response=True)
        # --------------------------------------------------
        # Static Framework Information
        # messages.append({
        #     "role": "system",
        #     "content": self.system_role
        # })

        #messages = self.persona_agent.get_framework_messages(messages)
        for message in messages:
            if type(message) == str and len(message) == 0:
                breakpoint()

        # --------------------------------------------------
        # User Input
        messages.append({
            "role": "user",
            "content": f"Current User Input: \"{self.persona_agent.current_user_input}\"."
        })

        llm_response = self.get_response(messages, json_response=False)
        try:
            llm_response = json.loads(llm_response)
        except:
            breakpoint()

        # TODO: Implement State Object for collecting data
        #state_obj = self.persona_agent.get_current_state()
        # process_user_input_response:
        #   - Records the llm_responses' data into the state's data object
        #   - Transitions to the next state if necessary
        #state_obj.process_user_input_response(llm_response)
        # breakpoint()
        self.persona_agent.state_manager.update_state_from_llm_response(llm_response)

        # TODO:
        #breakpoint()
        self.session.send_user_message(llm_response['agent_response'])

        return True


    def interactions(self, user_input=None):
        if user_input == None:
            if self.session.init_complete == False:
                # Query the Agent for the next steps
                self.interaction_get_conversation_start_point()
        else:
            # Continue the Socratic conversation to generate a response to the user's input
            self.interaction_respond_to_user_input()

        # If the user has not provided input, and the agent has already asked a question
        # Do nothing
        # if debug_printing:
        #     print("user_input:", self.session.user_input)
        #     print("in_progress:", self.session.agent_session.in_progress)
        #     print("no question skip")
        return True
