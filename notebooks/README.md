# IPCC-Navigator — 노트북 목록

실험별 노트북 구성과 주요 산출물을 정리합니다.
상세 실험 계획 및 결과는 `proposals/` 폴더의 IEP 문서를 참조하세요.

> 최종 수정일: 2026-04-29

---

## 목차

- [IEP-1001: 단순 청킹](#iep-1001-단순-청킹-simple-chunking)
- [IEP-1002: 구조 기반 청킹](#iep-1002-구조-기반-청킹-structural-chunking)
- [IEP-1003: 의미 기반 청킹](#iep-1003-의미-기반-청킹-semantic-chunking)
- [IEP-2001: 하이브리드 검색](#iep-2001-하이브리드-검색-bm25--vector)
- [IEP-2002: 리랭킹](#iep-2002-리랭킹-flashrank)
- [공통 의존성](#공통-의존성)
- [관련 문서](#관련-문서)

---

## IEP-1001: 단순 청킹 (Simple Chunking)

Chunk Size / Overlap 조합 6종을 비교해 최적 청킹 구간을 탐색하고, 배포용 청킹을 확정합니다.

### 노트북 구성

| 파일 | 내용 |
| :--- | :--- |
| `IEP1001-simple_chunking_recall.ipynb` | Context Recall 전용 평가 (6종 비교) |
| `IEP1001_case3_ragas_evaluation.ipynb` | CASE 3 RAGAS 4지표 전체 평가 · 3종 청킹 비교 · 생존 편향 보정 (judge: llama3.1:8b) |
| `IEP1001_case3_ragas_solar.ipynb` | CASE 3 RAGAS 재측정 — Faithfulness + Answer Relevancy (judge: solar-pro3) |

### 주요 결과

**6종 비교: Context Recall**

| Case | Chunk | Overlap | Recall | NaN |
| :---: | :---: | :---: | :---: | :---: |
| CASE 1 | 500 | 100 | 0.8143 | 9.0개 |
| CASE 2 | 800 | 150 | 0.8047 | 6.5개 |
| **CASE 3** ✅ | **1000** | **200** | **0.8537** | **6개** |
| CASE 4 | 1200 | 240 | 0.8567 | 15개 |
| CASE 5 | 1500 | 300 | 0.8480 | 6개 |
| CASE 6 | 2000 | 400 | 0.8452 | 30개 |

**CASE 3 RAGAS 4지표 — 최종 확정 수치** (2026-04-26)

| 유형 | Context Recall* | Context Precision* | Faithfulness† | Answer Relevancy† |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.7381 | **0.9133** | 0.5125 | 0.5910 |
| 비교 | 0.8600 | 0.6733 | 0.2818 | 0.2670 |
| 의견/예측 | **0.9757** | 0.7800 | 0.2619 | 0.4342 |
| 범위 밖 | 0.8264 | 0.0800 | 0.0774 | 0.0714 |
| **전체** | **0.8537** | **0.6117** | **0.2748** | **0.3409** |

*judge: `llama3.1:8b` (LLM 무관 지표)  
†judge: `solar-pro3` (2026-04-26 재측정)

**생존 편향 보정**

| 지표 | 낙관적 (NaN 제외) | 유효 샘플 | 보수적 (전체 100개) |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.8537 | 94개 | **0.8025** |
| Context Precision | 0.6117 | 100개 | **0.6117** |
| Faithfulness | 0.2748 | 62개 | **0.1704** |
| Answer Relevancy | 0.3409 | 100개 | **0.3409** |

> **배포 채택 근거**: 보수적 Recall 0.8025 (유효 94개) — IEP-1003 보수적 Recall 0.1292 (유효 15개) 대비 통계적 신뢰도 우위

### Solar RAGAS 재측정 상세 (2026-04-26)

**측정 환경**

| 항목 | 값 |
| :--- | :--- |
| Answer 생성 LLM | `solar-pro3` |
| Judge LLM | `solar-pro3` |
| Answer Relevancy 임베딩 | `jhgan/ko-sroberta-multitask` |
| Answer Relevancy strictness | 1 (Solar `n=1` 제약으로 기본값 3 사용 불가) |
| 소요 시간 | Answer 생성 149초 + Faithfulness 484초 + AR 169초 |

**⚠️ Solar RAGAS 호환 이슈**

| 이슈 | 원인 | 해결 |
| :--- | :--- | :--- |
| `n must be 1` (Answer Relevancy 전량 실패) | RAGAS 기본 `strictness=3` → `n=3` 요청 / Solar `n=1`만 지원 | `AnswerRelevancy(strictness=1)` |
| `$.input is invalid` (embedding 오류) | Solar embedding이 RAGAS 입력 형식 거부 | `jhgan` 임베딩으로 대체 |

> Answer Relevancy는 `strictness=1` + `jhgan` 임베딩 조합으로 측정. llama 수치(0.6143)와 직접 비교 불가.  
> Faithfulness는 Solar judge 기준으로 llama 대비 엄격하게 평가됨 (llama: 0.4361 → Solar: 0.2748).

---

## IEP-1002: 구조 기반 청킹 (Structural Chunking)

문서 계층 구조(헤딩 단위)를 활용한 청킹을 구현하고 RAGAS 4지표로 평가합니다.

### 노트북 구성

| 파일 | Day | 내용 |
| :--- | :---: | :--- |
| `IEP1002_day1_pdf_parse_heading_detect.ipynb` | Day 1 | PDF 진단 · 텍스트 추출 · 헤딩 패턴 탐지 |
| `IEP1002_day2_step1_heading_preprocess.ipynb` | Day 2 | 헤딩 전처리 (목차·러닝헤더·오탐 제거) |
| `IEP1002_day2_step2_structural_chunking.ipynb` | Day 2 | 청킹 로직 구현 · fallback 처리 · 분포 시각화 |
| `IEP1002_day2_step3_chromadb_smoketest.ipynb` | Day 2 | ChromaDB 저장 · 스모크 테스트 |
| `IEP1002_day3_ragas_evaluation.ipynb` | Day 3 | RAGAS 4지표 평가 · IEP-1001 비교 |

### 실행 순서

```
Day 1 → Day 2-Step 1 → Day 2-Step 2 → Day 2-Step 3 → Day 3
```

### 주요 결과

**청킹 (Day 2)**

| 항목 | 수치 |
| :--- | :--- |
| 확보 헤딩 수 | 48개 (원본 150개에서 전처리) |
| 최종 청크 수 | 284개 |
| 평균 청크 크기 | 1,669자 |
| fallback 비율 | 99.3% |

> **fallback 99.3% 원인**: pdfplumber가 2단 레이아웃에서 절 단위 헤딩(`X.X`, `X.X.X`)을 앞뒤 텍스트와 연결해 추출 → 헤딩 48개만 확보 → 실질적으로 헤딩 메타데이터가 붙은 고정 길이 청킹에 가까움.

**RAGAS 4지표** (judge: `llama3.1:8b`, 284청크, 골든 100개)

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.3333 | 0.3267 | 0.2794 | 0.5130 |
| 비교 | 0.7619 | 0.2133 | 0.2143 | 0.5073 |
| 의견/예측 | 0.9000 | 0.3067 | 0.2222 | 0.5161 |
| 범위 밖 | 0.7353 | 0.0133 | 0.1875 | 0.5041 |
| **전체** | **0.7106** | **0.2150** | **0.2258** | **0.5100** |

---

## IEP-1003: 의미 기반 청킹 (Semantic Chunking)

문장 간 임베딩 유사도 변화를 활용한 의미 기반 청킹을 구현하고 RAGAS 4지표로 평가합니다.

### 노트북 구성

| 파일 | Day | 내용 |
| :--- | :---: | :--- |
| `IEP1003_day3_chroma_smoke.ipynb` | Day 3 | p95 후처리(5,000자 상한) · ChromaDB 저장 · 스모크 테스트 4종 |
| `IEP1003_day4_ragas_evaluation.ipynb` | Day 4 | RAGAS 4지표 평가 · 3종 비교 · 배포용 청킹 확정 |

### 실행 순서

```
Day 3 → Day 4
```

각 노트북은 이전 노트북의 산출물을 Google Drive에서 로드합니다.

| 노트북 | 필요 입력 경로 |
| :--- | :--- |
| Day 3 | `IEP_1003/ipcc_chunks_semantic_p95.json` |
| Day 4 | `IEP_1003/chroma_db/`, `IEP_1002/golden_dataset_100.csv` |

> **주의**: `ipcc_pages.json`의 페이지 키는 `page_num`입니다 (`page` 아님).

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
| 평균 청크 크기 | 2,096자 |
| ChromaDB 컬렉션 | `ipcc_semantic_p95_v1` |

**스모크 테스트 4종 (Day 3)**

| 테스트 | 기준 | 결과 | 수치 |
| :--- | :--- | :---: | :--- |
| ① 청크 수 일치 | DB count == 후처리 청크 수 | ✅ | 253 == 253 |
| ② Retrieval 결과 | top-3 반환, 내용 관련성 있음 | ✅ | 3개 반환, 해수면·온난화 내용 포함 |
| ③ 유사도 점수 | 관련 질의 score < 0.75 | ✅ | 0.5933 / 0.6079 / 0.6268 |
| ④ 검색 분별력 | 무관 질의 score > 관련 질의 score | ✅ | 무관 1.40 vs 관련 0.61 (2.3배) |

> **기준값 조정 경위**: 초기 기준 0.5 적용 시 FAIL. `jhgan/ko-sroberta-multitask` + 한글 문서 특성상 cosine distance 0.5~0.7이 정상 범위임을 확인하여 **0.75**로 조정. 이후 동일 환경 스모크 테스트의 표준 기준값으로 채택.

**RAGAS 4지표** (judge: `llama3.1:8b`, 253청크, 골든 100개)

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.6667 | 0.6894 | 0.7500 | 0.4875 |
| 비교 | 1.0000 | 0.5606 | 0.3333 | 0.6661 |
| 의견/예측 | 0.7833 | 0.8177 | 0.4028 | 0.6330 |
| 범위 밖 | 1.0000 | 0.0303 | 0.1667 | 0.4842 |
| **전체** | **0.8611** | **0.5544** | **0.3869** | **0.5693** |

**NaN 발생 현황**

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 22 | 14 | 23 | 4 |
| 비교 | 22 | 14 | 22 | 3 |
| 의견/예측 | 20 | 9 | 19 | 2 |
| 범위 밖 | 21 | 14 | 22 | 3 |
| **전체** | **85** | **51** | **86** | **12** |

**생존 편향 보정** (NaN → 0점, 전체 100개 기준)

| 지표 | 낙관적 (NaN 제외) | 유효 샘플 | 보수적 (전체 100개) |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.8611 | 15개 | **0.1292** |
| Context Precision | 0.5544 | 49개 | **0.2716** |
| Faithfulness | 0.3869 | 14개 | **0.0541** |
| Answer Relevancy | 0.5693 | 88개 | **0.5010** |

> **NaN 주의**: 낙관적 수치는 측정 가능했던 케이스에서의 성능. 보수적 수치가 현재 파이프라인의 실제 안정성을 나타낸다. IEP-1001 CASE 3 보수적 Recall(0.8025, 유효 94개) 대비 통계적 신뢰도 현저히 낮음.

**3종 비교: Context Recall**

| 유형 | IEP-1001 CASE 3 | IEP-1002 | IEP-1003 | vs 1001 | vs 1002 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.8627 | 0.3333 | 0.6667 | -0.1960 | +0.3334 |
| 비교 | 0.8897 | 0.7619 | 1.0000 | +0.1103 | +0.2381 |
| 의견/예측 | 0.8875 | 0.9000 | 0.7833 | -0.1042 | -0.1167 |
| 범위 밖 | 0.8595 | 0.7353 | 1.0000 | +0.1405 | +0.2647 |
| **전체** | **0.8520** | **0.7106** | **0.8611** | **+0.0091** | **+0.1505** |

**배포용 청킹 확정**: NaN 85개(유효 15개)로 인한 생존 편향을 고려해 수치상 기준(Recall > 0.8520) 충족에도 불구하고 **IEP-1001 CASE 3(1000/200) 최종 채택**.

---

## IEP-2001: 하이브리드 검색 (BM25 + Vector)

벡터 단독 검색의 키워드·수치 매칭 취약성을 BM25로 보완하고, RRF 합산으로 검색 품질 개선을 시도했다.

### 노트북 구성

| 파일 | 내용 |
| :--- | :--- |
| `IEP2001_hybrid_search_experiment.ipynb` | BM25 인덱스 구축 · 하이브리드 검색 구현 · RAGAS 4지표 측정 · 벡터 단독 비교 |

### 실험 설정

| 항목 | 값 |
| :--- | :--- |
| 검색 방식 | BM25 + Vector RRF (k=60) |
| 토크나이저 | kiwipiepy (형태소 분석) |
| CANDIDATE_K | 10 |
| SIMILARITY_THRESHOLD | 0.28 |
| TOP_K | 3 |
| ChromaDB 컬렉션 | `ipcc_1001_case3_v1` (506청크, IEP-1001과 동일) |
| Judge LLM | `solar-pro3` (전 지표) |

### 주요 결과 (2026-04-27)

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.7200 | **0.8611** | 0.4937 | 0.4829 |
| 비교 | 0.3200 | 0.7633 | 0.2864 | 0.3401 |
| 의견/예측 | 0.5100 | 0.8000 | 0.2352 | 0.4324 |
| 범위 밖 | 0.5200 | 0.1467 | 0.0800 | 0.0650 |
| **전체** | **0.5175** | **0.6406** | **0.2672** | **0.3301** |

*judge: `solar-pro3` (전 지표)*

**생존 편향 보정**

| 지표 | 낙관적 (NaN 제외) | 유효 샘플 | 보수적 (전체 100개) |
| :--- | :---: | :---: | :---: |
| Faithfulness | 0.2672 | 66개 | **0.1764** |
| Answer Relevancy | 0.3301 | 100개 | **0.3301** |

**벡터 단독 vs 하이브리드 비교**

| 지표 | 벡터 단독 (IEP-1001)† | 하이브리드 (IEP-2001) | 변화 |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.8537 | 0.5175 | −0.3362 |
| Context Precision | 0.6117 | **0.6406** | **+0.0289** |
| Faithfulness | 0.2748 | 0.2672 | −0.0076 |
| Answer Relevancy | 0.3409 | 0.3301 | −0.0108 |
| 거절 수 | — | **17/100** | — |

†IEP-1001은 llama judge 기준 / IEP-2001은 Solar judge 기준 — 수치 직접 비교 불가, 방향성 참고용

> **Recall 급락 원인**: 거절 수 17/100. CANDIDATE_K=10 + threshold 0.28 조합이 borderline 질문을 과도하게 거절. Precision은 +0.0289로 유일하게 개선 — BM25 보완 효과는 확인됨.  
> **다음 단계**: 거절 로직 조정(threshold 하향 또는 TOP_K 기준 필터) 후 재측정 예정.

---

## IEP-2002: 리랭킹 (FlashRank)

벡터 검색 결과에 FlashRank 리랭킹을 추가해 Precision 개선을 시도했다.

### 노트북 구성

| 파일 | 내용 |
| :--- | :--- |
| `IEP2002_reranking_experiment.ipynb` | FlashRank 리랭킹 파이프라인 구현 · 모델 검증(실험 1, 2) · RAGAS 측정 준비 |

### 실험 설정

| 항목 | 값 |
| :--- | :--- |
| 리랭킹 모델 1 | `ms-marco-MiniLM-L-12-v2` |
| 리랭킹 모델 2 | `ms-marco-MultiBERT-L-12` |
| CANDIDATE_K | 10 |
| 거절 로직 | TOP_K(3) 기준 threshold — IEP-1001과 동일 |
| ChromaDB 컬렉션 | `ipcc_1001_case3_v1` (506청크, IEP-1001과 동일) |

### 결과 (2026-04-29)

**RAGAS 측정 전 모델 검증(Cell 6)에서 중단.**

질문 5개로 리랭킹 전후를 사람이 직접 판단한 결과:

| 질문 | 유형 | MiniLM | MultiBERT |
| :--- | :---: | :---: | :---: |
| 2011~2020년 온도 상승 | 사실확인 | ❌ 악화 | ❌ 악화 |
| 1.5°C 탄소 감축량 | 사실확인 | 🟡 유사 | 🟡 유사 |
| 해수면 상승 비교 | 비교 | ❌ 악화 | 🟡 유사 |
| 기후변화 생태계 영향 | 의견예측 | ❌ 악화 | ❌ 악화 |
| 환경 보호 개인 실천 | 경계케이스 | ✅ 거절 유지 | ✅ 거절 유지 |

> **중단 사유**: 두 모델 모두 용어집(page 136) 청크를 생태계 관련 질문의 1위로 오판. 용어집·부속서에 전문용어가 밀집되어 키워드 밀도를 높은 관련성으로 오인하는 문제. 모델 교체로 해결 불가 — 색인 전처리(메타 청크 분리) 선행 필요.  
> **Phase 3 이후 재시도 예정**: 용어집·부속서 청크를 색인에서 분리한 후 재실험.

---

## 공통 의존성

```
langchain-community
langchain-huggingface
langchain-openai
langchain-text-splitters
langchain-ollama
langchain-core
chromadb==0.5.11
sentence-transformers
ragas
openai
pandas
matplotlib
tqdm
```

> Phase 1 (청킹 실험): `langchain-ollama`, `langchain-experimental` 필요  
> Phase 2 (Solar 재측정): `langchain-openai`, `openai` 필요 (버전 고정 없음 — pip 자동 해결)

---

## 관련 문서

- [IEP-1000: RAGAS를 이용한 Context Recall 성능 측정](../proposals/IEP-1000-ragas-recall.md)
- [IEP-1001: 단순 청킹 방식의 청크 크기 실험 및 RAGAS 4대 지표 측정](../proposals/IEP-1001-simplechunking.md)
- [IEP-1002: 구조 기반 청킹 방식의 헤딩 탐지 실험 및 RAGAS 4대 지표 측정](../proposals/IEP-1002-structural-chunking.md)
- [IEP-1003: 의미 기반 청킹 방식의 threshold 실험 및 RAGAS 4대 지표 측정](../proposals/IEP-1003-semantic-chunking.md)
- [IEP-2001: 하이브리드 검색(BM25 + Vector)을 통한 검색 품질 개선](../proposals/IEP-2001-hybrid-search.md)
- [IEP-2002: 리랭킹(FlashRank)을 통한 검색 품질 개선 시도](../proposals/IEP-2002-reranking.md)
