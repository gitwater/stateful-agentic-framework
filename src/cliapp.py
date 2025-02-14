
from socratic_agent import SocraticAgent
from session import SessionState
from pprint import pprint

# TODO:
#   - Next step is to work with json resposnes
#   - Store state on disk for reuse
#   - On Final Answer, process the answer to make choices on what to do next with JSON response
#   - Introduce logic to analyze the json response to detect state changes to guide users
#   - If user doesn't want to follow then stick to the current state for a while then reasses
#   - Find a way to set some user goals (if needed)
#   - Find a way to take a quiz to get initial scores


default_client_id = 1

def main():
    session = SessionState(default_client_id)

    while True:
        user_msg = session.user.interactions()
        if user_msg != None:
            session.cli.write_json(user_msg)
        agent_msg = session.agent.interactions()
        # TODO: Hide Socratic conversation session from the User
        # and output only Agent questions and final answers
        session.cli.write_json(agent_msg)

    # while True:
    #     response = chat(session)
    #     if response != None:
    #         session.cli.write_json(response)
    #     response = active_message(session)
    #     session.cli.write_json(response)

if __name__ == "__main__":
    main()
