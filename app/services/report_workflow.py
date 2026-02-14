from __future__ import annotations

from typing import Any, Dict, TypedDict

from app.core.config import settings
from app.services import gemini_service
from app.services.rag_service import format_context, retrieve_textbook_context

try:
    from langgraph.graph import StateGraph, END  # type: ignore
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None  # type: ignore
    END = "END"  # type: ignore


class ReportState(TypedDict, total=False):
    subject: str
    unit_large: str
    unit_medium: str | None
    unit_small: str | None
    topic_title: str
    topic_description: str
    custom_instructions: str
    rag_context: str
    plan: str
    report: Dict[str, Any]
    critique: Dict[str, Any]
    revision_count: int
    provider: Dict[str, bool]


RUBRIC = """
1) 교과서 개념 연결성: 대주제/중주제/소주제와 문단이 직접 연결되어 있는가
2) 논리 구조: 주장-근거-해석 순서가 유지되는가
3) 학술성: 용어 사용이 정확하고 과장/추측이 적은가
4) 탐구 방법: 변수, 절차, 검증 방식이 구체적인가
5) 결론 품질: 결과 요약, 한계, 후속 탐구 제안이 있는가
""".strip()


async def _step_retrieve(state: ReportState) -> ReportState:
    chunks = retrieve_textbook_context(
        subject=state["subject"],
        unit_large=state["unit_large"],
        unit_medium=state.get("unit_medium"),
        unit_small=state.get("unit_small"),
        topic_title=state["topic_title"],
        top_k=4,
    )
    state["rag_context"] = format_context(chunks)
    return state


async def _step_plan(state: ReportState) -> ReportState:
    fallback = (
        "연구 질문 3개를 설정한다.\n"
        "1) 교과 개념이 주제에 어떻게 적용되는가\n"
        "2) 어떤 수학적 모델/분석 절차를 선택할 것인가\n"
        "3) 결과의 한계와 확장 가능성은 무엇인가"
    )
    prompt = f"""
다음 정보를 바탕으로 고등학생 심화탐구 보고서의 고난도 계획을 작성하세요.
주제: {state['topic_title']}
설명: {state.get('topic_description', '')}
교과서 문맥:
{state.get('rag_context', '')}

요구사항:
- Markdown 형식
- 탐구 질문 4개 이상
- 분석 절차를 단계별(자료-모형-검증-한계)로 제시
- 실제 보고서 작성 시 사용할 핵심 근거와 반례 가능성 표시
"""
    state["plan"] = await gemini_service.generate_text(prompt, fallback)
    return state


async def _step_generate(state: ReportState) -> ReportState:
    instructions = state.get("custom_instructions", "")
    strict_instructions = (
        f"{instructions}\n\n"
        "아래 교과서 문맥과 계획을 반드시 반영하세요.\n"
        "보고서 문체는 학술 보고서 수준으로 유지하고, 문장 밀도를 높이세요.\n"
        "각 섹션에서 핵심 용어를 정의하고 근거-해석-시사점 순서로 작성하세요.\n"
        f"[교과서 문맥]\n{state.get('rag_context', '')}\n\n"
        f"[탐구 계획]\n{state.get('plan', '')}"
    )
    state["report"] = await gemini_service.generate_report_content(
        topic_title=state["topic_title"],
        topic_description=state.get("topic_description", ""),
        custom_instructions=strict_instructions,
    )
    return state


async def _step_critique(state: ReportState) -> ReportState:
    critique = await gemini_service.critique_report(state.get("report", {}), RUBRIC)
    state["critique"] = critique
    return state


async def _step_rewrite(state: ReportState) -> ReportState:
    feedback = (state.get("critique") or {}).get("feedback", "")
    rewritten = await gemini_service.rewrite_report_with_feedback(
        report=state.get("report", {}),
        feedback=feedback,
        custom_instructions=state.get("custom_instructions", ""),
    )
    state["report"] = rewritten
    state["revision_count"] = state.get("revision_count", 0) + 1
    return state


async def _step_finalize(state: ReportState) -> ReportState:
    report = state.get("report") or {}
    required_keys = [
        "title",
        "research_question",
        "abstract",
        "introduction",
        "background",
        "methodology",
        "analysis",
        "limitations",
        "conclusion",
    ]
    for key in required_keys:
        value = report.get(key)
        if not isinstance(value, str) or len(value.strip()) < 20:
            report[key] = "해당 섹션은 품질 점검에서 보완이 필요합니다. 교과서 근거를 추가해 확장하세요."

    rag_context = state.get("rag_context", "")
    refs = []
    for line in rag_context.splitlines():
        if line.startswith("[") and "]" in line:
            refs.append(line.split(":", 1)[0])
    report["references"] = refs[:4]
    report["quality"] = state.get("critique", {})
    report["plan"] = state.get("plan", "")
    report["provider"] = state.get("provider", {})
    report["pipeline"] = {
        "langgraph_enabled": settings.USE_LANGGRAPH and LANGGRAPH_AVAILABLE,
        "revisions": state.get("revision_count", 0),
    }

    state["report"] = report
    return state


def _need_rewrite(state: ReportState) -> str:
    critique = state.get("critique") or {}
    revision_count = state.get("revision_count", 0)
    approved = bool(critique.get("approved", False))
    score = int(critique.get("score", 0))

    if approved or score >= 85 or revision_count >= settings.MAX_REPORT_REVISIONS:
        return "finalize"
    return "rewrite"


async def run_report_workflow(
    *,
    subject: str,
    unit_large: str,
    unit_medium: str | None,
    unit_small: str | None,
    topic_title: str,
    topic_description: str,
    custom_instructions: str,
) -> Dict[str, Any]:
    init_state: ReportState = {
        "subject": subject,
        "unit_large": unit_large,
        "unit_medium": unit_medium,
        "unit_small": unit_small,
        "topic_title": topic_title,
        "topic_description": topic_description,
        "custom_instructions": custom_instructions,
        "revision_count": 0,
        "provider": gemini_service.provider_status(),
    }

    if settings.USE_LANGGRAPH and not LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph is required but not available. Install with `pip install langgraph`.")

    if settings.USE_LANGGRAPH and LANGGRAPH_AVAILABLE and StateGraph is not None:
        workflow = StateGraph(ReportState)
        workflow.add_node("retrieve", _step_retrieve)
        workflow.add_node("plan", _step_plan)
        workflow.add_node("generate", _step_generate)
        workflow.add_node("critique", _step_critique)
        workflow.add_node("rewrite", _step_rewrite)
        workflow.add_node("finalize", _step_finalize)

        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "plan")
        workflow.add_edge("plan", "generate")
        workflow.add_edge("generate", "critique")
        workflow.add_conditional_edges(
            "critique",
            _need_rewrite,
            {
                "rewrite": "rewrite",
                "finalize": "finalize",
            },
        )
        workflow.add_edge("rewrite", "critique")
        workflow.add_edge("finalize", END)

        app = workflow.compile()
        result = await app.ainvoke(init_state)
        return result.get("report", {})

    state = await _step_retrieve(init_state)
    state = await _step_plan(state)
    state = await _step_generate(state)
    state = await _step_critique(state)
    while _need_rewrite(state) == "rewrite":
        state = await _step_rewrite(state)
        state = await _step_critique(state)
    state = await _step_finalize(state)
    return state.get("report", {})
