# Community of Agents

Community of Agents is a Python-based project that creates a web-based interactive system where AI agents interact with the user. Each agent has its own personality, maintains a conversation history, and can execute built-in tools when needed.

## Major Updates in 2025 Version

- **Migrated to Gradio Interface:** Replaced command-line interface with a modern web-based UI
- **Updated the Terminal version:** Re-added the command-line interface
- **Modular Architecture:**         Code split into logical classes and modules
- **Enhanced Toolbox System:**      New modular toolbox with dynamic tool management
- **Improved Error Handling:**      Better error catching and logging throughout
- **Web Interface Features:**       Added visual elements including agent avatar

## Architecture Overview

The project now uses a class-based architecture with these main components:

- **Agent Class:** Manages individual agent behavior and responses
- **Toolbox Class:** Handles tool registration and execution
- **CommunityOfAgents Class:** Manages multiple agents
- **Gradio Interface:** Provides web-based user interaction

## Installation

1. **Clone the Repository:**
```bash
git clone https://github.com/your-username/CommunityOfAgents.git
cd CommunityOfAgents
```

2. **Create a Virtual Environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

4. **Manual Install Dependencies:**
```bash
pip install -r gradio
pip install -r bs4
pip install -r ollama
pip install -r psutil
pip install -r pysensors
```


## Usage GUI

To start the web interface:
```bash
python COA.py
```

## Usage

To start the cli text interface:
Change the launch_gui = False in the file COA.py 
```bash
python COA.py
```


Your browser will open to `http://localhost:7860` with the chat interface.

## Available Commands

All previous commands work in the chat interface:

```
!agent list    - List all available agents
!agent details - Show details of the current agent
!agent history - Show conversation history
!agent system  - Show system prompt
!agent tools   - List all available tools
!version       - Show version
!quit or !bye  - Exit the application
!help         - Show this help message
```

## Example Interactions

1. **Using Tools:**
```
You: what time is it?
Rebecca>: Let me check that for you with my TimeKeeper tool.
[Tool Output: 2025-03-22 14:35:22]
Rebecca>: It's currently 14:35. Need anything else, chummer?
```

2. **System Status:**
```
You: check system status
Rebecca>: Let me run a quick diagnostic with my system metrics tool.
[Tool Output: CPU: 45%, Memory: 8.2GB/16GB...]
Rebecca>: Your system's running smooth - CPU's at 45% and you've got plenty of memory left.
```

3. **Browser Search:**
```
You: search for "latest AI news"
Rebecca>: Opening your browser to check that out for you.
[Browser opens with Google search]
```

## Code Structure

```
CommunityOfAgents/
├── agent/
│   └── agent.py           # Agent class definition
├── agents/
│   └── agents.py          # Contains the agent personalities
├── images/
│   └── agents.jpg         # Contains the images for the agent personalities
├── tools/
│   ├── Time_Keeper.py     # Time-related tools
│   ├── System_Status.py   # System monitoring tools
│   └── Browser_Search.py  # Web search tool
│   └── LLMVersionCheck.py # AI tools Web search tool
├── toolbox/
│   └── Toolbox.py         # Toolbox class definition
├── COA.py                 # Main application
└── README.md
└── requirements.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
