# IEP-4001: FastAPI 서비스화 및 로컬 실행 검증

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `Completed` |
| **작성일** | 2026-04-30 |

---

## 동기

IEP-1001~1003 청킹 실험과 IEP-2001~2002 검색 개선 실험을 통해 배포용 파이프라인이 확정됐다. 실험 환경(Colab 노트북)에서 검증된 RAG 파이프라인을 실제 서비스로 전환하는 것이 이 단계의 목표다.

단순히 동작하는 API를 만드는 것이 아니라, **Colab에서 확정된 설정값(메타데이터 키, threshold, 디바이스)을 코드에 정확히 반영하고, 로컬에서 동작을 검증**하는 것이 핵심이다. IEP-4002(Docker) → IEP-4003(Cloud Run) 배포의 출발점이 된다.

---

## 진행

### 서비스 구조 설계

```
IPCC-Navigator/
├── app/
│   ├── backend/
│   │   ├── main.py       FastAPI 앱 + 일일 200건 미들웨어
│   │   ├── rag.py        RAG 파이프라인 (검색 + Solar 호출)
│   │   ├── config.py     설정값 (threshold, 모델명, 경로)
│   │   ├── models.py     Pydantic 스키마
│   │   └── requirements.txt
│   └── frontend/
│       ├── app.py        Streamlit UI (IEP-4005·4006에서 확장)
│       └── requirements.txt
├── Dockerfile
├── .env.example
└── .gitignore
```

**엔드포인트**

| 메서드 | 경로 | 설명 |
| :--- | :--- | :--- |
| GET | `/health` | 서버 상태 + 오늘 요청 수 반환 |
| POST | `/chat` | 질문 수신 → RAG → 답변 + 출처 반환 |

### Colab 테스트에서 확정된 설정값 반영

Colab end-to-end 테스트(2026-04-22)에서 확인된 값을 그대로 반영했다.

| 항목 | 잘못된 값 | 확정값 | 확인 경위 |
| :--- | :--- | :--- | :--- |
| 페이지 메타데이터 키 | `page_num` | `page` | ChromaDB 실측 |
| 청크 식별자 키 | `chunk_id` | `source` | ChromaDB 실측 (`chunk_id` 키 없음) |
| 디바이스 | `cuda` | `mps` (Mac) / `cpu` (기타) | M4 환경 대응 |
| SIMILARITY_THRESHOLD | `0.28` | `0.20` | IEP-2001 방법E 채택 |

### 주요 트러블슈팅

#### 1. ChromaDB Distance Metric 문제 (핵심)

**증상**: 모든 질문에 거절 응답 반환.

**원인**: IEP-1001 실험 시 ChromaDB 컬렉션을 생성할 때 distance metric을 명시하지 않아 기본값인 **L2**로 인덱싱됐다. 텍스트 임베딩에서 L2 distance는 관련/비관련 질문을 구분하지 못한다.

```
L2 distance 측정 결과:
관련 질문  → 127.9 ~ 129.1  (낮을수록 유사)
범위 밖    → 123.1 ~ 124.7  ← 오히려 더 낮음
→ 구분 불가능
```

Cosine similarity를 직접 계산하자 명확하게 구분됐다.

```
Cosine similarity 직접 계산:
관련 질문  → 0.6643
범위 밖    → 0.0996
```

**해결**: 기존 L2 컬렉션에서 임베딩 벡터를 추출해 Cosine 컬렉션으로 복사했다. 임베딩 재계산 없이 데이터만 이전.

```python
new_col = client.create_collection(
    name='ipcc_1001_case3_cosine_v1',
    metadata={'hnsw:space': 'cosine'}  # 명시 필수
)
```

**결과**: Cosine 컬렉션에서 threshold 0.40 기준으로 관련/비관련 질문 정상 구분.

```
cosine distance → similarity (1 - distance):
관련 질문  → 0.62 ~ 0.66  ✅ threshold 통과
범위 밖    → 0.23 ~ 0.30  ❌ threshold 거절
```

#### 2. Python 버전 호환성 (Windows 환경)

Windows Python 3.14에서 `torch==2.2.2` 설치 불가. Python 3.11.9로 다운그레이드하고 가상환경 재생성으로 해결.

#### 3. LangChain 버전 충돌

`langchain 0.3.x`와 `langchain-chroma 1.1.0`이 `langchain-core` 의존성 충돌. `langchain 1.x` 계열로 전체 통일하여 해결.

#### 4. transformers 버그

`requirements.txt`에 `transformers`를 명시하지 않아 최신 버전이 자동 설치됐고, `nn` 미정의 오류 발생. `transformers==4.47.1`로 고정.

### 최종 확정값

| 항목 | 값 |
| :--- | :--- |
| ChromaDB 컬렉션 | `ipcc_1001_case3_cosine_v1` (hnsw:space=cosine) |
| SIMILARITY_THRESHOLD | `0.40` (cosine 컬렉션 기준) |
| TOP_K | `10` |
| 검색 방식 | `similarity_search_with_score` + `1 - distance` 직접 변환 |
| Python | `3.11.9` |

---

## 검증 결과

| 테스트 항목 | 기준 | 결과 |
| :--- | :--- | :---: |
| 관련 질문 답변 생성 | `answer` + `sources` 반환 | ✅ PASS |
| 출처 페이지 번호 | `sources[].page` 숫자 반환 | ✅ PASS |
| 범위 밖 질문 거절 | 거절 메시지 + 빈 `sources` | ✅ PASS |
| `/health` 엔드포인트 | 200 OK + 요청 수 반환 | ✅ PASS |

**관련 질문 답변 예시** ("지구 평균 온도는 얼마나 상승했나요?")

> 2011~2020년 기준으로 지구 평균 온도는 1850~1900년 대비 1.09°C [0.95°C~1.20°C] 상승했습니다. (p.20)

---

## 분석

### ChromaDB L2 vs Cosine — 텍스트 임베딩에서 L2가 동작하지 않는 이유

ChromaDB distance metric은 두 가지다.

| 방식 | 측정 대상 | 값 범위 | 텍스트 임베딩 적합성 |
| :--- | :--- | :--- | :--- |
| **L2 (유클리드 거리)** | 두 벡터 사이의 직선 거리 | 0 ~ ∞ | ❌ 벡터 크기에 민감 |
| **Cosine** | 두 벡터의 방향 차이 | 0 ~ 2 | ✅ 의미 유사도 측정에 적합 |

텍스트 임베딩 벡터는 크기(magnitude)가 모두 비슷하다. L2는 벡터의 크기에 민감하기 때문에, 크기가 비슷한 임베딩들 사이에서는 관련/비관련 질문을 구분하는 discriminative power가 거의 없다. 반면 Cosine은 벡터의 방향만 비교하므로 의미적 유사도를 정확하게 측정한다.

이번 실험에서 실측된 차이는 다음과 같다.

```
L2 distance:
관련 질문  → 127.9 ~ 129.1
범위 밖    → 123.1 ~ 124.7  ← 오히려 더 낮음 (더 유사??)
→ threshold로 구분 불가능

Cosine similarity (1 - cosine distance):
관련 질문  → 0.62 ~ 0.66
범위 밖    → 0.23 ~ 0.30
→ threshold 0.40으로 명확하게 구분
```

### Colab과 로컬 환경에서 score가 다르게 나온 원인

실험(Colab)에서는 `similarity_search_with_relevance_scores`가 정상 동작하는 것처럼 보였다. 이는 LangChain 구버전이 L2 distance를 내부적으로 변환해 0~1 범위로 출력했기 때문이다. 로컬 환경의 신버전 LangChain은 변환 공식이 달라져 음수가 반환됐다.

이처럼 `similarity_search_with_relevance_scores`는 **LangChain 버전에 따라 내부 변환 공식이 달라지는 함수**다. 버전 의존성을 없애기 위해 `similarity_search_with_score` + `1 - distance` 직접 변환 방식을 채택했다. cosine distance는 낮을수록 유사하므로 `1 - distance`가 곧 similarity다.

### ChromaDB 컬렉션 생성 시 distance metric 명시 규칙

**컬렉션 생성 시 반드시 `hnsw:space=cosine`을 명시해야 한다.** 명시하지 않으면 기본값 L2가 적용되어 threshold 기반 거절 로직이 의도대로 동작하지 않는다. 이후 모든 컬렉션 생성 코드에 이 규칙을 적용한다.

```python
# 올바른 컬렉션 생성 방식
collection = client.create_collection(
    name='collection_name',
    metadata={'hnsw:space': 'cosine'}  # 항상 명시
)
```

---

## 미해결 질문

- Mac M4(mps)에서 Windows(cpu) 대비 응답 속도 차이는? Colab 실측 1.72초가 로컬에서도 유지되는가?
- 일일 200건 카운터가 인메모리 방식이라 Cloud Run 재시작 시 초기화된다. 이를 허용할 것인가, 아니면 외부 저장소(Redis 등)로 영속화할 것인가?
- SIMILARITY_THRESHOLD 0.40이 실제 서비스에서 적절한가? Mac 환경에서 추가 스모크 테스트 필요.

---

## 계획

- **IEP-4002**: OrbStack으로 Docker 로컬 빌드 + 테스트
- **IEP-4003**: GCP Cloud Run 배포 + 실제 URL 확보
- **Mac 이전 후**: `mps` 디바이스 동작 확인 + threshold 0.40 재검증
- **Phase 3 진입 전**: `rag.py`를 `rag/retriever.py` + `rag/generator.py`로 분리 (하이브리드 검색 추가 대비)

---

## 참고자료

- [IEP-1001: 단순 청킹 방식의 청크 크기 실험 및 RAGAS 4대 지표 측정](./IEP-1001-simplechunking.md)
- [IEP-2001: 하이브리드 검색(BM25 + Vector)을 통한 검색 품질 개선](./IEP-2001-hybrid-search.md)
- [업스테이지 Solar API 문서](https://developers.upstage.ai)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com)
- 사용 환경 (2026-04-30)
  - 플랫폼: Windows 11 (로컬 검증), Mac M4 (배포 예정)
  - Python: 3.11.9
  - 임베딩: `jhgan/ko-sroberta-multitask` (768차원)
  - LLM: `solar-pro3` (Upstage)
  - 벡터 DB: ChromaDB, 컬렉션 `ipcc_1001_case3_cosine_v1` (506개 청크, cosine)
  - 주요 패키지: `fastapi==0.115.12`, `langchain==1.2.16`, `langchain-chroma==1.1.0`, `chromadb==1.5.8`, `torch==2.2.2`, `transformers==4.47.1`
