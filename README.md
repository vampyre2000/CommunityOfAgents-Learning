# Community of Agents

Community of Agents is a Python-based project that creates a command-line interactive system where AI agents interact with the user. Each agent has its own personality, maintains a conversation history, and can execute built-in tools (such as fetching the current time) when needed.

## Overview

This project demonstrates how to:
- **Create and Manage AI Agents:** Each agent has a personality, conversation history, and a toolbox of functions (tools) it can use.
- **Integrate Tools:** Agents can use tools (for example, `TimeKeeper`) to answer questions or perform specific tasks when they don't have a direct answer.
- **Interact via a Command Line Interface:** Users can load agents, send messages, view agent details, and check conversation history using simple commands.
- **Maintain a Conversation History:** Agents remember past interactions to provide context for future responses.
- **Handle and Parse JSON Responses:** The system is designed to extract and parse JSON responses even when they are wrapped in markdown formatting.

## Key Features

- **Interactive Chat Interface:** Engage with AI agents in real-time.
- **Toolbox Integration:** Automatically uses tools when needed.
- **Logging and Debugging:** Uses Python’s `logging` module for helpful debug messages.
- **Extensible Design:** Easily add new tools or agent types.
- **Command-Based Control:** Commands to load agents, list available agents, display details, and more.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your-username/CommunityOfAgents.git
   cd CommunityOfAgents

2. **Create a Virtual Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate

3. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt

4. **Usage:**
To start the application, run:
    ```bash
    python COA.py
    You will see a prompt (#>) where you can enter commands.

5. **Available Commands:**
    ```bash
    !agent load 1
    Loads the first agent (e.g., Agent Rebecca).

    !agent list
    Lists all loaded agents.

    !agent details 1
    Displays detailed information about the first agent.

    !agent system
    Shows the current system prompt of the agent.

    !agent history
    Displays the conversation history between you and the agent.

    !version
    Shows the software version.

    !help
    Displays a list of available commands.

    !quit
    Exits the application.

6. **Example Interaction:**
    Load an Agent:

    ```bash
    #> !agent load 1
    Agent Rebecca added.

7.  **Start a Conversation:**
    ```bash
    #> hello
    <Rebecca>: {"tool_choice": "no tool", "tool_input": "Hello there! How can I assist you today  "} ...
8. **Ask a Tool-Based Question:**
    ```bash
    #> what time is it?
    <Rebecca>: {"tool_choice": "TimeKeeper", "tool_input": null} ...

9. **Code Structure:**
    COA.py:
    Main script that contains the command line interface and core logic for agent interactions.

    agents/agents.py:
    Contains agent definitions (e.g., AGENT_REBECCA and AGENT_JOHN).

    tools/time_keeper.py:
    Contains the TimeKeeper function used by agents.

    README.md:
    This file, which outlines the project details and usage.

10. **Contributing:**
    Contributions are welcome! If you have suggestions or improvements, feel free to fork the repository and open a pull request. If you encounter any issues, please open an issue on GitHub.

    License
    This project is licensed under the MIT License.

    Feel free to reach out if you have any questions or need further assistance!

