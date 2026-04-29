# IEP-2001.2: 하이브리드 검색 방법 F (threshold 제거)

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `Completed` |
| **작성일** | 2026-04-30 |

---

## 동기

IEP-2001.1 방법 E(threshold=0.20)에서 거절 10/100, Recall 0.5600으로 회복됐지만 IEP-1001 Solar v2(Recall 0.6549)와의 격차가 여전히 존재했다. 남은 거절 10개가 Recall에 얼마나 영향을 주는지 정확히 알아야 threshold 설정의 적절성을 판단할 수 있다.

**방법 F**는 threshold를 완전히 제거하여 거절 0개 조건에서 측정하는 실험이다. 이 수치가 방법 E 대비 Recall upper bound 역할을 하며, 두 수치의 차이가 "threshold=0.20이 Recall에 미치는 비용"을 정량화한다.

---

## 진행

### 방법 설계

```
[방법 E — IEP-2001.1]              [방법 F — IEP-2001.2]
벡터 k=10 + BM25 k=10               벡터 k=10 + BM25 k=10
→ RRF → TOP_K=3                     → RRF → TOP_K=3
→ TOP_K 최고 score < 0.20 → 거절    → 거절 없음, 항상 TOP_K 반환
→ 거절 10/100                       → 거절 0/100
```

`hybrid_search()` 함수에서 threshold 체크 블록 전체를 제거했다. 그 외 모든 파라미터(TOP_K, BM25_CANDIDATE_K, RRF_K)는 방법 E와 동일하다.

### Cell 6 검증 결과 (2026-04-30)

모든 질문에서 3개 청크를 반환하는지 확인했다.

| 질문 | 방법 F 결과 | 비고 |
| :--- | :---: | :--- |
| 1.5°C 탄소 감축량 | 3개 반환 | — |
| 기후변화 생태계 영향 | 3개 반환 | — |
| 환경 보호 개인 실천 (score 0.2624) | 3개 반환 | 방법E에서 통과된 경계 케이스 |
| 해수면 상승 연안 도시 | 3개 반환 | — |
| **오늘 점심 메뉴** | **3개 반환** | 완전 범위 밖도 거절 없음 확인 |

### 실험 환경

| 항목 | 내용 |
| :--- | :--- |
| 노트북 | `IEP2001_2_hybrid_method_f.ipynb` |
| SIMILARITY_THRESHOLD | **없음** (threshold 제거) |
| TOP_K | 3 |
| BM25_CANDIDATE_K | 10 |
| RRF_K | 60 |
| 결과 저장 경로 | `IEP_2001/results_hybrid_f` |
| Judge LLM (전 지표) | `solar-pro3` |
| 실행 환경 | Google Colab T4 |
| 실행일 | 2026-04-30 |

---

## 결과

### RAGAS 4지표 (Solar judge)

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | — | — | — | — |
| 비교 | — | — | — | — |
| 의견/예측 | — | — | — | — |
| 범위 밖 | — | — | — | — |
| **전체** | **0.6835** | **0.5859** | **0.3200** | **0.4575** |

*(유형별 수치는 결과 CSV 참조)*

**거절 수: 0/100**

### NaN 현황

| 지표 | NaN | 유효 샘플 |
| :--- | :---: | :---: |
| Context Recall | 1개 | 99개 |
| Context Precision | 0개 | 100개 |
| Faithfulness | 50개 | 50개 |
| Answer Relevancy | 0개 | 100개 |

### 생존 편향 보정 (NaN → 0점, 전체 100개 기준)

| 지표 | 낙관적 (NaN 제외) | 유효 샘플 | 보수적 (전체 100개) |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.6835 | 99개 | **0.6767** |
| Context Precision | 0.5859 | 100개 | **0.5859** |
| Faithfulness | 0.3200 | 50개 | **0.1600** |
| Answer Relevancy | 0.4575 | 100개 | **0.4575** |

### 3-way 비교 (Solar judge 기준)

| 단계 | Recall | Precision | Faith (보수) | AR | 거절 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| IEP-1001 Solar v2 (벡터) | 0.6549 | 0.5608 | 0.1424 | 0.4075 | — |
| IEP-2001.1 방법E (thr=0.20) | 0.5600 | 0.6835 | 0.1792 | 0.3537 | 10/100 |
| **IEP-2001.2 방법F (thr 없음)** | **0.6835** | **0.5859** | **0.1600** | **0.4575** | **0/100** |

### 방법E → 방법F 변화

| 지표 | 방법E | 방법F | 변화 |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.5600 | **0.6835** | **+0.1235** ↑ |
| Context Precision | 0.6835 | 0.5859 | **−0.0976** ↓ |
| Faithfulness (보수) | 0.1792 | 0.1600 | −0.0192 ↓ |
| Answer Relevancy | 0.3537 | **0.4575** | **+0.1038** ↑ |
| 거절 | 10/100 | **0/100** | **−10** |

---

## 분석

### threshold 제거의 트레이드오프

방법 F의 핵심 발견은 **threshold 제거가 Recall과 Precision에 반대 방향으로 작용한다**는 점이다.

- **Recall +0.1235**: 거절 10개 해소로 Recall이 0.5600 → 0.6835로 회복됐다. IEP-1001 Solar v2(0.6549)도 넘어섰다. 즉 거절 10개가 Recall에 0.12의 비용을 부과하고 있었다.
- **Precision −0.0976**: threshold가 없으니 범위 밖 질문도 contexts를 반환한다. 무관한 청크가 포함되면서 Precision이 희석됐다.

### threshold=0.20의 위치

이 결과를 통해 threshold=0.20의 역할이 명확해진다.

```
threshold 없음(방법F): Recall 0.6835, Precision 0.5859
threshold 0.20(방법E): Recall 0.5600, Precision 0.6835
threshold 0.28(방법C): Recall 0.5175, Precision 0.6406
```

Recall과 Precision은 threshold와 역방향으로 움직인다. 방법 E(0.20)는 두 지표의 균형점으로 볼 수 있으며, 실제 서비스 배포에서 범위 밖 질문에 대한 거절 응답이 필요하다면 방법 E가 적합하다. 순수한 검색 품질 극대화가 목표라면 방법 F가 upper bound다.

### Faithfulness NaN 50개

거절 0개 조건에서 범위 밖 질문의 답변까지 Solar judge가 평가하면서 NaN이 방법 E(31개) 대비 증가했다. 범위 밖 질문은 contexts가 있어도 답변 근거를 Solar가 파싱하기 어렵기 때문으로 추정된다.

---

## 미해결 질문

- threshold 값을 0.15, 0.10으로 더 낮추면 Recall과 Precision의 교차점이 어디서 형성되는가?
- 범위 밖 유형을 측정에서 제외(in-scope 75개)하면 방법 E와 F의 Recall/Precision 격차가 달라지는가?
- 실제 서비스에서 범위 밖 거절의 사용자 경험 가치를 어떻게 정량화할 수 있는가?

---

## 결론: 배포 채택 권고

| 조건 | 채택 방법 |
| :--- | :--- |
| 서비스 배포 (거절 응답 필요) | **방법 E** (threshold=0.20) |
| 검색 품질 측정 upper bound | **방법 F** (threshold 없음) |

방법 E와 F의 수치를 README에 병기하여 threshold 선택의 근거를 데이터로 설명한다.

---

## 계획

- **rag.py 반영**: `SIMILARITY_THRESHOLD=0.20`으로 업데이트 후 IEP-4001 맥 로컬 재실행
- **IEP-2002**: 색인 전처리(용어집·부속서 분리) → FlashRank 리랭킹 재시도
- **README 갱신**: 3-way 비교표(Solar judge 기준) 업데이트

---

## 참고자료

- [IEP-2001: 하이브리드 검색(BM25 + Vector)을 통한 검색 품질 개선](./IEP-2001-hybrid-search.md)
- [IEP-2001.1: 하이브리드 검색 거절 로직 재조정](./IEP-2001-1-hybrid-threshold.md)
- [IEP-1001.1: IEP-1001 CASE 3 전 지표 Solar judge 재측정 (v2)](./IEP-1001-1-solar-v2.md)
- 실험 노트북: `notebooks/IEP2001_2_hybrid_method_f.ipynb`
- 사용 환경 (2026-04-30)
  - 플랫폼: Google Colab T4
  - 임베딩: `jhgan/ko-sroberta-multitask` (device: cuda)
  - Judge LLM: `solar-pro3` (Upstage)
  - 벡터DB: ChromaDB, 컬렉션 `ipcc_1001_case3_v1` (506개 청크)
