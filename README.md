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
    - Populate `profile.sh` with the following:
      ```bash
      . ./venv/bin/activate
      export OPENAI_API_KEY=''
      export ANTHROPIC_API_KEY=''
      ```

3. **Persona Configuration**
    - Create an agent configuration by following the instructions at the top of `config/template_config.yaml`

4. **Running the Agent**

    1. Open a terminal and navigate to your project directory.
    2. Load the Python environment if you have not aleady:
        ```bash
        . profile.sh
        ```
    3. Run the agent with the following command and arguments:
        ```bash
        python src/main.py `<config file path>`
        ```
    3. Open your browser and go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to connect to the agent.

    **Note:** If you quit the server, make sure to close your browser tab before starting the server again.
