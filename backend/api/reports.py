from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db
from models.orm import DigestReport
from models.schemas import (
    ApiResponse,
    DigestReportListItem,
    DigestReportOut,
    TopicSectionOut,
)

router = APIRouter()


@router.get("/reports/latest", response_model=ApiResponse[DigestReportOut])
def get_latest_report(db: Session = Depends(get_db)):
    report = db.query(DigestReport).order_by(DigestReport.created_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="No digest available yet")
    return ApiResponse(
        data=DigestReportOut(
            id=report.id,
            created_at=report.created_at,
            article_count=report.article_count,
            topic_sections=[TopicSectionOut(**s) for s in report.topic_sections],
        ),
        meta={"generated_at": str(report.created_at)},
    )


@router.get("/reports/{report_id}", response_model=ApiResponse[DigestReportOut])
def get_report_by_id(report_id: str, db: Session = Depends(get_db)):
    report = db.query(DigestReport).filter(DigestReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return ApiResponse(
        data=DigestReportOut(
            id=report.id,
            created_at=report.created_at,
            article_count=report.article_count,
            topic_sections=[TopicSectionOut(**s) for s in report.topic_sections],
        ),
        meta={"generated_at": str(report.created_at)},
    )


@router.get("/reports", response_model=ApiResponse[list[DigestReportListItem]])
def list_reports(db: Session = Depends(get_db)):
    reports = (
        db.query(DigestReport).order_by(DigestReport.created_at.desc()).limit(30).all()
    )
    items = [
        DigestReportListItem(
            id=r.id, created_at=r.created_at, article_count=r.article_count
        )
        for r in reports
    ]
    return ApiResponse(data=items, meta={"total": len(items)})
