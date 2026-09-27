from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str
    tavily_api_key: str
    groq_model: str
    max_search_queries: int = 4
    max_results_per_query: int = 5
    max_sources: int = 12
    max_content_chars: int = 9000
    request_timeout_seconds: int = 15
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
