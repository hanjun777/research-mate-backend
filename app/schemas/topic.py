from pydantic import BaseModel
from typing import List, Optional

class TopicRecommendRequest(BaseModel):
    subject: str
    unit_large: str
    unit_medium: Optional[str] = None
    unit_small: Optional[str] = None
    career: str
    difficulty: int
    mode: str = "new"  # new or refine

class TopicResponse(BaseModel):
    topic_id: str
    title: str
    reasoning: str
    description: str
    tags: List[str]
    difficulty: str
    related_subjects: List[str]

    class Config:
        from_attributes = True
