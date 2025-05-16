import logging
import ollama
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

def analyze_response(data: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    Analyzes an agent response to check for correctness and suggests improvements if needed.
    
    Args:
        data: Dictionary containing the user_question and agent_response, or a string with the response to analyze
        
    Returns:
        Dictionary with analysis results and potentially corrected response
    """
    try:
        # Handle both dictionary and string inputs
        if isinstance(data, str):
            agent_response = data
            user_question = "Unknown question"
            model = "qwen3:8b"  # Default model
        else:
            user_question = data.get("user_question", "")
            agent_response = data.get("agent_response", "")
            model = data.get("model", "qwen3:8b")
        
        # Create a system prompt for the analyzer
        system_prompt = """
        You are a response analyzer. Your job is to:
        1. Check if the provided response correctly answers the user's question while staying in character
        2. Identify errors or inconsistencies but stay in character
        3. Suggest improvements or corrections if needed
        4. Ensure the information is correctly formatted
        
        Return your analysis in the following JSON format:
        {
            "is_correct": true/false,
            "issues": ["issue1", "issue2", ...],
            "corrected_response": "improved response if needed"
        }
        
        If the response is correct, set "is_correct" to true and leave "issues" as an empty list.
        If the response is incorrect or could be improved, set "is_correct" to false, list the issues,
        and provide a corrected response.
        """
        
        # Context for the analyzer
        context = f"""
        USER QUESTION: {user_question}
        
        AGENT RESPONSE: {agent_response}
        
        While staying in character, analyze the agent's response to determine if it answers the user's question.
        Check logical consistency and ensure the format is easy to read.
        """
        
        # Get analysis from the model
        analysis = ollama.chat(
            model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': context}
            ],
            options={'temperature': 0.3}  # Lower temperature for more consistent analysis
        )
        
        # Extract the analysis result
        analysis_text = analysis['message']['content']
        
        # Parse the JSON response
        import json
        import re
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
        if json_match:
            try:
                analysis_json = json.loads(json_match.group(0))
                
                # Ensure all expected fields are present
                analysis_json.setdefault("is_correct", True)
                analysis_json.setdefault("issues", [])
                analysis_json.setdefault("corrected_response", agent_response)
                
                return {
                    "original_response": agent_response,
                    "is_correct": analysis_json.get("is_correct", True),
                    "issues": analysis_json.get("issues", []),
                    "corrected_response": analysis_json.get("corrected_response", agent_response),
                    "user_question": user_question,
                    "raw_analysis": analysis_text
                }
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from analysis")
        
        # Fallback if JSON parsing fails
        return {
            "original_response": agent_response,
            "is_correct": True,  # Assume correct if we can't parse the analysis
            "issues": ["Failed to parse analysis result"],
            "corrected_response": agent_response,
            "user_question": user_question,
            "raw_analysis": analysis_text
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_response: {str(e)}")
        return {
            "error": f"Error analyzing response: {str(e)}",
            "original_response": agent_response,
            "is_correct": True,  # Default to assuming correct on error
            "issues": [f"Error during analysis: {str(e)}"],
            "corrected_response": agent_response,
            "user_question": user_question if 'user_question' in locals() else "Unknown"
        }
