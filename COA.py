# The Community of Agents (COA) is a program that allows users to interact with multiple AI agents in a community.
# The program provides a command-line interface for users to load, interact with, and manage multiple AI agents. 
# The agents are designed to assist users with various tasks, such as answering questions, providing information, and performing specific functions.
# The COA program allows users to load different agents, view agent details, interact with agents, and switch between agents in the community.
# The program also provides a help menu with a list of available commands and options for users to navigate the system.
# The COA program is designed to be extensible, allowing users to add new agents with different capabilities and functions.
# Author: Vampy
# Version: 1.0

import re
import time
import ollama
import json
import logging
import textwrap
from termcolor import colored
from tools.time_keeper import TimeKeeper
from tools.LLMVersionCheck import get_disruption_date
from datetime import date, datetime
import platform
from typing import List, Dict, Optional

# Set the constants for the program
USERNAME = "Vampy"
AGENT_PATH = './agents/'
DATA_CACHE_DIR = "agents"
MODEL = 'phi4'

# Parameters for the Rebecca Agent personality
AGENT_REBECCA  = {
    "agent_id"   : "00001",
    "first_name" : "Rebecca",
    "last_name"  : "",
    "nick_name"  : "Becky",
    "handle"     : "Becca",
    "sex"        : "female",
    "age"        : "25",
    "hair"       : "Light green with twin tails",
    "country"    : "Australia",
    "city"       : "Sydney",
    "e-mail"     : "",
    "friends"    : [],
    "tools"      : ["search", "LLMVersion"],
    "personality": "Sharp-tongued, crass, violent, unpredictable, loyal, confident, street-smart, risqué, short-tempered, foul-mouthed, mischievous, cheeky.",
    "description": "Rebecca is a humanoid female cyborg with soft features and stark green skin with pink tattoos. She is a solo Mercenary for hire.",
    "mission"    : "Find the latest versions of AI tools and assist the user.",
    "data"       : {},
    "create_date": ""
}

logging.basicConfig(level=logging.DEBUG)  # Change to INFO or WARNING in production
logger = logging.getLogger(__name__)

class ToolBox:
    def __init__(self):
        self.tools_dict: Dict[str, Optional[str]] = {}

    def store(self, functions_list: List[callable]) -> Dict[str, Optional[str]]:
        """ 
        Stores the literal name and docstring of each function in the list.
        Parameters:
        functions_list (list): List of function objects to store.
        Returns: dict: Dictionary with function names as keys and their docstrings as values.
        """
        for func in functions_list:
            self.tools_dict[func.__name__] = func.__doc__
        return self.tools_dict

    def tools(self) -> str:
        """
        Parameters: None
        Returns: str: Dictionary of stored functions and their docstrings as a text string.
        Returns: Dictionary created in store as a text string.
        """

        tools_str = ""
        for name, doc in self.tools_dict.items():
            tools_str += f"{name}: \"{doc}\"\n"
            logger.debug(f"ToolBox:tools_str: {tools_str}")
        return tools_str.strip()

# Agent Class
class Agent:
    def __init__(self, agent: dict, username: str, model: str, tools: List[callable], temperature: float = 0.7):
        self.first_name = agent["first_name"]
        self.last_name = agent["last_name"]
        self.sex = agent["sex"]
        self.age = agent["age"]
        self.model = model
        self.personality = agent["personality"]
        self.description = agent["description"]
        self.mission=agent["mission"]
        self.temperature = temperature
        self.username = username
        self.country = agent["country"]
        self.city = agent["city"]
        self.conversation_history = ""
        self.system_prompt = f"You are a cyberpunk edgerunner and helpful assistant. Your name is {self.first_name}.\n You are {self.age} years old. {self.description}."
        self.introduction = f"Introduce yourself to {self.username}. Keep it short and describe how you can assist."
        self.intro_given = False
        self.agent_id = agent["agent_id"]
        self.tools = tools
        self.intro = True
        self.operating_system = platform.system()
        self.tool_descriptions = self.prepare_agent_tools()

    def prepare_agent_tools(self) -> str:
        """
        Stores the tools in the toolbox and returns their descriptions.
        Parameters: None
        Returns: str: Descriptions of the tools stored in the toolbox.
        """
        toolbox = ToolBox()
        toolbox.store(self.tools)
        logger.debug(f"Prepare_agent_tools {toolbox.tools()}")
        return toolbox.tools()

    def choose_agent_tools(self, agent_response):
        message = agent_response['message']['content']
        logger.debug(f"choose_agent_tools: Agent response: {message}")
        match = re.search(r"```json\s*(\{.*\})\s*```", f"{message}",re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                response_data = json.loads(json_str)
            except json.JSONDecodeError:
                logger.debug("Failed to parse JSON from agent response.")
                return message # Return the plain text response if JSON parsing fails
        
            tool_choice = response_data.get("tool_choice")
            tool_input = response_data.get("tool_input")
            agent_response = response_data.get("agent_response")
            logger.debug(f"tool_choice: {tool_choice} tool_input: {tool_input} agent_reponse: {agent_response}")
            if tool_choice == "no tool":
                response_data= {"tool_choice": tool_choice, "tool_input": tool_input, "agent_response": agent_response}
                return response_data
            else:
                
                for tool in self.tools:
                    if tool.__name__ == tool_choice:
                        logger.debug(f"tool_choice is: {tool_choice}")
                        logger.debug(f"tool_input is: {tool_input}")
                        tool_output = tool(tool_input) if tool_input else tool()
                        logger.debug(f"tool_ouput is: {tool_output}")
                        response_data= {"tool_choice": tool_choice, "tool_input": tool_input, "tool_output": tool_output,"agent_response":""}
                        return response_data
        else:
            logger.debug("No valid JSON found.")
            return message # Return the plain text response if no JSON is found

    def generate_prompt(self):
        """
        Generates the prompt template for the agent.
        """

        prompt=[
            {'role': 'system','content': self.system_prompt},
            {'role': 'user','content': self.user_prompt},
        ]
        options = {'temperature': 0}
        return prompt
    
    def update_system_prompt(self) -> None:
        """
        Updates the system prompt with the description of the agent and includes the conversation history.
        Returns:
        None
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

    def display_system_prompt(self) -> None:
        """
        Displays the current system prompt.
        """
        print(colored(self.system_prompt, 'blue'))

    def system_prompt_size(self) -> None:
        """
        Prints the size of the system prompt.
        """
        print(len(self.system_prompt))

    def display_tool_descriptions(self) -> None:
        """
        Displays the descriptions of the tools available to the agent.
        """
        print(colored(self.tool_descriptions, 'blue'))
        
    def agent_response(self, model: str) -> dict:
        """
        Generates the agent response using the specified model.
        """
        return ollama.chat(
            model,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': self.user_prompt}
            ],
            options={'temperature': self.temperature}
        )
    
    def update_history(self, user_input,agent_response) -> None:
        """
        Updates the conversation history
        """
        self.conversation_history += f"\n<{self.username}>   : {user_input} \n<AI Agent>: {agent_response}" # Update the conversation history
        
    def respond(self, user_input: str) -> None:
        """
        Processes the user message and generates a response.
        """
        
        if self.intro_given == False: # Check if the introduction has been given
            self.user_prompt = self.introduction
            self.update_system_prompt()
            self.intro_given = True
            agent_response = self.extract_json(self.agent_response(self.model),'agent_response')
            print(colored(f"<{self.first_name}>: {agent_response}", 'green'))
            self.update_history(user_input,agent_response)
            self.update_system_prompt()
        else:
            if not user_input: # Check if the user input is empty
                logger.debug(f"No resonse found from user input")
                return
            else:
                self.update_system_prompt() 
                self.user_prompt = user_input
                response = self.agent_response(self.model)
                tool_response = self.choose_agent_tools(response) # Check if a tool is available
                logger.debug(f"Tool response  {tool_response}")
                if tool_response['tool_choice']== "no tool":  #If no tool is available just return the agent response
                    print(colored(f"<{self.first_name}>: {tool_response['agent_response']}", 'green'))
                    self.update_history(user_input,tool_response)
                    self.update_system_prompt()
                else: # If a tool is available, return the tool response. The tool response is a JSON object with the tool choice, tool input and agent response
                    print(colored(f"<{self.first_name}>: {tool_response['tool_choice']}:{tool_response['tool_output']}", 'red'))
                    self.user_prompt = f"I have used the {tool_response['tool_choice']} tool and the output of the tool is {tool_response['tool_output']}. Please respond to the user with this information."
                    self.update_system_prompt()
                    response = self.agent_response(self.model)
                    print(colored(f"<{self.first_name}>: {self.extract_json(response,'agent_response')}", 'green'))
                    self.update_history(user_input,tool_response)
                    self.update_system_prompt()
        
    def extract_json(self, response: str,response_type) -> str:
        """
        Extracts the JSON object from the response and returns the content.
        """
        message = response['message']['content']
        match = re.search(r"```json\s*(\{.*\})\s*```", message, re.DOTALL)
        if  match:
            json_str = match.group(1)
            try:
                response_data = json.loads(json_str)
                agent_message = response_data.get("agent_response", "")
                return agent_message
            except  json.JSONDecodeError:
                print(colored(f"Failed to parse JSON from agent response.", 'red'))

    def show_message_history(self) -> None:
        """
        Displays the message history between the user and the agent.
        """
        print(colored(self.conversation_history, 'blue'))

    def show_agent_details(self) -> None:
        """
        Displays the details of the agent.
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
            f"Tools available: {self.tools}"
        ]
        print(colored("\n".join(details)), 'blue')

# Community of Agents Class
class CommunityOfAgents:
    def __init__(self):
        self.agents: list[Agent] = []

    def list_agents(self) -> None:
        if self.agents:
            for agent in self.agents:
                print(f"Agent available: {agent.first_name} {agent.last_name}")
        else:
            print("There are no local agents loaded.")

    def add_agent(self, agent) -> None:
        print(f"Agent {agent.first_name} {agent.last_name} added.")
        self.agents.append(agent)

    def remove_agent(self, agent) -> None:
        print(f"Agent {agent.first_name} {agent.last_name} removed.")
        self.agents.remove(agent)

# Helper Functions
def display_help() -> None:
    """
    Displays the available commands for the user.
    """
    commands_list = [
        "!agent list            : List all available agents",
        "!agent load <1|2>      : Load a specific agent",
        "!agent details <1|2>   : Display details of a specific agent",
        "!agent system <1|2>    : Display the system prompt of an agent",
        "!version               : Display the software version",
        "!help                  : Show this help message",
        "!quit                  : Quit the program",
    ]
    print("Available Commands:\n")
    print("\n".join(commands_list))

def commands() -> None:
    """
    Provides the logic of the commands for the systema d loads the agents and accepts input from the user
    """
    agents = CommunityOfAgents()
    agent1 = agent2 = None
    loop = True
    tools=[TimeKeeper,get_disruption_date] 
    agent1 = Agent(AGENT_REBECCA,USERNAME,MODEL,tools)
    agents.add_agent(agent1)
    agent1.respond("")

    while loop:
        command = input("#> ")
        if command.startswith("!"):
            if command == "!agent list":
                agents.list_agents()
            elif command == "!quit":
                loop = False
            elif command == "!version":
                print("Version 1.0")
            elif command == "!agent load 1":
                agent1 = Agent(AGENT_REBECCA,USERNAME,MODEL,tools)
                agents.add_agent(agent1)
            elif command == "!agent load 2":
                agent2 = Agent(AGENT_JOHN,USERNAME,MODEL,tools)
                agents.add_agent(agent2)
            elif command == "!agent details 1" and agent1:
                agent1.show_agent_details()
            elif command == "!agent details 2" and agent2:
                agent2.show_agent_details()
            elif command == "!agent history" and agent1:
                agent1.show_message_history()
            elif command == "!agent system" and agent1:
                agent1.display_system_prompt()
            elif command == "!agent size" and agent1:
                agent1.system_prompt_size()
            elif command == "!help":
                display_help()
            elif command == "!ps":
                print(ollama.ps())
            else:
                print(colored("Command not found.",'red'))
        else:
            if agent1:
                agent1.respond(command)
            else:
                print(colored(f"No agent loaded to respond.",'red'))      
        time.sleep(0.5)


if __name__ == "__main__":
    commands()
