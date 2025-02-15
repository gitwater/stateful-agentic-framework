import openai
import os
import json
import re
import time
from pprint import pprint
from memory import AgentMemory
from datetime import datetime
import hashlib
from agent import AgentCore

debug_printing = False
debug_printing = True
debug_converstation = True
debug_converstation = False

class SocraticAgentCore(AgentCore):

    def __init__(self, socratic_persona, persona_agent, model=None):

        llm_config = persona_agent.persona_config.framework_llm_config('socratic', socratic_persona=socratic_persona.lower())
        super().__init__(persona_agent, llm_config)

        if llm_config['model'] in AgentCore.openai_model_list:
            # OpenAI Prompt Role config
            self.socrate_agent_role = "system"
        else:
            # Anthropic Prompt Role config
            self.socrate_agent_role = "assistant"

        self.socratic_persona = socratic_persona
        self.other_socratic_persona = None
        self.response_history = []

        if self.socratic_persona == "Socrates":
            self.other_socratic_persona = "Theaetetus"
        elif self.socratic_persona == "Theaetetus":
            self.other_socratic_persona = "Socrates"

        self.system_role_single_agent = f"""
Socrates is one of three AI assistants who work together as the thinking and reasoning mind for an AI agent named {self.persona_agent.persona_config.config['persona']['name']}.

{self.persona_agent.persona_config.config['persona']['name']} describes themselves as {self.persona_agent.persona_config.config['persona']['description']}.
{self.persona_agent.persona_config.config['persona']['name']}'s purpose is {self.persona_agent.persona_config.config['persona']['purpose']}.

For now, {self.socratic_persona} is acting as the sole Agent to help with assessing the current state of the user with in the framework.
"""

        self.system_role = f"""
Socrates, Theaetetus, and Plato are three AI assistants. Together they work as the thinking and reasoning mind
for an AI agent named {self.persona_agent.persona_config.config['persona']['name']}.

{self.persona_agent.persona_config.config['persona']['name']} describes themselves as {self.persona_agent.persona_config.config['persona']['description']}.
{self.persona_agent.persona_config.config['persona']['name']}'s purpose is {self.persona_agent.persona_config.config['persona']['purpose']}.

Socrates and Theaetetus will engage in multi-round dialogue to come up with a response to the User's input.
Their response will take into account:
  - The User's input
  - {self.persona_agent.persona_config.config['persona']['name']}'s purpose
  - The current state and the goals of the state

Their discussion should balance quick responses with structured problem-solving depending on the nature of
the question. They should avoid logical errors, such as false dichotomy, hasty generalization, circular reasoning.
Responses should be as short as possible to keep token count low, but still include all necessary and
relevant information.

If they want to ask the user questions to further understand the context, they should ask the question as
part of their final answer. The user's response will be provided in the next round.

To ensure that their response is correct Plato will proofread their dialog and provide feedback to them.
Socrates and Theaetetus will ensure that Plato has proofread their dialog to esure he does not have any suggestions
before giving their final answer.

If they end up having multiple possible answers, they should continue analyzing until they reach a consensus.

When Socrates is ready to present the final answer, he should do so using the text @FAStart [insert answer] @FAEnd .
The final answer should only be generated once Plato no longer has any suggestions the answer. The answer must be
worded from the perspective of the agent speaking to the user. The final answer should flow with the Conversation
History so that it feels like the conversation has continuity of context.
"""
#If they encounter any issues with the validity of their answer, they should re-evaluate their reasoning and calculations.
#"""

        if self.socratic_persona == 'Plato':
            self.system_role += """Now as a proofreader, Plato, your task is to read through the dialogue between
Socrates and Theaetetus and identify any errors they made."""
        else:
            self.system_role += f"""Now, suppose that you are {self.socratic_persona}. Please discuss with
{self.other_socratic_persona} to find a response to the users input and context.

"""

        self.system_role += f"Generate responses for {self.socratic_persona} only. Responses from the other agents will be provided in the next round."


    def get_response(self, messages=None, add_to_history=False, json_response=False):
        if messages == None:
            # Insert Framework messages
            # System profile
            #
            messages = self.get_framework_messages()
            # Iterate over messages and appent to a local file
            with open("messages.json", "+a") as f:
                f.write("----------------------------------------\n")
                f.write(f"Agent: {self.socratic_persona}\n")
                json.dump(messages, f, indent=4)

        llm_response = super().get_response(messages, json_response)

        if add_to_history:
            self.response_history.append({
                    "role": "assistant",
                    "content": f"{self.socratic_persona}: {llm_response}"
                })

        return llm_response


    def update_response_history(self, role, message):
        if message == "":
            #breakpoint()
            return
        self.response_history.append({
            "role": role,
            "content": message
        })

    # def add_user_feedback(self, question, answer):
    #     self.response_history.append({
    #         "role": 'user',
    #         "content": f"the User's feedback to \"{question}\" is \"{answer}\""
    #     })

    def add_proofread(self, proofread):
        self.response_history.append({
            "role": self.socrate_agent_role,
            "content": f"Message from a proofreader Plato to Socrates and Theaetetus: {proofread}"
        })

    def get_framework_messages(self, system_role_type="socratic"):
        messages = []
        # --------------------------------------------------
        # Static Framework Information
        system_content = self.system_role

        messages.append({
            "role": "system",
            "content": system_content
        })

        # Framework: Static & Dynamic User Data
        #  - Awareness Dimensions
        #  - Framework states
        # State
        #  - User Awareness scores
        #  - Current state
        #  - Current state goals

        messages = self.persona_agent.get_framework_messages(messages)
        for message in messages:
            if type(message) == str and len(message) == 0:
                breakpoint()

        # --------------------------------------------------
        # User Input
        if system_role_type == "socratic":
            messages.append({
                "role": "user",
                "content": f"User input: \"{self.persona_agent.current_user_input}\"."
            })

            # --------------------------------------------------
            # User Engagement
            if self.socratic_persona == "Plato":
                assistant_role = f"Hi Theaetetus and Socrates, "
            else:
                assistant_role = f"Hi {self.other_socratic_persona}, "
            assistant_role += "let's respond to the user together. Please feel free to correct me if I make any mistakes."

            messages.append({
                "role": "assistant",
                "content": assistant_role
            })

        return messages

    # def get_conversation_starting_point(self):
    #     # Query the Agent for the initial steps
    #     messages = self.get_framework_messages(system_role_type="starting_point")
    #     response = self.get_response(messages, add_to_history=False, json_response=True)

    #     return response


class SocratesAgent(SocraticAgentCore):
    def __init__(self, persona_agent, model=None):
        super().__init__('Socrates', persona_agent, model)


class TheaetetusAgent(SocraticAgentCore):
    def __init__(self, persona_agent, model=None):
        super().__init__('Theaetetus', persona_agent, model)

class PlatoAgent(SocraticAgentCore):
    def __init__(self, persona_agent, model=None):
        super().__init__('Plato', persona_agent, model)
        self.proofread_see_previous_suggestions_count = 0
        self.proofread_suggestions_count = 0
        self.proofread_suggestions_count_max = 3

    def proofread(self):
        success_string = "Analysis looks reasonable. Socrates or Theatetus, please proceed with your final answer using the information you have, no more deliberating."
        suggestions_string = "Here are my suggestions:"

        if self.proofread_see_previous_suggestions_count >= self.proofread_suggestions_count_max or self.proofread_suggestions_count >= self.proofread_suggestions_count_max:
            #proof_read_input = f"You have reached the number of times you are allowed to respond with 'Please see my previous suggestions', please response with \"{success_string}\"."
            #proof_read_input = f"Socrates and Theaetetus have deliberated enough, please agree with their response with \"{success_string}\"."
            msg = f"{success_string}"
            # udpate history
            self.update_response_history("assistant", f"Plato: {msg}")
            return msg
        else:
            previous_suggest_instruction = "If you need to repeat your suggestions, please response with \"Please see my previous suggestions, waiting for more information, carry on working on a response\"."
            proof_read_input = f"""
            The above is the conversation between Socrates and Theaetetus. Your job is to challenge their answers.
            They were likely to have made multiple mistakes. Please correct them.
            {previous_suggest_instruction}
            Otherwise start with \"{suggestions_string}\"
            Do not ask the user any questions.\n"""

        pf_template = {
                "role":  self.socrate_agent_role,
                "content": proof_read_input
        }

        # If the latest response from Socrates or Theaetetus does not offer any new information, please response with \"Waiting for more information\".

        #msg = self.get_anthropic_response(self.history + [pf_template])
        messages = self.get_framework_messages() + [pf_template]
        msg = self.get_response(messages, add_to_history=True)
        #print("\n-----------------------------------\n")
        #print("\nPlato Proofread it!\n")

        # Check if msg contains "Please see my previous suggestions" increment a counter
        if "Please see my previous suggestions" in msg:
            self.proofread_see_previous_suggestions_count += 1

        print(f"############## Proofread suggestions count: {self.proofread_suggestions_count} >= {self.proofread_suggestions_count_max}\n")
        print(f"############## Proofread previous suggestions count: {self.proofread_see_previous_suggestions_count} >= {self.proofread_suggestions_count_max}\n")
        if msg.find(suggestions_string) != -1:
            self.proofread_suggestions_count += 1

        return msg


class SocraticSessionState:
    def __init__(self):
        self.in_progress = False
        self.in_progress_sub = False
        self.dialog_lead = None
        self.dialog_follower = None
        self.init_complete = False

class SocraticAgent:

    def __init__(self, session, persona_agent, model=None):
        #if model == None:
            #breakpoint()
        session.agent_session = SocraticSessionState()
        self.persona_agent = persona_agent
        self.session = session
        self.persona_config = persona_agent.persona_config.config
        self.socrates = SocratesAgent(self.persona_agent, model)
        self.theaetetus = TheaetetusAgent(self.persona_agent, model)
        self.plato = PlatoAgent(self.persona_agent, model)
        self.current_user_input = None
        #self.memory_system = AgentMemory(persona_config, self.socrates)


    def reset_response_conversation(self):
        self.socrates.response_history = []
        self.theaetetus.response_history = []
        self.plato.response_history = []
        self.plato.proofread_suggestions_count = 0
        self.plato.proofread_see_previous_suggestions_count = 0

    # Start a conversation to provide a response to the user's input
    def interaction_start_agent_conversation(self):
        self.session.agent_session.in_progress = True
        self.session.agent_session.dialog_lead, self.session.agent_session.dialog_follower = self.socrates, self.theaetetus

        self.session.send_agent_dialog_message('Socrates', f"Hi Theaetetus, let's solve this problem together. Please feel free to correct me if I make any logical mistakes.")
        print(f"Starting Socratic Conversation")
        return True

    def interaction_final_answer(self, rep):
        self.session.user_input = None
        self.session.agent_session.in_progress = False
        self.session.agent_session.in_progress_sub = False

        if ("@FAStart" in rep):
            final_answer_pattern = r"@FAStart\s*(.*?)\s*@FAEnd"
            final_answer_matches = re.findall(final_answer_pattern, rep, re.DOTALL)

            if len(final_answer_matches) > 0:
                final_answer = final_answer_matches[0]
                self.persona_agent.put_conversation_history('agent', final_answer)

            self.session.send_user_message(final_answer)

        elif "The context length exceeds my limit..." in rep:
            self.session.send_user_message("The dialog went too long, please try again.")
            #msg_list.append(
            #        {'role': 'System',
            #        'response': "The dialog went too long, please try again."})
            breakpoint()
        else:
            breakpoint()
        if debug_printing:
            print("user_input:", self.session.user_input)
            print("in_progress:", self.session.agent_session.in_progress)
            #print("msg list:")
            #print(msg_list)
            print("end conversation reset")

        self.reset_response_conversation()
        self.session.agent_session.in_progress_sub = False

        return True

    def interaction_proofread(self):
        pr = self.plato.proofread()
        if pr:
            self.session.send_agent_dialog_message('Plato', pr)
            #user_resp_msg_list.append(
            #    {'role': 'Plato',
            #    'response': pr})
            self.socrates.add_proofread(pr)
            self.theaetetus.add_proofread(pr)
            # feedback = self.ask_the_User(pr)
            # if feedback:
            #     for fed in feedback:
            #         q, a = fed["question"], fed["answer"]
            #         if debug_printing:
            #             print(f"\033[1mThe User:\033[0m Received Question: {q}\n\n  Answer: {a}\n")
            #         self.add_user_feedback(q, a)

        self.session.agent_session.dialog_lead, self.session.agent_session.dialog_follower = self.session.agent_session.dialog_follower, self.session.agent_session.dialog_lead

        return True


    def interaction_continue_socratic_conversation(self):
        #user_response_msg_list = []
        print(f"Continuing Socratic Conversation: {self.session.agent_session.in_progress_sub}")
        if True == True: # and self.session.in_progress_sub == False:
            print(f"Continuing Socratic Conversation: deliberating...")
            self.session.agent_session.in_progress_sub = True
            rep = self.session.agent_session.dialog_follower.get_response(messages=None, add_to_history=True)
            self.session.send_agent_dialog_message(self.session.agent_session.dialog_follower.socratic_persona, rep)
            #user_response_msg_list.append({'role': self.session.agent_session.dialog_follower.socratic_persona, 'response': rep})
            self.session.agent_session.dialog_lead.update_response_history("assistant", f"{self.session.agent_session.dialog_follower.socratic_persona}: {rep}")
            self.plato.update_response_history("assistant", f"{self.session.agent_session.dialog_follower.socratic_persona}: "+rep)
            # question_to_the_user = self.need_to_ask_the_User(rep)
            # if question_to_the_user:
            #     success = self.interaction_ask_user_question(question_to_the_user)
            #     if not success:
            #         breakpoint()
                #self.session.agent_session.dialog_follower.update_response_history("assistant", f"{self.session.agent_session.dialog_follower.socratic_persona}: Question to the User: {question_to_the_user}")
            # Sure fire way of detect "@FAStart" in the response
            if ("@FAStart" in rep):
                # or ("The context length exceeds my limit..." in rep):
                print(f"Socratic Conversation: Final answer detected")
                success = self.interaction_final_answer(rep)
                if success == False:
                    breakpoint()
            elif self.session.agent_session.in_progress_sub == True and self.session.agent_session.in_progress == True:
                print(f"Continuing Socratic Conversation: Proofreading")
                success = self.interaction_proofread()
                if not success:
                    breakpoint()
            else:
                breakpoint()

            # if debug_converstation:
            #     for message in user_response_msg_list:
            #         if message['role'] != 'System':
            #             message['response'] = 'Deliberating...'

            if debug_printing:
                print("user_input:", self.session.user_input)
                print("in_progress:", self.session.agent_session.in_progress)
                #print("msg list:")
                #print(user_response_msg_list)
        else:
            if debug_printing:
                print("Processing User Input")

        return True
        #return json.dumps(user_response_msg_list)

    # def interaction_ask_for_more_questions(self):
    #     self.session.asked_question = True
    #     if debug_printing:
    #         print("user_input:", self.session.user_input)
    #         print("asked_question:", self.session.asked_question)
    #         print("in_progress:", self.session.in_progress)
    #         print("ask user's question")
    #     if self.session.first_question:
    #         msg = "What's your question?"
    #     else:
    #         msg = "Do you have more questions?"
    #     return json.dumps([{'role': 'System',
    #                     'response': msg}])

    # def interaction_get_conversation_start_point(self, socratic=True):
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

        # return True


    # Processes the interactions with the User
    def interactions(self, user_input=None):
        # If the User has provided input, process it to generate a response
        if user_input != None:
            if self.session.agent_session.in_progress == False:
                self.interaction_start_agent_conversation()
        elif self.session.agent_session.in_progress:
            # Continue the Socratic conversation to generate a response to the user's input
            while self.session.agent_session.in_progress:
                self.interaction_continue_socratic_conversation()

        # If the user has not provided input, and the agent has already asked a question
        # Do nothing
        # if debug_printing:
        #     print("user_input:", self.session.user_input)
        #     print("in_progress:", self.session.agent_session.in_progress)
        #     print("no question skip")

        return True