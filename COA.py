import gradio as gr
import logging
import ollama
import os
import json
from pathlib import Path
from toolbox.Toolbox import Toolbox
from agent.agent import Agent  # Import the Agent class from the agents module
from agents.agents import AGENT_REBECCA  # Import the agents.py file to access the agent personality details.
from datetime import date
from typing import List, Dict, Optional, Tuple, Any, Union
from tools.Time_Keeper import TimeKeeper
from tools.LLMVersionCheck import get_disruption_dates, get_llm_versions
from tools.System_Status import get_system_metrics
from tools.Browser_Search import browser
from tools.List_Images import list_images, change_image
from tools.Weather_Info import get_weather
from tools.Calculator import calculate
from tools.Response_Analyzer import analyze_response

# Application constants
VERSION_INFO = "0.3.1"
USERNAME = "Vampy"
AGENT_PATH = './agents/'
DATA_CACHE_DIR = "agents"
CONFIG_FILE = "config.json"
MODELS = ['cogito:8b', 'gemma3:12b', 'phi4', 'qwen3:0.6b', 'qwen3:8b']
# Define the tools list globally
DEFAULT_TOOLS = [
    TimeKeeper, 
    get_disruption_dates, 
    get_llm_versions, 
    get_system_metrics,
    browser,
    list_images,
    change_image,
    get_weather,
    calculate,
    analyze_response
]
AGENT = AGENT_REBECCA

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Config:
    """
    Manages application configuration with persistence.
    """
    
    def __init__(self, config_file: str = CONFIG_FILE):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default.
        
        Returns:
            Dictionary containing configuration
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                default_config = {
                    "username": USERNAME,
                    "default_model": MODELS[4],
                    "launch_gui": True,
                    "max_history": 1000,
                    "temperature": 0.6,
                    "theme": "ocean"
                }
                self._save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Return default config on error
            return {
                "username": USERNAME,
                "default_model": MODELS[4],
                "launch_gui": True,
                "max_history": 1000,
                "temperature": 0.6,
                "theme": "ocean"
            }
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value and save.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        self._save_config(self.config)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary containing all configuration
        """
        return self.config.copy()


class CommunityOfAgents:
    """
    Manages a collection of Agent instances.
    """

    def __init__(self):
        """
        Initialize an empty community of agents.
        """
        self.agents: List[Agent] = []
        self.config = Config()

    def list_agents(self) -> str:
        """
        Lists all agents in the community.
        
        Returns:
            String listing all available agents
        """

        if self.agents:
            return "\n".join([f"Agent available: {agent.first_name} {agent.last_name}" for agent in self.agents])
        else:
            return "There are no local agents loaded."

    def add_agent(self, agent) -> str:
        """
        Adds an agent to the community.
        
        Args:
            agent: The Agent instance to add
            
        Returns:
            Confirmation message
        """

        self.agents.append(agent)
        return f"Agent {agent.first_name} {agent.last_name} added."

    def remove_agent(self, agent) -> str:
        """
        Removes an agent from the community.
        
        Args:
            agent: The Agent instance to remove
            
        Returns:
            Confirmation message
        """

        self.agents.remove(agent)
        return f"Agent {agent.first_name} {agent.last_name} removed."

    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        Retrieves an agent by its ID.
        
        Args:
            agent_id: The ID of the agent to retrieve
            
        Returns:
            The Agent instance or None if not found
        """
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        return None
    
    def get_agent_by_name(self, first_name: str) -> Optional[Agent]:
        """
        Retrieves an agent by its first name.
        
        Args:
            first_name: The first name of the agent to retrieve
            
        Returns:
            The Agent instance or None if not found
        """
        for agent in self.agents:
            if agent.first_name.lower() == first_name.lower():
                return agent
        return None


class Interface:
    """
    Interface class for the Community of Agents.
    
    This class provides methods to interact with the agents and manage the community.
    """

    def __init__(self, community: CommunityOfAgents, agent: Agent):
        """
        Initializes the interface with a given agent and community.
        
        Args:
            community: The CommunityOfAgents instance
            agent: The Agent instance to use
        """
        self.community = community
        self.agent = agent
        self.config = community.config
        self.launch_gui = self.config.get("launch_gui", True)
        self.console_history: List[Dict[str, str]] = []

    def command_interface(self, message: str, history: List[Dict[str, str]]) -> str:
        """
        Process command messages (starting with !) and return appropriate responses.
        
        Args:
            message: User input message
            history: Chat history (list of dictionaries with 'role' and 'content' keys)
            
        Returns:
            Response to the command
        """
        try:
            # Handle commands (messages starting with !)
            if message == "!agent list":
                return self.community.list_agents()
            elif message == "!quit" or message == "!bye":
                return "Goodbye!"
            elif message == "!version":
                return self.show_version()
            elif message == "!agent details":
                return self.agent.show_agent_details()
            elif message == "!agent history":
                return self.agent.conversation_history.show_history()
            elif message == "!agent history clear":
                # Check if the agent has a clear_message_history method
                if hasattr(self.agent.conversation_history, 'clear_message_history'):
                    return self.agent.conversation_history.clear_message_history()
                else:
                    # If not, create a new empty message history
                    self.agent.conversation_history.messages = []
                    return "Conversation history cleared."
            elif message == "!agent system":
                return self.agent.show_system_prompt()
            elif message == "!agent tools":
                return self.agent.toolbox.get_tool_list()
            elif message == "!agent model":
                return self.show_model()
            elif message == "!config":
                return self.show_config()
            elif message == "!help":
                return """Available Commands:
                !agent list    - List all available agents
                !agent details - Show details of the current agent
                !agent history - Show conversation history
                !agent history clear  - Clear conversation history
                !agent system  - Show system prompt
                !agent tools   - List all available tools
                !agent model   - Show current model information
                !config        - Show current configuration
                !version       - Show version
                !quit or !bye  - Exit the application
                !help          - Show this help message"""
            else:
                return f"Unknown command: {message}. Type !help for a list of commands."
        except Exception as e:
            logger.error(f"Error in command interface: {str(e)}")
            return f"Error processing command: {str(e)}"
    
    def cli_interface(self) -> None:
        """
        Starts the command-line interface for user interaction.
        
        This method handles user input and displays responses from the agent.
        """
        self.show_cli_welcome()
        
        # Main loop for user interaction
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                    
                if user_input.lower() in ["!quit", "!bye"]:
                    print("\nGoodbye!")
                    break
                
                # Process the input
                if user_input.startswith("!"):
                    # Handle commands
                    response = self.command_interface(user_input, self.console_history)
                    print("\nSystem:")
                    print(self.format_cli_output(response))
                else:
                    # Handle regular messages
                    response = self.agent.agent_response(user_input)
                    print("\nAgent:")
                    print(self.format_cli_output(response))
                    
                # Update console history
                self.console_history.append({"role": "user", "content": user_input})
                self.console_history.append({"role": "assistant", "content": response})
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error in CLI interface: {str(e)}")
                print(f"\nAn error occurred: {str(e)}")


    def format_cli_output(self, text: str, width: int = 120) -> str:
        """
        Formats text for CLI display with proper wrapping, indentation, and highlighting.
        
        Args:
            text: Text to format
            width: Maximum line width
        
        Returns:
            str: Formatted text
        """
        import textwrap
        
        # Check for self-correction indicator
        is_correction = "(Self-correction:" in text
        
        # Extract agent name prefix if present
        agent_prefix = ""
        if text.startswith(f"{self.agent.first_name}>:"):
            parts = text.split(":", 1)
            if len(parts) > 1:
                agent_prefix = parts[0] + ":"
                text = parts[1].strip()

        # Handle multiline responses
        if "\n" in text:
            lines = text.split("\n")
            wrapped_lines = []
            
            # Add agent prefix to first line if present
            if agent_prefix and lines:
                first_line = lines[0]
                wrapped = textwrap.fill(first_line, width=width, initial_indent="    ", 
                                    subsequent_indent="    ")
                wrapped_lines.append(f"{agent_prefix} {wrapped.lstrip()}")
                lines = lines[1:]
            
            # Process remaining lines
            for line in lines:
                if line.strip():  # Skip empty lines
                    # Highlight self-correction notes
                    if "(Self-correction:" in line:
                        wrapped = textwrap.fill(line, width=width, initial_indent="    ", 
                                            subsequent_indent="    ")
                        # Use terminal color codes for highlighting (yellow text)
                        wrapped_lines.append(f"\033[33m{wrapped}\033[0m")
                    else:
                        wrapped = textwrap.fill(line, width=width, initial_indent="    ", 
                                            subsequent_indent="    ")
                        wrapped_lines.append(wrapped)
                else:
                    wrapped_lines.append("")  # Preserve empty lines
                    
            return "\n".join(wrapped_lines)

        # Handle single line responses
        if agent_prefix:
            indented_text = textwrap.fill(text, width=width, initial_indent="    ", 
                                subsequent_indent="    ")
            return f"{agent_prefix} {indented_text.lstrip()}"
        else:
            return textwrap.fill(text, width=width, initial_indent="    ", 
                                subsequent_indent="    ")


    def show_cli_welcome(self) -> None:
        """Display welcome message with ASCII art."""
        ascii_art = rf"""
         ______     ______     ______
        /\  ___\   /\  __ \   /\  __ \
        \ \ \____  \ \ \_\ \  \ \  __ \
         \ \_____\  \ \_____\  \ \_\ \_\
          \/_____/   \/_____/   \/_/\/_/

        Community Of Agents v{VERSION_INFO}
        Powered by Ollama
        Date: {date.today().strftime('%Y-%m-%d')}
        Current Agent: {self.agent.first_name}
        """

        print(ascii_art)
        print("=" * 60)
        print("Type !help for available commands")
        print("=" * 60 + "\n")


    def gradio_interface(self) -> gr.Blocks:
        """
        Creates and configures the Gradio interface.

        Returns:
            gr.Blocks: Configured Gradio interface
        """
        theme = self.config.get("theme", "ocean")
        
        with gr.Blocks(title="Community of Agents", theme=theme) as interface:
            gr.Markdown(f"# Community of Agents v{VERSION_INFO}")
            gr.Markdown("The Community of Agents (COA) is a program that allows users to interact with multiple AI agents in a community.")

            with gr.Row():
                # Left column for the image and agent info
                with gr.Column(scale=1):
                    agent_img = gr.Image(value=f"./images/{self.agent.first_name}.jpg", 
                                        height=400, width=300, label="Agent Avatar")
                    
                    with gr.Accordion("Agent Information", open=True):
                        agent_info = gr.Markdown(f"""
                        **Name:** {self.agent.first_name} {self.agent.last_name}
                        **Age:** {self.agent.age}
                        **Location:** {self.agent.city}, {self.agent.country}
                        """)
                    
                    with gr.Accordion("Agent tools", open=False):
                        agent_info = gr.Markdown(f"""
                        **Tools:** {self.agent.tool_descriptions}
                        """)

                    with gr.Accordion("Available Commands", open=False):
                        gr.Markdown("""
                        - !agent list - List all available agents
                        - !agent details - Show details of the current agent
                        - !agent history - Show conversation history
                        - !agent history clear - Clear conversation history
                        - !agent system - Show system prompt
                        - !agent tools - List all available tools
                        - !agent model - Show current model information
                        - !config - Show current configuration
                        - !version - Show version
                        - !help - Show this help message
                        """)

                # Right column for chat components
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(type="messages",height=600, show_label=False, container=True)
                    
                    with gr.Row():
                        msg = gr.Textbox(placeholder="Type a message...", show_label=False, container=True)
                    
                    with gr.Row():
                        submit = gr.Button("Send", variant="primary")
                        clear = gr.Button("Clear Chat")
                        
                    with gr.Row():
                        model_dropdown = gr.Dropdown(
                            choices=MODELS,
                            value=self.agent.model,
                            label="Model"
                        )
                        temperature_slider = gr.Slider(
                            minimum=0.1, 
                            maximum=1.0, 
                            value=self.agent.temperature,
                            step=0.1,
                            label="Temperature"
                        )

            # Set up event handlers
            submit.click(fn=self.respond, inputs=[msg, chatbot], outputs=[msg, chatbot])
            msg.submit(fn=self.respond, inputs=[msg, chatbot], outputs=[msg, chatbot])
            clear.click(lambda: None, None, chatbot, queue=False)
            
            # Model and temperature change handlers
            def update_model(model):
                self.agent.model = model
                self.config.set("default_model", model)
                return f"Model changed to {model}"
                
            def update_temperature(temp):
                self.agent.temperature = temp
                self.config.set("temperature", temp)
                return f"Temperature changed to {temp}"
                
            model_dropdown.change(fn=update_model, inputs=[model_dropdown], outputs=[])
            temperature_slider.change(fn=update_temperature, inputs=[temperature_slider], outputs=[])
        
        return interface

    def start_interface(self) -> None:
        """
        Starts the Gradio or CLI interface for user interaction.   
        """
        # Create the appropriate interface
        if self.launch_gui:
            # Launch with GUI with custom size
            interface = self.gradio_interface()
            interface.launch(height=1440, width=1200)
        else:
            # Launch without GUI (for CLI or other purposes)
            self.cli_interface()

    def respond(self, message: str, history: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
        """
        Handle chat interactions and return updated message and history.

        Args:
            message: Current message from user
            history: Chat history

        Returns:
            tuple: (cleared message, updated history)
        """
        try:
            if not message:
                return "", history
                
            if message.startswith("!"):
                # Handle commands
                response = self.command_interface(message, history)
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return "", history
            else:
                # Handle regular chat messages
                response = self.agent.agent_response(message)
                
                # Check if response contains an image change request
                if "change_image" in response and ".jpg" in response:
                    # Extract image name from response
                    import re
                    match = re.search(r'([A-Za-z0-9_]+\.jpg)', response)
                    if match:
                        image_name = match.group(1)
                        # Update the image in the UI (this will be handled by the frontend)
                        logger.info(f"Image change requested: {image_name}")
                
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": response})
                return "", history
        except Exception as e:
            logger.error(f"Error in respond: {str(e)}")
            error_msg = f"Error processing your request: {str(e)}"
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_msg})
            return "", history

    def show_version(self) -> str:
        """
        Displays the current version of the program.
        
        Returns:
            String containing the version information
        """
        return f"Community of Agents Version: {VERSION_INFO}"

    def show_model(self) -> str:
        """
        Displays the model information.

        Returns:
            String containing the model information
        """
        try:
            return str(ollama.show(self.agent.model))
        except Exception as e:
            logger.error(f"Error showing model: {str(e)}")
            return f"Error retrieving model information: {str(e)}"
            
    def show_config(self) -> str:
        """
        Displays the current configuration.
        
        Returns:
            String containing the configuration information
        """
        config = self.config.get_all()
        return "\n".join([f"{key}: {value}" for key, value in config.items()])


if __name__== "__main__":
    try:
        # Initialize the community of agents
        community = CommunityOfAgents()
        
        # Get configuration
        config = community.config
        launch_gui = config.get("launch_gui", True)
        default_model = config.get("default_model", MODELS[4])
        temperature = config.get("temperature", 0.6)
        
        # Initialize the default agent with the specified personality and tools
        agent = Agent(AGENT, USERNAME, default_model, DEFAULT_TOOLS, temperature=temperature)
        
        # Add the agent to the community
        community.add_agent(agent)
        
        # Initialize the interface
        agent_interface = Interface(community, agent)
        
        # Start the interface
        agent_interface.start_interface()
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        print(f"Error starting application: {str(e)}")
