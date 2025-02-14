# Stateful Agentic Framework
## Setup Instructions

1. **Python Environment Setup**
    - Ensure you have Python 3 installed on your system.
    - Consider using a virtual environment:
      ```bash
      python3 -m venv venv
      source venv/bin/activate
      ```
    - Install required packages using `pip install -r requirements.txt` if a requirements file is provided.

2. **API Key Configuration**
    - Create a file named `profile.sh` in your project root.
    - Populate `profile.sh` with your API keys. For example:
    ```bash
    . ./venv/bin/activate
    export OPENAI_API_KEY=''
    export ANTHROPIC_API_KEY=''
      ```

3. **Initializing Environment**
    - After setting up the environment and API keys, you can run the project scripts that rely on these settings.
    - Make sure to reload your shell or source the `profile.sh` file to apply the changes:
      ```bash
      source profile.sh
      ```

4. **Persona Configuration**

    - Open `persona_configs.py` to set up and customize the agent's persona.
    - Configure additional parameters as needed to tailor the persona's behavior.
    - The configuration from this file is automatically loaded during the initialization of the `Session()` class in `session.py`.

5. **Running the Agent**

    1. Open a terminal and navigate to your project directory.
    2. Run the agent with the following command:
        ```bash
        python src/main.py
        ```
    3. Open your browser and go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to connect to the agent.

    **Note:** If you quit the server, make sure to close your browser tab before starting the server again.


Happy coding!