# Backend Production Guide

## 1) 필수 환경값
- `ENVIRONMENT=production`
- `SECRET_KEY`는 긴 랜덤 문자열(필수)
- `CORS_ALLOW_ORIGINS`는 프론트 도메인만 허용(콤마 구분)
- `ALLOWED_HOSTS`는 백엔드 도메인만 허용
- `AUTO_CREATE_TABLES=false` 권장

## 2) Cloud SQL
- `INSTANCE_CONNECTION_NAME`, `DB_USER`, `DB_PASS`, `DB_NAME` 설정
- Cloud Run에 `--add-cloudsql-instances`로 연결

## 3) LLM 키
- Vertex AI 사용: `GOOGLE_CLOUD_PROJECT`, `GEMINI_MODEL`
- OpenAI 호환 사용: `OPENAI_API_KEY`, `OPENAI_API_BASE`, `OPENAI_MODEL`
- 운영에서는 Secret Manager 사용 권장

## 4) 배포
```bash
cd research-mate-backend
export GCP_PROJECT=YOUR_PROJECT
export REGION=asia-northeast3
export INSTANCE_CONNECTION_NAME=project:region:instance
export DB_USER=...
export DB_NAME=...
export CORS_ALLOW_ORIGINS=https://your-frontend-domain.com
export ALLOWED_HOSTS=your-backend-domain.com
./deploy/deploy-cloud-run.sh
```

## 5) 배포 후 체크
- `GET /health`가 `status=ok` 반환
- 주제 추천 -> 보고서 생성 -> 폴링 -> 수정/채팅까지 E2E 테스트
- Cloud Logging에서 오류/타임아웃 확인
