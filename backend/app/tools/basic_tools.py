from langchain_core.tools import tool
import logging
from typing import List

logger = logging.getLogger(__name__)

@tool
def add_numbers(numbers: List[int]) -> int:
    """
    Adds a list of numbers and returns the sum.
    Useful for sanity checking tool execution.
    """
    logger.info(f"Tool execution: add_numbers for {numbers}")
    try:
        # Ensure input is a list of numbers
        if not isinstance(numbers, list):
            # Try to cast if it's a string representation? 
            # For now, assume the parser handles it or we fail.
            pass
        return sum(numbers)
    except Exception as e:
        logger.error(f"Error in add_numbers: {e}")
        return f"Error adding numbers: {e}"
