from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SourceCreate(BaseModel):
    type: Literal["rss", "newsapi", "hackernews"]
    url: str
    name: Optional[str] = None


class SourceUpdate(BaseModel):
    enabled: Optional[bool] = None
    url: Optional[str] = None
    name: Optional[str] = None


class SourceOut(BaseModel):
    id: str
    type: str
    url: str
    name: Optional[str] = None
    enabled: bool
    last_fetched_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TopicFilterCreate(BaseModel):
    keyword: str


class TopicFilterOut(BaseModel):
    id: str
    keyword: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiResponse(BaseModel, Generic[T]):
    data: Optional[T]
    error: Optional[str] = None
    meta: dict[str, Any] = {}


class ArticleOut(BaseModel):
    id: str
    title: str
    source: str
    url: str
    bullets: list[str]

    model_config = {"from_attributes": True}


class ActionableInsight(BaseModel):
    type: Literal["Apply", "Read More"]
    text: str


class TopicSectionOut(BaseModel):
    topic: str
    article_count: int
    actionable_insight: ActionableInsight
    articles: list[ArticleOut]


class DigestReportOut(BaseModel):
    id: str
    created_at: datetime
    article_count: int
    topic_sections: list[TopicSectionOut]

    model_config = {"from_attributes": True}


class DigestReportListItem(BaseModel):
    id: str
    created_at: datetime
    article_count: int

    model_config = {"from_attributes": True}


class FetchJobOut(BaseModel):
    id: str
    status: Literal["queued", "running", "done", "failed"]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    articles_added: Optional[int] = None
    error_message: Optional[str] = None
    report_id: Optional[str] = None

    model_config = {"from_attributes": True}


class UrlDigestRequest(BaseModel):
    urls: list[str]

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return cls(**v) if isinstance(v, dict) else v

    def model_post_init(self, __context: Any) -> None:
        if not self.urls:
            raise ValueError("urls must not be empty")
        if len(self.urls) > 20:
            raise ValueError("urls must contain at most 20 items")
        for url in self.urls:
            if not (url.startswith("http://") or url.startswith("https://")):
                raise ValueError(f"Invalid URL (must start with http/https): {url}")
