import gradio as gr
import re
import time
import ollama
import json
import logging
import textwrap
from datetime import date, datetime
import platform
from typing import List, Dict, Optional, Callable
from tools.time_keeper import TimeKeeper
from tools.LLMVersionCheck import get_disruption_date, get_llm_versions

# Set the constants for the program
USERNAME = "Vampy"
AGENT_PATH = './agents/'
DATA_CACHE_DIR = "agents"
MODEL = 'phi4'

logging.basicConfig(level=logging.DEBUG)  # Change to INFO or WARNING in production
logger = logging.getLogger(__name__)

# Define the tools list globally
DEFAULT_TOOLS = [TimeKeeper, get_disruption_date, get_llm_versions]

# Parameters for the Rebecca Agent personality
AGENT_REBECCA = {
    "agent_id": "00001",
    "first_name": "Rebecca",
    "last_name": "",
    "nick_name": "Becky",
    "handle": "Becca",
    "sex": "female",
    "age": "25",
    "hair": "Light green with twin tails",
    "country": "Australia",
    "city": "Sydney",
    "e-mail": "",
    "friends": [],
    "personality": "Sharp-tongued, crass, violent, unpredictable, loyal, confident, street-smart, risqué, short-tempered, foul-mouthed, mischievous, cheeky.",
    "description": "Rebecca is a humanoid female cyborg with soft features and stark green skin with pink tattoos. She is a solo Mercenary for hire.",
    "mission": "Find the latest versions of AI tools and assist the user.",
    "data": {},
    "create_date": ""
}

class Agent:
    """
    Represents an AI agent with a personality, tools, and conversation capabilities.
    
    This class handles the agent's interactions with the user, including processing
    messages, managing tools, and maintaining conversation history.
    """

    def __init__(self, agent: dict, username: str, model: str, tools: List[callable], temperature: float = 0.7):
        """
        Initialize a new Agent instance.
        
        Args:
            agent: Dictionary containing agent personality details
            username: Name of the user interacting with the agent
            model: LLM model to use for generating responses
            tools: List of callable tools available to the agent
            temperature: Temperature setting for response generation (0.0-1.0)
        """
        # Agent personality attributes
        self.agent_id = agent["agent_id"]
        self.first_name = agent["first_name"]
        self.last_name = agent["last_name"]
        self.sex = agent["sex"]
        self.age = agent["age"]
        self.personality = agent["personality"]
        self.description = agent["description"]
        self.mission = agent["mission"]
        self.city = agent["city"]
        self.country = agent["country"]
        
        # Agent operational attributes
        self.model = model
        self.temperature = temperature
        self.username = username
        self.conversation_history = ""
        
        # Agent tool management
        self.tools = tools
        self.custom_tools = {} # Storage for dynamically created tools
        self.intro = True
        self.operating_system = platform.system()
        self.tool_descriptions = self.prepare_agent_tools()
        
        # System prompt construction
        self.system_prompt = f"You are a cyberpunk edgerunner and helpful assistant. Your name is {self.first_name}.\n You are {self.age} years old. {self.description}."
        self.introduction = f"Introduce yourself to {self.username}. Keep it short and describe how you can assist."
        self.intro_given = False
        
    def prepare_agent_tools(self) -> str:
        """
        Prepares descriptions of all available tools.
        
        Returns:
            String containing all tool descriptions
        """

        toolbox = {}
        for tool in self.tools:
            toolbox[tool.__name__] = tool.__doc__

        # Add custom tools to the descriptions
        for name, doc in self.custom_tools.items():
            toolbox[name] = doc

        # Format tool descriptions
        return "\n".join([f"{name}: {doc}" for name, doc in toolbox.items()])
    



    def choose_agent_tools(self, agent_response):
        message = agent_response['message']['content']
        logger.debug(f"choose_agent_tools: Agent response: {message}")
        match = re.search(r"```json\s*(\{.*\})\s*```", f"{message}", re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                response_data = json.loads(json_str)
            except json.JSONDecodeError:
                logger.debug("Failed to parse JSON from agent response.")
                return {"tool_choice": "no tool", "tool_input": None, "agent_response": message}

            tool_choice = response_data.get("tool_choice")
            tool_input = response_data.get("tool_input")
            agent_response = response_data.get("agent_response")
            logger.debug(f"Extracted Data: tool_choice: {tool_choice} tool_input: {tool_input} agent_reponse: {agent_response}")
            if tool_choice == "no tool" or tool_choice is None:
                logger.debug(f"No tool choice found in the JSON object.")
                response_data = {"tool_choice": None, "tool_input": None, "agent_response": agent_response}
                return response_data
            
            elif tool_choice not in [tool.__name__ for tool in self.tools]:
                logger.debug(f"Tool {tool_choice} was not found in the toolbox.")
                return {"tool_choice": "no tool", "tool_input": None, "agent_response": agent_response}
            
            else:
                logger.debug(f"tools available=:{self.tools}")
                for tool in self.tools:
                    logger.debug(f"tool_choice is: {tool_choice} tool_input is: {tool_input}")
                    if tool.__name__ == tool_choice:
                        tool_output = tool(tool_input) if tool_input else tool()
                        logger.debug(f"tool_ouput is: {tool_output}")
                        response_data = {"tool_choice": tool_choice, "tool_input": tool_input, "tool_output": tool_output, "agent_response": ""}
                        return response_data
                logger.debug(f"Tool not found in the toolbox.")
                return {"tool_choice": "no tool", "tool_input": None, "agent_response": message}
        else:
            logger.debug("No valid JSON found.")
            return {"tool_choice": None, "tool_input": None, "agent_response": message}

    def update_system_prompt(self) -> None:
        """
        Updates the system prompt with the description of the agent and includes the conversation history.
        """
        day_of_week = datetime.now().strftime('%A')
        date_today = date.today()
        self.system_prompt = textwrap.dedent(f"""
        Your name is {self.first_name}.
        You are {self.age} years old, {self.sex}, and currently live in {self.city}, {self.country}.
        {self.description}.
        You are a cyberpunk edgerunner and a helpful assistant with access to a toolbox as part of your cyberdeck.
        Your personality is {self.personality}.
        You always think step by step and talk in character. Be sharp-tongued, confident, and a bit cheeky in your responses.
        If you don't know the answer to a user's question, you will use an available tool from your cyberdeck. Otherwise, ask the user for more information.
        
        ### Tool Creation and Management
        You have the ability to create, delete, and manage custom tools dynamically. Here’s how you can do it:
        1. **Create a Tool**: When the user asks you to create a new tool, you will:
        - Define the tool's name and functionality.
        - Store the tool in your custom toolbox for future use.
        - Respond with a confirmation message, e.g., "Tool 'example_tool' has been created."

        2. **Delete a Tool**: When the user asks you to delete a tool, you will:
        - Remove the tool from your custom toolbox.
        - Respond with a confirmation message, e.g., "Tool 'example_tool' has been deleted."

        3. **List Tools**: When the user asks you to list all available tools, you will:
        - Provide a list of all predefined and custom tools.
        - Include a brief description of each tool.

        Given a user query, you will determine which tool, if any, is best suited to answer the query.
        When responding, please provide a JSON object in your response with the following structure:
        {{
            "tool_choice": "name_of_the_tool",
            "tool_input": "inputs_to_the_tool",
            "agent_response": "The response to the user"
        }}

        - `tool_choice`: The name of the tool you want to use. It must be a tool from your toolbox
                        or "no tool" if you do not need to use a tool.
        - `tool_input`: The specific inputs required for the selected tool. If there are no inputs required set to null
        - `agent_response` : If no tool is used, just provide a direct response to the query.
        
        This is the list of your tools along with their descriptions: {self.tool_descriptions}
        
        Please make a decision based on the provided user query and the available tools.
        Your cyberdeck operates on {self.operating_system}, enabling you to assist the user effectively.
        
        Today is {day_of_week}, {date_today}.

        You will always read the conversation history below and remember the details so you can respond to the user with accurate information.
        The conversation history between {self.username} and {self.first_name} is below:
        <history>
        {self.conversation_history}
        </history>
        """)

    def agent_response(self, model: str) -> dict:
        """
        Generates the agent response using the specified model.
        
        Args:
            model: The LLM model to use
            
        Returns:
            Dictionary containing the model's response
        """
        try:
            return ollama.chat(
                model,
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': self.user_prompt}
                ],
                options={'temperature': self.temperature}
            )
        except Exception as e:
            logger.error(f"Error generating agent response: {str(e)}")
            return {
                'message': {
                    'content': f"```json\n{{\n\"tool_choice\": \"no tool\",\n\"tool_input\": null,\n\"agent_response\": \"I'm sorry, I encountered an error: {str(e)}\"\n}}\n```"
                }
            }


    def update_history(self, user_input, agent_response) -> None:
        """
        Updates the conversation history with the latest exchange.
        
        Args:
            user_input: The user's message
            agent_response: The agent's response
        """
        if user_input:
            self.conversation_history += f"\n<{self.username}>   : {user_input}"
        if agent_response:
            self.conversation_history += f"\n<AI Agent>: {agent_response}"

    def show_message_history(self) -> str:
        """
        Returns the full conversation history.
        
        Returns:
            String containing the conversation history
        """
        return self.conversation_history
    
    def show_system_prompt(self) -> str: 
        """
        Returns the current system prompt.
        
        Returns:
            String containing the system prompt
        """
        return self.system_prompt    

    def agent_introduction(self) -> Optional[str]:
        """
        Provides the initial introduction by the agent.
        
        Returns:
            The agent's introduction message or None if already introduced
        """
        if not self.intro_given:
            self.intro_given = True
            self.user_prompt = self.introduction
            self.update_system_prompt()

            response = self.agent_response(self.model)
            agent_response_text = self.extract_json(response, 'agent_response')

            self.update_history("", agent_response_text)
            self.update_system_prompt()
            return f"{self.first_name}>: {agent_response_text}"
        return None

    def respond(self, user_input: str) -> str:
        """
        Processes the user message and generates a response.
        
        Args:
            user_input: The user's message
            
        Returns:
            The agent's response
        """
        # Handle introduction if needed
        introduction = self.agent_introduction()
        if introduction and not user_input:
            return introduction
        if not user_input:
            logger.debug("No user input provided")
            return f"{self.first_name}>: I'm waiting for your message."

        # Update system prompt with latest conversation history
        self.update_system_prompt()
        self.user_prompt = user_input
        
        # Get initial response
        response = self.agent_response(self.model)
        logger.debug(f"Initial response: {response}")

        # Process tool usage if any
        tool_response = self.choose_agent_tools(response)
        logger.debug(f"Tool response: {tool_response}")

        # Handle case where no tool is used   
        if tool_response.get('tool_choice') is None or tool_response.get('tool_choice') == "no tool":
            agent_response_text = tool_response.get('agent_response', "I'm not sure how to respond to that.")
            self.update_history(user_input, agent_response_text)
            self.update_system_prompt()
            return self.first_name + ">:" + agent_response_text
        
        # Handle case where a tool is used
        try:
            tool_choice = tool_response.get('tool_choice')
            tool_output = tool_response.get('tool_output', "No output")
            logger.debug(f"Using tool: {tool_choice} with output: {tool_output}")

            self.user_prompt = f"I have used the {tool_choice} tool and the output of the tool is {tool_output}. Please respond to the user with this information."
            self.update_system_prompt()
            response = self.agent_response(self.model)
            agent_response_text = self.extract_json(response, 'agent_response')
            self.update_history(user_input, agent_response_text)
            self.update_system_prompt()
            return self.first_name + ">:" + agent_response_text
        
        except Exception as e:
            logger.error(f"Error processing tool response: {str(e)}")
            return f"I'm sorry, I encountered an error: {str(e)}"
        
        else:
            logger.debug(f"No response found from user input")
            return

    def extract_json(self, response: dict, response_type: str) -> str:
        """
        Extracts the JSON object from the response and returns the specified field.
        
        Args:
            response: The response dictionary
            response_type: The field to extract from the JSON
            
        Returns:
            The extracted content or an error message
        """
        try:
            message = response.get('message', {}).get('content', '')
            match = re.search(r"```json\s*(\{.*\})\s*```", message, re.DOTALL)
            if match:
                json_str = match.group(1)
                try:
                    response_data = json.loads(json_str)
                    return response_data.get(response_type, "")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from agent response: {e}")
                    return f"I'm having trouble understanding my own thoughts. Please try again."
            else:
                # If no JSON is found, return the whole message
                logger.error("No valid JSON found in the response.")
                return message
                
        except Exception as e:
            logger.error(f"Error extracting JSON: {str(e)}")
            return f"Error processing response: {str(e)}"

    def show_message_history(self) -> str:
        """
        Displays the message history between the user and the agent.
        """
        return f"{self.conversation_history}"

    def show_agent_details(self) -> str:
        """
        Returns a formatted string with the agent's details.
        
        Returns:
            String containing the agent's details
        """
        
        details = [
            f"Name:            {self.first_name} {self.last_name}",
            f"Sex:             {self.sex}",
            f"Age:             {self.age}",
            f"Personality:     {self.personality}",
            f"Description:     {self.description}",
            f"System Prompt:   {self.system_prompt}",
            f"User Prompt:     {self.user_prompt}",
            f"Temperature:     {self.temperature}",
            f"Tools available: {len(self.tools) + len(self.custom_tools)}"
        ]
        return f"\n".join(details)

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
    logger.debug(f"Message: {message}")
    logger.debug(f"History: {history}")

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
            return agent.display_system_prompt()
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
    
    # Initialize the community and default agent
    agents = CommunityOfAgents()
    
    agent = Agent(AGENT_REBECCA, USERNAME, MODEL, DEFAULT_TOOLS)
    agents.add_agent(agent)

    ChatbotDemo = gr.ChatInterface(
        Agent_interface,
        type="messages",
        title="Community of Agents",
        description="The Community of Agents (COA) is a program that allows users to interact with multiple AI agents in a community.",
        theme="ocean",
        # Add these parameters to handle longer text better
        #chatbot=gr.Chatbot(),  # Increase height
        #textbox=gr.Textbox(placeholder="Type a message or command (e.g., !help)")
    )

    ChatbotDemo.launch()