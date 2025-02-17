# Stateful Agentic Framework

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)]()

A **declarative, configuration-based** approach for building conversational agents without any coding. Easily define states and goals in YAML, store data in structured goals, and let the framework handle conversation flow.

---

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Experimental](#experimental)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Databases](#databases)
8. [Examples](#examples)
9. [TODO / Roadmap](#todo--roadmap)
10. [Contributing](#contributing)
11. [License](#license)
12. [Acknowledgments](#acknowledgments)

---

## Introduction

The **Stateful Agentic Framework** is designed to simplify the process of creating and managing conversational agents. Instead of writing extensive code or complicated scripts, you can configure states, goals, and data structures in a YAML file. The framework then guides the conversation logically to collect and store information according to each state’s goals.

This project is ideal for:
- **Technical teams** wanting quick prototypes of conversational agents.
- **Business analysts** who need to automate data collection without deep coding knowledge.
- **Researchers & enthusiasts** exploring advanced agentic architectures.

---

## Features

- **Declarative Configuration**: Define conversation logic and data handling in an expressive YAML format.
- **State & Goal Management**: Set up multiple states, each containing goals and associated data structures.
- **Lightweight & Extensible**: Easily integrate new states, data flows, or custom expansions.
- **Browser-Based UI**: Connect through a local server to interact with your agent directly in your browser.
- **Local Databases**: Stores conversation history, goals, and embeddings locally in SQLite and Vector DB.

---

## Experimental

**Disclaimer**: The Stateful Agentic Framework is **new and experimental**. It’s under active development and not yet ready for production environments. We encourage early adopters, researchers, and enthusiasts to try it out, provide feedback, and even contribute; however, please be aware of the following:

- **Breaking Changes**: As we refine core features, you may see rapid iteration and frequent updates that can introduce breaking changes or adjustments in APIs, configurations, or internal data structures.
- **Limited Testing**: While we test the framework internally, a robust suite of automated tests and long-term performance benchmarks is still in progress. For critical projects, we recommend thoroughly testing your agent configurations before deployment.
- **Incomplete Documentation**: Sections of the documentation may still be maturing or missing entirely, as we balance building new features with improving clarity and usability.
- **Community Feedback**: Your insights, bug reports, and suggestions will play a major role in shaping the roadmap. We invite you to open issues or submit pull requests to help us prioritize features and improve stability.

Despite its evolving nature, we believe this framework offers a promising direction for **no-code**, **declarative**, and **flexible** agent development. Thank you for joining us on this journey, and we appreciate your patience and contributions as the project grows.

---
## Installation

### 1. Python Environment Setup
1. Ensure you have **Python 3** installed.
2. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install required packages (if a `requirements.txt` is provided):
   ```bash
   pip install -r requirements.txt
   ```

### 2. API Key Configuration
1. Create a file named `profile.sh` in the project root.
2. Populate `profile.sh` with:
   ```bash
   . ./venv/bin/activate
   export OPENAI_API_KEY=''
   export ANTHROPIC_API_KEY=''
   ```
3. **Note**: You can add other environment variables if your agent requires them.

---

## Configuration

### Agent Configuration (YAML)
Create an agent configuration by following the instructions at the top of `config/template_config.yaml`. Below is a simplified snippet from the template:

```yaml
persona:
  name: "<agent name>"
  description: |
    <Enter a brief description of the agent.>
  purpose: |
    <Enter the purpose of the agent.>

states:
  example_state_1:
    purpose: |
      <Enter the purpose of this state.>
    output_format: |
      **Example Data:** <states.example_state_1.goals.gather_initial_info.data.initial_info>
    goals:
      example_1_goal:
        goal: |
          <Enter the goal of this state.>
        data:
          example_1_variable: "type <data_type>: <Enter the data description here>"
```

Within each `state` you define:
- **purpose**: A short description of what that state is meant to accomplish.  
- **output_format**: A template describing how the output will be displayed.  
- **goals**: Each goal can contain sub-goals and a data structure.

---

## Usage

1. **Open a Terminal** and navigate to your project directory.
2. **Load the Python environment** (if not already):
   ```bash
   . profile.sh
   ```
3. **Run the agent**:
   ```bash
   python src/main.py <path to your config file>
   ```
4. **Access in your browser**:  
   Go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to interact with your agent.

> **Important**: If you quit the server, make sure to close your browser tab before starting the server again to avoid caching issues.

---

## Databases

The framework uses local databases to store conversation data:

- **SQL Database**: `db/sql/<agent name>.db`
- **Vector Database**: `db/vector/<agent name>.db/`

The vector database is used to store semantic embeddings for long-term memory retrieval, while the SQL database is for structured data, states, and other agent metadata.

---

## Examples

1. **Simple State Configuration**  
   - Check `config/template_config.yaml` for a minimal configuration example.  
   - Copy the file, fill in your `persona`, `states`, `goals`, and run.

2. **Advanced Setup**  
   - Modify default settings and experiment with advanced states, custom data structures, or specialized reasoning agents.

---

## TODO / Roadmap

* **Fix Socratic Agent** – Refine multi-agent dialogue system.  
* **Add Tooling for Agents**  
  - Web search (Google, Wolfram Alpha, etc.)  
  - Python scripting to validate technical answers  
* **Explore Alternative Reasoning Agent Types**  
  - Chain of Thought (CoT), Self-Consistency, Tree of Thought (ToT), ReWOO, ReACT, DERA, etc.  
* **Memory System Improvements**  
  - **Short-term**: Currently the last 10 utterances.  
  - **Long-term**: Use semantic and episodic context stored in a vector DB to refine retrieval.  
* **Multi-user System**  
  - Shared documents or data between multiple users.  
  - Possible SSO integration.  
* **Governance and Security**  
  - [Guardrails](https://github.com/guardrails-ai/guardrails)  
  - Encrypted PII data  
* **External Database Support**  
  - Local storage using SQLite & ChromaDB; potentially other backends in the future.

---

## Contributing

Contributions are welcome! Feel free to open an issue to report bugs or propose new features. If you want to submit a pull request:

1. Fork the repository.
2. Create a new feature branch.
3. Make changes and commit.
4. Open a PR against the `main` branch.

---

## License

This project is released under the [MIT License](LICENSE). Feel free to modify and distribute as you see fit.

---

## Acknowledgments

- Inspired by leading conversational frameworks and modern agentic architectures.
- Big thanks to the open-source community for libraries like [OpenAI](https://github.com/openai), [ChromaDB](https://github.com/chroma-core), and more.

---

**Happy Building!**  
_We look forward to seeing the conversational agents you create with the Stateful Agentic Framework._
