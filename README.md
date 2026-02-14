# Research-Mate Backend

고등학생 심화 탐구 보고서 플랫폼용 FastAPI 백엔드입니다.

## 핵심 기능
- 교과/단원 기반 주제 추천 (`/api/v1/topics/recommend`)
- 단일 주제 기반 보고서 비동기 생성 (`/api/v1/reports/generate`)
- 보고서 조회/수정/북마크/목록
- 보고서 우측 AI 채팅 (`/api/v1/reports/{report_id}/chat`)
- 교과서 텍스트 기반 RAG + 단계형 보고서 생성 워크플로우
- `계획 -> 생성 -> 비평 -> 재작성(최대 N회)` 품질 보정 루프
- LangGraph 설치 시 StateGraph 기반 실행, 미설치 시 동일 단계 폴백 실행

## 디렉터리
- `app/services/rag_service.py`: 교과서 문맥 검색
- `app/services/report_workflow.py`: 엄격 생성 파이프라인
- `app/services/gemini_service.py`: Vertex AI 모델 호출
- `app/data/textbook/math.txt`: 수학 교과서 샘플 지식 베이스

## 실행
```bash
cd research-mate-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 필수 환경변수(.env)
```env
PROJECT_NAME=Research-Mate
API_V1_STR=/api/v1
SECRET_KEY=CHANGE_THIS_TO_A_SECURE_SECRET_KEY

# DB
DB_USER=
DB_PASS=
DB_NAME=
INSTANCE_CONNECTION_NAME=

# Vertex AI (권장)
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.0-flash

# OpenAI-compatible (선택)
OPENAI_API_KEY=
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Workflow
USE_LANGGRAPH=true
MAX_REPORT_REVISIONS=2
TEXTBOOK_DATA_DIR=app/data/textbook
```

## 참고
- `INSTANCE_CONNECTION_NAME`가 없으면 로컬 SQLite(`test.db`)로 동작합니다.
- `OPENAI_API_KEY`가 있으면 OpenAI-compatible API를 우선 사용하고, 없으면 Vertex AI를 사용합니다.
- LangGraph 미설치여도 워크플로우는 폴백 경로로 동작합니다.
