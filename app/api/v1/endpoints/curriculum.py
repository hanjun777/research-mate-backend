from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.curriculum_subject import CurriculumSubject
from app.models.curriculum_unit import CurriculumUnit

router = APIRouter()

@router.get("/subjects", response_model=List[str])
async def get_subjects(
    db: AsyncSession = Depends(get_db),
) -> List[str]:
    """
    Get supported subjects.
    """
    result = await db.execute(select(CurriculumSubject).order_by(CurriculumSubject.id.asc()))
    rows = result.scalars().all()
    return [row.name for row in rows]

@router.get("/units")
async def get_units(
    subject: str = Query(..., description="Subject name e.g. 수학"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get unit hierarchy for a specific subject.
    """
    subject_result = await db.execute(
        select(CurriculumSubject).where(CurriculumSubject.name == subject)
    )
    subject_row = subject_result.scalars().first()
    if not subject_row:
        raise HTTPException(status_code=404, detail="Subject not found")

    units_result = await db.execute(
        select(CurriculumUnit)
        .where(CurriculumUnit.subject_id == subject_row.id)
        .order_by(CurriculumUnit.id.asc())
    )
    units = units_result.scalars().all()

    # Build hierarchy: large -> medium -> small
    large_map: Dict[str, Dict[str, Any]] = {}
    for row in units:
        if row.unit_large not in large_map:
            large_map[row.unit_large] = {
                "unit_large": row.unit_large,
                "children": [],
            }

        if row.unit_medium:
            medium_list = large_map[row.unit_large]["children"]
            medium = next((m for m in medium_list if m["unit_medium"] == row.unit_medium), None)
            if medium is None:
                medium = {"unit_medium": row.unit_medium, "children": []}
                medium_list.append(medium)
            if row.unit_small and row.unit_small not in medium["children"]:
                medium["children"].append(row.unit_small)

    return list(large_map.values())
