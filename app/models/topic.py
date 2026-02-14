from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Topic(Base):
    __tablename__ = "topics"

    topic_id = Column(String, primary_key=True, index=True) # UUID
    title = Column(String, nullable=False)
    reasoning = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True) # List of strings
    difficulty = Column(String, nullable=True)
    related_subjects = Column(JSON, nullable=True) # List of strings
    
    # Metadata for filtering/context
    subject = Column(String, nullable=True)
    unit_large = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # We might not strictly link Topic to User in the spec (recommendation is stateless?), 
    # but saving 'bookmarked' or 'generated' topics usually requires a link.
    # The spec has 'reports' linked to topics. 
    # Let's assume topics generated are transient unless saved, or saved by default.
    # Spec [POST] /topics/recommend returns a list. It doesn't explicitly save them to DB?
    # Spec [GET] /search/topics implies "Archived topics".
    # So we should probably save them.
