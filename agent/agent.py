import json
import re
import time
import ollama
from typing import List, Dict, Optional, Callable
import logging
from toolbox.Toolbox import Toolbox
import platform
from datetime import date, datetime
import textwrap
logging.basicConfig(level=logging.DEBUG)  # Change to INFO or WARNING in production
logger = logging.getLogger(__name__)


class Agent:
    """
    Represents an AI agent with a personality, tools, and conversation capabilities.
    
    This class handles the agent's interactions with the user, including processing
    messages, managing tools, and maintaining conversation history.
    
    Attributes:
        agent_id (str): Unique identifier for the agent
        first_name (str): Agent's first name
        last_name (str): Agent's last name
        sex (str): Agent's gender
        age (str): Agent's age
        personality (str): Description of agent's personality traits
        description (str): Physical description of the agent
        mission (str): Agent's primary mission or goal
        model (str): LLM model used for generating responses
        temperature (float): Temperature setting for response generation
        tools (List[callable]): List of tools available to the agent
        custom_tools (Dict): Dictionary of dynamically created tools
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
        logger.debug(f"Creating toolbox with tools: {tools}")
        self.toolbox = Toolbox(tools)  #Create toolbox
        #self.toolbox.add_tools(tools)  #add a list of tools to toolbox
        
        self.custom_tools = {} # Storage for dynamically created tools
        self.intro = True
        self.operating_system = platform.system()
        #self.tool_descriptions = self.prepare_agent_tools()
        self.tool_descriptions = self.toolbox.prepare_agent_tools()
        
        # System prompt construction
        self.system_prompt = f"You are a cyberpunk edgerunner and helpful assistant. Your name is {self.first_name}.\n You are {self.age} years old. {self.description}."
        self.introduction = f"Introduce yourself to {self.username}. Keep it short and describe how you can assist."
        self.intro_given = False
        
       
    def choose_agent_tools(self, agent_response: json) -> dict:
        """
        Chooses the appropriate tool to use based on the agent's response. 
        If no tool is selected, the response is returned as is.
        Args:
            agent_response: The agent's response containing the tool choice and input.
        Returns a dictionary with the tool choice, input, and agent response.
        """

        #logger.debug(f"choose_agent_tools: Agent response: {agent_response}")
        tool_choice = self.extract_json(agent_response, "tool_choice").strip()
        #logger.debug(f"Extracted Data: tool_choice: {tool_choice}")
        tool_input = self.extract_json(agent_response, "tool_input")
        #logger.debug(f"Extracted Data: tool_input: {tool_input}")
        agent_resp_text = self.extract_json(agent_response, "agent_response")
        logger.debug(f"Extracted Data: tool_choice: {tool_choice} tool_input: {tool_input} agent_response: {agent_resp_text}")
        # If no tool is selected (or explicitly "no tool"), simply return the response.
        if not tool_choice or tool_choice.lower() == "no tool":
            logger.debug("No tool choice found in the JSON object.")
            return {"tool_choice": None, "tool_input": None, "agent_response": agent_resp_text}
        # Check whether the tool exists in our toolbox.
        if self.toolbox.check_tool_exists(tool_choice):
            return self.toolbox.execute_tool(tool_choice, tool_input)
        else:
            return {"tool_choice": None, "tool_input": None, "agent_response": "I'm sorry, I don't have that tool."}
        

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
        You have the ability to create, delete, and manage custom tools dynamically. Here's how you can do it:
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
        "{{
            "tool_choice": "name_of_the_tool",
            "tool_input": "inputs_to_the_tool",
            "agent_response": "The response to the user"
        }}"

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
        <BEGIN HISTORY>
        {self.conversation_history}
        <END HISTORY>
        
        """)

    def show_system_prompt(self) -> str: 
        """
        Returns the current system prompt.
        
        Returns:
            String containing the system prompt
        """
        return self.system_prompt    

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

    def update_message_history(self, user_input, agent_response) -> None:
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

            response = self.agent_response(self.model)['message']['content']
            agent_response_text = self.extract_json(response, 'agent_response')

            self.update_message_history("", agent_response_text)
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
        logger.debug(f"message history {self.conversation_history}")
        self.update_system_prompt()
        self.user_prompt = user_input

        # Get initial response
        response = self.get_initial_response()
        logger.debug(f"Initial response: {response}")

        # Process tool usage if any
        tool_response = self.choose_agent_tools(response)
        logger.debug(f"Tool response: {tool_response}")

        # Handle case where no tool is used   
        if tool_response.get('tool_choice') is None or tool_response.get('tool_choice') == "no tool":
            return self.handle_no_tool_response(user_input, tool_response)

        # Handle case where a tool is used
        return self.handle_tool_response(user_input, tool_response)

    def get_initial_response(self) -> str:
        """
        Generates the initial response from the agent.
        
        Returns:
            The initial response content
        """
        return self.agent_response(self.model)['message']['content']

    def handle_no_tool_response(self, user_input: str, tool_response: dict) -> str:
        """
        Handles the case where no tool is used in the response.
        
        Args:
            user_input: The user's message
            tool_response: The tool response dictionary
            
        Returns:
            The agent's response
        """
        agent_response_text = tool_response.get('agent_response', "I'm not sure how to respond to that.")
        self.update_message_history(user_input, agent_response_text)
        self.update_system_prompt()
        return f"{self.first_name}>: {agent_response_text}"

    def handle_tool_response(self, user_input: str, tool_response: dict) -> str:
        """
        Handles the case where a tool is used in the response.
        
        Args:
            user_input: The user's message
            tool_response: The tool response dictionary
            
        Returns:
            The agent's response
        """
        try:
            tool_choice = tool_response.get('tool_choice')
            tool_output = tool_response.get('tool_output', "No output")
            logger.debug(f"Using tool: {tool_choice} with output: {tool_output}")
            self.user_prompt = f"I have used the {tool_choice} tool and the output of the tool is {tool_output}. Please respond to the user with this information."
            self.update_system_prompt()
            response = self.get_initial_response()
            agent_response_text = self.extract_json(response, "agent_response")
            self.update_message_history(user_input, agent_response_text)
            self.update_system_prompt()
            return f"{self.first_name}>: {agent_response_text}"
        except Exception as e:
            logger.error(f"Error processing tool response: {str(e)}")
            return f"I'm sorry, I encountered an error: {str(e)}"

    def extract_json(self, response: json, response_type: str) -> str:
        """
        Extracts the JSON object from the response and returns the specified field.
        
        Args:
            response: The response dictionary from ollama.chat
            response_type: The field to extract from the JSON
            
        Returns:
            str: The extracted content or an error message
        """
        try:
            # Look for JSON block between backticks
            match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if  match:
                json_str = match.group(1).strip()
                logger.debug(f"Found JSON between backticks: {json_str}")
            else:
                # Try to parse the entire response as JSON
                json_str = response.strip()
                logger.debug(f"Extracted JSON string: {json_str}")
                
            # Try to parse the JSON string
            try:
                response_data = json.loads(json_str)
                result = response_data.get(response_type, "")
                logger.debug(f"Successfully extracted {response_type}: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from content: {e}")
                return "I'm having trouble understanding my own thoughts. Please try again."
                    
        except Exception as e:
            logger.error(f"Error in extract_json: {str(e)}")
            return f"Error processing response: {str(e)}"

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
