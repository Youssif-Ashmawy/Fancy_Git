from abc import ABC, abstractmethod
from typing import Optional

class BaseModel(ABC):
    """Base class for AI models"""
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the AI model is accessible and working"""
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """Get information about the current model"""
        pass

    @abstractmethod
    def _call_model(self, prompt: str) -> Optional[str]:
        """Make an API call to the model and return the response text"""
        pass