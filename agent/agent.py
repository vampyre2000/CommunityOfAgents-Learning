import json
import re
import ollama
from typing import List, Dict, Optional, Callable
import logging
from toolbox.Toolbox import Toolbox
import platform
from datetime import date, datetime
import textwrap

logger = logging.getLogger(__name__)

class Message:
    """
    Represents a message in the conversation history.
    
    This class handles the storage and retrieval of messages, ensuring that the
    conversation history is maintained within a specified length limit.
    
    Attributes:
        username (str): The name of the user
        agent_name (str): The name of the agent
        max_length (int): Maximum number of messages to store
        messages (List[str]): List of messages in the conversation history
    """

    def __init__(self, username: str, agent_name: str, max_length: int):
        self.username = username
        self.agent_name = agent_name
        self.max_length = max_length
        self.messages = []

    def update_history(self, user_input: str, agent_response: str) -> None:
        """
        Updates the conversation history with a new message.
        
        Args:
            user_input: The user's message
            agent_response: The agent's response
        """
        if len(self.messages) >= self.max_length:
            self.messages.pop(0)  # Remove oldest message if max length exceeded
        self.messages.append(f"{self.username}>: {user_input}")
        self.messages.append(f"{self.agent_name}>: {agent_response}")

    def show_history(self) -> str:
        """
        Returns the conversation history as a formatted string.
        
        Returns:
            String containing the conversation history
        """
        return "\n".join(self.messages)


class Agent:
    """
    Represents an AI agent with a personality, tools, and conversation capabilities.

    This class handles the agent's interactions with the user, including processing
    messages, managing tools, and maintaining conversation history.

    The agent maintains state, processes user messages, manages tools, and generates
    context-aware responses while staying in character. It can dynamically:
    - Select and execute tools from its cyberdeck
    - Maintain conversation context
    - Update its system prompt based on current state

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
        conversation_history (List[str]): Record of conversation exchanges
    """

    def __init__(self, agent: dict, username: str, model: str, tools: List[callable], temperature: float = 0.6):
        """
        Initialize a new Agent instance.
        
        Args:
            agent: Dictionary containing agent personality details
            username: Name of the user interacting with the agent
            model: LLM model to use for generating responses
            tools: List of callable tools available to the agent
            temperature: Temperature setting for response generation (0.0-1.0)
        """

        self.MAX_HISTORY_LENGTH = 1000  # Maximum conversation history entries

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
        self.conversation_history = Message(self.username, self.first_name,self.MAX_HISTORY_LENGTH)
        #self.conversation_history = []  # Initialize conversation history as a list

        # Initialize tool system
        logger.debug(f"Initializing toolbox with {len(tools)} tools: [{tools}]")
        self.toolbox = Toolbox(tools)
        self.custom_tools = {} # Storage for dynamically created tools
        self.tool_descriptions = self.toolbox.prepare_agent_tools()

        # System state
        self.intro_given = False
        self.operating_system = platform.system()  

        self.introduction = (f"Introduce yourself to {self.username}. "
                           "Keep it short and describe how you can assist.")
        self.user_prompt = ""

        #self.agent_introduction(self)

    def check_json_response(self, response: str) -> Dict:
        """
        Checks if the response contains a valid JSON object and extracts fields.
        """
        try:
            logger.debug(f"Raw response before parsing: {response}")
            
            # Sanitize the response to escape invalid characters and fix unterminated strings
            sanitized_response = response.replace('\\"', '"')  # Unescape any escaped quotes
            sanitized_response = re.sub(r'(?<!\\)"([^"]*?)$', r'"\1"', sanitized_response)  # Fix missing closing quotes
            
            json_patterns = [
                r"```json\s*(\{.*?\})\s*```",  # JSON between ```json ``` blocks
                r"json\s*(\{.*?\})\s*",        # JSON after json keyword
                r"```(\{.*?\})\s*```",         # JSON between ``` blocks
                r"(\{.*?\})\s*",               # JSON between curly braces
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, sanitized_response, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                    logger.debug(f"Sanitized JSON string: {json_str}")
                    response_data = json.loads(json_str)  # Parse the JSON
                    logger.debug(f"Parsed JSON data: {response_data}")
                    return {
                        "tool_choice": response_data.get("tool_choice"),
                        "tool_input": response_data.get("tool_input"),
                        "agent_response": response_data.get("agent_response")
                    }
            
            # If no JSON block found, treat as plain text
            logger.debug("No JSON block found, treating as plain text")
            return {
                "tool_choice": "None",
                "tool_input": "None",
                "agent_response": response.strip()
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return {
                "tool_choice": "None",
                "tool_input": "None",
                "agent_response": f"Error parsing JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "tool_choice": "None",
                "tool_input": "None",
                "agent_response": f"Error processing response: {str(e)}"
            }


    def choose_agent_tools(self, agent_response: dict) -> dict:
        """
        Chooses the appropriate tool to use based on the agent's response.
    
        Args:
            agent_response: The agent's response containing tool choice and input
        
        Returns:
            dict: Response containing tool choice, input, and agent response
        """
         
        try:
            # Extract the content from the message structure
            logger.debug(f"Received agent_respose: {agent_response}")
            tool_choice = agent_response.get('tool_choice')
            tool_input = agent_response.get('tool_input')
            agent_resp_text = agent_response.get('agent_response')
            
            logger.debug(f"Extracted fields - tool: {tool_choice}, input: {tool_input}, response: {agent_resp_text}")
            if tool_choice == "None":
                logger.debug("No tool choice found or explicitly no tool")
                return {
                    "tool_choice": "None",
                    "tool_input": "None",
                    "agent_response": agent_resp_text
                }
            # Check if tool exists and execute it
            if self.toolbox.check_tool_exists(tool_choice):
                logger.debug(f"Executing tool: {tool_choice}")
                return self.toolbox.execute_tool(tool_choice, tool_input)
            # Tool wasn't found
            logger.warning(f"Tool not found: {tool_choice}")
            return {
                "tool_choice": "None",
                "tool_input": "None",
                "agent_response": f"I don't have access to the tool '{tool_choice}'"
        }
            
        except Exception as e:
            logger.error(f"Error in choose_agent_tools: {str(e)}")
            return {
                "tool_choice": "None",
                "tool_input": "None",
                "agent_response": f"Error processing tool request: {str(e)}"
        }
        

    def update_system_prompt(self) -> None:
        """
        Updates the system prompt with the description of the agent and includes the conversation history.
        """
        day_of_week = datetime.now().strftime('%A')
        date_today = date.today()
        self.system_prompt = textwrap.dedent(rf"""
        ### Current Date and Time        
        Today is {day_of_week}, {date_today}.                                    
        ### Identity
        Your name is {self.first_name}. You are {self.age} years old, {self.sex}, and currently live in {self.city}, {self.country}.
        {self.description}.
        You are a cyberpunk edgerunner and a helpful assistant with access to a toolbox as part of your cyberdeck.
        Your personality is {self.personality}.
        You always think step by step and talk in character. Be sharp-tongued, confident, and a bit cheeky in your responses.
        ### Mission
        If you don't know the answer to a user's question, you will try to use an available tool from your cyberdeck. 
        Otherwise, ask the user for more information.
        You will always provide a JSON object as your response with the following structure
        '''json{{
            "tool_choice": "name_of_the_tool",
            "tool_input": "inputs_to_the_tool",
            "agent_response": "The response to the user"
        }}'''
        You will always use the same format for your responses, even if the user doesn't ask for it.
        ### Toolbox    
        Your cyberdeck is your toolbox and operates on {self.operating_system}, enabling you to assist the user effectively.
        When the user asks what tools you have, you will provide a list of the tools available in your toolbox.
        The list of your tools available along with their descriptions:
        ### Tools
        {self.tool_descriptions}
        ### Tool Management
        Please make a decision based on the provided user query and your available tools.
        
        1. Given a user query, you will determine which tool, if any, is best suited to answer the query.
        
        - `tool_choice`: The name of the tool you want to use. It must be a tool from your toolbox
                        or "None" if you do not need to use a tool.
        - `tool_input`: The specific inputs required for the selected tool. If there are no inputs required set to "None"
        - `agent_response` : If no tool is used, just provide a direct response to the query.

        2. When responding to the user you must always provide a JSON object as your response with the following structure:
        '''json{{
            "tool_choice": "name_of_the_tool",
            "tool_input": "inputs_to_the_tool",
            "agent_response": "The response to the user"
        }}'''
        
        ### Response Format when no tool is used or is not needed or available
        
        '''json{{
            "tool_choice": "None",
            "tool_input":  "None",
            "agent_response": "The response to the user"
        }}'''

        ### Response Format when a tool is used
        '''json{{
            "tool_choice": "calculator",
            "tool_input":  "2+2",
            "agent_response": "The result is 4"
        }}'''        

        When you use a tool, always remember to format the output of the tool to be easy to read and understand.
        If the tool output is too long, you will summarize it and provide the most relevant information to the user.
        If the tool output is a list, you will always provide the first 10 items of the list and say that there are more items.
        
        ### Conversation History
        You will always read the conversation history below and remember the details so you can respond to the user with accurate information.
        The conversation history between {self.username} and {self.first_name} is below:
        <conversation_history>
        {self.conversation_history.show_history()}
        </conversation_history>
        """)

    def show_system_prompt(self) -> str: 
        """
        Returns the current system prompt.
        
        Returns:
            String containing the system prompt
        """
        return self.system_prompt    

    def llm_response(self, model: str) -> dict:
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
                    'content': f"```json\n{{\n\"tool_choice\": \"None\",\n\"tool_input\": \"None\",\n\"agent_response\": \"I'm sorry, I encountered an error: {str(e)}\"\n}}\n```"
                }
            }


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
            response = self.llm_response(self.model)['message']['content']
            parsed_response = self.check_json_response(response)
            agent_resp_text = parsed_response.get('agent_response')
            logger.debug(f"Agent introduction: {agent_resp_text}")
            self.conversation_history.update_history("", agent_resp_text)
            self.update_system_prompt()
            logger.debug(f"Agent introduction: {agent_resp_text}")
            return f"{self.first_name}>: {agent_resp_text}"
        return None

    def agent_response(self, user_input: str) -> str:
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
        raw_response = self.llm_response(self.model)['message']['content']
        logger.debug(f"Initial response: {raw_response}")

        # Extract and log the <think> section
        think_match = re.search(r"<think>(.*?)</think>", raw_response, re.DOTALL)
        think_text = "None"
        if think_match:
            think_text = think_match.group(1).strip()
            logger.debug(f"Think section: {think_text}")
            print(f"Think: {think_text}")  # Print the <think> section for visibility

        # Check for JSON response and extract fields
        response = self.check_json_response(raw_response)
        logger.debug(f"Checked response: {response}")

        # Process tool usage if any
        tool_response = self.choose_agent_tools(response)
        logger.debug(f"Tool response: {tool_response}")

        # Handle case where no tool is used   
        if tool_response.get('tool_choice') == "None":
            return self.handle_no_tool_response(user_input, tool_response)
        else:
            # Handle case where a tool is used
            return self.handle_tool_response(user_input, tool_response)

    
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
        self.conversation_history.update_history(user_input, agent_response_text)
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
            response = self.llm_response(self.model)['message']['content']
            agent_response=self.check_json_response(response)
            agent_resp_text = agent_response.get('agent_response')
            self.conversation_history.update_history(user_input, agent_resp_text)
            self.update_system_prompt()
            return f"{self.first_name}>: {agent_resp_text}"
        except Exception as e:
            logger.error(f"Error processing tool response: {str(e)}")
            return f"I'm sorry, I encountered an error: {str(e)}"

    def show_agent_details(self) -> str:
        """
        Returns a formatted string with the agent's details.
        
        Returns:
            String containing the agent's details
        """
        
        # Format the agent's details
        details = [
            f"Agent ID:        {self.agent_id}",
            f"Name:            {self.first_name} {self.last_name}",
            f"Sex:             {self.sex}",
            f"Age:             {self.age}",
            f"Personality:     {self.personality}",
            f"Description:     {self.description}",
            f"System Prompt:   {self.system_prompt}",
            f"User Prompt:     {self.user_prompt}",
            f"Temperature:     {self.temperature}",
            f"Tools available: {len(self.toolbox) + len(self.custom_tools)}"
        ]
        return f"\n".join(details)
