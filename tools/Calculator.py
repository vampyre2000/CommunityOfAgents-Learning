import logging
import re
from typing import Union, List, Dict, Any
import math

logger = logging.getLogger(__name__)

def tokenize(expression: str) -> List[str]:
    """
    Tokenize the expression into numbers, operators, and functions.
    
    Args:
        expression: The mathematical expression to tokenize
        
    Returns:
        List of tokens
    """
    # Add spaces around operators and parentheses for easier tokenization
    expression = re.sub(r'([+\-*/^(),%])', r' \1 ', expression)
    # Handle negative numbers
    expression = re.sub(r'(\s+)-(\s+)?(\d+)', r' - \3', expression)
    # Split by whitespace
    tokens = expression.split()
    return tokens

def calculate(expression: str) -> str:
    """
    Evaluates a mathematical expression and returns the result.
    
    Args:
        expression: A mathematical expression as a string (e.g., "2 + 2", "5 * (3 + 2)")
        
    Returns: str: The result of the calculation or an error message
    """
    try:
        # Clean the expression
        expression = expression.strip().lower()
        
        # Check for empty expression
        if not expression:
            return "Please provide a mathematical expression."
        
        # Replace common mathematical terms
        expression = expression.replace('pi', str(math.pi))
        expression = expression.replace('e', str(math.e))
        
        # Handle square root
        expression = re.sub(r'sqrt\s*\(\s*([^)]+)\s*\)', r'(\1)**0.5', expression)
        
        # Handle trigonometric functions
        expression = re.sub(r'sin\s*\(\s*([^)]+)\s*\)', r'math.sin(\1)', expression)
        expression = re.sub(r'cos\s*\(\s*([^)]+)\s*\)', r'math.cos(\1)', expression)
        expression = re.sub(r'tan\s*\(\s*([^)]+)\s*\)', r'math.tan(\1)', expression)
        
        # Handle logarithmic functions
        expression = re.sub(r'log\s*\(\s*([^)]+)\s*\)', r'math.log10(\1)', expression)
        expression = re.sub(r'ln\s*\(\s*([^)]+)\s*\)', r'math.log(\1)', expression)
        
        # Replace ^ with ** for exponentiation
        expression = expression.replace('^', '**')
        
        # Evaluate the expression
        result = eval(expression, {"__builtins__": None}, {"math": math})
        
        # Format the result
        if isinstance(result, (int, float)):
            # For integers, return as integer
            if result == int(result):
                return str(int(result))
            # For floating point, limit to 6 decimal places
            return f"{result:.6f}".rstrip('0').rstrip('.') if '.' in f"{result:.6f}" else f"{result:.6f}"
        else:
            return str(result)
    
    except SyntaxError:
        return "Syntax error in the expression. Please check your input."
    except (ValueError, TypeError):
        return "Invalid values in the expression. Please check your input."
    except ZeroDivisionError:
        return "Division by zero is not allowed."
    except Exception as e:
        logger.error(f"Error in calculate: {str(e)}")
        return f"Error calculating result: {str(e)}"

if __name__ == "__main__":
    # Test the calculator
    test_expressions = [
        "2 + 2",
        "5 * (3 + 2)",
        "10 / 2",
        "2^3",
        "sqrt(16)",
        "sin(0)",
        "log(100)",
        "pi * 2",
        "1/0"  # This should return an error
    ]
    
    for expr in test_expressions:
        print(f"{expr} = {calculate(expr)}")
