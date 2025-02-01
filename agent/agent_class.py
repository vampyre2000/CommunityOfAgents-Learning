# Agent Class
import ollama
import re
from datetime import date
from datetime import datetime
from toolbox.toolbox import ToolBox
from termcolor import colored
import platform

DEBUG=False

def debug_print(message: str, enabled: bool = DEBUG) -> None:
    """
    Prints debug messages if debugging is enabled.
    """
    if enabled:
        print(message)

class Agent:
    def __init__(self,agent,username,model,tools,temperature=0.7):
        self.first_name  = agent["first_name"]
        self.last_name   = agent["last_name"]
        self.sex         = agent["sex"]
        self.age         = agent["age"]
        self.model       = model
        self.personality = agent["personality"]
        self.description = agent["description"]
        self.temperature = temperature
        self.username    = username
        self.country     = agent["country"]
        self.city        = agent["city"]
        self.conversation_history = ""
        self.system_prompt = f"You are a cyberpunk edgerunner and helpful assistant. Your name is {self.first_name}.\n You are {self.age} years old. {self.description}."
        self.user_prompt   = f"Introduce yourself to {self.username}. Keep it short and describe how you can assist."
        self.tools=tools
        self.intro=True
        self.operating_system=platform.system()
        self.tool_descriptions = self.prepare_agent_tools()

        
    def prepare_agent_tools(self) -> str:
        """
        Stores the tools in the toolbox and returns their descriptions.
        Parameters: None
        Returns:
            str: Descriptions of the tools stored in the toolbox.
        """
        toolbox = ToolBox()
        toolbox.store(self.tools)
        debug_print(f"Prepare_agent_tools {toolbox.tools()}")
        return toolbox.tools()

    def choose_agent_tools(self,agent_response):
            """
            Extract the tool_choice from the agent's response using regex
            Parameters: None
            Returns: 
            """
            debug_print(f"choose_agent_tools: Agent respose: {agent_response['message']['content']}")
            match = re.search(r'"tool_choice":\s*"([^"]+)"', agent_response['message']['content'])
            if not match:
                debug_print("No tool_choice found.")
                return None

            tool_choice = match.group(1)
            #print(f"choose_agent_tools: Tool choice: {tool_choice}")
                
            # Extract tool_input if available
            tool_input_match = re.search(r'"tool_input":\s*"([^"]*)"', agent_response['message']['content'])
                #print(f"choose_agent_tools: tool_input_match {tool_input_match}")
            tool_input = tool_input_match.group(1) if tool_input_match else None
            #print(f"tool_input:::{tool_input}")
            #print(f"choose_agent_tools: tool_input {tool_input}")
            # Iterate through the tools and execute the corresponding tool
            
            for tool in self.tools:
                if tool.__name__ == tool_choice:
                    return tool(tool_input) if tool_input else tool()
                        #print(colored(response,'cyan'))
            debug_print(f"No {tool_choice} found")
            return None

    def generate_prompt(self):
        """
        Generates the prompt template for the agent.
        """

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


    def update_system_prompt(self) -> None:
        """
        Updates the system prompt with the description of the agent and includes the conversation history.
        Returns:
        None
        """

        day_of_week = datetime.now().strftime('%A')
        date_today = date.today()
        
        self.system_prompt = f"""
        Your name is {self.first_name}.
        You are {self.age} years old, {self.sex}, and currently live in {self.city}, {self.country}.
        {self.description}.
        You are a cyberpunk edgerunner and a helpful assistant with access to a toolbox as part of your cyberdeck.
        If you don't know the answer to a user's question, you will use an available tool from your cyberdeck. Otherwise, ask the user for more information.
        Given a user query, you will determine which tool, if any, is best suited to answer the query.
        You will generate the following JSON response:
        {{
            "tool_choice": "name_of_the_tool",
            "tool_input": "inputs_to_the_tool"
        }}
        - `tool_choice`: The name of the tool you want to use. It must be a tool from your toolbox
                        or "no tool" if you do not need to use a tool.
        - `tool_input`: The specific inputs required for the selected tool.
                        If no tool is used, just provide a direct response to the query.
        
        This is the list of your tools along with their descriptions: {self.tool_descriptions}
        
        Please make a decision based on the provided user query and the available tools.
        Your cyberdeck operates on {self.operating_system}, enabling you to assist the user effectively.
        
        Today is {day_of_week}, {date_today}.
        You always think step by step and talk in character.
        You will always read the conversation history below and remember the details so you can respond to the user with accurate information.
        
        Below is the conversation history between {self.username} and {self.first_name}:
        <BEGIN HISTORY>
        {self.conversation_history}
        <END HISTORY>
        """

    
    def update_system_prompt1(self) -> None:
        """
        Updates the system prompt with the description of the agent and included the conversation history.
        Returns:
        None:
        """

        dayofweek=datetime.now().strftime('%A')
        date_today = date.today()
        self.system_prompt=f"""
        Your name is {self.first_name}.
        You are {self.age} years old, {self.sex} and currently live in {self.city} {self.country}.
        {self.description}.
        You are a cyberpunk edgerunner and helpful assistant with access to a toolbox as part of your cyberdeck.
        If you don't know the answer to a user's question, you will use an available tool from your cyberdeck, otherwise ask the user for more information.
        Given a user query, you will determine which tool, if any, is best suited to answer the query.
        You will generate the following JSON response:
        "tool_choice":"name_of_the_tool","tool_input":"inputs_to_the_tool"
        -`tool_choice`: The name of the tool you want to use. It must be a tool from your toolbox
                   or "no tool" if you do not need to use a tool.
        -`tool_input`: The specific inputs required for the selected tool.
                If no tool, just provide a response to the query.
        This is the list of your tools along with their descriptions: {self.tool_descriptions}
        
        Please make a decision based on the provided user query and the available tools.
        Your cyberdesk has {self.operating_system} as its operating system, it allows you to help the user.
        
        Today is {dayofweek} {date_today}
        You always think think Step by Step and talk in character.
        You will always read the conversation history below and remember the details so you can respond to the user with correct information.
        Use the conversation history below between the BEGINBelow is the coversation converation history between {self.username} and {self.first_name}.
        <BEGIN HISTORY>\n{self.conversation_history}\n<END HISTORY>
        """

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
        
    def agent_response(self, model):
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

    def respond(self,message):
        """
        Generates the response from the agent.
        """
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
