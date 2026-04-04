from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.core.database import get_db
from app.models.inquiry import Inquiry
from app.models.inquiry_message import InquiryMessage
from app.models.user import User
from app.schemas.inquiry import InquiryCreate, InquiryResponse, InquiryReply

router = APIRouter()

@router.post("/", response_model=InquiryResponse)
async def create_inquiry(
    request: InquiryCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Submit a new inquiry or feedback."""
    inquiry = Inquiry(
        user_id=current_user.id,
        category=request.category,
        email=current_user.email,
        content=request.content,
        status="pending"
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    
    # Reload with messages to satisfy the schema (even though it's empty initially)
    result = await db.execute(
        select(Inquiry)
        .options(selectinload(Inquiry.messages))
        .where(Inquiry.id == inquiry.id)
    )
    return result.scalars().first()

@router.post("/{inquiry_id}/reply", response_model=InquiryResponse)
async def reply_inquiry(
    inquiry_id: int,
    request: InquiryReply,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Submit a follow-up reply to an existing inquiry."""
    result = await db.execute(select(Inquiry).where(Inquiry.id == inquiry_id, Inquiry.user_id == current_user.id))
    inquiry = result.scalars().first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    message = InquiryMessage(
        inquiry_id=inquiry.id,
        is_admin=False,
        content=request.content
    )
    db.add(message)
    inquiry.status = "pending"  # Update status back to pending so admin sees it
    
    await db.commit()
    
    result = await db.execute(
        select(Inquiry)
        .options(selectinload(Inquiry.messages))
        .where(Inquiry.id == inquiry_id)
    )
    return result.scalars().first()

@router.get("/me", response_model=List[InquiryResponse])
async def list_my_inquiries(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get history of inquiries for the current logged-in user."""
    result = await db.execute(
        select(Inquiry)
        .options(selectinload(Inquiry.messages))
        .where(Inquiry.user_id == current_user.id)
        .order_by(Inquiry.created_at.desc())
    )
    return result.scalars().all()
