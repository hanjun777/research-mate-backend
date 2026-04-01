import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import AsyncSessionLocal, Base, engine, close_connectors
from app.models.curriculum_subject import CurriculumSubject
from app.models.curriculum_unit import CurriculumUnit

async def seed_sample() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        from sqlalchemy import select
        result = await db.execute(select(CurriculumSubject))
        if result.scalars().first():
            print("Database already has data. Skipping sample seed.")
            return

        # Add Subjects
        math = CurriculumSubject(name="수학")
        science = CurriculumSubject(name="과학")
        db.add_all([math, science])
        await db.flush()

        # Add Units for Math
        units_math = [
            CurriculumUnit(subject_id=math.id, unit_large="수학 I", unit_medium="지수함수와 로그함수", unit_small="지수"),
            CurriculumUnit(subject_id=math.id, unit_large="수학 I", unit_medium="지수함수와 로그함수", unit_small="로그"),
            CurriculumUnit(subject_id=math.id, unit_large="수학 I", unit_medium="삼각함수", unit_small="삼각함수의 뜻"),
            CurriculumUnit(subject_id=math.id, unit_large="수학 II", unit_medium="함수의 극한과 연속", unit_small="함수의 극한"),
        ]
        
        # Add Units for Science
        units_science = [
            CurriculumUnit(subject_id=science.id, unit_large="물리학 I", unit_medium="역학과 에너지", unit_small="힘과 운동"),
            CurriculumUnit(subject_id=science.id, unit_large="화학 I", unit_medium="물질의 구성", unit_small="원자의 구조"),
        ]
        
        db.add_all(units_math + units_science)
        await db.commit()
        print("Sample curriculum seed completed.")

if __name__ == "__main__":
    async def main() -> None:
        try:
            await seed_sample()
        finally:
            await engine.dispose()
            await close_connectors()

    asyncio.run(main())
