# 📓 Project Thought Log: IPCC AR6 기반 AI 분석 플랫폼 (Path A to B)

<details>
<summary>🚀 <b>[2026-02-25] 프로젝트 핵심 요약 및 현재 상태 (클릭하여 확인)</b></summary>

- **최종 목표:** IPCC AR6 보고서 기반 신뢰성 있는 AI 분석 챗봇 구축
- **현재 단계:** **경로 A (표준 RAG)** - Google Colab GPU 환경에서 6개 섹션 인덱싱 및 파이프라인 구축 중
- **핵심 결정:** 로컬 리소스(RAM 3.7GB) 한계로 인해 **WSL2 구동 보류**, 클라우드(Colab T4) 인프라로 즉각 선회하여 속도 확보
- **다음 목표:** 경로 A 완성 후 **경로 B (지식 그래프 & TDA)** 고도화 착수
</details>

---

## 1. 프로젝트 개요 (Overview)
* **목표:** IPCC 6차 보고서(AR6)의 방대한 데이터를 체계적으로 분석하고, 신뢰성 있는 답변을 제공하는 AI 챗봇 구축.
* **핵심 전략:** 표준 RAG(경로 A)를 통해 빠르게 MVP를 완성한 후, 지식 그래프 및 TDA(경로 B)로 고도화.

---

## 2. 인프라 설계 및 제약 극복 (Infrastructure & Constraints)
### 하드웨어 사양 및 환경
* **Host PC:** 낮은 스펙의 CPU + GPU X
* **제약 사항:**
    - 실제 가용 메모리 약 3.7GB로 로컬 LLM(8B 모델) 직접 구동 시 시스템 불안정 우려.

### 인프라 결정 (Decision)
* **WSL2 보류 (2026-02-25):** WSL2 설치에는 성공했으나, 로컬 RAM 부족 및 모델 구동 시 시스템 불안정성을 고려하여 **전략적 보류** 결정.
* **Google Colab (Tesla T4 GPU) 확정:** 15GB의 GPU VRAM을 활용하여 Llama 3(8B) 모델의 추론 속도와 RAG 파이프라인의 안정성 확보.
* **Ollama 활용:** 로컬 LLM 서빙 도구의 표준인 Ollama를 Colab 환경에 이식하여 비용 제로(Free) 인프라 구축.

---

## 3. 데이터 엔지니어링 (Data Engineering)
### 데이터셋 (Target Documents)
1. `Annex_1_Glossary`: 용어 정의의 기준점.
2. `Annex_2_Acronyms`: 약어 해석의 기준점.
3. `Section_1~4`: IPCC AR6 종합보고서의 본문 섹션(Section 1, 2, 3, 4).

### 전처리 및 인덱싱 전략
* **구조적 분할:** 원본 PDF를 섹션별로 분할하여 노이즈 제거 및 검색 정확도 향상.
* **메타데이터 필터링(Metadata Filtering):** 각 데이터 조각(Chunk)에 출처 섹션 정보를 태깅. "용어 정의는 Annex 1에서, 현황 분석은 Section 2에서"와 같은 정밀한 검색 로직 구현 가능.
* **임베딩 모델:** 한국어와 영어 모두 지원하는 `ko-sroberta-multitext-canine` 모델을 선정하여 다국어 대응 기반 마련.

---

## 4. 기술 로드맵 (Roadmap: Path A to B)
### [Phase 1] 경로 A: Vector-based RAG (현재 진행)
* **방식:** 벡터 유사도 기반 검색 + Ollama(Llama 3) 생성.
* **장점:** 빠른 구현과 표준화된 아키텍처. 실질적인 '동작하는 서비스' 확인.

### [Phase 2] 경로 B: GraphRAG & TDA (차후 계획)
* **방식:** NotebookLM을 활용한 개체(Entity) 추출 -> 지식 그래프 구축 -> TDA(위상적 데이터 분석) 시각화.
* **목표:** 단순 검색의 한계를 넘어 데이터 간의 논리적 연결 고리를 분석하고 시각적 통찰 제공.

---

## 📅 과거 히스토리 및 연구 기록

<details>
<summary><b>2026-02-24: GraphRAG 및 TDA 결합 전략 및 비용 최적화</b></summary>

- **전략**: MS GraphRAG의 높은 비용을 피하기 위해 Gemini 1.5 Flash 무료 티어와 오픈소스 임베딩 모델을 조합한 커스텀 파이프라인 설계.
- **TDA 성공**: `KeplerMapper`를 활용한 고차원 데이터 시각화 성공 및 클러스터링 파라미터 최적화 확인.
</details>

<details>
<summary><b>2026-02-20: 프로젝트 초기 설정 및 데이터 로드맵</b></summary>

- **데이터 전략**: SYR(종합보고서) 챕터별 관리 체계 구축.
- **그래프 해석**: 보고서 내 Figure에 대한 텍스트 설명 데이터를 별도로 구축하여 단순 RAG의 한계 극복 시도.
</details>

<details>
<summary><b>📚 [문헌 연구] JCCR 논문 분석 및 전략 고도화</b></summary>

- **참고 문헌**: 김선회·윤순진(2025), "IPCC 정책결정자를 위한 요약 보고서의 계량 텍스트 분석"
- **청킹 전략**: 논문의 분석 단위를 참고하여 **'5개 문장 단위 슬라이딩 윈도우'** 설정.
- **페르소나**: AR6의 특징인 '정책적 실천 및 행동 촉구'를 강조하는 답변 톤앤매너 수립.
</details>
