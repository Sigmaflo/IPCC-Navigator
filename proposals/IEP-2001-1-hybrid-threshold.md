# IEP-2001.1: 하이브리드 검색 거절 로직 재조정 (threshold 하향)

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `Completed` |
| **작성일** | 2026-04-30 |

---

## 동기

IEP-2001에서 하이브리드 검색(BM25 + Vector RRF)을 도입했으나 Context Recall이 0.5175로 벡터 단독 대비 급락했다. 원인은 거절 수 17/100으로 분석됐다.

거절 과다의 구조적 원인은 SIMILARITY_THRESHOLD(0.28)를 CANDIDATE_K=10개 전체에 적용하는 방식(방법 C)이었다. TOP_K=3 결과를 RRF로 확정하기 전 단계에서 필터링하므로, borderline 질문(score 0.20~0.28)이 TOP_K에 올라오지도 못한 채 거절됐다.

본 실험에서는 threshold를 0.28 → 0.20으로 하향 조정하는 **방법 E**를 시도하여 거절 수를 줄이고 Recall 회복을 검증한다.

---

## 진행

### 방법 설계

IEP-2001에서 시도한 방법 D(TOP_K 결과 기준 threshold 적용)는 Cell 6 검증에서 방법 C와 거절 기준이 동일함을 확인하여 폐기했다.

> **방법 D 폐기 이유**: TOP_K 결과 중 최고 벡터 score도 결국 CANDIDATE_K=10 중 하나의 score다. 10개 전부 threshold 미달이면 TOP_K 최고 score도 미달이므로 방법 C와 결과가 동일하다.

**방법 E**: `SIMILARITY_THRESHOLD = 0.20` (0.28 → 하향)

```
[방법 C — IEP-2001]               [방법 E — IEP-2001.1]
CANDIDATE_K=10 결과에             CANDIDATE_K=10 결과에
threshold 0.28 적용                threshold 0.20 적용
→ 거절 17/100                      → 거절 감소 기대
```

### Cell 6 검증 결과 (2026-04-30)

| 질문 | 방법 C (threshold 0.28) | 방법 E (threshold 0.20) | 변화 |
| :--- | :---: | :---: | :---: |
| 1.5°C 탄소 감축량 | 통과 | 통과 | — |
| 기후변화 생태계 영향 | 통과 | 통과 | — |
| 환경 보호 개인 실천 (score 0.2624) | 거절 | **통과** | ✅ 개선 |
| 해수면 상승 연안 도시 | 통과 | 통과 | — |
| 오늘 점심 메뉴 | 거절 | 거절 | — |

경계 케이스(score 0.2624)가 방법 E에서 통과로 전환됐고, 완전 범위 밖 질문은 여전히 거절됐다.

### 실험 환경

| 항목 | 내용 |
| :--- | :--- |
| 노트북 | `IEP2001_1_hybrid_reranking_fix.ipynb` |
| SIMILARITY_THRESHOLD | **0.20** (0.28 → 하향) |
| TOP_K | 3 |
| BM25_CANDIDATE_K | 10 |
| RRF_K | 60 |
| 결과 저장 경로 | `IEP_2001/results_hybrid_e` |
| Judge LLM (전 지표) | `solar-pro3` |
| 실행 환경 | Google Colab T4 |
| 실행일 | 2026-04-30 |

---

## 결과

### RAGAS 4지표 (Solar judge)

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.7200 | 0.8229 | 0.4774 | 0.5743 |
| 비교 | 0.3600 | 0.7933 | 0.3308 | 0.3575 |
| 의견/예측 | 0.5600 | 0.8767 | 0.3699 | 0.4637 |
| 범위 밖 | 0.6000 | 0.2467 | 0.0000 | 0.0192 |
| **전체** | **0.5600** | **0.6835** | **0.2597** | **0.3537** |

**거절 수: 10/100** (방법 C 17/100 → -7)

### NaN 현황

| 지표 | NaN | 유효 샘플 |
| :--- | :---: | :---: |
| Context Recall | 1개 | 99개 |
| Context Precision | 0개 | 100개 |
| Faithfulness | 31개 | 69개 |
| Answer Relevancy | 0개 | 100개 |

### 생존 편향 보정 (NaN → 0점, 전체 100개 기준)

| 지표 | 낙관적 (NaN 제외) | 유효 샘플 | 보수적 (전체 100개) |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.5600 | 99개 | **0.5544** |
| Context Precision | 0.6835 | 100개 | **0.6835** |
| Faithfulness | 0.2597 | 69개 | **0.1792** |
| Answer Relevancy | 0.3537 | 100개 | **0.3537** |

### 3-way 비교 (Solar judge 기준)

| 단계 | Recall | Precision | Faith (보수) | AR | 거절 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| IEP-1001 Solar v2 (벡터) | 0.6549 | 0.5608 | 0.1424 | 0.4075 | — |
| IEP-2001 방법C (thr=0.28) | 0.5175 | 0.6406 | 0.1764 | 0.3301 | 17/100 |
| **IEP-2001.1 방법E (thr=0.20)** | **0.5600** | **0.6835** | **0.1792** | **0.3537** | **10/100** |

---

## 분석

### Recall 회복 폭이 제한적인 이유

거절 17→10으로 줄었지만 Recall은 0.5175→0.5600으로 소폭만 회복됐다. 남은 거절 10개와 비교 유형의 구조적 약점(Recall 0.3600)이 전체 평균을 끌어내린다.

방법 E와 IEP-1001 Solar v2의 Recall 격차가 0.09로 줄었다는 점은 긍정적이다. judge가 동일한 조건에서 하이브리드 검색이 벡터 단독 대비 Recall을 완전히 회복하지 못한 이유는 거절 10개가 아직 남아있기 때문이다.

### Precision은 명확한 우위

Context Precision 0.6835로 IEP-1001 Solar v2(0.5608) 대비 +0.1227 높다. BM25가 키워드 매칭으로 관련성 높은 청크를 보완적으로 올린 효과가 Precision에서 일관되게 확인된다. 특히 사실 확인(0.8229), 의견/예측(0.8767) 유형에서 두드러진다.

### threshold=0.20의 적절성

방법 E와 방법 F(threshold 완전 제거)의 비교로 판단 가능하다. threshold를 완전히 제거하면 Recall이 더 올라가지만 Precision이 하락하는 트레이드오프가 존재한다. 0.20이 Recall과 Precision의 균형점이 되는지는 IEP-2001.2에서 확인한다.

---

## 미해결 질문

- threshold를 완전히 제거하면(방법 F) Recall은 어느 수준까지 회복되는가? → IEP-2001.2에서 측정
- 비교 유형 Recall 0.3600이 낮은 원인은 거절인가, 검색 품질 자체의 한계인가?
- threshold=0.20이 실제 서비스 거절 로직으로 적절한가? 0.20 미만 score 질문들의 실제 내용은?

---

## 계획

- **IEP-2001.2**: threshold 완전 제거(방법 F) 측정 → Recall upper bound 확인 및 방법 E와 트레이드오프 비교
- **rag.py 반영**: IEP-2001.2 측정 후 방법 E/F 중 배포 채택 결정
- **IEP-2002**: 거절 로직 조정 완료 후 색인 전처리(용어집·부속서 분리) → FlashRank 리랭킹 재시도

---

## 참고자료

- [IEP-2001: 하이브리드 검색(BM25 + Vector)을 통한 검색 품질 개선](./IEP-2001-hybrid-search.md)
- [IEP-2001.2: 하이브리드 검색 방법 F (threshold 제거)](./IEP-2001-2-hybrid-method-f.md)
- [IEP-1001.1: IEP-1001 CASE 3 전 지표 Solar judge 재측정 (v2)](./IEP-1001-1-solar-v2.md)
- 실험 노트북: `notebooks/IEP2001_1_hybrid_reranking_fix.ipynb`
- 사용 환경 (2026-04-30)
  - 플랫폼: Google Colab T4
  - 임베딩: `jhgan/ko-sroberta-multitask` (device: cuda)
  - Judge LLM: `solar-pro3` (Upstage)
  - 벡터DB: ChromaDB, 컬렉션 `ipcc_1001_case3_v1` (506개 청크)
