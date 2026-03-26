from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from config import Settings, get_settings
from db import SessionLocal
from summarizer.client import AnthropicLLMClient, LLMClient


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    return AnthropicLLMClient(api_key=settings.anthropic_api_key)
