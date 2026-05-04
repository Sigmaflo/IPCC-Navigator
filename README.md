# 🧭 IPCC-Navigator: 기후 과학 데이터 내비게이터

IPCC AR6 한글 번역본을 기반으로, 누구나 기후변화에 대해 쉽게 질문하고  
**출처와 함께** 답변받을 수 있는 RAG 챗봇입니다.

"동작하는 챗봇"이 아닌 **"측정된 신뢰도가 있는 챗봇"** 을 목표로 합니다.

[![Python](https://img.shields.io/badge/Python-3.11.x-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/)
[![Solar](https://img.shields.io/badge/LLM-Solar_Pro3-orange)](https://console.upstage.ai/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-purple)](https://www.trychroma.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://ipcc-navigator-gkrymert2vvxuwxjcdkqj7.streamlit.app/)

---

## 🌐 데모

| 서비스 | URL |
| :--- | :--- |
| Streamlit UI | [ipcc-navigator.streamlit.app](https://ipcc-navigator-gkrymert2vvxuwxjcdkqj7.streamlit.app/) |

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
| 일반인/전문가 답변 | 쉬운 언어의 일반인용 + 원문 수치 기반 전문가용 답변 분리 |
| 신뢰도 3지표 | 근거 일치도·출처 충분성·범위 내 여부 실시간 표시 |

---

## 📊 성능 지표 (RAGAS 평가)

청킹 방식 3종(단순·구조·의미 기반), 검색 방식 4종(벡터 단독·하이브리드 방법C·방법E·방법F) 실험을 완료했습니다.

**현재 배포 설정**: 단순 청킹 CASE 3 (1000/200) + 벡터 단독 검색 (cosine, threshold=0.40)

> 실험 상세 내용은 [`proposals/`](./proposals) 폴더의 IEP 문서를 참고하세요.

---

### 검색 방식 비교 (judge: solar-pro3 전 지표 통일, IEP-1001 Solar v2 baseline)

모든 수치는 동일한 judge(solar-pro3)로 측정해 공정하게 비교할 수 있습니다.  
Faithfulness는 생존 편향 보정값(NaN → 0점, 전체 100개 기준)을 사용합니다.

| 검색 방식 | Context Recall | Context Precision | Faithfulness (보수) | Answer Relevancy | 거절 수 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 벡터 단독 · thr=0.40 ✅ **배포** | 0.6549 | 0.5608 | 0.1424 | 0.4075 | — |
| 하이브리드 방법C · thr=0.28 | 0.5175 | 0.6406 | 0.1764 | 0.3301 | 17/100 |
| 하이브리드 방법E · thr=0.20 | 0.5600 | **0.6835** | 0.1792 | 0.3537 | 10/100 |
| 하이브리드 방법F · thr 없음 | **0.6835** | 0.5859 | 0.1600 | **0.4575** | 0/100 |

> **방법E 채택 배경**: threshold=0.20은 Recall과 Precision의 균형점. 방법F(threshold 없음)는 Recall upper bound(0.6835)로 서비스 거절 응답이 없어 배포에 부적합.  
> **현재 배포 코드는 벡터 단독**: 방법E는 cosine 컬렉션 기준 재실험 후 Phase 3에서 반영 예정.

---

### 청킹 방식 비교 (judge 혼재 — 방향성 참고용)

> ⚠️ 아래 수치는 judge가 통일되지 않아 직접 비교에 주의가 필요합니다.  
> IEP-1001 CASE 3: Recall/Precision은 `llama3.1:8b`, Faithfulness/AR은 `solar-pro3`  
> IEP-1002·1003: 전 지표 `llama3.1:8b`  
> **배포 채택 근거로는 보수적 Recall(생존 편향 보정)을 사용합니다.**

| 청킹 방식 | Context Recall | Context Precision | Faithfulness | Answer Relevancy | NaN (Recall) | 보수적 Recall |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 단순 CASE 3 (1000/200) ✅ **배포** | 0.8537 | 0.6117 | 0.4361 | 0.6143 | 6개 | **0.8025** |
| 구조 기반 (IEP-1002) | 0.7106 | 0.2150 | 0.2258 | 0.5100 | 34개 | 0.6674 |
| 의미 기반 p95 (IEP-1003) | 0.8611 | 0.5544 | 0.3869 | 0.5693 | 85개 | **0.1292** |

> **배포 채택 근거**: 보수적 Recall 기준 CASE 3(0.8025, 유효 94개) vs IEP-1003(0.1292, 유효 15개). IEP-1003은 수치상 Recall이 높아 보이지만 NaN 85개의 생존 편향으로 신뢰도가 낮다.  
> **리랭킹(IEP-2002) 중단**: ms-marco 계열 모델이 용어집(page 136) 청크를 생태계 질문 1위로 오판. 색인 전처리(용어집·부속서 분리)가 선결 조건임을 확인하고 중단. Phase 3 이후 재시도 예정.

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
| 프론트엔드 | Streamlit (Streamlit Cloud 배포) |
| 백엔드 | FastAPI, Uvicorn |
| LLM | 업스테이지 Solar (`solar-pro3`) |
| 임베딩 | jhgan/ko-sroberta-multitask (768차원, 한국어 특화) |
| 벡터 DB | ChromaDB (cosine, 컬렉션: `ipcc_1001_case3_cosine_v1`, 506청크) |
| 청킹 | chunk_size=1000, overlap=200 |
| 유사도 임계값 | 0.40 (cosine 컬렉션 기준, 2026-04-30 확정) |
| 인프라 | GCP Cloud Run, GCS |
| 컨테이너 | Docker (linux/amd64, 2.62GB) |

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

## 🐳 Docker 실행

```bash
# 빌드 (amd64 명시 필수 — Mac M4 arm64 환경 대응)
docker buildx build \
  --platform linux/amd64 \
  -t ipcc-rag:local .

# 실행 (ChromaDB는 볼륨 마운트로 주입)
docker run -p 8080:8080 \
  -e UPSTAGE_API_KEY=<your_key> \
  -e DEVICE=cpu \
  -e CHROMA_DIR=/tmp/chroma_cosine \
  -v /path/to/your/chroma_cosine:/tmp/chroma_cosine \
  ipcc-rag:local
```

---

## ☁️ Cloud Run 재배포

```bash
# 1. amd64로 빌드 + GCR 푸시
docker buildx build \
  --platform linux/amd64 \
  -t gcr.io/<PROJECT_ID>/ipcc-rag:latest \
  --push .

# 2. Cloud Run 배포
gcloud run deploy ipcc-rag \
  --image gcr.io/<PROJECT_ID>/ipcc-rag:latest \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 60 \
  --min-instances 0 \
  --max-instances 1 \
  --set-env-vars "UPSTAGE_API_KEY=<your_key>,GCS_BUCKET=ipcc-rag-chromadb,CHROMA_DIR=/tmp/chroma_cosine,DEVICE=cpu"
```

> Cloud Run은 앱 기동 시 GCS 버킷(`ipcc-rag-chromadb`)에서 ChromaDB를 `/tmp/chroma_cosine`으로 자동 다운로드합니다.

---

## 🔧 환경변수 목록

| 변수명 | 필수 | 설명 | 예시 |
| :--- | :---: | :--- | :--- |
| `UPSTAGE_API_KEY` | ✅ | 업스테이지 Solar API 키 | `up_xxxx` |
| `CHROMA_DIR` | ✅ | ChromaDB 로컬 경로 | `/tmp/chroma_cosine` |
| `GCS_BUCKET` | Cloud Run만 | GCS 버킷명 (로컬 실행 시 불필요) | `ipcc-rag-chromadb` |
| `DEVICE` | — | 임베딩 디바이스 (기본값: `cpu`) | `mps` (Mac) / `cuda` (GPU) |

---

## 🩺 트러블슈팅

| 증상 | 원인 | 해결 |
| :--- | :--- | :--- |
| 모든 질문이 거절됨 | ChromaDB 컬렉션이 L2 distance로 생성됨 | cosine 컬렉션(`hnsw:space=cosine`)으로 재인덱싱 |
| `exec format error` | Mac M4(arm64) 이미지를 Cloud Run(amd64)에 배포 | `--platform linux/amd64` 명시 후 재빌드 |
| 모델 다운로드 `ValueError` | CVE-2025-32434 — transformers가 torch 2.6+ 강제 요구 | `torch==2.6.0` CPU only 사용 |
| `similarity_search` 음수 score | LangChain 버전별 변환 공식 불일치 | `similarity_search_with_score` + `1 - distance` 직접 변환 |

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
  "answer_simple": "쉬운 언어로 설명한 일반인용 답변...",
  "sources": [
    {
      "page": 20,
      "preview": "2011~2020년 전 지구 지표면 온도는...",
      "source": "KO_IPCC_AR6_SYR_FullVolume.pdf"
    }
  ],
  "trust": {
    "relevance_score": 0.64,
    "coverage_score": 0.80,
    "is_in_scope": true
  }
}
```

### `POST /chat/expert`

**요청**
```json
{ "question": "지구 온난화의 주요 원인은 무엇인가?" }
```

**응답**
```json
{
  "answer": "[핵심 요약] ... [주요 변화] ... [근거] ..."
}
```

### `GET /info`

```json
{
  "llm_model": "solar-pro3",
  "embedding_model": "jhgan/ko-sroberta-multitask",
  "chroma_collection": "ipcc_1001_case3_cosine_v1",
  "similarity_threshold": 0.40,
  "top_k": 10,
  "document": "IPCC AR6 종합보고서 (한글 번역본, 188페이지)"
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
│       ├── app.py           # Streamlit UI (일반인/전문가 답변, 신뢰도 3지표)
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
| IEP-4002 | Docker 컨테이너화 | ✅ 완료 |
| IEP-4003 | GCP Cloud Run 배포 | ✅ 완료 |
| IEP-4005 | 실시간 진행 로그 (st.status 3단계) | ✅ 완료 |
| IEP-4006 | 답변 신뢰도 3지표 (근거 일치도·출처 충분성·범위 내 여부) | ✅ 완료 |
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
torch==2.6.0
pydantic==2.10.6
python-dotenv==1.1.0
google-cloud-storage==2.19.0
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
Phase 2  배포 (IEP-4001~4006)         ✅ 완료
Phase 3  검색 개선 (IEP-2001~1004)    🔄 병행 진행
Phase 4  LangGraph Agent              ⏳ 미착수
```
