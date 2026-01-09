from abc import ABC, abstractmethod
from typing import Dict, Any

from ..base_llm import BaseLLMWrapper

class BaseNode(ABC):
    """
    Abstract base class for LangGraph nodes.
    """    
    def __init__(self, model: BaseLLMWrapper = None, name: str = "node"):
        self.model = model
        self.name = name

    @abstractmethod
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Entry point for LangGraph execution"""
        pass