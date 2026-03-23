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

    # Provider routing — controls which provider each AIEngine task uses
    analysis_provider: str = "ollama"       # handles git error analysis
    explanation_provider: str = "ollama"    # handles 'explain' command
    translation_provider: str = "ollama"    # reserved for future use

    default_ollama_model: str = "llama3.2" 
    ollama_api_url: str = "http://localhost:11434"
    ollama_timeout: int = 30
    ollama_max_retries: int = 3
    ollama_temperature: float = 0.3
    ollama_max_tokens_to_sample: int = 500

    openai_api_key: str = "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"
    open_ai_api_base: str = ""
    default_openai_model: str = "gpt-4"  # For future OpenAI integration
    openai_temperature: float = 0.3  # For future OpenAI integration
    openai_max_tokens_to_sample: int = 300  # For future OpenAI integration

    model_provider: str = "ollama"  # Options: 'ollama', 'openai', 'anthropic'

    anthropic_api_key: str = ""  # For future Anthropic integration
    anthropic_api_base: str = ""  # For future Anthropic integration
    anthropic_max_tokens_timeout: int = 5  # Represents the max tokens timeout for Anthropic API calls during connection tests
    default_anthropic_model: str = "claude-2"  # For future Anthropic integration
    anthropic_temperature: float = 0.3  # For future Anthropic integration
    anthropic_max_tokens_to_sample: int = 300  # For future Anthropic integration