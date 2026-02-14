import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from sqlalchemy import delete

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import AsyncSessionLocal, Base, engine, close_connectors
from app.models.curriculum_subject import CurriculumSubject
from app.models.curriculum_unit import CurriculumUnit

ROOT_DIR = Path(__file__).resolve().parents[3]
SUBJECTS_CSV = ROOT_DIR / "math_subjects_rows.csv"
CURRICULUM_CSV = ROOT_DIR / "math_curriculum_rows.csv"


def _parse_timestamp(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


async def seed() -> None:
    if not SUBJECTS_CSV.exists() or not CURRICULUM_CSV.exists():
        raise FileNotFoundError(
            f"CSV file not found. expected: {SUBJECTS_CSV} and {CURRICULUM_CSV}"
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Reset tables for deterministic seeding.
        await db.execute(delete(CurriculumUnit))
        await db.execute(delete(CurriculumSubject))
        await db.commit()

        subject_map: Dict[str, int] = {}

        with SUBJECTS_CSV.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("name") or "").strip()
                if not name:
                    continue
                subject = CurriculumSubject(
                    id=int(row["id"]) if row.get("id") else None,
                    name=name,
                    created_at=_parse_timestamp((row.get("created_at") or "").strip()),
                )
                db.add(subject)
                await db.flush()
                subject_map[name] = subject.id

        await db.commit()

        with CURRICULUM_CSV.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                subject_name = (row.get("subject") or "").strip()
                subject_id = subject_map.get(subject_name)
                if not subject_id:
                    continue

                unit = CurriculumUnit(
                    id=int(row["id"]) if row.get("id") else None,
                    subject_id=subject_id,
                    unit_large=(row.get("unit_large") or "").strip(),
                    unit_medium=((row.get("unit_medium") or "").strip() or None),
                    unit_small=((row.get("unit_small") or "").strip() or None),
                    created_at=_parse_timestamp((row.get("created_at") or "").strip()),
                )
                if not unit.unit_large:
                    continue
                db.add(unit)

        await db.commit()
        print("Curriculum seed completed.")


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        try:
            await seed()
        finally:
            await engine.dispose()
            await close_connectors()

    asyncio.run(main())
