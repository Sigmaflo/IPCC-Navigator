# CLAUDE.md

## 프로젝트
IPCC AR6 한글 번역본 기반 RAG 챗봇 포트폴리오.

## 현재 단계
Phase 2 진입 예정 — IEP-4001 FastAPI 서비스화

## 기술 스택
- 임베딩: jhgan/ko-sroberta-multitask
- 벡터DB: ChromaDB (cosine), 컬렉션: ipcc_semantic_p95_v1
- 실험 LLM: llama3.1:8b / 배포 LLM: Claude API haiku
- 평가: RAGAS / 실험 환경: Google Colab T4

## 코드 규칙
- Config는 Step 0 셀에 집중
- f-string 내 \n 사용 금지
- ipcc_pages.json 키는 page_num
- Mac 로컬 실행 시 device="mps"

## 커밋 규칙
- 메시지는 한글로 작성
