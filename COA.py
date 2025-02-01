import re
import os
import time
from termcolor import colored
from toolbox.toolbox import ToolBox
from tools.time_keeper import TimeKeeper
from agent.agent_class import Agent
from agents.agents import AGENT_REBECCA
from agents.agents import AGENT_JOHN

# Constants
USERNAME       = "Vampy"
AGENT_PATH     = './agents/'
DATA_CACHE_DIR = "agents"

MODEL          = 'phi4'
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
                agent2 = Agent(AGENT_JOHN,USERNAME,tools)
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
