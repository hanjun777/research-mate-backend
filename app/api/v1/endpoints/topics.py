import time
import logging
from typing import Any, List
 
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.api import deps
from app.core.database import get_db
from app.models.report import Report
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicRecommendRequest, TopicResponse
from app.services import gemini_service
 
router = APIRouter()
logger = logging.getLogger(__name__)
 
 
@router.post("/recommend", response_model=List[TopicResponse])
async def recommend_topics(
    request: TopicRecommendRequest,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return exactly one recommended topic and persist it."""
    start_time = time.time()
    try:
        generated_topics = await gemini_service.generate_topics_from_gemini(
            subject=request.subject,
            unit_large=request.unit_large,
            unit_medium=request.unit_medium,
            unit_small=request.unit_small,
            career=request.career,
            difficulty=request.difficulty,
        )
        duration = time.time() - start_time
        logger.info(f"Gemini generation took {duration:.2f} seconds")

        if not generated_topics:
            raise HTTPException(status_code=500, detail="Failed to generate topic")

        topic_payload = generated_topics[0]
        topic = Topic(
            topic_id=topic_payload.get("topic_id"),
            title=topic_payload.get("title"),
            reasoning=topic_payload.get("reasoning"),
            description=topic_payload.get("description"),
            tags=topic_payload.get("tags"),
            difficulty=topic_payload.get("difficulty"),
            related_subjects=topic_payload.get("related_subjects"),
            subject=request.subject,
            unit_large=request.unit_large,
            user_id=current_user.id,
        )
        db.add(topic)
        await db.flush()
        
        # Create a report entry immediately
        import uuid
        report_id = str(uuid.uuid4())
        report = Report(
            report_id=report_id,
            title=topic.title,
            status="topic_generated",
            content={
                "reasoning": topic.reasoning,
                "description": topic.description,
                "tags": topic.tags,
                "__meta": {
                    "progress": 0,
                    "phase": "topic_selected",
                    "message": "주제가 선정되었습니다. 보고서 생성을 시작해 주세요."
                }
            },
            report_type="general", # Default
            topic_id=topic.topic_id,
            user_id=current_user.id,
        )
        db.add(report)
        
        await db.commit()

        topic_payload["report_id"] = report_id
        return [topic_payload]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
