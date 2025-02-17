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
8. [TODO / Roadmap](#todo--roadmap)
9. [Contributing](#contributing)
10. [License](#license)
11. [Acknowledgments](#acknowledgments)
12. [Contributors](#contributors)

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

Although you can manually edit the YAML files to define your agent, one of the **fastest and most flexible** ways to create or update a configuration is by using a Large Language Model (LLM). You can use any generative model (e.g., OpenAI, Anthropic, Gemini, etc.) to quickly produce a structured configuration that suits your agent’s specific role and purpose.

### 1. Use an LLM Prompt to Generate a Configuration

Copy and paste the prompt below along with the `config/template_config.yaml` file into your preferred LLM interface, replacing the placeholders (`<role>`, `<purpose>`) and adding additional details as needed to align with your agent’s objectives.

```text
# Prompt for generating a real world Stateful Agent Framework configuration:
---------------------------------------------------------------------------------
You are a <role> with the purpose of <purpose>.

Please first investigate and create a plan for generating a real world Stateful Agentic Framework configuration 
using the role that you have declared. Generate as many states as required that a professional in this space 
would apply to a real situation. Also generate the HUD and any other parts of the configuration to ensure that 
this agent config includes all relevant information and design to achieve your purpose.
Use state names that reflect their purpose.

<Research and include any other details relevant to the agent's role and purpose here.>

<Paste config/template_config.yaml here>
---------------------------------------------------------------------------------
```

When you submit this prompt, the LLM will provide a YAML configuration that you can then copy into your project. Adjust or refine any of the generated fields as needed for your application.

### 2. Validate, Refine, and Fine-Tune

After generating your initial YAML configuration using an LLM, it’s critical to **validate**, **refine**, and **fine-tune** it to ensure your agent behaves as intended. Here’s what we recommend:

1. **Review the Generated Configuration**  
   - Check that each state aligns with your conversation flow, goals, and overall purpose.  
   - Ensure the persona and data structures meet your use case requirements.
   - Spend time researching the role, methodologies, and domain-specific constraints with an LLM to generate comprehensive, detailed content for your agent. This ensures each state and goal is deeply informed by best practices, relevant regulations, real-world scenarios, and user needs—ultimately leading to more accurate and engaging interactions.
  
2. **Update or Remove Unnecessary Data**  
   - The LLM may provide extra states or data fields. Feel free to delete or rename them as needed.  
   - Simplify or elaborate on any text values (purpose, goals, data descriptions, etc.) to better fit your agent’s role.

3. **Iterate & Test**  
   - Run the framework with your updated configuration and observe its output.  
   - Experiment with different phrasing and formatting to see how the agent’s responses change.  
   - We highly recommend versioning your configuration (e.g., via Git) so you can easily revert to a working setup if necessary.
   - **Important:** If you modify states and their data structures, the database might go out of sync. Due to the experimental nature of this framework, the only workaround is to remove the databases and start over. Refer to the [Databases](#databases) section for details on where your data is stored.     

4. **Continue Fine-Tuning**  
   - As you refine the YAML, adjusting text values in the persona, states, goals, and data structures can significantly alter the agent’s behavior.  
   - Keep iterating until you find a setup that aligns perfectly with your objectives.  
   - For large or collaborative projects, consider storing your configuration in a shared repository so the entire team can review and propose improvements.

5. **Share Feedback & Contribute**  
   - If you find new patterns or have ideas to improve the core architecture, we’d love your input!  
   - Feel free to open an **issue** or submit a **pull request** to this repository with your suggestions, bug reports, or enhancements.  
   - Your contributions help the community evolve the framework and ensure that future releases stay robust and feature-rich.

By taking the time to validate, refine, and fine-tune your configuration, you’ll craft an agent that is both **highly functional** and **tailored** to your unique needs—all while helping to improve the project for everyone.

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

## TODO / Roadmap

* **Fix Socratic Agent** – Refine multi-agent dialogue system.  
* **Add Tooling for Agents**  
  - Web search (Google, Wolfram Alpha, etc.)  
  - Python scripting to validate technical answers  
* **Explore Alternative Reasoning Agent Types**  
  - Chain of Thought (CoT), Self-Consistency, Tree of Thought (ToT), ReWOO, ReACT, DERA, etc.  
* **Memory System Improvements**  
  - **Short-term**: Currently the last 10 utterances.  
  - **Long-term**: Currently genreates semantic and episodic topics from utterance hisotry and stored in a vector DB to refine retrieval.
* **Multi-user System**  
  - Share data between multiple users.  
  - SSO integration.  
* **Governance and Security**  
  - [Guardrails](https://github.com/guardrails-ai/guardrails)  
  - Encrypted PII data  
* **External Database Support**  
  - Currently supoort local storage only using SQLite & ChromaDB

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

## Contributors

This project is developed by **Waterbear Networks Inc**, co-owned by **Kevin Lindsay** and **Karen Smecher**:

- **Kevin Lindsay** – Principal Engineer and original author of the codebase.
- **Karen Smecher** – Manages social presence, community building, and contributes to strategic direction.

For questions or contributions, please open an issue or submit a pull request.

---

**Happy Building!**  
_We look forward to seeing the conversational agents you create with the Stateful Agentic Framework._
