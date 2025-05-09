import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class Toolbox:
    """
    Toolbox class that contains all tools.
    """

    def __init__(self, tools: Optional[List[callable]] = None):
        """
        Initialize a new Toolbox instance.
        
        Args:
            tools (Optional[List[callable]]): Initial list of tools to add to the toolbox.
                If None, starts with an empty toolbox.
        """
        self.toolbox = []
        self.custom_tools = {}
        if tools:
            self.add_tools(tools)
        logger.debug(f"Toolbox initialized with tools: {self.toolbox}")

    def add_tool(self, tool):
        """
        Adds a tool to the toolbox.

        Args:
            tool: Tool to add to the toolbox
        """
        self.toolbox.append(tool)
        logger.debug(f"Tool {tool.__name__} added to the toolbox")

    def add_tools(self, toollist):
        """
        Adds a list of tools to the toolbox.

        Args:
            toollist: List of tools to add to the toolbox
        """
        for tool in toollist:
            self.add_tool(tool)

    def remove_tool(self, tool):
        """
        Removes a tool from the toolbox.

        Args:
            tool: Tool to remove from the toolbox
        """
        self.toolbox.remove(tool)
        logger.debug(f"Tool {tool.__name__} removed from the toolbox")

    def add_custom_tool(self, name, doc):
        """
        Adds a custom tool to the toolbox.

        Args:
            name: Name of the custom tool
            doc: Description of the custom tool
        """
        self.custom_tools[name] = doc
        logger.debug(f"Custom tool {name} added to the toolbox")

    def prepare_agent_tools(self) -> str:
        """
        Prepares descriptions of all available tools.
        
        Returns:
            str: A formatted string containing all tool descriptions.
        """
        toolbox_dict = {tool.__name__: tool.__doc__.strip() for tool in self.toolbox}
        return "\n".join([f"{name}: {doc}" for name, doc in toolbox_dict.items()])

    def get_tool_list(self) -> str:
        """
        Returns a list of all available tools in the toolbox.
        
        Returns:
            str: A formatted string containing all tool names.
        """
        tool_list = [tool.__name__ for tool in self.toolbox]
        return "\n".join(tool_list)
        logger.debug(f"Tool list: {tool_list}")
    
    def check_tool_exists(self, tool_choice: str) -> bool:
        """
        Check whether the tool exists in our toolbox.
        
        Args:
            tool_choice: The name of the tool to check
            
        Returns:
            bool: True if the tool exists, False otherwise
        """
        exists = tool_choice in [tool.__name__ for tool in self.toolbox]
        logger.debug(f"Tool {tool_choice} {'found' if exists else 'not found'} in the toolbox.")
        return exists
        
    def __len__(self) -> int:
        """
        Returns the number of tools in the toolbox.
        
        Returns:
            int: Number of tools in the toolbox
        """
        return len(self.toolbox)

    def execute_tool(self, tool_choice: str, tool_input: str) -> dict:
        """
        Executes the specified tool if it exists.
        
        Args:
            tool_choice: The name of the tool to execute
            tool_input: The input to provide to the tool
            
        Returns:
            dict: The result of the tool execution
        """
        for tool in self.toolbox:
            if tool.__name__ == tool_choice:
                logger.debug(f"Executing tool {tool_choice} with input: {tool_input}")
                try:
                    # Check if the tool requires input
                    if tool_input and tool_input != "None":
                        # If the tool requires input, pass it to the tool
                        tool_output = tool(tool_input)
                    else:
                        # If the tool doesn't require input, call it without arguments
                        tool_output = tool()
                    logger.debug(f"Executed tool {tool_choice} with output: {tool_output}")
                    return {"tool_choice": tool_choice, "tool_input": tool_input, "tool_output": tool_output}
                except TypeError as e:
                    logger.error(f"Error executing tool {tool_choice}: {str(e)}")
                    return {"tool_choice": "None", "tool_input": "None", "tool_output": f"Error: {str(e)}"}

        # Fallback if for some reason the tool wasn't executed.
        logger.debug("Tool not executed. Returning default response.")
        return {"tool_choice": "None", "tool_input": "None", "tool_output": "None"}
