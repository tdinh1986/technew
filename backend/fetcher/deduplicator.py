from __future__ import annotations

from sqlalchemy.orm import Session

from fetcher.base import RawArticle, url_hash
from models.orm import Article


def deduplicate(articles: list[RawArticle], db: Session) -> list[RawArticle]:
    if not articles:
        return []
    hashes = {url_hash(a.url) for a in articles}
    existing = {
        row.url_hash
        for row in db.query(Article.url_hash).filter(Article.url_hash.in_(hashes))
    }
    return [a for a in articles if url_hash(a.url) not in existing]
