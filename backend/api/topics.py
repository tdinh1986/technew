from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db
from models.orm import TopicFilter
from models.schemas import ApiResponse, TopicFilterCreate, TopicFilterOut

logger = logging.getLogger(__name__)
router = APIRouter()


def _topic_to_out(topic: TopicFilter) -> TopicFilterOut:
    return TopicFilterOut.model_validate(topic)


@router.post("/topics", response_model=ApiResponse[TopicFilterOut])
def create_topic(body: TopicFilterCreate, db: Session = Depends(get_db)):
    existing = db.query(TopicFilter).filter(TopicFilter.keyword == body.keyword).first()
    if existing:
        raise HTTPException(status_code=409, detail="Topic keyword already exists")
    topic = TopicFilter(keyword=body.keyword)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return ApiResponse(data=_topic_to_out(topic))


@router.get("/topics", response_model=ApiResponse[list[TopicFilterOut]])
def list_topics(db: Session = Depends(get_db)):
    topics = db.query(TopicFilter).all()
    return ApiResponse(
        data=[_topic_to_out(t) for t in topics],
        meta={"total": len(topics)},
    )


@router.delete("/topics/{topic_id}", response_model=ApiResponse[None])
def delete_topic(topic_id: str, db: Session = Depends(get_db)):
    topic = db.query(TopicFilter).filter(TopicFilter.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    db.delete(topic)
    db.commit()
    return ApiResponse(data=None)
