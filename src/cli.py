import readline
import textwrap
import json


class CLI:
    def __init__(self, username):
        # Enable readline history and editing capabilities
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set editing-mode emacs")  # Enables Ctrl-A, Ctrl-E, etc.
        readline.parse_and_bind('"\\e[A": history-search-backward')  # Up arrow
        readline.parse_and_bind('"\\e[B": history-search-forward')   # Down arrow

    def write(self, text, quiet=False, initial_indent='    ', subsequent_indent='    '):
        # Split the text by \n and textwrap each line
        text_lines = text.split('\n')
        full_wrapped_text = ""
        for line in text_lines:
            wrapped_text = textwrap.fill(
                line,
                width=100,
                initial_indent=initial_indent,
                subsequent_indent=subsequent_indent)
            full_wrapped_text += wrapped_text + '\n'
            if not quiet:
                print(wrapped_text)
            initial_indent = subsequent_indent
        return full_wrapped_text

    def write_json(self, json_data, quiet=False):
        # Pretty print the JSON data
        write_data = json.loads(json_data)
        if write_data == None:
            breakpoint()
        for message in write_data:
            #normalized_response = message['response'][:65].replace('\n', ' ')
            #print(f"{message['role']}: {normalized_response}")
            self.write(f"{message['role']}: {message['response']}", quiet, initial_indent='    ', subsequent_indent='        ')
            print()

    def read_input(self, prompt=None):
        if prompt == None:
            prompt = "User > "
        try:
            # Read input from the prompt with enhanced capabilities
            user_input = input(prompt)
        except EOFError:
            # Handle EOF (Ctrl-D) gracefully
            print("\nInput interrupted.")
            return None

        return user_input
