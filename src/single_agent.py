from src.agent import AgentCore
from pprint import pprint
import json
import logging


class SingleAgent(AgentCore):
    def __init__(self, session, persona_agent):
        llm_config = persona_agent.persona_config.framework_llm_config("single")
        super().__init__("SingleAgent", persona_agent, llm_config)
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

    def interaction_respond_to_user_input(self, user_input):

        # Take user input and process it through the State
        #
        messages = self.persona_agent.get_framework_messages([], state_data_json_response=True, user_input=user_input)
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

        self.session.send_debug_message("agent_prompt", "---------------------------------------------------------------------")
        #self.session.send_debug_message("agent_prompt", "Agent Prompt:")        
        #for message in messages:
        #    self.session.send_debug_message("agent_prompt", f"{message['content']}")
        #self.session.send_debug_message("agent_prompt", "---------------------------------------------------------------------")

        messages.append({
            "role": "user",
            "content": f"User Input: \"{user_input}\"."
        })        
        llm_response = self.get_response(messages, json_response=False)
        # Regex to repalce all newlines with '\n' between 
        try:
            llm_response = json.loads(llm_response)
        except Exception as e:            
            # Send as much info as we can to the user
            self.session.send_debug_message("agent_response", f"Error: single_agent: interaction_respond_to_user_input: {e}")
            self.session.send_debug_message("agent_response", f"Response: {llm_response}")
        # TODO: Implement State Object for collecting data
        #state_obj = self.persona_agent.get_current_state()
        # process_user_input_response:
        #   - Records the llm_responses' data into the state's data object
        #   - Transitions to the next state if necessary
        #state_obj.process_user_input_response(llm_response)
        # breakpoint()
        self.persona_agent.state_manager.update_state_from_llm_response(llm_response)

        self.session.send_user_message(llm_response['agent_response'])

        return llm_response


    async def interactions(self, user_input=None):
        agent_response = None
        if user_input != None:            # Continue the Socratic conversation to generate a response to the user's input
            agent_response = self.interaction_respond_to_user_input(user_input)

        # If the user has not provided input, and the agent has already asked a question
        # Do nothing
        # if debug_printing:
        #     logging.info("user_input:", self.session.user_input)
        #     logging.info("in_progress:", self.session.agent_session.in_progress)
        #     logging.info("no question skip")
        return agent_response
