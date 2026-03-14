from openai import OpenAI
from src.config_manager import ConfigManager

class OpenAIModel:
    def __init__(self, model_name: str = "gpt4all", config_manager: ConfigManager = ConfigManager()):
        self.config_manager = config_manager
        self.api_key = self.config_manager.config.openai_api_key
        self.client = OpenAI(api_key=self.api_key)

    def analyze_error_messages(self, error_messages: list[dict]) -> str:
        """Use OpenAI to analyze error messages and provide insights"""
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured. Please set it in .fancygit_config")

        # Prepare the prompt for the AI model
        prompt = "Analyze the following Git error messages and provide insights:\n\n"
        for error in error_messages:
            prompt += f"- {error['severity'].upper()}: {error['message']} (File: {error.get('file', 'N/A')}, Line: {error.get('line', 'N/A')})\n"

        prompt += "\nProvide possible causes and solutions for these errors."

        # Call the OpenAI API to get insights
        try:
            response = self.client.chat.completions.create(
                model=self.config_manager.config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return "Failed to analyze error messages due to an API error."