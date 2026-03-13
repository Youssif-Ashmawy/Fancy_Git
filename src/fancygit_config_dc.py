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
    default_model: str = "llama3.2" 