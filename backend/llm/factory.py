import yaml
import os
from typing import Dict, Any
from .base import BaseLLMAdapter
from .lmstudio import LMStudioAdapter
from .llamacpp import LlamaCPPAdapter
from langchain_openai import ChatOpenAI

class LLMFactory:
    @staticmethod
    def _load_config() -> Dict[str, Any]:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception:
            return {}

    @staticmethod
    def get_adapter() -> BaseLLMAdapter:
        config = LLMFactory._load_config()
        llm_config = config.get("llm", {})
        
        provider = llm_config.get("default_provider", "lm_studio")
        model = llm_config.get("model", "local-model")
        temperature = llm_config.get("temperature", 0.1)
        max_tokens = llm_config.get("max_tokens", 1024)

        if provider == "lm_studio":
            return LMStudioAdapter(model=model, temperature=temperature, max_tokens=max_tokens)
        elif provider == "llamacpp":
            return LlamaCPPAdapter(model=model, temperature=temperature, max_tokens=max_tokens)
        elif provider == "openai":
            # Direct mapping without custom adapter wrapper
            class OpenAIAdapter(BaseLLMAdapter):
                def get_model(self):
                    return ChatOpenAI(
                        api_key=os.environ.get("OPENAI_API_KEY", "dummy"),
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
            return OpenAIAdapter()
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

    @staticmethod
    def get_model():
        adapter = LLMFactory.get_adapter()
        primary_model = adapter.get_model()
        
        # Implement robust fallback to llama.cpp if LM Studio fails
        # Assuming Llama.cpp is the designated secondary local engine per roadmap
        if isinstance(adapter, LMStudioAdapter):
            try:
                fallback_adapter = LlamaCPPAdapter()
                fallback_model = fallback_adapter.get_model()
                return primary_model.with_fallbacks([fallback_model])
            except Exception as e:
                # If fallback fails to instantiate, just return primary
                print(f"Failed to initialize fallback model: {e}")
                
        return primary_model
        
    @staticmethod
    async def test_connection() -> bool:
        """
        Pings the primary LLM to ensure it is awake and loaded before accepting tasks.
        """
        try:
            model = LLMFactory.get_model()
            # A tiny payload just to check network/model health
            response = await model.ainvoke("ping")
            if response:
                return True
        except Exception as e:
            print(f"[CRITICAL] LLM Health Check Failed: {e}")
        return False
