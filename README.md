# 🧭 IPCC-Navigator: 기후 과학 데이터 내비게이터

IPCC AR6 한글 번역본을 기반으로, 누구나 기후변화에 대해 쉽게 질문하고  
**출처와 함께** 답변받을 수 있는 RAG 챗봇입니다.

"동작하는 챗봇"이 아닌 **"측정된 신뢰도가 있는 챗봇"** 을 목표로 합니다.

[![Python](https://img.shields.io/badge/Python-3.11.x-blue)](https://www.python.org/)
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
| 거절 응답 | 보고서 범위 밖 질문은 오답 대신 거절 메시지 반환 |
| 요청 제한 | 일일 200건 제한으로 API 비용 관리 |

---

## 📊 성능 지표 (RAGAS 평가)

청킹 방식 3종(단순·구조·의미 기반), 검색 방식 3종(벡터 단독·하이브리드 방법E·방법F) 실험을 완료했습니다.

**현재 배포 설정**: 단순 청킹 CASE 3 (1000/200) + 벡터 단독 검색 (cosine, threshold=0.40)

> Phase 3에서 전 지표 동일 judge 기준으로 재측정 후 상세 수치를 공개할 예정입니다.
> 실험 상세 내용은 [`proposals/`](./proposals) 폴더의 IEP 문서를 참고하세요.

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
    ├─ ChromaDB 유사도 검색 (TOP_K=10, 컬렉션: ipcc_1001_case3_cosine_v1)
    │   cosine distance → similarity = 1 - distance
    │
    ├─ similarity < 0.40 → 거절 메시지 반환
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
| 벡터 DB | ChromaDB (cosine, 컬렉션: `ipcc_1001_case3_cosine_v1`, 506청크) |
| 청킹 | chunk_size=1000, overlap=200 |
| 유사도 임계값 | 0.40 (cosine 컬렉션 기준, 2026-04-30 확정) |
| 인프라 | GCP Cloud Run, GCS (예정) |
| 컨테이너 | Docker (예정) |

---

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.11.x
- 업스테이지 API 키 ([console.upstage.ai](https://console.upstage.ai))
- ChromaDB 데이터 (`ipcc_1001_case3_cosine_v1`)

### 2. 설치

```bash
git clone https://github.com/Sigmaflo/IPCC-Navigator.git
cd IPCC-Navigator

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r app/backend/requirements.txt
```

### 3. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어 실제 값 입력:

```
UPSTAGE_API_KEY=up_your_api_key_here
CHROMA_DIR=/path/to/your/chroma_cosine
```

### 4. 서버 실행

```bash
cd app/backend
uvicorn main:app --reload
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
      "page": 20,
      "preview": "2011~2020년 전 지구 지표면 온도는...",
      "source": "KO_IPCC_AR6_SYR_FullVolume.pdf"
    }
  ]
}
```

### `GET /health`

```json
{
  "status": "ok",
  "requests_today": 3,
  "limit": 200
}
```

---

## 📁 프로젝트 구조

```
IPCC-Navigator/
├── app/
│   ├── backend/
│   │   ├── main.py          # FastAPI 앱 + 일일 200건 미들웨어
│   │   ├── rag.py           # RAG 파이프라인 (검색 + Solar 호출)
│   │   ├── config.py        # 설정값 (threshold, 모델명, 경로)
│   │   ├── models.py        # Pydantic 스키마
│   │   └── requirements.txt
│   └── frontend/
│       ├── app.py           # Streamlit UI (예정)
│       └── requirements.txt
├── proposals/               # IEP 실험 문서
├── notebooks/               # 실험 노트북
├── docs/
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
| IEP-2001 | 하이브리드 검색 (BM25 + Vector RRF) | ✅ 완료 |
| IEP-2002 | 리랭킹 (FlashRank) — 색인 전처리 필요로 중단 | ✅ 완료 |
| IEP-4001 | FastAPI 서비스화 + 로컬 동작 확인 | ✅ 완료 |
| IEP-4002 | Docker 컨테이너화 | ⏳ 예정 |
| IEP-4003 | GCP Cloud Run 배포 | ⏳ 예정 |
| IEP-1004 | 파서 교체 (Docling) | ⏳ Phase 3 |
| IEP-3001 | LangGraph Agent | ⏳ Phase 4 |

---

## 📦 주요 패키지 버전

```
fastapi==0.115.12
uvicorn[standard]==0.34.0
openai==2.31.0
langchain==1.2.16
langchain-chroma==1.1.0
langchain-huggingface==1.2.2
chromadb==1.5.8
sentence-transformers==3.4.1
transformers==4.47.1
torch==2.2.2
pydantic==2.10.6
python-dotenv==1.1.0
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