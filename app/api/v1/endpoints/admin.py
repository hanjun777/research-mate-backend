from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.core.database import get_db
from app.models.credit_transaction import CreditTransaction
from app.models.payment import PaymentOrder
from app.models.user import User
from app.models.inquiry import Inquiry
from app.schemas.inquiry import InquiryAnswer, InquiryResponse, InquiryMessageUpdate

router = APIRouter()

ADMIN_EMAIL = "coldbootcp@gmail.com"


class AdminCreditAdjustRequest(BaseModel):
    package_code: str
    delta: int  # positive = add, negative = remove


class AdminUserPackageCredit(BaseModel):
    package_code: str
    credit_balance: int


class AdminUserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    credit_balance: int
    created_at: str
    package_credits: list[AdminUserPackageCredit]


class AdminCreditAdjustResponse(BaseModel):
    user_id: int
    package_code: str
    new_balance: int
    delta: int


async def _require_admin(current_user: User = Depends(deps.get_current_user)) -> User:
    if current_user.email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def _get_package_credit_balances(db: AsyncSession, user_id: int) -> dict[str, int]:
    result = await db.execute(
        select(
            CreditTransaction.package_code,
            func.coalesce(func.sum(CreditTransaction.delta), 0),
        )
        .where(CreditTransaction.user_id == user_id)
        .group_by(CreditTransaction.package_code)
    )

    return {
        package_code: max(0, int(total or 0))
        for package_code, total in result.all()
    }


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    response = []
    for user in users:
        pcb = await _get_package_credit_balances(db, user.id)
        package_credits = [
            AdminUserPackageCredit(package_code=code, credit_balance=balance)
            for code, balance in pcb.items()
        ]
        # Always include both package codes even if zero
        existing_codes = {p.package_code for p in package_credits}
        for code in ("basic", "premium-review"):
            if code not in existing_codes:
                package_credits.append(AdminUserPackageCredit(package_code=code, credit_balance=0))

        response.append(
            AdminUserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                credit_balance=user.credit_balance or 0,
                created_at=user.created_at.isoformat() if user.created_at else "",
                package_credits=package_credits,
            )
        )
    return response


@router.post("/users/{user_id}/credits", response_model=AdminCreditAdjustResponse)
async def adjust_user_credits(
    user_id: int,
    body: AdminCreditAdjustRequest,
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tx_type = "EARN" if body.delta > 0 else "SPEND"
    reason = "admin_adjustment"

    db.add(
        CreditTransaction(
            user_id=user.id,
            package_code=body.package_code,
            delta=body.delta,
            transaction_type=tx_type,
            reason=reason,
        )
    )
    user.credit_balance = max(0, (user.credit_balance or 0) + body.delta)
    await db.commit()
    await db.refresh(user)

    pcb = await _get_package_credit_balances(db, user.id)
    new_balance = pcb.get(body.package_code, 0)

    return AdminCreditAdjustResponse(
        user_id=user.id,
        package_code=body.package_code,
        new_balance=new_balance,
        delta=body.delta,
    )


from sqlalchemy.orm import selectinload
from app.models.inquiry_message import InquiryMessage

@router.get("/inquiries", response_model=list[InquiryResponse])
async def list_admin_inquiries(
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all inquiries for admin review."""
    result = await db.execute(
        select(Inquiry)
        .options(selectinload(Inquiry.messages))
        .order_by(Inquiry.created_at.desc())
    )
    return result.scalars().all()


@router.post("/inquiries/{inquiry_id}/answer", response_model=InquiryResponse)
async def answer_inquiry(
    inquiry_id: int,
    body: InquiryAnswer,
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Submit a reply to a user's inquiry."""
    result = await db.execute(select(Inquiry).where(Inquiry.id == inquiry_id))
    inquiry = result.scalars().first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    message = InquiryMessage(
        inquiry_id=inquiry.id,
        is_admin=True,
        content=body.answer
    )
    db.add(message)
    inquiry.status = "answered"
    
    # We update the original answer column too for simplicity in the basic UI fallback, 
    # but the primary source of truth for chat is now messages.
    inquiry.answer = body.answer 
    
    await db.commit()
    
    result = await db.execute(
        select(Inquiry)
        .options(selectinload(Inquiry.messages))
        .where(Inquiry.id == inquiry_id)
    )
    return result.scalars().first()

@router.put("/inquiries/{inquiry_id}/messages/{message_id}", response_model=InquiryResponse)
async def update_inquiry_message(
    inquiry_id: int,
    message_id: int,
    body: InquiryMessageUpdate,
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Edit an existing admin message in an inquiry."""
    result = await db.execute(
        select(InquiryMessage)
        .where(InquiryMessage.id == message_id, InquiryMessage.inquiry_id == inquiry_id)
    )
    message = result.scalars().first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
        
    if not message.is_admin:
        raise HTTPException(status_code=403, detail="Can only edit admin messages")

    message.content = body.content
    await db.commit()

    # Also update inquiry.answer if this is the first/only message (optional fallback)
    inquiry_res = await db.execute(select(Inquiry).where(Inquiry.id == inquiry_id))
    inquiry = inquiry_res.scalars().first()
    if inquiry:
        # Check if it's the very first admin message
        first_admin_msg = await db.execute(
            select(InquiryMessage)
            .where(InquiryMessage.inquiry_id == inquiry_id, InquiryMessage.is_admin == True)
            .order_by(InquiryMessage.created_at.asc())
            .limit(1)
        )
        first_msg = first_admin_msg.scalars().first()
        if first_msg and first_msg.id == message_id:
            inquiry.answer = body.content
            await db.commit()

    result = await db.execute(
        select(Inquiry)
        .options(selectinload(Inquiry.messages))
        .where(Inquiry.id == inquiry_id)
    )
    return result.scalars().first()
