# IEP-2001.3: 하이브리드 검색 방법E — cosine 컬렉션 기준 재실험

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `Completed` |
| **작성일** | 2026-05-08 |

---

## 동기

IEP-2001.1(방법E, threshold=0.20)은 L2 컬렉션(`ipcc_1001_case3_v1`) 기준으로 측정됐다. 그런데 IEP-4001(FastAPI 서비스화) 과정에서 L2 컬렉션이 cosine 컬렉션(`ipcc_1001_case3_cosine_v1`)으로 교체됐다.

배포 환경(cosine)과 실험 환경(L2)이 불일치한 상태에서는 측정 수치를 배포 결정의 근거로 쓸 수 없다. 특히 두 컬렉션의 distance 분포가 전혀 다르므로(L2: 138~140, cosine: 0.33~0.38), threshold=0.20의 실질적 효과도 달라진다. 이 불일치를 해소하기 위해 cosine 컬렉션 기준으로 방법E를 재실험한다.

---

## IEP-2001.1 대비 변경점

| 항목 | IEP-2001.1 (구버전) | IEP-2001.3 (이번) |
| :--- | :--- | :--- |
| ChromaDB 컬렉션 | `ipcc_1001_case3_v1` (L2) | `ipcc_1001_case3_cosine_v1` (cosine) |
| 벡터 검색 방식 | `similarity_search_with_relevance_scores` | `similarity_search_with_score` + `1 - distance` 직접 변환 |
| SIMILARITY_THRESHOLD | 0.20 | 0.20 (동일) |
| TOP_K | 3 | **10** (배포 설정과 동일) |
| Baseline | IEP-1001 Solar v1 (judge 혼용) | **IEP-1001 Solar v2** (전 지표 Solar judge 통일) |

---

## 진행

### 실험 환경

| 항목 | 내용 |
| :--- | :--- |
| 노트북 | `IEP2001_2_hybrid_method_E_cosine.ipynb` |
| ChromaDB 컬렉션 | `ipcc_1001_case3_cosine_v1` (hnsw:space=cosine, 506청크) |
| SIMILARITY_THRESHOLD | 0.20 |
| TOP_K | 10 |
| BM25_CANDIDATE_K | 10 |
| RRF_K | 60 |
| Judge LLM (전 지표) | `solar-pro3` |
| Answer Relevancy strictness | 1 (Solar `n=1` 제약) |
| Answer Relevancy 임베딩 | `jhgan/ko-sroberta-multitask` |
| 실행 환경 | Google Colab T4 |
| 실행일 | 2026-05-08 |

### 핵심 변경: cosine 컬렉션 벡터 검색 방식

```python
# 변경 전 (IEP-2001.1 — LangChain 버전별 변환 공식 불일치 문제)
vectorstore.similarity_search_with_relevance_scores(question, k=k)

# 변경 후 (IEP-2001.3 — 직접 변환)
raw_results = vectorstore.similarity_search_with_score(question, k=k)
return [(doc, 1 - dist) for doc, dist in raw_results]
# cosine distance → similarity 직접 변환
```

### 하이브리드 검색 구조 (방법E)

```
질문
 ├─ 벡터 검색 (cosine)  → (doc, 1-cosine_distance) × 10개
 └─ BM25 검색           → (doc, bm25_score) × 10개
           ↓
     RRF 합산 (RRF_K=60)
           ↓
     TOP_K=10 결과 확정
           ↓
 TOP_K 중 최고 cosine similarity < 0.20 → 거절
 최고 cosine similarity ≥ 0.20 → 답변 생성
```

### Cell 6 — 스모크 테스트 결과

cosine 컬렉션 기준 score 범위 확인.

| 질문 | 최고 similarity | 판정 | 비고 |
| :--- | :---: | :---: | :--- |
| 1.5°C 탄소 감축량 | 0.64+ | ✅ 통과 | 관련 질문 |
| 기후변화 생태계 영향 | 0.62+ | ✅ 통과 | 관련 질문 |
| 환경 보호 개인 실천 | 0.26+ | ✅ 통과 | 경계 케이스 (threshold 0.20 통과) |
| 오늘 점심 메뉴 | 0.23 미만 | ❌ 거절 | 완전 범위 밖 |

cosine 컬렉션 실측값과 일치 (관련: 0.62~0.66, 범위 밖: 0.23~0.30).

### 트러블슈팅

| 오류 | 원인 | 해결 |
| :--- | :--- | :--- |
| `KeyError: '_type'` | ChromaDB 버전 충돌 (컬렉션 포맷 불일치) | `chromadb==0.5.11` 고정 |
| `ImportError: cannot import 'Search'` | langchain-chroma 버전 불일치 | `langchain-chroma==0.1.4` 고정 |
| Faithfulness NaN 57개 | Solar `max_tokens=512` 부족 → `LLMDidNotFinishException` | 다음 실험부터 `max_tokens=1024` 적용 예정 |

---

## 결과

### RAGAS 4지표 (Solar judge, k=10)

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.9600 | 0.7133 | 0.6979 | 0.7269 |
| 비교 | 0.6400 | 0.6842 | 0.6944 | 0.4967 |
| 의견/예측 | 0.8681 | 0.7716 | 0.3333 | 0.6104 |
| 범위 밖 | 0.5800 | 0.2929 | 0.2130 | 0.2109 |
| **전체** | **0.7609** | **0.6125** | **0.4690** | **0.5112** |

**거절 수: 0/100**

### NaN 현황

| 지표 | NaN | 유효 샘플 |
| :--- | :---: | :---: |
| Context Recall | — | — |
| Context Precision | — | — |
| Faithfulness | 57개 | 43개 |
| Answer Relevancy | 0개 | 100개 |

> Faithfulness NaN 57개: IEP-1001 Solar v2 (55개)와 동일 수준 — 비교 조건 유효.
> 원인: Solar judge `max_tokens=512` 부족. 다음 실험부터 1024 적용.

### 생존 편향 보정 (NaN → 0점, 전체 100개 기준)

| 지표 | 낙관적 (NaN 제외) | 유효 샘플 | 보수적 (전체 100개) |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.7609 | — | — |
| Context Precision | 0.6125 | — | — |
| Faithfulness | 0.4690 | 43개 | **0.2017** |
| Answer Relevancy | 0.5112 | 100개 | **0.5112** |

### IEP-1001 Solar v2 (벡터 단독) 대비 비교

| 지표 | 벡터 단독 (baseline) | 방법E cosine | 변화 |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.6549 | **0.7609** | **+0.1060** ↑ |
| Context Precision | 0.5608 | **0.6125** | **+0.0517** ↑ |
| Faithfulness (낙관) | 0.3165 | **0.4690** | **+0.1525** ↑ |
| Faithfulness (보수) | 0.1424 | **0.2017** | **+0.0593** ↑ |
| Answer Relevancy | 0.4075 | **0.5112** | **+0.1037** ↑ |
| 거절 수 | — | **0/100** | — |

### 유형별 변화 (vs IEP-1001 Solar v2)

| 유형 | Recall 변화 | Precision 변화 | Faith 변화 | AR 변화 |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | +0.1600 | +0.1127 | +0.1333 | +0.1078 |
| 비교 | +0.1800 | +0.0622 | **+0.5515** | +0.0878 |
| 의견/예측 | +0.1667 | +0.0093 | +0.0083 | +0.1237 |
| 범위 밖 | **-0.0800** | +0.0331 | +0.0610 | +0.0954 |

### 전체 하이브리드 실험 비교 (Solar judge 기준)

| 단계 | Recall | Precision | Faith (보수) | AR | 거절 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| IEP-1001 벡터 단독 (baseline) | 0.6549 | 0.5608 | 0.1424 | 0.4075 | — |
| IEP-2001 방법C (thr=0.28, L2) | 0.5175 | 0.6406 | 0.1764 | 0.3301 | 17/100 |
| IEP-2001.1 방법E (thr=0.20, L2) | 0.5600 | 0.6835 | 0.1792 | 0.3537 | 10/100 |
| IEP-2001.2 방법F (thr 없음, L2) | 0.6835 | 0.5859 | 0.1600 | 0.4575 | 0/100 |
| **IEP-2001.3 방법E (thr=0.20, cosine)** | **0.7609** | **0.6125** | **0.2017** | **0.5112** | **0/100** |

---

## 분석

### 전 지표 개선 — cosine 컬렉션의 효과

이번 실험의 가장 중요한 발견은 **컬렉션 교체(L2 → cosine)만으로 전 지표가 대폭 개선됐다**는 점이다. 방법E의 검색 로직 자체는 IEP-2001.1과 동일하지만 cosine 컬렉션을 쓰자 Recall이 0.5600 → 0.7609, AR이 0.3537 → 0.5112로 크게 뛰었다.

이는 두 가지 효과가 복합된 결과다. 첫째, cosine 컬렉션에서 벡터 검색의 정확도 자체가 향상됐다. jhgan 임베딩은 cosine 거리 기반으로 학습됐으므로 cosine 컬렉션에서 의미 유사도 측정이 더 정확하다. 둘째, TOP_K를 3에서 10으로 늘려 RRF 합산 풀이 넓어졌다. 더 많은 청크를 BM25와 합산하므로 멀티 청크가 필요한 비교 유형에서 특히 Recall이 개선됐다.

### 비교 유형 Faithfulness 0.1429 → 0.6944 (+0.5515)

가장 극적인 변화다. 비교 유형은 두 시나리오의 수치·차이점을 요구하는 질문이라 특정 숫자와 키워드를 정확히 찾아야 한다. BM25가 이 키워드를 직접 매칭해 관련 청크를 올려주고, cosine 컬렉션에서 벡터 유사도 측정이 정확해지면서 Solar가 실제 보고서 수치에 근거한 답변을 생성할 수 있게 됐다.

### 범위 밖 Recall 소폭 하락 (-0.0800)

범위 밖 질문의 Recall이 0.6600 → 0.5800으로 소폭 하락했다. threshold=0.20이 일부 범위 밖 질문을 통과시켜 답변을 생성하게 되었는데, 생성된 답변의 품질이 낮아 Recall이 떨어진 것으로 추정된다. 그러나 거절 0/100이므로 실제 서비스에서는 사용자가 답변을 받는다. 이 트레이드오프가 수용 가능한 수준인지 판단이 필요하다.

### threshold=0.20의 적절성 재확인

거절 0/100으로 IEP-2001.2 방법F(threshold 없음)와 동일한 거절 수를 기록하면서도 Recall(0.7609)이 방법F(0.6835)보다 높다. 이는 cosine 컬렉션에서 threshold=0.20이 사실상 모든 관련 질문을 통과시키는 수준임을 의미한다. cosine 컬렉션의 범위 밖 질문 score(0.23~0.30)가 threshold=0.20에 가까운 경우 일부 통과하더라도 전체 품질에 큰 영향을 주지 않는다.

---

## 미해결 질문

- 배포 코드에 방법E를 반영할 것인가? 전 지표 개선이 명확하지만 rag.py 수정 + GCS 재업로드 + Cloud Run 재배포 작업이 필요하다.
- 범위 밖 Recall -0.0800은 서비스 품질에 실질적 영향을 주는가? threshold를 0.25~0.30으로 올리면 범위 밖 거절이 늘어나며 트레이드오프가 어떻게 변하는가?
- Faithfulness NaN 57개를 `max_tokens=1024`로 줄이면 보수적 수치가 얼마나 개선되는가?
- IEP-1004(MinerU 파서)로 재인덱싱 후 방법E를 재적용하면 추가 개선이 가능한가?

---

## 결론: 배포 반영 권고

| 지표 | 벡터 단독 (현재 배포) | 방법E cosine | 개선 여부 |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.6549 | **0.7609** | ✅ +0.11 |
| Context Precision | 0.5608 | **0.6125** | ✅ +0.05 |
| Faithfulness (보수) | 0.1424 | **0.2017** | ✅ +0.06 |
| Answer Relevancy | 0.4075 | **0.5112** | ✅ +0.10 |

전 지표 개선 + 거절 0/100 — 배포 반영을 권고한다. 단, 범위 밖 Recall 소폭 하락(-0.0800) 모니터링 필요.

---

## 계획

- **rag.py 반영 (미결)**: BM25 인덱스 구축 + 하이브리드 검색 함수 추가, THRESHOLD=0.20, TOP_K=10 유지
- **Cloud Run 재배포**: rag.py 수정 후 Docker 재빌드 + 재배포
- **README 수치 갱신**: 검색 방식 비교표에 방법E cosine 행 추가
- **IEP-1004**: MinerU 파서 교체 실험 완료 후 수치 비교

---

## 참고자료

- [IEP-2001: 하이브리드 검색(BM25 + Vector)을 통한 검색 품질 개선](./IEP-2001-hybrid-search.md)
- [IEP-2001.1: 하이브리드 검색 거절 로직 재조정](./IEP-2001-1-hybrid-threshold.md)
- [IEP-2001.2: 하이브리드 검색 방법F (threshold 제거)](./IEP-2001-2-hybrid-method-f.md)
- [IEP-1001.1: IEP-1001 CASE 3 전 지표 Solar judge 재측정 (v2)](./IEP-1001-1-solar-v2.md)
- [IEP-4001: FastAPI 서비스화 — ChromaDB cosine 컬렉션 전환](./IEP-4001-fastapi.md)
- 실험 노트북: `IEP2001_2_hybrid_method_E_cosine.ipynb`
- 사용 환경 (2026-05-08)
  - 플랫폼: Google Colab T4
  - 임베딩: `jhgan/ko-sroberta-multitask` (device: cuda)
  - Judge LLM: `solar-pro3` (Upstage, 전 지표)
  - 벡터DB: ChromaDB `ipcc_1001_case3_cosine_v1` (506개 청크, hnsw:space=cosine)
  - 주요 패키지: `chromadb==0.5.11`, `langchain-chroma==0.1.4`, `rank-bm25`, `kiwipiepy`, `ragas`
