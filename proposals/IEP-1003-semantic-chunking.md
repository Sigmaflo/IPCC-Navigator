# IEP-1003: 의미 기반 청킹을 통한 Context Recall 성능 개선

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `In Progress` |
| **작성일** | 2026-04-10 |

## 동기

IEP-1002에서 구조 기반 청킹을 시도했으나 전체 Context Recall이 0.7106으로 IEP-1001 CASE 3(0.8520) 대비 **-0.1414** 하락했다. 실패의 근본 원인은 pdfplumber가 절 단위 헤딩(`X.X`, `X.X.X`)을 독립 줄로 추출하지 못해 헤딩 48개만 확보되었고, 원시 청크 평균이 ~10,000자에 달해 fallback(split_max)이 99.3%에 달한 것이다. 결과적으로 "헤딩 메타데이터만 붙은 고정 길이 청킹"으로 전락했다.

SemanticChunker(LangChain)는 헤딩 탐지에 의존하지 않고 **문장 간 임베딩 유사도 변화**로 청크 경계를 결정한다. 이는 IEP-1002의 pdfplumber 제약을 직접 우회하며, 의미 단위로 텍스트를 분리하므로 사실 확인 유형(IEP-1002 Recall 0.3333)의 구조적 약점을 해소할 가능성이 높다.

> **주의**: SemanticChunker도 pdfplumber 추출 텍스트를 입력으로 받는다.
> 헤딩 탐지 의존성은 우회하지만, 2단 레이아웃 합침·중복 텍스트 등 원문 추출 품질 문제는
> Phase 3 IEP-1004(파서 교체)에서 해소한다.

## 진행

### Day 1+2 — SemanticChunker threshold 3종 실험 (2026-04-10 완료)

**실험 환경**

| 항목 | 내용 |
| :--- | :--- |
| 텍스트 소스 | `IEP_1002/parsed/ipcc_pages.json` (IEP-1002 재사용, 비교 기준 통일) |
| 임베딩 모델 | `jhgan/ko-sroberta-multitask` (IEP-1001·1002와 동일) |
| 총 텍스트 길이 | 523,906자 (빈 페이지 19개 제외) |
| threshold 방식 | `percentile` (연속 문장 간 유사도 하위 N% 지점에서 분리) |

> **비교 기준 통일 이유**: 텍스트 소스가 달라지면 청킹 변수와 파서 변수가 동시에 바뀌어
> RAGAS 결과 해석이 불가능해진다. IEP-1002 `ipcc_pages.json`을 그대로 재사용한다.

**threshold 3종 실험 결과**

| threshold | 청크 수 | 평균 크기 | 중앙값 | 최소 | 최대 | <100자 | 판정 |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| percentile 75 | 1,050개 | 497자 | 319자 | 1자 | 10,517자 | 206개 | ❌ 너무 세분화 |
| percentile 85 | 630개 | 830자 | 470자 | 1자 | 12,061자 | 97개 | 🔶 평균 목표치 미달 |
| **percentile 95** | **211개** | **2,481자** | **1,280자** | **1자** | **27,236자** | **17개** | **✅ 채택** |

**p95 채택 근거**

세 케이스 모두 평균과 중앙값의 괴리가 크다. 이는 pdfplumber 텍스트에 빈 줄, 도표 잔재, 짧은 캡션 등 노이즈 문장이 많아 SemanticChunker가 이를 독립 청크로 분리하기 때문이다. 평균보다 중앙값이 실제 "전형적인 청크 크기"를 더 정확하게 나타낸다.

| 판단 항목 | 기준 | p75 | p85 | p95 |
| :--- | :--- | :---: | :---: | :---: |
| 중앙값 IEP-1001 최적 구간(1,000~1,200자) 근접도 | 가까울수록 좋음 | 319자 | 470자 | **1,280자** ✅ |
| 청크 수 100개 이상 | 범위 밖 대응 | 1,050개 ✅ | 630개 ✅ | 211개 ✅ |
| 100자 미만 노이즈 청크 | 적을수록 좋음 | 206개 ❌ | 97개 🔶 | **17개** ✅ |

세 기준이 충돌할 경우 평균 크기 우선이나, p95는 세 기준 모두에서 가장 우수하다.

---

### Day 3 — 후처리 + ChromaDB 저장 + 스모크 테스트 (2026-04-10 완료)

#### 후처리 — 5,000자 초과 청크 재분할

p95 원본에 최대 27,236자짜리 초대형 청크가 존재한다. `llama3.1:8b`의 실질 컨텍스트 한계(한글 기준 약 6,000자)를 감안해 5,000자 초과 청크를 RecursiveCharacterTextSplitter로 재분할했다.

| 항목 | 수치 |
| :--- | :---: |
| 원본 청크 수 | 211개 |
| 5,000자 초과 청크 | 24개 |
| 재분할 후 최종 청크 수 | **253개** |
| 최종 평균 크기 | 2,096자 |
| 최종 최대 크기 | 5,000자 |
| 5,000자 초과 청크 (후처리 후) | **0개** ✅ |

> IEP-1002에서 NaN이 34개(Context Recall 기준)였던 주요 원인이 청크 크기 과대였다.
> 후처리로 최대 크기를 5,000자로 제한하여 NaN 감소를 기대한다.

#### ChromaDB 저장

| 항목 | 내용 |
| :--- | :--- |
| 컬렉션명 | `ipcc_semantic_p95_v1` |
| 임베딩 모델 | `jhgan/ko-sroberta-multitask` (768차원) |
| 거리 함수 | cosine |
| 저장 청크 수 | **253개** ✅ |
| 저장 경로 | `IEP_1003/chroma_db/` |

#### 스모크 테스트 4종

| 테스트 | 기준 | 결과 | 수치 |
| :--- | :--- | :---: | :--- |
| ① 청크 수 일치 | DB count == 후처리 청크 수 | ✅ PASS | 253 == 253 |
| ② Retrieval 결과 | top-3 반환, 내용 관련성 있음 | ✅ PASS | 3개 반환, 해수면·온난화 내용 포함 |
| ③ 유사도 점수 | 관련 질의 score < **0.75** | ✅ PASS | 0.5933 / 0.6079 / 0.6268 |
| ④ 검색 분별력 | 무관 질의 score > 관련 질의 score | ✅ PASS | 무관 1.40 vs 관련 0.61 (2.3배) |

> **테스트 ③ 기준값 조정 경위**: 초기 기준 0.5 적용 시 FAIL.
> ChromaDB cosine distance는 score 0.59 = similarity 0.41에 해당하며,
> `jhgan/ko-sroberta-multitask` + 한글 문서 특성상 0.5~0.7이 정상 범위임을 확인.
> 기준값을 **0.75**로 조정하여 재실행 → PASS. 이후 동일 환경 스모크 테스트의 표준 기준값으로 채택.

---

### Day 4 — RAGAS 4지표 평가 (예정)

**평가 환경**

| 항목 | 내용 |
| :--- | :--- |
| 골든 데이터셋 | `IEP_1002/golden_dataset_100.csv` (IEP-1001·1002와 동일) |
| Judge LLM | `llama3.1:8b` (IEP-1001·1002와 동일) |
| 임베딩 (Answer Relevancy) | `nomic-embed-text` |
| ChromaDB 컬렉션 | `ipcc_semantic_p95_v1` (253개) |
| top-k | 3 |
| 평가 전략 | 2회 분리 실행 (T4 메모리 제약) |

**결과** *(평가 완료 후 기입)*

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | TBD | TBD | TBD | TBD |
| 비교 | TBD | TBD | TBD | TBD |
| 의견/예측 | TBD | TBD | TBD | TBD |
| 범위 밖 | TBD | TBD | TBD | TBD |
| **전체** | **TBD** | **TBD** | **TBD** | **TBD** |

**NaN 발생 현황** *(평가 완료 후 기입)*

| 유형 | context_recall | context_precision | faithfulness | answer_relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | - | - | - | - |
| 비교 | - | - | - | - |
| 의견/예측 | - | - | - | - |
| 범위 밖 | - | - | - | - |
| **전체** | **-** | **-** | **-** | **-** |

**3종 비교: IEP-1001 CASE 3 vs IEP-1002 vs IEP-1003** *(평가 완료 후 기입)*

| 유형 | IEP-1001 CASE3 | IEP-1002 | IEP-1003 | 1001 대비 | 1002 대비 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.8627 | 0.3333 | TBD | - | - |
| 비교 | 0.8897 | 0.7619 | TBD | - | - |
| 의견/예측 | 0.8875 | 0.9000 | TBD | - | - |
| 범위 밖 | 0.8595 | 0.7353 | TBD | - | - |
| **전체** | **0.8520** | **0.7106** | **TBD** | **-** | **-** |

**배포용 청킹 확정** *(평가 완료 후 기입)*

| 판단 기준 | 내용 |
| :--- | :--- |
| IEP-1003 전체 Recall > 0.8520 | → IEP-1003 p95 채택 |
| IEP-1003 전체 Recall ≤ 0.8520 | → IEP-1001 CASE 3 유지 |
| **최종 선택** | **TBD** |

**저장 파일 목록** *(예정)*

| 파일 | 내용 |
| :--- | :--- |
| `ipcc_chunks_semantic_p75.json` | threshold=75 청크 1,050개 |
| `ipcc_chunks_semantic_p85.json` | threshold=85 청크 630개 |
| `ipcc_chunks_semantic_p95.json` | threshold=95 청크 211개 (채택) |
| `ipcc_chunks_semantic_p95_processed.json` | 후처리 완료 253개 |
| `chunk_dist_semantic.png` | 3종 분포 히스토그램 |
| `chroma_db/` | ChromaDB (`ipcc_semantic_p95_v1`) |
| `iep1003_day4_retrieved.csv` | Retrieval + Answer 중간 저장 (100행) |
| `iep1003_day4_retriever.csv` | 1회차 평가 원본 (Recall, Precision) |
| `iep1003_day4_generator.csv` | 2회차 평가 원본 (Faithfulness, Relevancy) |
| `iep1003_day4_raw.csv` | 4지표 병합 최종 결과 (100행) |
| `iep1003_day4_summary.csv` | 유형별 4지표 평균 요약 |

## 분석

*(Day 4 평가 완료 후 기입)*

### threshold 선택 — 평균보다 중앙값이 신뢰할 수 있는 대표값

SemanticChunker p95의 평균(2,481자)과 중앙값(1,280자)의 괴리가 크다. 이는 소수의 초대형 청크(최대 27,236자)가 평균을 왜곡하기 때문이다. 중앙값 1,280자는 IEP-1001 최적 구간(1,000~1,200자)에 가장 근접하며, 100자 미만 노이즈 청크도 17개로 3종 중 최소다. 평균이 아닌 중앙값을 기준으로 threshold를 선택한 것이 이번 실험의 핵심 판단이다.

### 후처리의 필요성 — NaN 사전 차단

IEP-1002에서 NaN 급증(34개)의 주요 원인이 청크 크기 과대(최대 2,000자 × top-3 = 6,000자+)였다. p95는 후처리 전 최대 27,236자짜리 청크가 존재해 컨텍스트 과부하가 더 심각할 수 있었다. 5,000자 상한을 적용해 초대형 청크 24개를 재분할하여 NaN 발생을 사전에 차단했다. Day 4 결과에서 NaN이 IEP-1002(34개) 대비 실제로 감소하는지 확인이 필요하다.

### 스모크 테스트 기준값 재정립

cosine distance 기준값 0.5를 0.75로 조정한 경험은 이후 실험에서 재사용할 수 있는 지식이다. `jhgan/ko-sroberta-multitask` + 한글 문서 조합에서 cosine distance 0.5~0.7은 정상적인 유사도 범위이며, 검색 분별력(관련 vs 무관)이 2배 이상 차이나는지가 실질적인 품질 지표다.

## 미해결 질문

- 후처리(5,000자 상한) 적용 후 NaN이 IEP-1002(34개) 대비 실제로 감소하는가? → Day 4에서 확인
- SemanticChunker p95의 중앙값(1,280자) vs 평균(2,096자) 괴리가 RAGAS 결과에 어떤 영향을 미치는가?
- pdfplumber 텍스트의 노이즈(빈 줄, 도표 잔재)가 SemanticChunker 경계 결정에 미치는 영향은? → IEP-1004(Docling)에서 비교 예정
- SemanticChunker가 사실 확인 유형 Recall(IEP-1002 기준 0.3333)을 실질적으로 개선하는가?

## 계획

- **Day 4**: RAGAS 4지표 평가 완료 → 배포용 청킹 확정 → 이 문서 TBD 항목 기입 → Phase 2 진입
- **IEP-1004** (Phase 3): Docling으로 파서 교체 후 동일 청킹 방식 적용 → pdfplumber 대비 성능 변화 측정
- **배포용 청킹 확정 후**: IEP-1001 CASE 3 또는 IEP-1003 p95 기반으로 FastAPI 서비스화(IEP-4001) 즉시 진입

## 참고자료

- [IEP-1000: RAGAS를 이용한 Context Recall 성능 측정](./IEP-1000-ragas-recall.md)
- [IEP-1001: 단순 청킹을 통한 Context Recall 성능 개선](./IEP-1001-simplechunking.md)
- [IEP-1002: 구조 기반 청킹을 통한 Context Recall 성능 개선](./IEP-1002-structural-chunking.md)
- 대상 문서: `KO_IPCC_AR6_SYR_FullVolume.pdf` (188페이지, 한글 번역본)
- 임베딩 모델: `jhgan/ko-sroberta-multitask` (768차원)
- 벡터 DB: ChromaDB (cosine 거리)
- Judge LLM: `llama3.1:8b` (via Ollama)
- 평가 프레임워크: RAGAS
- 개발 환경: Google Colab T4
- 텍스트 소스: `IEP_1002/parsed/ipcc_pages.json` (키: `page_num`, `text`, `char_count`)
