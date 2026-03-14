from abc import ABC, abstractmethod
from langchain_core.language_models.chat_models import BaseChatModel

class BaseLLMAdapter(ABC):
    @abstractmethod
    def get_model(self) -> BaseChatModel:
        """Returns the underlying LangChain chat model."""
        pass
