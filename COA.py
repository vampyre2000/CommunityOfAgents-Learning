import gradio as gr
import re
import time
import ollama
import json
import logging
import textwrap
from toolbox.Toolbox import Toolbox
from agent.agent import Agent  # Import the Agent class from the agents module
from agents.agents import AGENT_REBECCA  # Import the agents.py file to access the agent personality details.
from datetime import date, datetime
from typing import List, Dict, Optional, Callable
from tools.Time_Keeper import TimeKeeper
from tools.LLMVersionCheck import get_disruption_dates, get_llm_versions
from tools.System_Status import get_system_metrics
from tools.Browser_Search import browser

# Set the constants for the program
USERNAME = "Vampy"
AGENT_PATH = './agents/'
DATA_CACHE_DIR = "agents"
MODEL = 'phi4'
#MODEL = 'llama3.2'

logging.basicConfig(level=logging.DEBUG)  # Change to INFO or WARNING in production
logger = logging.getLogger(__name__)

# Define the tools list globally
DEFAULT_TOOLS = [TimeKeeper, get_disruption_dates, get_llm_versions, get_system_metrics, browser]

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

def Agent_interface(message: str, history: List[tuple[str, str]]) -> str:
    """
    Processes user commands and messages, routing them to the appropriate agent.
    
    Args:
        message: The user's message or command
        history: The conversation history
        
    Returns:
        The response to the user
    """
    #logger.debug(f"Message: {message}")
    #logger.debug(f"History: {history}")

    # Handle commands (messages starting with !)
    if message.startswith("!"):
        if message == "!agent list":
            return agents.list_agents()
        elif message == "!quit" or message == "!bye":
            return "Goodbye!"
        elif message == "!version":
            return "Version 1.0"
        elif message == "!agent history":
            return agent.show_message_history()
        elif message == "!agent system":
            return agent.show_system_prompt()
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

if __name__ == "__main__":
    # Initialize the default agent with the specified personality and tools
    agent = Agent(AGENT, USERNAME, MODEL, DEFAULT_TOOLS)
    
    # Initialize the community and default agent
    agents = CommunityOfAgents()
    agents.add_agent(agent)

    # Create the Gradio interface
    with gr.Blocks(title="Community of Agents", theme="ocean") as interface:
        gr.Markdown("# Community of Agents")
        gr.Markdown("The Community of Agents (COA) is a program that allows users to interact with multiple AI agents in a community.")
        
        with gr.Row():

            gr.Image(value="./images/agent.jpg",height=300, width=300,scale=0.5)
                #gr.Image(value="./images/agent.jpg", label="Agent Image", height=300, width=300)
            #chatbot = gr.ChatInterface(Agent_interface,type="messages",title="Chat",description="Chat with the agent",scale=7)
            chatbot = gr.ChatInterface(Agent_interface,type="messages")

    interface.launch()