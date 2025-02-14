# import required libraries
import json
import openai
import anthropic

debug_token_printing = True

class AgentCore:
    LLM_API="anthropic"
    LLM_API="openai"

    def __init__(self, persona_agent, model=None):
        self.persona_agent = persona_agent
        self.response_history = []
        self.model = model

        print(f"LLM: {AgentCore.LLM_API}: {self.model}")

        if AgentCore.LLM_API == "anthropic":
            self.llm_client = anthropic.Anthropic()
            self.socrate_agent_role = "assistant"
            self.model = 'claude-3-5-sonnet-latest'
            #self.model = 'claude-3-5-haiku-latest'
        elif AgentCore.LLM_API == "openai":
            self.llm_client = openai.OpenAI()
            self.socrate_agent_role = "system"
            self.model = 'gpt-4o-mini'
            #self.model = 'gpt-3.5-turbo'
            self.model = 'gpt-4o'
        else:
            print("LLM API not set")
            breakpoint()


    def get_gpt_response(self, messages, json_response=False):
        if json_response:
            response_format = "json_object"
        else:
            response_format = "text"
        try:
            res = self.llm_client.chat.completions.create(
                    model=self.model,
                    response_format={"type": response_format},
                    temperature=0.5,
                    top_p=1.0,
                    presence_penalty=0.0,
                    messages = messages
                )
            msg = res.choices[0].message.content
        except openai.OpenAIError as e:
            if "maximum context length" in str(e):
                # Handle the maximum context length error here
                msg = "The context length exceeds my limit..."
            else:
                # Handle other errors here
                msg = f"I enconter an when using my backend model.\n\n Error: {str(e)}"
            print(f"!!! ERROR: {msg}: Retrying!!")
            breakpoint()
            return ""

        return msg

    def get_anthropic_response(self, messages):
        try:
            message = self.llm_client.messages.create(
                #model="claude-3-5-sonnet-latest",
                model=self.model,
                max_tokens=2000,
                temperature=0,
                system=messages[0]['content'],
                messages=messages[1:]
            )
            #breakpoint()
        except Exception as e:
            print(e)
            breakpoint()
        response = ''.join(block.text for block in message.content)
        if response == "":
            breakpoint()
        return response
        #return message.content

    def get_embeddings(self, input_text):
        if AgentCore.LLM_API == "anthropic":
            embeddings = self.llm_client.embeddings.create(
                model=self.model,
                input_text=input_text
            )
        elif AgentCore.LLM_API == "openai":
            embeddings = self.llm_client.embeddings.create(
                model='text-embedding-ada-002',
                #model='text-embedding-3-small',
                #model='text-embedding-3-large'
                input=input_text,
                encoding_format="float"
            )
        else:
            print("LLM API not set")
            breakpoint()

        return embeddings.data[0].embedding

    def get_response(self, messages=None, json_response=False):
        if messages == None:
            breakpoint()

        count = 0
        while True:
            if AgentCore.LLM_API == "anthropic":
                msg = self.get_anthropic_response(messages)
            elif AgentCore.LLM_API == "openai":
                msg = self.get_gpt_response(messages, json_response)
            else:
                print("LLM API not set")
                breakpoint()
            if len(msg) > 0:
                break
            count += 1
            if count > 5:
                print("No response from the model")
                breakpoint()
            else:
                print(">>>>>>> No response from the model, retrying...")
                breakpoint()

        # Print the number of tokens in the messages and the response
        # A token is 4 bytes
        if debug_token_printing:
            print(f"\n>>>>>>>>> {self.socrate_agent_role}: Get Response: Input Tokens: {len(''.join([m['content'] for m in messages]))/4}: Output Tokens: {len(msg)/4}\n")

        if json_response:
            msg = json.loads(msg)

        return msg


    def get_framework_messages(self, system_role_type="socratic"):
        return self.agent.get_framework_messages(system_role_type)

    def get_conversation_starting_point(self, socractic=True):
        return self.agent.get_conversation_starting_point(socractic)

