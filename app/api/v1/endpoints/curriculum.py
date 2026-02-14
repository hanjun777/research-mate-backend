from fastapi import APIRouter, HTTPException, Query
from typing import List, Any
from app.core.curriculum_data import SUBJECTS, UNITS

router = APIRouter()

@router.get("/subjects", response_model=List[str])
def get_subjects() -> List[str]:
    """
    Get supported subjects.
    """
    return SUBJECTS

@router.get("/units")
def get_units(subject: str = Query(..., description="Subject name e.g. 수학")) -> Any:
    """
    Get unit hierarchy for a specific subject.
    """
    if subject not in UNITS:
        # If we return empty list for unknown subjects or 404? 
        # Spec doesn't strictly say, but usually empty list or error.
        # Let's return empty list if present in SUBJECTS but no data, or 404 if invalid subject?
        if subject in SUBJECTS:
            return []
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return UNITS[subject]
