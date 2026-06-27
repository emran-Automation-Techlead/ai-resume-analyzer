from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str
    openai_model: str = "gpt-4o"
    claude_model: str = "claude-sonnet-4-6"
    max_resume_size_mb: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
