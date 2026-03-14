from dataclasses import dataclass

@dataclass
class FancyGitConfig:
    confirmation_enabled: bool = True
    ai_analysis_enabled: bool = True
    loading_animation: str = "run"
    max_visualization_commits: int = 40
    days_for_insights: int = 30
    default_insights_output_format: str = "console"
    open_browser_for_insights: bool = True
    default_ollama_model: str = "llama3.2" 
    openai_api_key: str = ""  # For future OpenAI integration
    open_ai_api_base: str = ""  # For future OpenAI integration
    model_provider: str = "ollama"  # Options: 'ollama', 'openai', 'anthropic'
    anthropic_api_key: str = ""  # For future Anthropic integration
    anthropic_api_base: str = ""  # For future Anthropic integration