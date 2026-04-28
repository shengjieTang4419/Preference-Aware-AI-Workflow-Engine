from abc import ABC, abstractmethod
from typing import Optional
from crewai import LLM


class BaseLLMProvider(ABC):
    
    @abstractmethod
    def create_llm(self, model: str, **kwargs) -> LLM:
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass
    
    @abstractmethod
    def get_available_models(self) -> list[str]:
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        pass
