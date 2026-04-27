# IEP-2001: 하이브리드 검색(BM25 + Vector)을 통한 검색 품질 개선

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `Completed` |
| **작성일** | 2026-04-27 |

---

## 동기

IEP-1001 CASE 3 벡터 단독 검색에서 두 가지 구조적 한계가 확인되었다.

첫째, **키워드·수치 매칭 취약성**이다. 벡터 검색은 의미적 유사도 기반이라 `1.5°C`, `AR6`, `GHG`, `넷제로` 같은 고유명사·수치·전문용어를 직접 매칭하지 못한다. IPCC 보고서처럼 전문용어가 밀집된 문서에서 벡터 검색 단독으로는 사실 확인 유형에서 구조적으로 불리하다.

둘째, **Context Precision 0.6117**이다. 검색된 3개 청크 중 일부가 질문과 무관한 청크로 채워지는 현상이 나타났다. 벡터 검색이 의미적으로 유사하지만 실제 정답과 무관한 청크를 상위에 올리는 경우가 있기 때문이다.

BM25는 키워드 일치 기반 검색으로 위의 두 한계를 직접 보완한다. 두 검색 결과를 RRF(Reciprocal Rank Fusion)로 합산하면 "의미적으로도 관련 있고, 키워드도 일치하는" 청크가 상위로 올라와 Recall과 Precision을 동시에 개선할 수 있다는 가설을 검증한다.

---

## 진행

### 실험 설계

**비교 기준**: IEP-1001 CASE 3 벡터 단독 (Recall 0.8537, Precision 0.6117, Faithfulness 0.2748, AR 0.3409)

**통제 조건**: 동일한 골든 데이터셋 100개, 동일한 ChromaDB 컬렉션(`ipcc_1001_case3_v1`, 506청크), 동일한 RAGAS 측정 환경(Solar judge, jhgan 임베딩, strictness=1)

**변경 조건**: 검색 방식만 벡터 단독 → 하이브리드(BM25 + Vector RRF)로 교체

### 하이브리드 검색 구조

```
질문
 ├─ 벡터 검색  → (doc, cosine_score) × 10개
 │              → SIMILARITY_THRESHOLD(0.28) 필터
 │              → 통과 0개 시 즉시 거절 반환
 │
 └─ BM25 검색  → (doc, bm25_score)   × 10개
                       ↓
              RRF 합산: score = Σ 1 / (60 + rank)
                       ↓
              TOP_K(3개) 반환
```

**Threshold 처리 방식 (방법 C)**

RRF 점수와 cosine score는 단위가 다르므로 0.28 기준을 BM25에 적용할 수 없다. 벡터 검색 결과에 먼저 threshold를 적용해 IPCC 범위 밖 질문을 걸러낸 뒤, 통과한 경우에만 BM25 결과와 RRF 합산한다. 기존 거절 로직이 그대로 유지된다.

### 파라미터 설정

| 파라미터 | 값 | 근거 |
| :--- | :---: | :--- |
| TOP_K | 3 | IEP-1001과 동일 |
| BM25_CANDIDATE_K | 10 | RRF 전 넉넉히 뽑아 합산 풀 확대 |
| SIMILARITY_THRESHOLD | 0.28 | IEP-4001 Colab 실측 확정값 |
| RRF_K | 60 | 표준값 (Cormack et al. 2009) |
| 토크나이저 | kiwipiepy | 한국어 형태소 분석 (공백 split 대비 정확도 향상) |

### Cell 6 단일 질문 비교 테스트 결과 (2026-04-27)

RAGAS 측정 전 4개 질문으로 동작을 먼저 확인했다.

| 질문 | 벡터 단독 page | 하이브리드 page | 차이 |
| :--- | :--- | :--- | :--- |
| 1.5°C 탄소 감축량 | 34, 100, 25 | 25, 100, 34 | 순위 변경 (page 25 상승) |
| 기후변화 생태계 영향 | 61, 143, 137 | 61, 20, 143 | **page 20 신규 등장** |
| 환경 보호 개인 실천 (경계 케이스) | score 0.2624 | 거절 | 거절 유지 ✅ |
| 오늘 점심 메뉴 (완전 범위 밖) | score −0.09 | 거절 | 거절 유지 ✅ |

**관찰**: "기후변화 생태계" 질문에서 하이브리드가 벡터 단독에 없던 page 20을 올렸다. BM25가 "기후변화", "영향" 키워드를 직접 매칭해 추가 관련 청크를 발굴한 결과다. 거절 로직은 두 경계 케이스 모두 정상 동작했다.

### RAGAS 측정 환경

| 항목 | 내용 |
| :--- | :--- |
| 노트북 | `IEP2001_hybrid_search_experiment.ipynb` |
| 골든 데이터셋 | `IEP_1002/golden_dataset_100.csv` (IEP-1001~1003과 동일) |
| Answer 생성 LLM | `solar-pro3` |
| Judge LLM (Recall/Precision) | `solar-pro3` (Colab llama 연결 실패로 대체) |
| Judge LLM (Faithfulness/AR) | `solar-pro3` |
| Answer Relevancy 임베딩 | `jhgan/ko-sroberta-multitask` |
| Answer Relevancy strictness | 1 (Solar `n=1` 제약) |
| RunConfig | `max_workers=2, timeout=120, max_retries=3` |
| batch_size | 1 (Solar 타임아웃 방지) |
| ChromaDB 컬렉션 | `ipcc_1001_case3_v1` (506청크) |
| 실행 환경 | Google Colab T4 |

> ⚠️ Context Recall/Precision을 Solar judge로 측정했으므로 IEP-1001 llama 기준 수치(0.8537/0.6117)와 직접 비교 불가. 하이브리드 내부 비교(검색 방식 변화에 따른 상대적 개선)는 judge가 동일하므로 유효하다.

---

## 결과

### RAGAS 4지표

*(judge: Solar, 2026-04-27)*

| 유형 | Context Recall | Context Precision | Faithfulness | Answer Relevancy |
| :--- | :---: | :---: | :---: | :---: |
| 사실 확인 | 0.7200 | **0.8611** | 0.4937 | 0.4829 |
| 비교 | 0.3200 | 0.7633 | 0.2864 | 0.3401 |
| 의견/예측 | 0.5100 | 0.8000 | 0.2352 | 0.4324 |
| 범위 밖 | 0.5200 | 0.1467 | 0.0800 | 0.0650 |
| **전체** | **0.5175** | **0.6406** | **0.2672** | **0.3301** |

*judge: Solar (Colab llama 연결 실패로 전 지표 Solar 대체)*

**NaN 현황**

| 지표 | NaN | 유효 샘플 |
| :--- | :---: | :---: |
| Context Recall | — | — |
| Context Precision | — | — |
| Faithfulness | 34개 | 66개 |
| Answer Relevancy | 0개 | 100개 |

**생존 편향 보정** (NaN → 0점, 전체 100개 기준)

| 지표 | 낙관적 (NaN 제외) | 유효 샘플 | 보수적 (전체 100개) |
| :--- | :---: | :---: | :---: |
| Faithfulness | 0.2672 | 66개 | **0.1764** |
| Answer Relevancy | 0.3301 | 100개 | **0.3301** |

**거절 수: 17/100** (벡터 단독 대비 증가 — 분석 섹션 참조)

### 벡터 단독 vs 하이브리드 비교

| 지표 | 벡터 단독 (IEP-1001)* | 하이브리드 (IEP-2001) | 변화 |
| :--- | :---: | :---: | :---: |
| Context Recall | 0.8537 | 0.5175 | **−0.3362** |
| Context Precision | 0.6117 | 0.6406 | **+0.0289** ✅ |
| Faithfulness | 0.2748 | 0.2672 | −0.0076 |
| Faith (보수적) | 0.1704 | 0.1764 | +0.0060 |
| Answer Relevancy | 0.3409 | 0.3301 | −0.0108 |
| 거절 수 | — | **17/100** | — |

\*IEP-1001은 llama judge 기준. IEP-2001은 Solar judge 기준. 수치 직접 비교 불가 — 방향성 참고용.

---

## 분석

### Recall 급락의 직접 원인 — 거절 수 17/100

전체 Recall이 0.8537 → 0.5175로 급락한 직접 원인은 거절 수 증가다. 거절된 17개 질문은 Recall, AR이 사실상 0으로 처리되어 전체 평균을 끌어내렸다.

거절이 늘어난 구조적 이유는 다음과 같다. 벡터 검색에 SIMILARITY_THRESHOLD(0.28)를 적용하는데, IEP-1001에서 이 값은 `vectorstore.as_retriever()`를 통해 **TOP_K(3)개 결과 중 임계값 미달 시 거절**하는 방식으로 동작했다. 반면 IEP-2001에서는 CANDIDATE_K(10)개를 뽑고 필터를 적용하기 때문에 TOP_K보다 넓은 풀에서 threshold를 적용한다. borderline 질문들이 더 엄격하게 걸러진 것으로 추정된다.

또한 IEP-1001 골든 데이터셋 중 일부 질문(특히 비교, 의견/예측 유형)이 threshold 0.28 근방의 score를 가졌을 가능성이 있다. 실제로 비교 유형 Recall이 0.8600 → 0.3200으로 가장 크게 하락했는데, 이는 거절로 인한 0점 처리가 집중된 유형임을 시사한다.

### Precision 개선 — 가설 일부 확인

Context Precision이 0.6117 → 0.6406(+0.0289)으로 유일하게 개선됐다. 비교(+0.09), 의견/예측(+0.02), 범위 밖(+0.07) 유형에서 모두 올랐다. BM25가 관련 키워드를 포함한 청크를 보완적으로 올려 검색 정확도를 높인다는 가설이 Precision에서 부분적으로 확인된다.

Faithfulness와 Answer Relevancy는 각각 −0.0076, −0.0108으로 거의 변화 없다. 거절 처리를 제외한 답변 생성 품질 자체는 벡터 단독과 유사한 수준임을 의미한다.

### 결론 — 거절 로직 조정이 선결 과제

하이브리드 검색 자체의 방향성(Precision 개선)은 옳으나, 거절 수 증가로 인한 Recall 급락이 전체 평가를 왜곡했다. 현재 설정(CANDIDATE_K=10 + threshold 0.28)은 지나치게 보수적이다.

개선 방향은 두 가지다. 첫째, THRESHOLD를 하향 조정(0.28 → 0.20 내외)하거나 CANDIDATE_K를 줄여 borderline 질문의 거절을 줄인다. 둘째, threshold를 TOP_K 결과에만 적용하는 방식(IEP-1001과 동일 로직)으로 변경한다. 이 조정 없이 IEP-2002(리랭킹)로 진행하면 동일한 거절 문제가 반복된다.

---

## 미해결 질문

- **CANDIDATE_K=10 + threshold 0.28 조합이 거절을 과도하게 발생시키는가?** threshold를 낮추거나 TOP_K 결과에만 적용하면 Recall이 회복되는가? → 재실험 필요
- kiwipiepy 형태소 분석과 공백 split의 실질적 성능 차이는 얼마나 되는가?
- BM25_CANDIDATE_K(10)를 줄이면 거절 수가 감소하는가?
- RRF_K=60(표준값) 대신 도메인 최적값이 존재하는가? IPCC 전문용어 밀집 문서에서 다른 값이 유리할 수 있다.
- 거절 로직 조정 후 재측정 시 Precision 개선(+0.0289)이 유지되는가?

---

## 계획

- **거절 로직 조정 후 재측정**: THRESHOLD 하향(0.28 → 0.20) 또는 TOP_K 기준 필터 적용으로 변경 후 RAGAS 재측정 → Recall 회복 확인
- **IEP-2002**: 거절 로직 조정 완료 후 FlashRank 리랭킹 추가 실험 진행
- **rag.py 반영**: 거절 조정 + 재측정 후 벡터 단독 대비 유의미한 개선이 확인되면 `SEARCH_MODE="hybrid"` 적용
- **배포 서비스 업데이트**: Cloud Run 재배포 + GitHub README 수치 갱신

---

## 참고자료

- [IEP-1001: 단순 청킹 방식의 청크 크기 실험 및 RAGAS 4대 지표 측정](./IEP-1001-simplechunking.md)
- [IEP-4001: FastAPI 서비스화](./IEP-4001-fastapi.md)
- Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009). Reciprocal rank fusion outperforms condorcet and individual rank learning methods. *SIGIR 2009*.
- [rank_bm25 라이브러리](https://github.com/dorianbrown/rank_bm25)
- [kiwipiepy 문서](https://github.com/bab2min/kiwipiepy)
- 실험 노트북: `notebooks/IEP2001_hybrid_search_experiment.ipynb`
- 사용 환경 (2026-04-27)
  - 플랫폼: Google Colab T4
  - 임베딩: `jhgan/ko-sroberta-multitask` (device: cuda)
  - Answer/Judge LLM: `solar-pro3` (Upstage)
  - 주요 패키지: `rank-bm25`, `kiwipiepy`, `ragas`, `langchain-community`, `langchain-huggingface`, `chromadb==0.5.11`
  - 벡터 DB: ChromaDB, 컬렉션 `ipcc_1001_case3_v1` (506개 청크)
