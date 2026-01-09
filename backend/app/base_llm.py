from abc import ABC, abstractmethod
from typing import List
from langchain_core.messages import BaseMessage


class BaseLLMWrapper(ABC):
    """
    Base class for all transformer based models.
    """
    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    def unload_model(self):
        pass

    @abstractmethod
    def generate(self, messages: List[BaseMessage]) -> str:
        """
        Takes conversation history and returns a string response.
        TODO: Potential update to return structured tool calls
        """
        pass
