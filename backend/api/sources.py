from __future__ import annotations

import logging

import feedparser
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db
from models.orm import Source
from models.schemas import ApiResponse, SourceCreate, SourceOut, SourceUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def _validate_rss_feed(url: str) -> str | None:
    """Return None if valid, or an error message string if invalid."""
    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        return f"Could not fetch feed: {exc}"
    if getattr(feed, "bozo", False) and getattr(feed, "bozo_exception", None):
        return f"Malformed RSS feed: {feed.bozo_exception}"
    if not getattr(feed, "entries", []):
        return "RSS feed has no entries"
    return None


def _source_to_out(source: Source) -> SourceOut:
    return SourceOut.model_validate(source)


@router.post("/sources", response_model=ApiResponse[SourceOut])
def create_source(body: SourceCreate, db: Session = Depends(get_db)):
    if body.type == "rss":
        err = _validate_rss_feed(body.url)
        if err:
            raise HTTPException(status_code=422, detail=err)

    name = body.name
    if body.type == "rss" and not name:
        try:
            feed = feedparser.parse(body.url)
            name = getattr(feed.feed, "title", None) or None
        except Exception:
            pass

    source = Source(type=body.type, url=body.url, name=name)
    db.add(source)
    db.commit()
    db.refresh(source)
    return ApiResponse(data=_source_to_out(source))


@router.get("/sources", response_model=ApiResponse[list[SourceOut]])
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    return ApiResponse(
        data=[_source_to_out(s) for s in sources],
        meta={"total": len(sources)},
    )


@router.patch("/sources/{source_id}", response_model=ApiResponse[SourceOut])
def update_source(source_id: str, body: SourceUpdate, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if body.enabled is not None:
        source.enabled = body.enabled
    if body.url is not None:
        if source.type == "rss":
            err = _validate_rss_feed(body.url)
            if err:
                raise HTTPException(status_code=422, detail=err)
        source.url = body.url
    if body.name is not None:
        source.name = body.name
    db.commit()
    db.refresh(source)
    return ApiResponse(data=_source_to_out(source))


@router.delete("/sources/{source_id}", response_model=ApiResponse[SourceOut])
def delete_source(source_id: str, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.enabled = False
    db.commit()
    db.refresh(source)
    return ApiResponse(data=_source_to_out(source))
