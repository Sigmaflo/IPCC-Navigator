# 🧭 IPCC-Navigator: 기후 과학 데이터 내비게이터

IPCC AR6 한글 번역본을 기반으로, 누구나 기후변화에 대해 쉽게 질문하고  
**출처와 함께** 답변받을 수 있는 RAG 챗봇입니다.

"동작하는 챗봇"이 아닌 **"측정된 신뢰도가 있는 챗봇"** 을 목표로 합니다.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/)
[![Solar](https://img.shields.io/badge/LLM-Solar_Pro3-orange)](https://console.upstage.ai/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-purple)](https://www.trychroma.com/)

---

## 📌 프로젝트 배경

IPCC AR6 종합보고서는 기후변화의 과학적 근거를 담은 가장 신뢰할 수 있는 1차 자료입니다.  
그러나 188페이지의 전문 문서로 일반 시민이 직접 접근하기 어렵습니다.

- 뉴스·SNS의 기후 정보는 요약·왜곡·출처 불명확 문제가 반복됩니다.
- 일반 LLM 챗봇은 보고서 내용을 오답 생성(hallucination)할 위험이 있습니다.
- **RAG 기술**을 적용해 원문에서만 답변하고, 출처를 함께 제공합니다.

---

## ✨ 주요 기능

| 기능 | 설명 |
| :--- | :--- |
| 자연어 질문 | 전문 지식 없이 일상 언어로 기후 과학 원문 기반 답변 획득 |
| 출처 표시 | 모든 답변에 페이지 번호 + 원문 미리보기 제공 |
| 거절 응답 | 보고서 범위 밖 질문은 오답 대신 "찾을 수 없습니다" 반환 |
| 요청 제한 | 일일 200건 제한으로 API 비용 관리 |

---

## 📊 성능 지표 (RAGAS 평가)

청킹 방식 3종 실험 후 **단순 청킹 CASE 3 (1000자 / 오버랩 200자)** 채택.

### 청킹 방식별 비교

| 청킹 방식 | Context Recall | Context Precision | 유효 샘플 |
| :--- | :---: | :---: | :---: |
| Baseline 단순 청킹 (500/100) | 0.814 | — | 91/100 |
| **최적 단순 청킹 (1000/200)** | **0.854** | **0.612** | **94/100** |
| 구조 기반 청킹 | 0.711 | 0.215 | 100/100 |
| 의미 기반 청킹 p95 † | 0.861 | 0.554 | 15/100 |

> † 의미 기반 청킹은 NaN 85개 생존 편향 포함 수치 — 통계적 신뢰도 낮음

### 채택 방식 (단순 청킹 CASE 3) 4지표 최종 수치

Judge LLM: Context Recall/Precision → llama3.1:8b / Faithfulness, Answer Relevancy → solar-pro3

| 질문 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.738 | 0.913 | 0.513 | 0.591 |
| 비교 | 0.860 | 0.673 | 0.282 | 0.267 |
| 의견/예측 | 0.976 | 0.780 | 0.262 | 0.434 |
| 범위 밖 | 0.826 | 0.080 | 0.077 | 0.071 |
| **전체** | **0.854** | **0.612** | **0.275 ‡** | **0.341 §** |

> ‡ Faithfulness: Solar judge 기준, NaN 38개 포함 — 보수적 수치 0.170  
> § Answer Relevancy: strictness=1 (Solar n=1 제약), jhgan 임베딩 기준

### 검색 방식별 비교 (IEP-2001)

| 지표 | 벡터 단독 | 하이브리드 (BM25+RRF) | 변화 |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.854 * | 0.518 | −0.336 |
| Context Precision | 0.612 * | **0.641** | **+0.029** |
| Faithfulness | 0.275 | 0.267 | −0.008 |
| Answer Relevancy | 0.341 | 0.330 | −0.011 |
| 거절 수 | — | 17/100 | — |

> \* 벡터 단독: llama judge / 하이브리드: Solar judge — 직접 비교 불가, 방향성 참고용  
> Recall 급락 원인: threshold 0.28 기준 과다 거절(17건) — 거절 로직 재조정 예정

---

## 🏗 시스템 아키텍처

```
사용자 질문
    │
    ▼
FastAPI /chat
    │
    ├─ 질문 임베딩 (jhgan/ko-sroberta-multitask, 768차원)
    │
    ├─ ChromaDB 유사도 검색 (TOP_K=3, 컬렉션: ipcc_1001_case3_v1)
    │
    ├─ 유사도 < 0.28 → "IPCC 보고서에서 찾을 수 없습니다" 반환
    │
    ├─ Solar LLM 답변 생성 (solar-pro3)
    │
    └─ 답변 + 출처(page · preview) 반환
```

---

## 🛠 기술 스택

| 구분 | 내용 |
| :--- | :--- |
| 백엔드 | FastAPI, Uvicorn |
| LLM | 업스테이지 Solar (`solar-pro3`) |
| 임베딩 | jhgan/ko-sroberta-multitask (768차원, 한국어 특화) |
| 벡터 DB | ChromaDB (코사인 유사도, 컬렉션: `ipcc_1001_case3_v1`) |
| 청킹 | chunk_size=1000, overlap=200, 총 506청크 |
| 유사도 임계값 | 0.28 (실측 기반, 2026-04-22 확정) |
| 인프라 | GCP Cloud Run, GCS |
| 컨테이너 | Docker |

---

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.11+
- 업스테이지 API 키 ([console.upstage.ai](https://console.upstage.ai))
- ChromaDB 데이터 (`ipcc_1001_case3_v1`)

### 2. 설치

```bash
git clone https://github.com/Sigmaflo/IPCC-Navigator.git
cd IPCC-Navigator

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 실제 값 입력:

```
UPSTAGE_API_KEY=up_your_api_key_here
CHROMA_DIR=/path/to/your/chroma_db
```

### 4. 서버 실행

```bash
uvicorn app.main:app --reload
```

### 5. 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# 질문
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "지구 온난화의 주요 원인은 무엇인가?"}'
```

---

## 📡 API 명세

### `POST /chat`

**요청**
```json
{ "question": "지구 온난화의 주요 원인은 무엇인가?" }
```
> 질문 길이: 2~500자

**응답**
```json
{
  "answer": "IPCC AR6에 따르면 인간 활동으로 인한 온실가스 배출이...",
  "sources": [
    {
      "page": 12,
      "preview": "2011~2020년 전 지구 지표면 온도는...",
      "source": "ipcc_ar6_syr_kr.pdf"
    }
  ]
}
```

### `GET /health`

```json
{
  "status": "ok",
  "today_requests": 3,
  "daily_limit": 200,
  "remaining": 197
}
```

---

## 📁 프로젝트 구조

```
IPCC-Navigator/
├── app/
│   ├── config.py      # 환경변수 및 상수
│   ├── models.py      # Pydantic 요청/응답 모델
│   ├── rag.py         # RAG 파이프라인
│   └── main.py        # FastAPI 서버
├── notebooks/
│   ├── IEP1001_case3_ragas_evaluation.ipynb
│   ├── IEP1001_case3_ragas_solar.ipynb
│   ├── IEP1003_day4_ragas_evaluation.ipynb
│   └── IEP2001_hybrid_search_experiment.ipynb
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## 🧪 실험 기록 (IEP 시리즈)

| IEP | 내용 | 상태 |
| :--- | :--- | :---: |
| IEP-1000 | RAGAS Context Recall 기준 측정 | ✅ 완료 |
| IEP-1001 | 단순 청킹 6종 비교 실험 | ✅ 완료 |
| IEP-1002 | 구조 기반 청킹 실험 | ✅ 완료 |
| IEP-1003 | 의미 기반 청킹 실험 (SemanticChunker) | ✅ 완료 |
| IEP-2001 | 하이브리드 검색 (BM25 + Vector) | ✅ 완료 (거절 로직 재조정 예정) |
| IEP-4001 | FastAPI 서비스화 | 🔄 진행 중 |
| IEP-4002 | Docker 컨테이너화 | ⏳ 예정 |
| IEP-4003 | GCP Cloud Run 배포 | ⏳ 예정 |
| IEP-2002 | Reranking (FlashRank → BGE) | ⏳ 예정 |
| IEP-1004 | 파서 교체 (Docling) | ⏳ 예정 |

---

## 📦 Requirements

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-dotenv==1.0.1
openai==2.31.0
langchain-openai==1.2.0
langchain-community==0.3.31
langchain-huggingface==1.0.1
chromadb==0.5.11
sentence-transformers==3.4.1
torch==2.7.1
pydantic==2.9.2
```

---

## 📄 데이터 출처

본 프로젝트는 **IPCC AR6 종합보고서 한글 번역본**을 사용합니다.

> IPCC, 2023: 기후변화 2022: 종합보고서.  
> 기상청 번역본. CC BY 4.0

---

## 🗺 로드맵

```
Phase 1  청킹 실험 (IEP-1000~1003)    ✅ 완료
Phase 2  배포 (IEP-4001~4003)         🔄 진행 중
Phase 3  검색 개선 (IEP-2001~1004)    🔄 병행 진행
Phase 4  LangGraph Agent              ⏳ 미착수
```
