# IPCC RAG Chatbot — 노트북 목록

---

# IEP-1003: 의미 기반 청킹 (Semantic Chunking)

IPCC AR6 SYR 한글 번역본(188페이지)을 대상으로 문장 간 임베딩 유사도 변화를 활용한
의미 기반 청킹을 구현하고, ChromaDB에 저장 후 스모크 테스트를 진행합니다.

## 노트북 구성

| 파일 | Day | 내용 | 주요 산출물 |
| :--- | :---: | :--- | :--- |
| `IEP1003_day1_2_semantic_chunking.ipynb` | Day 1+2 | SemanticChunker threshold 3종 실험 · 청크 분포 시각화 · p95 채택 | `ipcc_chunks_semantic_p75.json` `ipcc_chunks_semantic_p85.json` `ipcc_chunks_semantic_p95.json` `chunk_dist_semantic.png` |
| `IEP1003_day3_chroma_smoke.ipynb` | Day 3 | p95 후처리(5,000자 상한) · ChromaDB 저장 · 스모크 테스트 4종 | `ipcc_chunks_semantic_p95_processed.json` `chroma_db/` |

## 실행 순서

```
Day 1+2 → Day 3
```

각 노트북은 이전 노트북의 산출물을 Google Drive에서 로드합니다.
실행 전 경로를 확인하세요.

- Day 1+2: `PAGES_JSON = IEP_1002/parsed/ipcc_pages.json`
- Day 3: `CHUNKS_JSON = IEP_1003/ipcc_chunks_semantic_p95.json`

> **텍스트 소스 주의**: `ipcc_pages.json`의 페이지 키는 `page_num`입니다 (`page` 아님).

## 주요 결과

### threshold 3종 실험 (Day 1+2)

| threshold | 청크 수 | 평균 크기 | 중앙값 | <100자 | 채택 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| percentile 75 | 1,050개 | 497자 | 319자 | 206개 | — |
| percentile 85 | 630개 | 830자 | 470자 | 97개 | — |
| **percentile 95** | **211개** | **2,481자** | **1,280자** | **17개** | **✅** |

**p95 채택 근거**: 중앙값 1,280자가 IEP-1001 최적 구간(1,000~1,200자)에 가장 근접.
평균이 2,481자로 부풀어 보이는 것은 소수 초대형 청크 때문이며, 중앙값이 실제 대표값.
100자 미만 노이즈 청크 17개로 3종 중 최소 → NaN 발생 위험 낮음.

### 후처리 + ChromaDB 저장 (Day 3)

| 항목 | 수치 |
| :--- | :--- |
| 원본 p95 청크 수 | 211개 |
| 5,000자 초과 청크 | 24개 → RecursiveCharacterTextSplitter로 재분할 |
| **최종 청크 수** | **253개** |
| 최종 평균 크기 | 2,096자 |
| 최종 최대 크기 | 5,000자 |
| 임베딩 모델 | `jhgan/ko-sroberta-multitask` |
| 거리 함수 | cosine |
| 컬렉션명 | `ipcc_semantic_p95_v1` |

> **후처리 이유**: p95 원본 최대 크기 27,236자는 `llama3.1:8b` 컨텍스트 한계를 초과.
> 5,000자 상한 적용으로 IEP-1002에서 발생한 NaN 급증(34개)을 사전 차단.

### 스모크 테스트 4종 (Day 3)

**평가 환경**: 임베딩 모델 `jhgan/ko-sroberta-multitask` · cosine distance

| 테스트 | 기준 | 결과 | 수치 |
| :--- | :--- | :---: | :--- |
| ① 청크 수 일치 | DB count == 후처리 청크 수 | ✅ PASS | 253 == 253 |
| ② Retrieval 결과 | top-3 반환, 내용 관련성 있음 | ✅ PASS | 3개 반환 |
| ③ 유사도 점수 | 관련 질의 score < 0.75 | ✅ PASS | 0.59 ~ 0.63 |
| ④ 검색 분별력 | 무관 질의 score > 관련 질의 score | ✅ PASS | 무관 1.40 vs 관련 0.61 |

> **스모크 테스트 ③ 기준값**: `jhgan/ko-sroberta-multitask` + 한글 문서 조합에서
> cosine distance 0.5~0.7은 정상 범위. 기준값을 **0.75**로 설정.

## 의존성

```
langchain-experimental
langchain-community
langchain-huggingface
langchain-text-splitters
langchain-core
chromadb>=1.5.0
sentence-transformers>=5.0.0
matplotlib
tqdm
fonts-nanum
```

## 관련 문서

- [IEP-1003-semantic-chunking.md](../proposals/IEP-1003-semantic-chunking.md)
- [IEP-1002-structural-chunking.md](../proposals/IEP-1002-structural-chunking.md)

---

# IEP-1002: 구조 기반 청킹 (Structural Chunking)

IPCC AR6 SYR 한글 번역본(188페이지)을 대상으로 문서 계층 구조를 활용한
구조 기반 청킹을 구현하고, ChromaDB에 저장 후 RAGAS 4지표로 평가합니다.

## 노트북 구성

| 파일 | Day | 내용 | 주요 산출물 |
| :--- | :---: | :--- | :--- |
| `IEP1002_day1_pdf_parse_heading_detect.ipynb` | Day 1 | PDF 진단 · 텍스트 추출 · 헤딩 패턴 탐지 | `ipcc_raw.txt` `ipcc_pages.json` `ipcc_headings.json` |
| `IEP1002_day2_step1_heading_preprocess.ipynb` | Day 2 | 헤딩 전처리 (목차·러닝헤더·오탐 제거) | `ipcc_headings_clean.json` |
| `IEP1002_day2_step2_structural_chunking.ipynb` | Day 2 | 청킹 로직 구현 · fallback 처리 · 분포 시각화 | `ipcc_chunks_structural.json` `ipcc_headings_final.json` `chunk_dist_structural.png` |
| `IEP1002_day2_step3_chromadb_smoketest.ipynb` | Day 2 | ChromaDB 저장 · 스모크 테스트 | `chroma_db/` `smoke_test_structural.txt` |
| `IEP1002_day3_ragas_evaluation.ipynb` | Day 3 | RAGAS 4지표 평가 · IEP-1001 비교 | `iep1002_day3_raw.csv` `iep1002_day3_summary.csv` |

## 실행 순서

```
Day 1 → Day 2 Step 1 → Day 2 Step 2 → Day 2 Step 3 → Day 3
```

각 노트북은 이전 노트북의 산출물을 Google Drive에서 로드합니다.
실행 전 `DRIVE_BASE` 경로(`/content/drive/MyDrive/IPCC_data/IEP_1002`)를 확인하세요.

## 주요 결과

### 청킹 (Day 2)

| 항목 | 수치 |
| :--- | :--- |
| 최종 헤딩 수 | 48개 (Day 1 원본 150개에서 전처리) |
| 최종 청크 수 | 284개 |
| 평균 청크 크기 | 1,669자 |
| fallback 비율 | 99.3% (split_max) |
| 임베딩 모델 | `jhgan/ko-sroberta-multitask` |
| 거리 함수 | cosine |
| 스모크 테스트 | 4/4 PASS |

> **fallback 99.3% 원인**: pdfplumber가 절 단위 헤딩(`X.X`, `X.X.X`)을
> 독립된 줄이 아닌 앞뒤 텍스트와 연결해 추출하여 헤딩 48개만 확보됨.
> 실질적으로 헤딩 메타데이터가 붙은 고정 길이 청킹에 가까움.

### RAGAS 4지표 평가 (Day 3)

**평가 환경**: 골든 데이터셋 100개 · Judge LLM `llama3.1:8b` · top-k 3

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.3333 | 0.3267 | 0.2794 | 0.5130 |
| 비교 | 0.7619 | 0.2133 | 0.2143 | 0.5073 |
| 의견/예측 | 0.9000 | 0.3067 | 0.2222 | 0.5161 |
| 범위 밖 | 0.7353 | 0.0133 | 0.1875 | 0.5041 |
| **전체** | **0.7106** | **0.2150** | **0.2258** | **0.5100** |

**IEP-1001 CASE 3 대비 Context Recall 비교**

| 유형 | IEP-1001 CASE3 | IEP-1002 | 차이 |
| :--- | :---: | :---: | :---: |
| 사실 확인 | 0.8627 | 0.3333 | -0.5294 |
| 비교 | 0.8897 | 0.7619 | -0.1278 |
| 의견/예측 | 0.8875 | 0.9000 | +0.0125 |
| 범위 밖 | 0.8595 | 0.7353 | -0.1242 |
| **전체** | **0.8520** | **0.7106** | **-0.1414** |

## 의존성

```
pdfplumber
chromadb>=1.5.0
sentence-transformers>=5.0.0
langchain-community
langchain-huggingface
langchain-ollama
ragas
matplotlib
tqdm
```

## 관련 문서

- [IEP-1003-semantic-chunking.md](../proposals/IEP-1003-semantic-chunking.md)
- [IEP-1002-structural-chunking.md](../proposals/IEP-1002-structural-chunking.md)
- [IEP-1001-simplechunking.md](../proposals/IEP-1001-simplechunking.md)
