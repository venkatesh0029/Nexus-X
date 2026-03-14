import os
from langchain_openai import ChatOpenAI
from .base import BaseLLMAdapter

class LlamaCPPAdapter(BaseLLMAdapter):
    def __init__(self, base_url: str = None, model: str = "local-model", temperature: float = 0.1, max_tokens: int = 1024):
        self.base_url = base_url or os.environ.get("LLAMACPP_URL", "http://localhost:8080/v1")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_model(self) -> ChatOpenAI:
        return ChatOpenAI(
            base_url=self.base_url,
            api_key="llama-cpp", # llama.cpp doesn't require a real key
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
