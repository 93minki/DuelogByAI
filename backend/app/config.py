from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    database_url: str = "postgresql+asyncpg://duelog:duelog@localhost:5432/duelog"

    jwt_secret: str = "change-me"
    jwt_expire_days: int = 7
    cookie_name: str = "duelog_token"
    cookie_secure: bool = False

    openai_api_key: str = ""
    openai_model_moderator: str = "gpt-5-mini"
    openai_model_debater: str = "gpt-5"
    openai_model_summary: str = "gpt-5-mini"

    exa_api_key: str = ""
    exa_num_results: int = 5

    typesafe_api_key: str = ""
    typesafe_base_url: str = "https://api.typesafe.ai"
    jev_model: str = "jev-latest"
    jev_min_confidence: float = 0.6

    daily_debate_limit: int = 10
    max_search_calls_per_turn: int = 20

    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def checkpoint_db_url(self) -> str:
        """psycopg(LangGraph 체크포인터)용 접속 문자열."""
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
