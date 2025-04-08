import gradio as gr
import logging
from toolbox.Toolbox import Toolbox
from agent.agent import Agent  # Import the Agent class from the agents module
from agents.agents import AGENT_REBECCA  # Import the agents.py file to access the agent personality details.
from datetime import date, datetime
from typing import List, Dict, Optional, Callable
from tools.Time_Keeper import TimeKeeper
from tools.LLMVersionCheck import get_disruption_dates, get_llm_versions
from tools.System_Status import get_system_metrics

console_history = []

VERSION_INFO="0.1.0"
# Set the constants for the program
USERNAME = "Vampy"
AGENT_PATH = './agents/'
DATA_CACHE_DIR = "agents"
MODEL = 'phi4'
#MODEL = 'gemma3'

logging.basicConfig(level=logging.WARNING)  # Change to INFO or WARNING in production
logger = logging.getLogger(__name__)

# Define the tools list globally
DEFAULT_TOOLS = [TimeKeeper, get_disruption_dates, get_llm_versions, get_system_metrics]

# Parameters for the Rebecca Agent personality
AGENT=AGENT_REBECCA

class CommunityOfAgents:
    """
    Manages a collection of Agent instances.
    """
    
    def __init__(self):
        """Initialize an empty community of agents."""
        self.agents: list[Agent] = []

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

def show_version() -> str:
    """
    Displays the current version of the program.
    
    Returns:
        String containing the version information
    """
    return f"Community of Agents Version: {VERSION_INFO}"

def Agent_interface(message: str, history: List[tuple[str, str]]) -> str:

    # Handle commands (messages starting with !)
    if message.startswith("!"):
        if message == "!agent list":
            return agents.list_agents()
        elif message == "!quit" or message == "!bye":
            return "Goodbye!"
        elif message == "!version":
            return show_version()
        elif message == "!agent details":
            return agent.show_agent_details()
        elif message == "!agent history":
            return agent.show_message_history()
        elif message == "!agent system":
            return agent.show_system_prompt()
        elif message == "!agent system":
            return agent.show_agent_tools()
        elif message == "!help":
            return """Available Commands:
            !agent list    - List all available agents
            !agent details - Show details of the current agent
            !agent history - Show conversation history
            !agent system  - Show system prompt
            !agent tools   - List all available tools
            !version       - Show version
            !quit or !bye  - Exit the application
            !help          - Show this help message"""
        else:
            return f"Unknown command: {message}. Type !help for a list of commands."
        
    # Handle regular messages
    else:
        if agent:
            return agent.respond(message)
        else:
            return "No agent loaded to respond."

def create_interface(agent, respond_fn) -> gr.Blocks:
    """
    Creates and configures the Gradio interface.
    
    Args:
        agent: The Agent instance to use
        respond_fn: The function to handle responses
        
    Returns:
        gr.Blocks: Configured Gradio interface
    """
    with gr.Blocks(title="Community of Agents", theme="ocean") as interface:
        gr.Markdown("# Community of Agents")
        gr.Markdown("The Community of Agents (COA) is a program that allows users to interact with multiple AI agents in a community.")
        
        with gr.Row():
            # Left column for the image
            with gr.Column(scale=1):
                dynamic_img = gr.Image(
                    value="./images/agent.jpg", 
                    height=300, 
                    width=300, 
                    label="Agent Avatar"
                )
            
            # Right column for chat components
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    height=750,
                    show_label=False,
                    container=True,
                    bubble_full_width=False
                )
                msg = gr.Textbox(
                    placeholder="Type a message...",
                    show_label=False,
                    container=True
                )
                with gr.Row():
                    submit = gr.Button("Send", variant="primary")
                    clear = gr.Button("Clear")

        # Set up event handlers
        submit.click(
            fn=respond_fn,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
        )
        msg.submit(
            fn=respond_fn,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
        )
        clear.click(lambda: None, None, chatbot, queue=False)
        
    return interface

def format_cli_output(text: str, width: int = 120) -> str:
        """
        Formats text for CLI display with proper wrapping and indentation.
        
        Args:
            text: Text to format
            width: Maximum line width
        
        Returns:
            str: Formatted text
        """
        import textwrap
        
        # Handle multiline responses
        if "\n" in text:
            lines = text.split("\n")
            wrapped_lines = []
            for line in lines:
                if line.strip():  # Skip empty lines
                    wrapped = textwrap.fill(line, width=width, initial_indent="    ", 
                                        subsequent_indent="    ")
                    wrapped_lines.append(wrapped)
            return "\n".join(wrapped_lines)
        
        # Handle single line responses
        return textwrap.fill(text, width=width, initial_indent="    ", 
                            subsequent_indent="    ")

def respond(message, history):
        """
        Handle chat interactions and return updated message and history.
    
        Args:
            message: Current message from user
            history: Chat history
        
        Returns:
            tuple: (cleared message, updated history)
        """
        try:
            if message.startswith("!"):
                # Handle commands
                response = Agent_interface(message, history)
                history.append((message, response))
                return "", history
                # Check if response contains an image change request
            else:
                # Handle regular chat messages
                response = agent.respond(message)
                history.append((message, response))
                return "", history
        except Exception as e:
            logger.error(f"Error in respond: {str(e)}")
            return "", history   

def show_cli_welcome():
    """Display welcome message with ASCII art."""
    ascii_art = f"""
     ______     ______     ______    
    /\  ___\   /\  __ \   /\  __ \   
    \ \ \____  \ \ \_\ \  \ \  __ \  
     \ \_____\  \ \_____\  \ \_\ \_\ 
      \/_____/   \/_____/   \/_/\/_/ 
                                     
    Community Of Agents v{VERSION_INFO}
    Powered by Ollama
    Date: {date.today().strftime('%Y-%m-%d')}
    """
    
    print(ascii_art)
    print("=" * 50)
    print("Type !help for available commands")
    print("=" * 50 + "\n")



if __name__ == "__main__":

    #Choose to launch the GUI or not
    launch_gui = True

    # Initialize the default agent with the specified personality and tools
    agent = Agent(AGENT, USERNAME, MODEL, DEFAULT_TOOLS)
    
    # Initialize the community and default agent
    agents = CommunityOfAgents()
    agents.add_agent(agent)
    
    if launch_gui:#
        #  Launch with GUI with custom size
        interface = create_interface(agent, respond)
        interface.launch(
            height=1000,
            width=1200
        )
    else:
        # Launch without GUI (for CLI or other purposes)
        show_cli_welcome()
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ["!quit", "!bye"]:
                    print("\nGoodbye!")
                    break
                    
                response = respond(user_input, console_history)
                if isinstance(response, tuple):
                    # Handle response from respond() function
                    _, history = response
                    last_response = history[-1][1] if history else "No response"
                    print("\nAgent:")
                    print(format_cli_output(last_response))
                else:
                    # Handle direct string response
                    print("\nAgent:")
                    print(format_cli_output(response))
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error: {str(e)}")
                print("\nAn error occurred. Please try again.")
    