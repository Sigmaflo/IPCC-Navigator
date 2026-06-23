# CLAUDE.md

## 프로젝트
IPCC AR6 한글 번역본 기반 RAG 챗봇 포트폴리오.
"동작하는 챗봇"이 아닌 "측정된 신뢰도가 있는 챗봇"을 목표로 함.

## 현재 단계
Phase 3 진행 중 — 검색 품질 보완
- IEP-1004 MinerU 파서 실험 중 (Colab)
- IEP-2001.2 방법E cosine 재실험 완료 → 배포 반영 여부 미결정
- Phase 1, 2 완료 (배포 URL 보유)

## 기술 스택
- 임베딩: jhgan/ko-sroberta-multitask (768차원)
- 벡터DB: ChromaDB (cosine), 컬렉션: ipcc_1001_case3_cosine_v1
- 청킹: chunk_size=1000, overlap=200 (CASE 3), 506청크
- SIMILARITY_THRESHOLD: 0.40 (cosine 기준, 2026-04-30 확정)
- 배포 LLM: 업스테이지 Solar (solar-pro3)
- 실험 LLM: llama3.1:8b (Ollama)
- 평가: RAGAS
- 인프라: GCP Cloud Run + Streamlit Cloud
- 실험 환경: Google Colab T4 / Mac Mini M4

## 확정된 설정값
- ChromaDB 메타데이터 키: page (int), source (PDF 경로) — chunk_id 없음
- similarity = 1 - cosine_distance (직접 변환, LangChain 의존 금지)
- TOP_K: 10
- Solar base_url: https://api.upstage.ai/v1
- 환경변수: UPSTAGE_API_KEY

## 코드 규칙
- f-string 내 \n 사용 금지
- Mac 로컬 실행 시 device="mps" (Colab은 "cuda", Cloud Run은 "cpu")
- ChromaDB 컬렉션 생성 시 반드시 metadata={'hnsw:space': 'cosine'} 명시
- similarity_search_with_relevance_scores 사용 금지 (버전별 변환 공식 불일치)

## 커밋 규칙
- 메시지는 한글로 작성
