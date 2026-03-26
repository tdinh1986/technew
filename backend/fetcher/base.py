from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawArticle:
    url: str
    title: str
    snippet: str
    source_name: str
    published_at: datetime | None = None


class AbstractFetcher(ABC):
    @abstractmethod
    async def fetch(self) -> list[RawArticle]:
        """Fetch articles from the source. Returns empty list on error."""


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()
