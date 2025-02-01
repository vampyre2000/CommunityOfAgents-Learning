import re
message=["tool_choice":"TimeKeeper","tool_input":"None"]
#tool_descriptions = self.prepare_agent_tools()
print(f"choose_agent_tools: {message['message']['content']}")
match = re.search(r'"tool_choice":\s*"([^"]+)"', agent_response['message']['content'])
if match:
    tool_choice = match.group(1)
    print(f"choose_agent_tools: Tool choice: {tool_choice}")
