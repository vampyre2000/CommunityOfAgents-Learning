import re
import os
from datetime import date
import time
import ollama
from termcolor import colored
import requests 
from toolbox.toolbox import ToolBox
from tools.time_keeper import TimeKeeper

# Constants
USERNAME       = "Vampy"
AGENT_PATH     = './Agents/'
DATA_CACHE_DIR = "agents"
# Agent Data
AGENT_REBECCA  = {
    "agent_id"   : "",
    "first_name" : "Rebecca",
    "last_name"  : "",
    "nick_name"  : "Becky",
    "handle"     : "",
    "sex"        : "female",
    "age"        : "25",
    "hair"       : "",
    "e-mail"     : "",
    "friends"    : [],
    "tools"      : ["search", "LLMVersion"],
    "personality": "Sharp-tongued, crass, violent, unpredictable, loyal, confident, street-smart, risqué, short-tempered, foul-mouthed, mischievous, cheeky.",
    "description": "Rebecca is a humanoid female cyborg with soft features and stark green skin with pink tattoos.",
    "mission"    :     "Find the latest versions of AI tools and assist the user.",
    "data"       : {},
    "create_date": ""
}

AGENT_JOHN = {
    "agent_id"   : "",
    "first_name" : "John",
    "last_name"  : "",
    "nick_name"  : "Silverhand",
    "handle"     : "",
    "sex"        : "male",
    "age"        : "45",
    "hair"       : "",
    "e-mail"     : "",
    "friends"    : [],
    "tools"      : ["search", "LLMVersion"],
    "personality": "Sharp-tongued, crass, violent, unpredictable, loyal, confident, street-smart, risqué, short-tempered, foul-mouthed, mischievous, cheeky.",
    "description": "John is a humanoid male cyborg with one cybernetic arm.",
    "mission"    : "Find the latest versions of AI tools.",
    "data"       : {},
    "create_date": ""
}

# Agent Class
class Agent:
    def __init__(self,agent,tools,temperature=0.7):
        self.first_name = agent["first_name"]
        self.last_name = agent["last_name"]
        self.sex = agent["sex"]
        self.age = agent["age"]
        self.personality = agent["personality"]
        self.description = agent["description"]
        self.conversation_history = ""
        self.system_prompt = f"You are a cyberpunk edgerunner and helpful assistant. Your name is {self.first_name}.\n You are {self.age} years old. {self.description}.\n\nYou will read the conversation history below and remember details about what you say next. You must think Step by Step. Below is the coversation converation history between {USERNAME} and {self.first_name}.\n\n<BEGIN HISTORY>\n{self.conversation_history}\n<END HISTORY>\n!"
        self.user_prompt = f"Introduce yourself to {USERNAME}. Keep it short and describe how you can assist."
        self.temperature = temperature
        self.tools=tools

    def prepare_tools(self):
        """
        Stores the tools in the toolbox and returns their descriptions.

        Returns:
        str: Descriptions of the tools stored in the toolbox.
        """
        toolbox = ToolBox()
        toolbox.store(self.tools)
        tool_descriptions = toolbox.tools()
        return tool_descriptions

    def generate_prompt(self):
        """Generates the prompt template for the agent."""
        prompt=[
            {
                'role': 'system',
                'content': self.system_prompt,
            },
            {
                'role': 'user',
                'content': self.user_prompt,
            },
             ],
        options = {'temperature': 0}
        return prompt
    
    def update_system_prompt(self):
        """updates the system prompt with the description of the agent and included the conversation history."""
        
        tool_descriptions = self.prepare_tools()
        self.system_prompt=f"""
        You are a cyberpunk edgerunner and helpful assistant with access to a toolbox as part of your cyberdeck.
        Your name is {self.first_name}.
        You are {self.age} years old. 
        {self.description}.
        Today is {date.today()}
        You will read the conversation history below and remember details about what you say next.
        You must think Step by Step.
        Given a user query, you will determine which tool, if any, is best suited to answer the query.
        You will generate the following JSON response:
        "tool_choice": "name_of_the_tool",
        "tool_input": "inputs_to_the_tool"
        -`tool_choice`: The name of the tool you want to use. It must be a tool from your toolbox
                   or "no tool" if you do not need to use a tool.
        -`tool_input`: The specific inputs required for the selected tool.
                If no tool, just provide a response to the query.
        Here is a list of your tools along with their descriptions:
        {tool_descriptions}
        Please make a decision based on the provided user query and the available tools.
        Below is the coversation converation history between {USERNAME} and {self.first_name}.
        <BEGIN HISTORY>\n{self.conversation_history}\n<END HISTORY>
        """

    def display_system_prompt(self):
        """Displays the current system prompt."""

        print(self.system_prompt)

    def respond(self, message):
        """Generates the response from the agent."""
    
        if message:
            print(colored(f"<{self.first_name}>: received message.", 'blue'))
            self.user_prompt = message

        # Generate the agent's response using ollama
        response = ollama.chat(model="llama3.1", messages=[
            {
                'role': 'system',
                'content': self.system_prompt,
            },
            {
                'role': 'user',
                'content': self.user_prompt,
            },
        ], options={'temperature': 0})

        # Add the conversation history
        self.conversation_history += f"\n<{USERNAME}>   : {message} \n<AI Agent>: {response['message']['content']}"
        self.update_system_prompt()
        print(colored(response, 'blue'))

        # Extract the tool_choice from the agent's response using regex
        match = re.search(r'"tool_choice":\s*"([^"]+)"', response['message']['content'])
        if match:
            tool_choice = match.group(1)
            print(f"Tool choice: {tool_choice}")
            
            # Extract tool_input if available
            tool_input_match = re.search(r'"tool_input":\s*"([^"]*)"', response['message']['content'])
            tool_input = tool_input_match.group(1) if tool_input_match else None
            
            # Iterate through the tools and execute the corresponding tool
            for tool in self.tools:
                if tool.__name__ == tool_choice:
                    if tool_input and tool_input!="NONE":
                        response = tool(tool_input)
                    else:
                        response = tool()
                    
                    print(colored(response,'cyan'))
                    return
        else:
            print("No tool_choice found")
            print(colored(f"<{self.first_name}>: {response['message']['content']}",'blue'))

    def display_message_history(self):
        print(colored(self.conversation_history,'green'))

    def display_agent_details(self):
        print(f"Name:           {self.first_name} {self.last_name}")
        print(f"Sex:            {self.sex}")
        print(f"Age:            {self.age}")
        print(f"Personality:    {self.personality}")
        print(f"Description:    {self.description}")
        print(f"System Prompt:  {self.system_prompt}")
        print(f"User Prompt:    {self.user_prompt}")
        print(f"Temperature:    {self.temperature}")
        print(f"Tools available: {self.tools}")

# Community of Agents Class
class CommunityOfAgents:
    def __init__(self):
        self.agents = []

    def list_agents(self):
        if self.agents:
            for agent in self.agents:
                print(f"Agent available: {agent.first_name} {agent.last_name}")
        else:
            print("There are no local agents.")

    def add_agent(self, agent):
        self.agents.append(agent)

    def remove_agent(self, agent):
        self.agents.remove(agent)






# Commands Functionality
def help():
    print("Available Commands:\n")
    print("!agent list            : Prints the list of agents")
    print("!agent load <agent>    : Loads a particular agent")
    print("!agent details <agent> : Prints the details of a particular agent")
    print("!agent system <agent>  : Prints the system prompt of a particular agent")
    print("!version               : Prints the version of software")
    print("!help                  : Prints this help message")
    print("!quit                  : quits the program")
    print()

def commands():
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
                agent1 = Agent(AGENT_REBECCA,tools)
                agents.add_agent(agent1)
            elif command == "!agent load 2":
                agent2 = Agent(AGENT_JOHN,tools)
                agents.add_agent(agent2)
            elif command == "!agent details 1" and agent1:
                agent1.display_agent_details()
            elif command == "!agent details 2" and agent2:
                agent2.display_agent_details()
            elif command == "!agent history" and agent1:
                agent1.display_message_history()
            elif command == "!agent system" and agent1:
                agent1.display_system_prompt()
            elif command == "!help":
                help()
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
