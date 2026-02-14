from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class CurriculumUnit(Base):
    __tablename__ = "curriculum_units"
    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "unit_large",
            "unit_medium",
            "unit_small",
            name="uq_curriculum_unit_path",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("curriculum_subjects.id"), nullable=False, index=True)
    unit_large = Column(String, nullable=False)
    unit_medium = Column(String, nullable=True)
    unit_small = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
