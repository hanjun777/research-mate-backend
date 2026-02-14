from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.topic import Topic
from app.schemas.topic import TopicRecommendRequest, TopicResponse
from app.services import gemini_service

router = APIRouter()


@router.post("/recommend", response_model=List[TopicResponse])
async def recommend_topics(
    request: TopicRecommendRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return exactly one recommended topic and persist it."""
    try:
        generated_topics = await gemini_service.generate_topics_from_gemini(
            subject=request.subject,
            unit_large=request.unit_large,
            unit_medium=request.unit_medium,
            unit_small=request.unit_small,
            career=request.career,
            difficulty=request.difficulty,
        )

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
            user_id=None,
        )
        db.add(topic)
        await db.commit()

        return [topic_payload]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
