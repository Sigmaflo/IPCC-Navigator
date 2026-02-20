# 🧭 IPCC-Navigator: 기후 과학과 대중을 잇는 데이터 내비게이터

> **"복잡한 기후 과학의 전문 용어를 일상의 언어로 통역하고, 문장마다 과학적 근거의 무게를 연결합니다."**

**IPCC-Navigator**는 전 세계에서 가장 공신력 있는 기후 변화 보고서인 **IPCC(기후 변화에 관한 정부 간 협의체) 제6차 평가보고서(AR6)**를 기반으로 합니다. 일반인의 궁금증에 대해 인공지능이 답변하되, 모든 답변의 근거를 실제 보고서 원문과 매칭하여 제공하는 **고신뢰 기후 정보 탐색 서비스**입니다.

---

## ✨ 핵심 기능 (Key Features)

### 1. 🔍 문장 단위 출처 추적 (Traceability)
* 답변의 모든 문장에 대해 실제 IPCC 보고서의 출처(보고서 종류, 장, 페이지, 표/그림 번호)를 표시합니다.
* 사용자가 링크를 클릭하면 해당 근거가 포함된 **실제 PDF 페이지**를 즉시 확인하고 검증할 수 있습니다.

### 2. ⚖️ 과학적 확신도 보존 (Scientific Rigor)
* "무조건 발생한다"는 식의 단정 대신, IPCC 원문의 **보정된 언어(Calibrated Language)**를 그대로 유지합니다.
* 과학적 **확신도(Confidence)**와 **가능성(Likelihood)**을 명시하여 정보 왜곡을 방지합니다.

### 3. 📉 시나리오별 미래 탐색 (Scenario Explorer)
* 인류의 선택(SSP 시나리오)에 따라 달라지는 미래 예측치를 직관적으로 비교합니다.
* 탄소 배출량 조절에 따른 온도 변화 등 수치 데이터를 그래프를 통해 쉽게 이해할 수 있습니다.

---

## 🛠 기술 스택 (Tech Stack)

* **언어:** Python
* **데이터 정제:** Pandas, Docling (PDF 레이아웃 파싱)
* **AI 아키텍처:** RAG (Retrieval-Augmented Generation)
* **웹 프레임워크:** Streamlit
* **데이터베이스:** Vector Database

---

## 📂 프로젝트 구조 (Project Structure)

```text
├── docs/               # UI 와이어프레임 및 기획 문서
├── notebooks/          # PDF 데이터 파싱 및 정제 실험 (Jupyter Notebook)
├── src/                # 메인 애플리케이션 소스 코드
│   ├── engine/         # RAG 검색 및 데이터 처리 로직
│   └── app.py          # Streamlit 웹 UI
├── data/               # IPCC 보고서 메타데이터 및 전처리 데이터
└── README.md           # 프로젝트 개요
