import uuid
from typing import Any, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal, get_db
from app.models.report import Report
from app.models.topic import Topic
from app.schemas.report import (
    BookmarkRequest,
    ReportChatRequest,
    ReportChatResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportListResponse,
    ReportResponse,
    ReportUpdateRequest,
)
from app.services import gemini_service
from app.services.report_workflow import run_report_workflow

router = APIRouter()


async def generate_report_task(report_id: str, topic_id: str, custom_instructions: str) -> None:
    async with AsyncSessionLocal() as db:
        try:
            topic_result = await db.execute(select(Topic).where(Topic.topic_id == topic_id))
            topic = topic_result.scalars().first()
            if not topic:
                report_result = await db.execute(select(Report).where(Report.report_id == report_id))
                report = report_result.scalars().first()
                if report:
                    report.status = "failed"
                    await db.commit()
                return

            content = await run_report_workflow(
                subject=topic.subject or "수학",
                unit_large=topic.unit_large or "미적분",
                unit_medium=None,
                unit_small=None,
                topic_title=topic.title,
                topic_description=topic.description or "",
                custom_instructions=custom_instructions or "",
            )

            report_result = await db.execute(select(Report).where(Report.report_id == report_id))
            report = report_result.scalars().first()
            if report:
                report.content = content
                report.status = "completed"
                db.add(report)
                await db.commit()
        except Exception as e:
            report_result = await db.execute(select(Report).where(Report.report_id == report_id))
            report = report_result.scalars().first()
            if report:
                report.status = "failed"
                report.content = {
                    "error": str(e),
                    "hint": "환경 변수와 LangGraph/LLM API 설정을 확인하세요.",
                }
                await db.commit()


@router.post("/generate", response_model=ReportGenerateResponse)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    topic_result = await db.execute(select(Topic).where(Topic.topic_id == request.topic_id))
    topic = topic_result.scalars().first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    report_id = str(uuid.uuid4())
    report = Report(
        report_id=report_id,
        title=topic.title,
        status="generating",
        topic_id=topic.topic_id,
        user_id=None,
    )
    db.add(report)
    await db.commit()

    background_tasks.add_task(
        generate_report_task,
        report_id,
        request.topic_id,
        request.custom_instructions or "",
    )

    return {
        "report_id": report_id,
        "status": "generating",
        "estimated_time": 30,
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    body: ReportUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.content = body.content
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


@router.get("", response_model=List[ReportListResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
) -> Any:
    query = (
        select(Report, Topic)
        .join(Topic, Report.topic_id == Topic.topic_id)
        .order_by(Report.created_at.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    response = []
    for report, topic in rows:
        response.append(
            ReportListResponse(
                report_id=report.report_id,
                title=report.title,
                created_at=report.created_at,
                status=report.status,
                is_bookmarked=report.is_bookmarked,
                subjects=[topic.subject] if topic and topic.subject else [],
            )
        )
    return response


@router.patch("/{report_id}/bookmark")
async def bookmark_report(
    report_id: str,
    body: BookmarkRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.is_bookmarked = body.is_bookmarked
    await db.commit()
    return {"status": "success"}


@router.post("/{report_id}/chat", response_model=ReportChatResponse)
async def chat_with_report(
    report_id: str,
    body: ReportChatRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    reply = await gemini_service.chat_about_report(
        report_title=report.title,
        report_content=report.content or {},
        user_message=body.message,
    )
    return {"reply": reply}


@router.get("/{report_id}/pdf")
async def download_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_content = b"%PDF-1.4\n% Mock PDF placeholder for report export\n"
    return Response(content=pdf_content, media_type="application/pdf")
