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

logging.basicConfig(level=logging.DEBUG)  # Change to INFO or WARNING in production
logger = logging.getLogger(__name__)

# Define the tools list globally
tools = [TimeKeeper, get_disruption_date, get_llm_versions]

class Agent:
    def __init__(self, agent: dict, username: str, model: str, tools: List[callable], temperature: float = 0.7):
        self.first_name = agent["first_name"]
        self.last_name = agent["last_name"]
        self.sex = agent["sex"]
        self.age = agent["age"]
        self.model = model
        self.personality = agent["personality"]
        self.description = agent["description"]
        self.mission = agent["mission"]
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
        """
        toolbox = {}
        for tool in self.tools:
            toolbox[tool.__name__] = tool.__doc__
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
        """
        return ollama.chat(
            model,
            messages=[
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': self.user_prompt}
            ],
            options={'temperature': self.temperature}
        )

    def update_history(self, user_input, agent_response) -> None:
        """
        Updates the conversation history
        """
        self.conversation_history += f"\n<{self.username}>   : {user_input} \n<AI Agent>: {agent_response}"

    def show_message_history(self) -> str:
        """
        Displays the message history between the user and the agent.
        """
        return self.conversation_history
    
    def show_system_prompt(self) -> str: 
        """
        Displays the system prompt for the agent.
        """
        return self.system_prompt    

    def agent_introduction(self) -> None:
        """
        Give the initial introduction by the agent
        """
        if not self.intro_given:
            self.intro_given = True
            self.user_prompt = self.introduction
            self.update_system_prompt()
            agent_response = self.extract_json(self.agent_response(self.model), 'agent_response')
            self.update_history("", agent_response)
            self.update_system_prompt()
            return self.first_name + ">:" + agent_response
        else:
            return

    def respond(self, user_input: str) -> str:
        """
        Processes the user message and generates a response.
        """
        self.agent_introduction()
        if user_input:
            self.update_system_prompt()
            self.user_prompt = user_input
            response = self.agent_response(self.model)
            logger.debug(f"Respond  {response}")
            tool_response = self.choose_agent_tools(response)
            logger.debug(f"Tool response  {tool_response}")
            if tool_response['tool_choice'] == "no tool" or tool_response['tool_choice'] is None:
                self.update_history(user_input, tool_response['agent_response'])
                self.update_system_prompt()
                return self.first_name + ">:" + tool_response['agent_response']
            else:
                print(f"<{self.first_name}>: {tool_response['tool_choice']}:{tool_response['tool_output']}")
                self.user_prompt = f"I have used the {tool_response['tool_choice']} tool and the output of the tool is {tool_response['tool_output']}. Please respond to the user with this information."
                self.update_system_prompt()
                response = self.agent_response(self.model)
                agent_response = self.extract_json(response, 'agent_response')
                self.update_history(user_input, agent_response)
                self.update_system_prompt()
                return self.first_name + ">:" + agent_response
        else:
            logger.debug(f"No response found from user input")
            return

    def extract_json(self, response: str, response_type) -> str:
        """
        Extracts the JSON object from the response and returns the content.
        """
        message = response['message']['content']
        match = re.search(r"```json\s*(\{.*\})\s*```", message, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                response_data = json.loads(json_str)
                agent_message = response_data.get("agent_response", "")
                return agent_message
            except json.JSONDecodeError:
                print(f"Failed to parse JSON from agent response.")

    def show_message_history(self) -> str:
        """
        Displays the message history between the user and the agent.
        """
        return f"{self.conversation_history}"

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
        return f"\n".join(details)

class CommunityOfAgents:
    def __init__(self):
        self.agents: list[Agent] = []

    def list_agents(self) -> str:
        if self.agents:
            return "\n".join([f"Agent available: {agent.first_name} {agent.last_name}" for agent in self.agents])
        else:
            return "There are no local agents loaded."

    def add_agent(self, agent) -> str:
        self.agents.append(agent)
        return f"Agent {agent.first_name} {agent.last_name} added."

    def remove_agent(self, agent) -> str:
        self.agents.remove(agent)
        return f"Agent {agent.first_name} {agent.last_name} removed."

def Agent_interface(message, history):
    """
    Provides the logic of the commands for the system and loads the agents and accepts input from the user.
    """
    logger.debug(f"Message: {message}")
    logger.debug(f"History: {history}")
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
            return "Available Commands:\n!agent list\n!agent load 1\n!agent details 1\n!agent history\n!agent system\n!agent size\n!version\n!quit\n!bye"
        else:
            return "Command not found."
    else:
        if agent:
            return agent.respond(message)
        else:
            return "No agent loaded to respond."

if __name__ == "__main__":
    agents = CommunityOfAgents()
    tools = [TimeKeeper, get_disruption_date, get_llm_versions]
    agent = Agent(AGENT_REBECCA, USERNAME, MODEL, tools)
    agents.add_agent(agent)

    ChatbotDemo = gr.ChatInterface(
        Agent_interface,
        type="messages",
        title="Community of Agents",
        description="The Community of Agents (COA) is a program that allows users to interact with multiple AI agents in a community.",
        theme="ocean"
    )

    ChatbotDemo.launch()