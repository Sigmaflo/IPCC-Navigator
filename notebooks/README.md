# IPCC-Navigator — 노트북 목록

실험별 노트북 구성과 주요 산출물을 정리합니다.
상세 실험 계획 및 결과는 `proposals/` 폴더의 IEP 문서를 참조하세요.

---

## IEP-1003: 의미 기반 청킹 (Semantic Chunking)

IPCC AR6 SYR 한글 번역본(188페이지)을 대상으로 문장 간 임베딩 유사도 변화를 활용한
의미 기반 청킹을 구현하고, ChromaDB에 저장 후 RAGAS 4지표로 평가합니다.

### 노트북 구성

| 파일 | Day | 내용 | 주요 산출물 |
| :--- | :---: | :--- | :--- |
| `IEP1003_day1_2_semantic_chunking.ipynb` | Day 1+2 | SemanticChunker threshold 3종 실험 · 청크 분포 시각화 · p95 채택 | `ipcc_chunks_semantic_p75.json` `ipcc_chunks_semantic_p85.json` `ipcc_chunks_semantic_p95.json` `chunk_dist_semantic.png` |
| `IEP1003_day3_chroma_smoke.ipynb` | Day 3 | p95 후처리(5,000자 상한) · ChromaDB 저장 · 스모크 테스트 4종 | `ipcc_chunks_semantic_p95_processed.json` `chroma_db/` |
| `IEP1003_day4_ragas_evaluation.ipynb` | Day 4 | RAGAS 4지표 평가 · IEP-1001·1002 3종 비교 · 배포용 청킹 확정 | `iep1003_day4_raw.csv` `iep1003_day4_summary.csv` |

### 실행 순서

```
Day 1+2 → Day 3 → Day 4
```

각 노트북은 이전 노트북의 산출물을 Google Drive에서 로드합니다.
실행 전 경로를 확인하세요.

- Day 1+2: `PAGES_JSON = IEP_1002/parsed/ipcc_pages.json`
- Day 3: `CHUNKS_JSON = IEP_1003/ipcc_chunks_semantic_p95.json`
- Day 4: `CHROMA_DIR = IEP_1003/chroma_db`, `GOLDEN_CSV = IEP_1002/golden_dataset_100.csv`

> **텍스트 소스 주의**: `ipcc_pages.json`의 페이지 키는 `page_num`입니다 (`page` 아님).

### 주요 결과

**threshold 3종 실험 (Day 1+2)**

| threshold | 청크 수 | 평균 크기 | 중앙값 | <100자 | 채택 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| percentile 75 | 1,050개 | 497자 | 319자 | 206개 | — |
| percentile 85 | 630개 | 830자 | 470자 | 97개 | — |
| **percentile 95** | **211개** | **2,481자** | **1,280자** | **17개** | **✅** |

**후처리 + ChromaDB 저장 (Day 3)**

| 항목 | 수치 |
| :--- | :--- |
| 원본 p95 청크 수 | 211개 |
| 5,000자 초과 청크 | 24개 → RecursiveCharacterTextSplitter로 재분할 |
| **최종 청크 수** | **253개** |
| 최종 평균 크기 | 2,096자 |
| ChromaDB 컬렉션 | `ipcc_semantic_p95_v1` |

**스모크 테스트 4종 (Day 3)**

| 테스트 | 기준 | 결과 | 수치 |
| :--- | :--- | :---: | :--- |
| ① 청크 수 일치 | DB count == 후처리 청크 수 | ✅ PASS | 253 == 253 |
| ② Retrieval 결과 | top-3 반환, 내용 관련성 있음 | ✅ PASS | 3개 반환 |
| ③ 유사도 점수 | 관련 질의 score < 0.75 | ✅ PASS | 0.59 ~ 0.63 |
| ④ 검색 분별력 | 무관 질의 score > 관련 질의 score | ✅ PASS | 무관 1.40 vs 관련 0.61 (2.3배) |

**RAGAS 4지표 평가 (Day 4)**

평가 환경: 골든 데이터셋 100개 · Judge LLM `llama3.1:8b` · top-k 3

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.6667 | 0.6894 | 0.7500 | 0.4875 |
| 비교 | 1.0000 | 0.5606 | 0.3333 | 0.6661 |
| 의견/예측 | 0.7833 | 0.8177 | 0.4028 | 0.6330 |
| 범위 밖 | 1.0000 | 0.0303 | 0.1667 | 0.4842 |
| **전체** | **0.8611** | **0.5544** | **0.3869** | **0.5693** |

> **NaN 주의**: Context Recall NaN 85개 / 100개. 유효 샘플 15개 기준 평균으로
> 생존 편향이 강하게 작용했다. IEP-1001 CASE 3 대비 통계적 신뢰도가 낮다.

**3종 비교: Context Recall**

| 유형 | IEP-1001 CASE3 | IEP-1002 | IEP-1003 |
| :--- | :---: | :---: | :---: |
| 사실 확인 | 0.8627 | 0.3333 | 0.6667 |
| 비교 | 0.8897 | 0.7619 | 1.0000 |
| 의견/예측 | 0.8875 | 0.9000 | 0.7833 |
| 범위 밖 | 0.8595 | 0.7353 | 1.0000 |
| **전체** | **0.8520** | **0.7106** | **0.8611** |

**배포용 청킹 확정**: NaN 85개(유효 샘플 15개)로 인한 생존 편향을 고려하여
수치상 기준(Recall > 0.8520) 충족에도 불구하고 **IEP-1001 CASE 3(1000/200) 최종 채택**.

---

## IEP-1002: 구조 기반 청킹 (Structural Chunking)

IPCC AR6 SYR 한글 번역본(188페이지)을 대상으로 문서 계층 구조를 활용한
구조 기반 청킹을 구현하고, ChromaDB에 저장 후 RAGAS 4지표로 평가합니다.

### 노트북 구성

| 파일 | Day | 내용 | 주요 산출물 |
| :--- | :---: | :--- | :--- |
| `IEP1002_day1_pdf_parse_heading_detect.ipynb` | Day 1 | PDF 진단 · 텍스트 추출 · 헤딩 패턴 탐지 | `ipcc_raw.txt` `ipcc_pages.json` `ipcc_headings.json` |
| `IEP1002_day2_step1_heading_preprocess.ipynb` | Day 2 | 헤딩 전처리 (목차·러닝헤더·오탐 제거) | `ipcc_headings_clean.json` |
| `IEP1002_day2_step2_structural_chunking.ipynb` | Day 2 | 청킹 로직 구현 · fallback 처리 · 분포 시각화 | `ipcc_chunks_structural.json` `chunk_dist_structural.png` |
| `IEP1002_day2_step3_chromadb_smoketest.ipynb` | Day 2 | ChromaDB 저장 · 스모크 테스트 | `chroma_db/` `smoke_test_structural.txt` |
| `IEP1002_day3_ragas_evaluation.ipynb` | Day 3 | RAGAS 4지표 평가 · IEP-1001 비교 | `iep1002_day3_raw.csv` `iep1002_day3_summary.csv` |

### 실행 순서

```
Day 1 → Day 2 Step 1 → Day 2 Step 2 → Day 2 Step 3 → Day 3
```

### 주요 결과

**청킹 (Day 2)**

| 항목 | 수치 |
| :--- | :--- |
| 최종 헤딩 수 | 48개 (Day 1 원본 150개에서 전처리) |
| 최종 청크 수 | 284개 |
| 평균 청크 크기 | 1,669자 |
| fallback 비율 | 99.3% (split_max) |

> **fallback 99.3% 원인**: pdfplumber가 2단 레이아웃에서 절 단위 헤딩(`X.X`, `X.X.X`)을
> 독립 줄이 아닌 앞뒤 텍스트와 연결해 추출 → 헤딩 48개만 확보 →
> 실질적으로 헤딩 메타데이터가 붙은 고정 길이 청킹에 가까움.

**RAGAS 4지표 평가 (Day 3)**

평가 환경: 골든 데이터셋 100개 · Judge LLM `llama3.1:8b` · top-k 3

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.3333 | 0.3267 | 0.2794 | 0.5130 |
| 비교 | 0.7619 | 0.2133 | 0.2143 | 0.5073 |
| 의견/예측 | 0.9000 | 0.3067 | 0.2222 | 0.5161 |
| 범위 밖 | 0.7353 | 0.0133 | 0.1875 | 0.5041 |
| **전체** | **0.7106** | **0.2150** | **0.2258** | **0.5100** |

---

## 공통 의존성

```
langchain-experimental
langchain-community
langchain-huggingface
langchain-text-splitters
langchain-ollama
langchain-core
chromadb>=1.5.0
sentence-transformers>=5.0.0
ragas
pandas
matplotlib
tqdm
```

## 관련 문서

- [IEP-1000: RAGAS를 이용한 Context Recall 성능 측정](../proposals/IEP-1000-ragas-recall.md)
- [IEP-1001: 단순 청킹을 통한 Context Recall 성능 개선](../proposals/IEP-1001-simplechunking.md)
- [IEP-1002: 구조 기반 청킹을 통한 Context Recall 성능 개선](../proposals/IEP-1002-structural-chunking.md)
- [IEP-1003: 의미 기반 청킹을 통한 Context Recall 성능 개선](../proposals/IEP-1003-semantic-chunking.md)