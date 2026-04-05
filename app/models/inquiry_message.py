from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class InquiryMessage(Base):
    __tablename__ = "inquiry_messages"

    id = Column(Integer, primary_key=True, index=True)
    inquiry_id = Column(Integer, ForeignKey("inquiries.id", ondelete="CASCADE"), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inquiry = relationship("Inquiry", back_populates="messages")
