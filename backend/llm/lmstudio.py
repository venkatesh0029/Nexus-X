import os
import requests
from langchain_openai import ChatOpenAI
from .base import BaseLLMAdapter

class LMStudioAdapter(BaseLLMAdapter):
    def __init__(self, base_url: str = None, model: str = "local-model", temperature: float = 0.1, max_tokens: int = 1024):
        self.base_url = base_url or os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = self._get_active_model(model)

    def _get_active_model(self, fallback_model: str) -> str:
        """
        Dynamically queries LM Studio for the currently loaded model ID.
        Newer versions of LM Studio reject the 'local-model' alias.
        """
        try:
            response = requests.get(f"{self.base_url}/models", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data and "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["id"]
        except Exception as e:
            print(f"Warning: Could not fetch active model from LM Studio: {e}")
        return fallback_model

    def get_model(self) -> ChatOpenAI:
        return ChatOpenAI(
            base_url=self.base_url,
            api_key="lm-studio", # LM Studio doesn't require a real key
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
