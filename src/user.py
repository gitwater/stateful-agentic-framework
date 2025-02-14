import json

class User:
    def __init__(self, session):
        self.session = session

    def generate_response(self, user_input, mode="question"):
        if mode == "question":
            return f"You just said: {user_input}\n\nA conversation among (Socrates, Theaetetus, and Plato) will begin shortly..."
        elif mode == "feedback":
            return f"Received your feedback: {user_input}"
        return "Connecting..."

    def interactions(self):
        if self.session.init_complete == False:
            return None
        chat_response = json.dumps([])
        if self.session.user_input is None or self.session.wait_for_the_user:
            user_input = self.session.cli.read_input()
            if self.session.user_input is None:
                self.session.user_input = user_input
                self.session.agent.process_user_input(self.session.user_input)
                response = self.generate_response(self.session.user_input, mode="question")

            if self.session.wait_for_the_user:
                self.session.agent.add_user_feedback(self.session.all_questions_to_the_user, user_input)
                self.session.all_questions_to_the_user = ""
                self.session.wait_for_the_user = False
                response = self.generate_response(user_input, mode="feedback")

            chat_response = json.dumps([{'role': 'System','response': response}])

        return chat_response