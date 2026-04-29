# IEP-1001.1: IEP-1001 CASE 3 전 지표 Solar judge 재측정 (v2)

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `Completed` |
| **작성일** | 2026-04-30 |

---

## 동기

IEP-2001 및 IEP-2001.1 실험에서 전 지표를 Solar judge로 측정한 반면, IEP-1001 CASE 3의 baseline은 Context Recall/Precision이 llama3.1:8b judge 기준이었다. judge가 다른 수치를 직접 비교하는 것은 부당하며, 특히 Recall 수치 해석에 혼선을 야기한다.

두 실험의 비교를 공정하게 만들기 위해 **전 지표를 Solar judge로 통일**하는 재측정을 진행했다. 동시에 retriever k=3(IEP-1001 원본) → k=10(IEP-2001.1 CANDIDATE_K와 동일 조건)으로 변경하여 contexts 구성 조건도 통일했다.

---

## 진행

### 실험 환경

| 항목 | 내용 |
| :--- | :--- |
| 노트북 | `IEP1001_case3_ragas_solar_v2.ipynb` |
| ChromaDB 컬렉션 | `ipcc_1001_case3_v1` (506청크) |
| retriever k | 10 (IEP-2001.1 CANDIDATE_K와 동일) |
| Judge LLM (전 지표) | `solar-pro3` |
| Answer Relevancy 임베딩 | `jhgan/ko-sroberta-multitask` |
| Answer Relevancy strictness | 1 (Solar `n=1` 제약) |
| 결과 저장 경로 | `IEP_1001_CASE3/results_solar_v2` |
| 실행 환경 | Google Colab T4 |
| 실행일 | 2026-04-30 |

### v1 대비 변경 사항

| 항목 | v1 (IEP-1001 원본) | v2 (이번) |
| :--- | :--- | :--- |
| Context Recall/Precision judge | llama3.1:8b | **solar-pro3** |
| Faithfulness/AR judge | solar-pro3 | solar-pro3 (동일) |
| retriever k | 3 | **10** |
| 결과 경로 | `results_solar` | `results_solar_v2` |

---

## 결과

### RAGAS 4지표 (Solar judge, k=10)

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.8000 | 0.6006 | 0.5646 | 0.6191 |
| 비교 | 0.4600 | 0.6220 | 0.1429 | 0.4089 |
| 의견/예측 | 0.7014 | 0.7623 | 0.3250 | 0.4867 |
| 범위 밖 | 0.6600 | 0.2598 | 0.1520 | 0.1155 |
| **전체** | **0.6549** | **0.5608** | **0.3165** | **0.4075** |

### NaN 현황

| 지표 | NaN | 유효 샘플 |
| :--- | :---: | :---: |
| Context Recall | 1개 | 99개 |
| Context Precision | 1개 | 99개 |
| Faithfulness | 55개 | 45개 |
| Answer Relevancy | 0개 | 100개 |

### 생존 편향 보정 (NaN → 0점, 전체 100개 기준)

| 지표 | 낙관적 (NaN 제외) | 유효 샘플 | 보수적 (전체 100개) |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.6549 | 99개 | **0.6484** |
| Context Precision | 0.5608 | 99개 | **0.5552** |
| Faithfulness | 0.3165 | 45개 | **0.1424** |
| Answer Relevancy | 0.4075 | 100개 | **0.4075** |

### Solar v2 vs Solar v1 vs llama 비교

| 지표 | Solar v2 (이번) | Solar v1 | llama3.1:8b |
| :--- | :---: | :---: | :---: |
| Context Recall | **0.6549** | — (미측정) | 0.8537 |
| Context Precision | **0.5608** | — (미측정) | 0.6117 |
| Faithfulness | **0.3165** | 0.2748 (+0.0417) | 0.4361 |
| Answer Relevancy | **0.4075** | 0.3409 (+0.0666) | 0.6143 |

---

## 분석

### judge 차이가 Recall 수치에 미친 영향

가장 중요한 발견은 **llama가 Solar보다 관대한 judge**라는 점이다. llama 기준 Recall 0.8537이 Solar 기준 0.6549로 -0.1988 하락했다. 이는 IEP-2001/2001.1의 Solar 기준 Recall(0.52~0.56)이 IEP-1001 llama 기준(0.8537)보다 낮게 나온 원인의 상당 부분이 judge 차이였음을 의미한다. Solar judge로 통일한 이번 측정이 공정한 비교 기준이 된다.

### Faithfulness NaN 55개

v1(NaN 38개) 대비 NaN이 55개로 증가했다. retriever k=10으로 contexts가 길어지면서 Solar judge의 파싱 실패가 늘어난 것으로 추정된다. 보수적 Faithfulness가 0.1424로 낙관적(0.3165)의 절반 이하다. IEP-3002(Faithfulness NaN 감소를 위한 프롬프트 튜닝)의 필요성이 더욱 높아졌다.

### Faithfulness/AR이 v1 대비 소폭 개선된 이유

k=10으로 contexts를 더 많이 제공하니 Solar가 근거 있는 답변을 더 잘 생성한 것으로 보인다. Faithfulness +0.0417, AR +0.0666으로 두 지표 모두 개선됐다.

---

## 미해결 질문

- Faithfulness NaN 55개의 근본 원인은 contexts 길이(k=10)인가, Solar judge 프롬프트 파싱 실패인가?
- k=3(원본)과 k=10(이번) 조건에서 Recall/Precision 차이는 얼마나 나는가? → 별도 측정 필요
- llama judge와 Solar judge의 Recall 판정 기준 차이를 정량화할 수 있는가?

---

## 계획

- **IEP-2001.1/2001.2와 공정 비교**: 이번 측정 수치(Solar v2)를 README의 새 baseline으로 업데이트
- **IEP-3002**: Faithfulness NaN 감소를 위한 Solar judge 프롬프트 튜닝 진행

---

## 참고자료

- [IEP-1001: 단순 청킹 방식의 청크 크기 실험 및 RAGAS 4대 지표 측정](./IEP-1001-simplechunking.md)
- [IEP-2001: 하이브리드 검색(BM25 + Vector)을 통한 검색 품질 개선](./IEP-2001-hybrid-search.md)
- [IEP-2001.1: 하이브리드 검색 거절 로직 재조정](./IEP-2001-1-hybrid-threshold.md)
- 실험 노트북: `notebooks/IEP1001_case3_ragas_solar_v2.ipynb`
- 사용 환경 (2026-04-30)
  - 플랫폼: Google Colab T4
  - 임베딩: `jhgan/ko-sroberta-multitask` (device: cuda)
  - Judge LLM: `solar-pro3` (Upstage, 전 지표)
  - 벡터DB: ChromaDB, 컬렉션 `ipcc_1001_case3_v1` (506개 청크)
