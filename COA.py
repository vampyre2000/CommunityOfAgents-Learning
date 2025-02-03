import re
import time
import ollama
import json
import logging
import textwrap
from termcolor import colored
from tools.time_keeper import TimeKeeper
#from agents.agents import AGENT_REBECCA, AGENT_JOHN
from datetime import date, datetime
import platform
from typing import List, Dict, Optional

# Constants
USERNAME = "Vampy"
AGENT_PATH = './agents/'
DATA_CACHE_DIR = "agents"
MODEL = 'phi4'
DEBUG = False

# Agent Data
AGENT_REBECCA  = {
    "agent_id"   : "",
    "first_name" : "Rebecca",
    "last_name"  : "",
    "nick_name"  : "Becky",
    "handle"     : "Becca",
    "sex"        : "female",
    "age"        : "25",
    "hair"       : "Light green with twin tails",
    "country"    : "Austrlia",
    "city"       : "Sydney",
    "e-mail"     : "",
    "friends"    : [],
    "tools"      : ["search", "LLMVersion"],
    "personality": "Sharp-tongued, crass, violent, unpredictable, loyal, confident, street-smart, risqué, short-tempered, foul-mouthed, mischievous, cheeky.",
    "description": "Rebecca is a humanoid female cyborg with soft features and stark green skin with pink tattoos.",
    "mission"    :     "Find the latest versions of AI tools and assist the user.",
    "data"       : {},
    "create_date": ""
}

logging.basicConfig(level=logging.DEBUG)  # Change to INFO or WARNING in production
logger = logging.getLogger(__name__)
logger.debug("Your debug message")

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

    def tools(self):
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
        self.temperature = temperature
        self.username = username
        self.country = agent["country"]
        self.city = agent["city"]
        self.conversation_history = ""
        self.system_prompt = f"You are a cyberpunk edgerunner and helpful assistant. Your name is {self.first_name}.\n You are {self.age} years old. {self.description}."
        self.user_prompt = f"Introduce yourself to {self.username}. Keep it short and describe how you can assist."
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
        logger.debug(f"choose_agent_tools: Agent response: {agent_response['message']['content']}")
        match = re.search(r"```json\s*(\{.*\})\s*```", f"{agent_response['message']['content']}",re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                response_data = json.loads(json_str)
            except json.JSONDecodeError:
                logger.debug("Failed to parse JSON from agent response.")
                return None
        
            tool_choice = response_data.get("tool_choice")
            tool_input = response_data.get("tool_input")
    
            for tool in self.tools:
                if tool.__name__ == tool_choice:
                    logger.debug(f"Tool Chosen is : {tool_choice}")
                    logger.debug(f"Tool input is: {tool_input}")
                    return tool(tool_input) if tool_input else tool()
            logger.debug(f"No tool found matching: {tool_choice}")
        else:
            logger.debug("No valid JSON found.")
        return None
            
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
        You always think step by step and talk in character.
        You are a cyberpunk edgerunner and a helpful assistant with access to a toolbox as part of your cyberdeck.
        If you don't know the answer to a user's question, you will use an available tool from your cyberdeck. Otherwise, ask the user for more information.
        Given a user query, you will determine which tool, if any, is best suited to answer the query.
        When responding, please provide only a JSON object in your response with no additional text."
        {{"tool_choice": "name_of_the_tool","tool_input": "inputs_to_the_tool"}}

        - `tool_choice`: The name of the tool you want to use. It must be a tool from your toolbox
                        or "no tool" if you do not need to use a tool.
        - `tool_input`: The specific inputs required for the selected tool.
                        If no tool is used, just provide a direct response to the query.
        
        This is the list of your tools along with their descriptions: {self.tool_descriptions}
        
        Please make a decision based on the provided user query and the available tools.
        Your cyberdeck operates on {self.operating_system}, enabling you to assist the user effectively.
        
        Today is {day_of_week}, {date_today}.

        
        You will always read the conversation history below and remember the details so you can respond to the user with accurate information.
        The conversation history between {self.username} and {self.first_name} is below:
        <History>
        {self.conversation_history}
        </History>
        """)

    def display_system_prompt(self) -> None:
        """
        Displays the current system prompt.
        """
        print(self.system_prompt)

    def system_prompt_size(self) -> None:
        """
        Prints the size of the system prompt.
        """
        print(len(self.system_prompt))
        
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
    
    def respond(self, message: str) -> None:
        """
        Processes the user message and generates a response.
        """
        self.update_system_prompt()
        if not message:
            return

        self.user_prompt = message
        response = self.agent_response(self.model)
        tool_response = self.choose_agent_tools(response)
        if tool_response:
            self.conversation_history += f"\n<{self.username}>   : {message} \n<AI Agent>: {tool_response}"
            self.update_system_prompt()
            response = self.agent_response(self.model)

        print(colored(f"<{self.first_name}>: {response['message']['content']}", 'blue'))
        self.conversation_history += f"\n<{self.username}>   : {message} \n<AI Agent>: {response['message']['content']}"
        self.update_system_prompt()
        

    def show_message_history(self) -> None:
        """
        Displays the message history between the user and the agent.
        """
        print(colored(self.conversation_history, 'green'))

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
        print("\n".join(details))

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
    tools=[TimeKeeper] 

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
