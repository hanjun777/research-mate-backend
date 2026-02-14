# Research-Mate API Specification (FastAPI)

본 문서는 Research-Mate 서비스의 프론트엔드(Next.js)와 완벽하게 연동되기 위한 백엔드 API 명세서입니다.

## 1. 공통 사항 (Common)
- **Base URL**: `http://localhost:8000/api/v1` (개발 환경 기준)
- **Content-Type**: `application/json`
- **Health Check**: `GET /health` (서버 상태 확인)

---

## 2. 인증 및 사용자 (Auth & User)
### [POST] /auth/register
- **설명**: 신규 회원 가입
- **Body**: `{ "email": "user@example.com", "password": "...", "name": "학생이름" }`
- **Response**: `201 Created`

### [POST] /auth/token
- **설명**: 로그인 (JWT Access Token 발급)
- **Content-Type**: `application/x-www-form-urlencoded` (OAuth2 Password Request)
- **Body**: `username={email}&password={password}`
- **Response**: `{ "access_token": "...", "token_type": "bearer" }`

### [GET] /auth/me
- **설명**: 현재 로그인한 사용자 정보 조회 (헤더 표시용)
- **Header**: `Authorization: Bearer {token}`
- **Response**: `{ "id": 1, "email": "...", "name": "김학생", "avatar_url": "..." }`

---

## 3. 교과 과정 (Curriculum)
### [GET] /curriculum/subjects
- **설명**: 지원하는 교과목 목록 반환
- **Response**: `["수학", "물리학", "화학", "생명과학", "정보", "지구과학", "영어", "한국사"]`

### [GET] /curriculum/units
- **설명**: 특정 과목의 대/중/소단원 계층 정보 조회
- **Query**: `subject=수학`
- **Response**:
  ```json
  [
    {
      "unit_large": "미적분",
      "children": [ ... ]
    }
  ]
  ```

---

## 4. 주제 추천 (Topic Recommendation)
### [POST] /topics/recommend
- **설명**: AI 기반 맞춤형 탐구 주제 추천
- **Header**: `Authorization: Bearer {token}`
- **Body**:
  ```json
  {
    "subject": "수학",
    "unit_large": "미분방정식",
    "unit_medium": "...", 
    "unit_small": "...", 
    "career": "의공학자",
    "difficulty": 100,
    "mode": "new" // "new" (새로 생성) or "refine" (기존 기반 고도화)
  }
  ```
- **Response**:
  ```json
  [
    {
      "topic_id": "uuid",
      "title": "미분방정식을 활용한 감염병 확산 모델 분석",
      "reasoning": "사용자의 진로와 교과 흥미를 연결...",
      "description": "SIR 모델을 직접 구현하여...",
      "tags": ["수학", "생명과학"],
      "difficulty": "심화",
      "related_subjects": ["정보", "통계"]
    }
  ]
  ```

---

## 5. 보고서 관리 (Reports)
### [POST] /reports/generate
- **설명**: 선택한 주제로 보고서 생성 시작 (Async Task)
- **Body**: `{ "topic_id": "uuid", "custom_instructions": "..." }`
- **Response**: `{ "report_id": "uuid", "status": "generating", "estimated_time": 30 }`

### [GET] /reports/{report_id}
- **설명**: 보고서 상세 내용 및 생성 상태 조회 (Polling)
- **Response**:
  ```json
  {
    "report_id": "uuid",
    "status": "completed", // generating, completed, failed
    "title": "...",
    "content": {
        "introduction": "...",
        "background": "...",
        "methodology": "...",
        "conclusion": "..."
    },
    "created_at": "timestamp"
  }
  ```

### [GET] /reports
- **설명**: 나의 보고서 목록 조회
- **Response**: `[ { "report_id", "title", "subjects": ["수학"], "created_at": "...", "status": "completed" } ]`

### [GET] /reports/{report_id}/pdf
- **설명**: 완성된 보고서를 PDF 파일로 다운로드
- **Response**: `application/pdf` binary stream

### [PATCH] /reports/{report_id}/bookmark
- **설명**: 보고서 즐겨찾기 상태 변경
- **Body**: `{ "is_bookmarked": true }`

---

## 6. 검색 및 기타 (Search & Misc)
### [GET] /search/topics (Optional)
- **설명**: 기존 생성된 주제 아카이브 검색
- **Query**: `q=인공지능`

## 7. Error Handling Spec
- **400 Bad Request**: 입력값 오류
- **401 Unauthorized**: 토큰 만료 또는 없음
- **404 Not Found**: 리소스 없음
- **422 Validation Error**: Pydantic 유효성 검사 실패
- **Error Body**: `{ "detail": "User friendly error message", "code": "ERR_001" }`
