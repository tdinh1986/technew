from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str
    news_api_key: str = ""
    database_url: str = "sqlite:///./technew.db"
    fetch_interval_hours: int = 6
    rss_feed_urls: str = ""

    @property
    def rss_feeds(self) -> list[str]:
        return [
            stripped for u in self.rss_feed_urls.split(",") if (stripped := u.strip())
        ]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
