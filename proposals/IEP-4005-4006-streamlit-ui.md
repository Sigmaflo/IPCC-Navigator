# IEP-4005·4006: Streamlit UI 구현 — 실시간 진행 로그 + 답변 신뢰도 3지표

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `Completed` |
| **작성일** | 2026-05-02 |

---

## 동기

IEP-4003에서 FastAPI 백엔드가 Cloud Run에 배포됐다. 그러나 `/chat` 엔드포인트는 터미널 curl로만 접근 가능한 상태였고, 일반 사용자가 사용할 수 있는 인터페이스가 없었다.

이 단계의 목표는 두 가지다.

첫째, **IEP-4005(실시간 진행 로그)**: RAG 파이프라인이 어떤 단계를 거쳐 답변을 생성하는지 사용자에게 실시간으로 보여준다. "블랙박스"처럼 느껴지는 AI 답변에 과정의 투명성을 더한다.

둘째, **IEP-4006(답변 신뢰도 3지표)**: RAGAS로 측정한 신뢰성 수치를 서비스 차원에서 구현한다. 개별 질문에 대해 근거 일치도·출처 충분성·범위 내 여부를 실시간으로 계산하여 사용자에게 제공한다.

두 기능을 Streamlit UI와 통합하여 구현하면서, 동시에 **일반인/전문가 답변 분리**와 **투명성 조치**도 설계에 포함했다.

---

## 진행

### UI 설계 원칙

외부 피드백을 반영한 설계 방향:

> "엔진은 잘 만들었는데, 사용자 경험이 아직 연구용이다"

- "정보 제공 앱"이 아닌 **"이해를 도와주는 도구"**
- 일반인도 이해할 수 있는 언어 + 수치를 함께 제공
- 투명성: 챗봇이 무엇을 근거로 답변하는지 명확히 표시

### 백엔드 확장 (models.py, rag.py, main.py)

UI 요구사항을 충족하기 위해 백엔드를 먼저 확장했다.

#### 응답 모델 확장 (models.py)

```python
class TrustScore(BaseModel):
    relevance_score: float   # 근거 일치도: 검색된 청크 similarity 평균
    coverage_score: float    # 출처 충분성: 반환 청크 수 / TOP_K
    is_in_scope: bool        # 범위 내 여부: SIMILARITY_THRESHOLD 통과 여부

class ChatResponse(BaseModel):
    answer_simple: str       # 일반인용 답변
    sources: List[SourceItem]
    trust: TrustScore

class ExpertResponse(BaseModel):
    answer: str              # 전문가용 답변
```

#### RAG 함수 분리 (rag.py)

기존 `query()` 단일 함수에서 역할별로 분리했다.

| 함수 | 역할 |
| :--- | :--- |
| `_retrieve()` | ChromaDB 검색·필터링·scores 수집 |
| `_build_context()` | 컨텍스트 문자열 구성 |
| `_call_llm()` | Solar API 호출 |
| `_calc_trust()` | 신뢰도 3지표 계산 |
| `query_simple()` | 일반인용 답변 + 신뢰도 반환 |
| `query_expert()` | 전문가용 답변 반환 |

기존에 `_score`로 수집되고 버려지던 cosine similarity 값을 `filtered_scores`로 수집해 신뢰도 계산에 활용했다.

#### 신뢰도 3지표 계산 방식

| 지표 | 계산식 | 의미 |
| :--- | :--- | :--- |
| 근거 일치도 | `mean(filtered_scores)` | 검색된 청크가 질문과 얼마나 관련 있는가 |
| 출처 충분성 | `len(filtered_scores) / TOP_K` | TOP_K 대비 실제 통과한 청크 비율 |
| 범위 내 여부 | `bool(filtered)` | SIMILARITY_THRESHOLD 통과 여부 |

#### 프롬프트 전략 확정

| 프롬프트 | 핵심 규칙 |
| :--- | :--- |
| `SYSTEM_PROMPT_SIMPLE` | 첫 문장: 한 줄 핵심 → 체감·위험성 중심 → 마지막: 지금 왜 중요한가. 4~5문장 |
| `SYSTEM_PROMPT_EXPERT` | [핵심 요약] / [주요 변화] / [근거] 3단 구조 강제. 주요 변화마다 IPCC 신뢰 수준 명시 |

#### 엔드포인트 확장 (main.py)

| 엔드포인트 | 역할 |
| :--- | :--- |
| `GET /info` | 투명성 조치 — 모델명·threshold·TOP_K·문서 정보 반환 |
| `POST /chat` | 일반인용 답변 + 신뢰도 3지표 |
| `POST /chat/expert` | 전문가용 답변 (별도 호출) |

`/chat/expert`는 버튼 클릭 시만 호출되도록 설계하여 불필요한 API 비용을 방지했다.

### Streamlit UI 구현 (app.py)

#### 화면 구성

```
┌─────────────────────────────────────────────┐
│  🌍 IPCC Navigator                          │
│  ⚠️ IPCC AR6 문서 기반 답변만 제공          │ ← 고지 배너 (투명성 ①)
│  🔧 시스템 정보 [expander]                  │ ← /info 연동 (투명성 ③)
├─────────────────────────────────────────────┤
│  질문 입력창 / [질문하기] 버튼              │
├─────────────────────────────────────────────┤
│  ✅ 질문 임베딩  ✅ 문서 검색  ⏳ 생성 중  │ ← st.status (IEP-4005)
├─────────────────────────────────────────────┤
│  🙋 일반인용 답변                            │
│  ─────────────────────                      │
│  [🔬 전문가용 답변 보기] 버튼               │
├─────────────────────────────────────────────┤
│  근거 일치도  ████░  0.64  중간  일부 불확실성 있음  │ ← IEP-4006
│  출처 충분성  ████████  0.80  높음  충분한 출처      │
│  범위 내 여부  ✅ 범위 내                   │
├─────────────────────────────────────────────┤
│  📄 출처 카드 (page · preview · source)     │
└─────────────────────────────────────────────┘
```

#### IEP-4005 — 실시간 진행 로그 구현

`st.status`를 사용해 3단계 진행 상황을 순차 표시했다.

```python
with st.status("답변을 생성하고 있습니다...", expanded=True) as status:
    st.write("🔍 질문 임베딩 중...")
    st.write("📚 관련 문서 검색 중...")
    # API 호출
    st.write("✍️ 답변 생성 중...")
    status.update(label="완료 ✅", state="complete", expanded=False)
```

SSE 방식도 검토했으나 FastAPI 엔드포인트 추가 비용 대비 `st.status`가 현 단계에서 충분하다고 판단했다.

#### IEP-4006 — 신뢰도 3지표 UI

수치 + 레이블 + 한 줄 설명을 함께 표시했다.

```
근거 일치도  ████████░░  0.80  높음  근거가 질문과 잘 일치합니다
출처 충분성  ██████░░░░  0.60  중간  일부 출처만 검색되었습니다
범위 내 여부  ✅ 범위 내
```

레이블 기준:

| 점수 | 레이블 |
| :--- | :--- |
| 0.7 이상 | 높음 |
| 0.4 이상 | 중간 |
| 0.4 미만 | 낮음 |

#### 주요 트러블슈팅

**전문가용 답변 탭 초기화 문제**

처음에 `st.tabs()`로 일반인용/전문가용 탭을 분리했다. 전문가용 탭에서 버튼을 클릭하면 `st.rerun()`이 호출되고 탭이 첫 번째(일반인용)로 초기화되는 문제가 발생했다.

| 시도 | 결과 |
| :--- | :--- |
| `st.tabs()` + `st.rerun()` | 탭 초기화 문제 발생 |
| `st.expander()` + `st.rerun()` 없음 | 버튼 클릭 후 답변 미표시 |
| 세션 토글 + `st.rerun()` | ✅ 해결 |

최종 해결책: `show_expert` 세션 상태 대신 `expert_answer` 유무만으로 판단하는 단순한 구조로 변경했다.

```python
# expert_answer 없으면 버튼 표시
if not st.session_state.expert_answer:
    if st.button("🔬 전문가용 답변 보기"):
        # API 호출 → expert_answer 세션 저장 → st.rerun()
else:
    # 전문가 답변 표시 (버튼 없음)
```

### 배포 — Streamlit Cloud

| 항목 | 내용 |
| :--- | :--- |
| 배포 방식 | Streamlit Cloud (GitHub Private 연결) |
| Main file path | `app/frontend/app.py` |
| Secrets | `API_BASE = "https://[CLOUD_RUN_URL]"` |
| Streamlit URL | `https://[STREAMLIT_URL].streamlit.app/` |

Cloud Run(백엔드)과 Streamlit Cloud(프론트)를 분리 배포하는 구조를 채택했다. 현 단계에서는 Streamlit Cloud가 빠른 검증에 최적이며, 서비스 성장 후 Cloud Run으로 이전을 검토한다.

---

## 분석

### 잘 된 점

**일반인/전문가 분리 설계**는 이 서비스의 핵심 차별점이다. 동일한 RAG 결과를 두 가지 관점으로 제공하는 것은 "정보 접근성"과 "연구 활용성"을 동시에 달성하는 구조다.

**신뢰도 3지표**는 RAGAS 측정 수치를 서비스 차원으로 구현한 시도다. 수치(0~1) + 레이블(높음/중간/낮음) + 한 줄 설명의 3단 표시로 일반인도 답변의 신뢰성을 직관적으로 파악할 수 있다.

**버려지던 `_score`를 활용**한 것이 핵심이다. 기존 코드에서 이미 계산되고 있었지만 `_score`로 무시되던 값을 수집하여 신뢰도 계산에 활용했다. 추가 API 호출 없이 구현 가능했다.

### 개선 필요한 점

**프롬프트 효과 검증 미완료**: 일반인용/전문가용 프롬프트를 개선했지만 RAGAS로 정량 측정하지 않았다. "체감"과 "구조화"가 실제로 개선됐는지는 정성적 평가에 의존하고 있다.

**전문가용 답변이 구조를 따르지 않는 경우**: Solar가 [핵심 요약] / [주요 변화] / [근거] 구조를 항상 따르지 않는다. 프롬프트 강도를 높이거나 후처리로 구조를 보완하는 방법을 검토해야 한다.

**신뢰도 지표의 한계**: 근거 일치도는 cosine similarity 평균으로, 출처 충분성은 단순 청크 수 비율로 계산한다. 이 수치가 실제 답변 품질을 얼마나 대표하는지 RAGAS 지표와의 상관관계 검증이 필요하다.

---

## 미해결 질문

- 개선된 프롬프트(일반인용/전문가용)가 RAGAS 수치에 미치는 영향은? → 별도 측정 필요
- 신뢰도 3지표(근거 일치도, 출처 충분성)와 RAGAS Context Recall/Precision의 상관관계는?
- 전문가용 답변의 3단 구조(핵심 요약/주요 변화/근거)가 Solar에서 안정적으로 출력되지 않는 경우 후처리 로직이 필요한가?
- `st.status` 방식은 실제 진행 상황을 반영하지 않는다. 진짜 스트리밍이 필요한 시점은 언제인가?

---

## 계획

- **README Streamlit URL 추가** (완료 ✅)
- **Phase 3 진입**: 하이브리드 방법E(BM25 + Vector, THRESHOLD=0.20)를 cosine 컬렉션 기준으로 재실험 후 rag.py 반영
- **프롬프트 정량 평가**: 개선된 프롬프트로 RAGAS 4지표 재측정 (IEP-3002 연계)
- **전문가용 구조화 강화**: Solar 응답의 3단 구조 준수율 측정 및 후처리 검토
- **Streamlit Cloud → Cloud Run 이전**: 서비스 성장 시

---

## 참고자료

- [IEP-4001: FastAPI 서비스화](./IEP-4001-fastapi.md)
- [IEP-4002: Docker 컨테이너화](./IEP-4002-docker.md)
- [IEP-4003: GCP Cloud Run 배포](./IEP-4003-cloudrun.md)
- [Streamlit 공식 문서](https://docs.streamlit.io)
- [Streamlit Cloud 배포 문서](https://docs.streamlit.io/streamlit-community-cloud)
- 사용 환경 (2026-05-02)
  - 프론트엔드: Streamlit 1.45.0
  - 백엔드: FastAPI 0.115.12 (Cloud Run)
  - LLM: solar-pro3 (Upstage)
  - 배포: Streamlit Cloud (GitHub Private 연결)
  - 로컬 테스트: Mac Mini M4, `DEVICE=mps`
