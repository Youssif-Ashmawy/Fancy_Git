from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """Base class for AI models"""
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the AI model is accessible and working"""
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """Get information about the current model"""
        pass

    # @abstractmethod
    # def analyze_error_messages(self, messages: list[dict]) -> str:
    #     """Analyze error/warning messages and provide insights"""
    #     pass

    # @abstractmethod
    # def _build_analysis_prompt(self, messages: list[dict]) -> str:
    #     """Build a prompt for analyzing error messages"""
    #     pass

    # @abstractmethod
    # def build_explain_prompt(self, error_message: dict) -> str:
    #     """Build a prompt for explaining a specific error message"""
    #     pass