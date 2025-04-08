import json
import re
import logging
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_json_response(response: str) -> Dict[str, Any]:
    """
    Checks if the response contains a valid JSON object and extracts fields.
    
    Args:
        response: The response string that may contain JSON
        
    Returns:
        Dict containing tool_choice, tool_input, and agent_response
    """
    try:
        logger.debug(f"Processing response: {response}")
        
        # Look for JSON block between backticks
        match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            logger.debug(f"Found JSON between backticks: {json_str}")
            
            # Try to parse the JSON string
            response_data = json.loads(json_str)
            logger.debug(f"Parsed JSON data: {response_data}")
            
            # Extract fields directly from response_data
            return {
                "tool_choice": response_data.get("tool_choice"),
                "tool_input": response_data.get("tool_input"),
                "agent_response": response_data.get("agent_response")
            }
        
        # If no JSON block found, treat entire response as plain text
        logger.debug("No JSON block found, treating as plain text")
        return {
            "tool_choice": None,
            "tool_input": None,
            "agent_response": response.strip()
        }
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return {
            "tool_choice": None,
            "tool_input": None,
            "agent_response": f"Error parsing JSON: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "tool_choice": None,
            "tool_input": None,
            "agent_response": f"Error processing response: {str(e)}"
        }

def run_tests():
    """Run test cases for the JSON response checker"""
    test_cases = [
        (
            """```json
            {"tool_choice": "browser", "tool_input": "search('latest news')"}
            ```""",
            "Valid JSON with tool choice"
        ),
        (
            "Plain text response",
            "Non-JSON response"
        ),
        (
            """```json
            {"invalid": json}
            ```""",
            "Invalid JSON"
        )
    ]
    
    for test_input, test_name in test_cases:
        print(f"\nTesting: {test_name}")
        result = check_json_response(test_input)
        print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()