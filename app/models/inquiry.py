from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    category = Column(String(50), nullable=False) # feedback, bug, feature, other
    email = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    status = Column(String(20), default="pending") # pending, answered
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="inquiries")
    messages = relationship("InquiryMessage", back_populates="inquiry", cascade="all, delete-orphan", order_by="InquiryMessage.created_at")
