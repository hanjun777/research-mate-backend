from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import re

from app.core.config import settings


@dataclass
class RetrievedChunk:
    title: str
    content: str
    score: int


def _tokenize(text: str) -> List[str]:
    lowered = text.lower()
    tokens = re.findall(r"[a-zA-Z0-9가-힣]+", lowered)
    return [t for t in tokens if len(t) > 1]


def _load_subject_text(subject: str) -> str:
    base_dir = Path(settings.TEXTBOOK_DATA_DIR)
    file_map: Dict[str, str] = {
        "수학": "math.txt",
    }
    filename = file_map.get(subject, "math.txt")
    path = base_dir / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_sections(raw: str) -> List[tuple[str, str]]:
    if not raw.strip():
        return []

    sections: List[tuple[str, str]] = []
    current_title = "일반"
    current_lines: List[str] = []

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("[") and line.endswith("]") and len(line) > 2:
            if current_lines:
                sections.append((current_title, " ".join(current_lines)))
            current_title = line[1:-1].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, " ".join(current_lines)))

    return sections


def retrieve_textbook_context(
    *,
    subject: str,
    unit_large: str,
    unit_medium: str | None,
    unit_small: str | None,
    topic_title: str,
    top_k: int = 3,
) -> List[RetrievedChunk]:
    raw = _load_subject_text(subject)
    sections = _parse_sections(raw)
    if not sections:
        return []

    query = " ".join(filter(None, [subject, unit_large, unit_medium, unit_small, topic_title]))
    query_tokens = set(_tokenize(query))

    scored: List[RetrievedChunk] = []
    for title, content in sections:
        combined = f"{title} {content}"
        tokens = _tokenize(combined)
        score = sum(1 for token in tokens if token in query_tokens)
        if score <= 0:
            continue
        scored.append(RetrievedChunk(title=title, content=content, score=score))

    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:top_k]


def format_context(chunks: List[RetrievedChunk]) -> str:
    if not chunks:
        return "참고 교과서 문맥을 찾지 못했습니다."
    lines: List[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        lines.append(f"[{idx}] {chunk.title}: {chunk.content}")
    return "\n".join(lines)
