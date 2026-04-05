from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class InquiryCreate(BaseModel):
    category: str
    content: str
    email: Optional[EmailStr] = None

class InquiryAnswer(BaseModel):
    answer: str

class InquiryReply(BaseModel):
    content: str

class InquiryMessageUpdate(BaseModel):
    content: str

class InquiryMessageResponse(BaseModel):
    id: int
    inquiry_id: int
    is_admin: bool
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class InquiryResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    category: str
    email: Optional[str] = None
    content: str
    answer: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[InquiryMessageResponse] = []

    class Config:
        from_attributes = True
