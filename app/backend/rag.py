import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI

from config import (
    UPSTAGE_API_KEY,
    UPSTAGE_BASE_URL,
    LLM_MODEL,
    EMBEDDING_MODEL,
    CHROMA_DIR,
    CHROMA_COLLECTION,
    TOP_K,
    SIMILARITY_THRESHOLD,
)

# 디바이스 설정 (환경변수로 주입, 기본값 cpu)
# 로컬 Mac: DEVICE=mps / 컨테이너: 환경변수 없음 → cpu 자동 적용
device = os.environ.get("DEVICE", "cpu")

# 임베딩 모델 초기화
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": device},
)

# ChromaDB 로드
vectorstore = Chroma(
    collection_name=CHROMA_COLLECTION,
    embedding_function=embeddings,
    persist_directory=CHROMA_DIR,
)

# Solar LLM 클라이언트 (OpenAI 호환)
client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url=UPSTAGE_BASE_URL,
)

# ── 시스템 프롬프트 ────────────────────────────────────────────────────────────

SYSTEM_PROMPT_SIMPLE = """당신은 IPCC AR6 종합보고서(한글 번역본)를 일반 시민에게 쉽게 설명하는 도우미입니다.
반드시 제공된 컨텍스트만 참고하여 답변하세요.
컨텍스트에 없는 내용은 추측하지 말고 모른다고 답하세요.

답변 작성 규칙:
- 첫 문장은 반드시 "한 줄 핵심"으로 시작하세요. 질문의 핵심 답변을 직접적으로 말하세요.
- 이어서 "우리 일상에서 어떻게 느껴지는가"를 중심으로 설명하세요. 단순 나열이 아닌 체감과 위험성을 전달하세요.
- 전문 용어는 반드시 괄호 안에 쉬운 설명을 덧붙이세요. 예: 온실가스(지구를 담요처럼 감싸 온도를 높이는 기체)
- 수치보다 비유를 우선하세요. 예: "0.5도 차이가 폭염 사망자 수를 2배로 만듭니다"
- 마지막 문장은 "그래서 지금 왜 중요한가"로 마무리하세요.
- 전체 4~5문장, 한국어로 작성하세요."""

SYSTEM_PROMPT_EXPERT = """당신은 IPCC AR6 종합보고서(한글 번역본) 전문 연구 도우미입니다.
반드시 제공된 컨텍스트만 참고하여 답변하세요.
컨텍스트에 없는 내용은 추측하지 말고 모른다고 답하세요.

답변은 반드시 아래 구조로 작성하세요:

[핵심 요약]
질문에 대한 핵심 결론을 2~3문장으로 작성하세요. 가장 중요한 내용을 먼저 말하세요.

[주요 변화]
번호 목록으로 3가지 이내로 작성하세요. 각 항목 뒤에 IPCC 신뢰 수준을 반드시 명시하세요.
예: 1. 극단적 폭염 빈도 증가 (높은 신뢰도)

[근거]
컨텍스트에서 직접 인용한 수치와 표현을 사용하세요. 각 항목 앞에 페이지를 명시하세요.
예: - p.34: "..."

답변은 한국어로 작성하세요."""

OUT_OF_SCOPE_ANSWER = (
    "죄송합니다. 해당 질문은 IPCC AR6 보고서 범위를 벗어난 것 같습니다. "
    "기후변화 관련 질문을 해주세요."
)


# ── 내부 유틸 ────────────────────────────────────────────────────────────────

def _retrieve(question: str) -> tuple[list, list, list]:
    """
    ChromaDB에서 검색 후 필터링된 결과를 반환합니다.

    Returns:
        filtered_docs  : List[Document]
        filtered_scores: List[float]  (similarity, 0~1)
        sources        : List[dict]
    """
    raw_results = vectorstore.similarity_search_with_score(question, k=TOP_K)
    results = [(doc, 1 - score) for doc, score in raw_results]

    filtered = [(doc, score) for doc, score in results if score >= SIMILARITY_THRESHOLD]

    if not filtered:
        return [], [], []

    filtered_docs = []
    filtered_scores = []
    sources = []

    for doc, score in filtered:
        page = doc.metadata.get("page", 0)
        source = doc.metadata.get("source", "")
        preview = doc.page_content[:200].replace("\n", " ")

        filtered_docs.append(doc)
        filtered_scores.append(score)
        sources.append({
            "page": page + 1,
            "preview": preview,
            "source": os.path.basename(source),
        })

    return filtered_docs, filtered_scores, sources


def _build_context(docs: list) -> str:
    parts = []
    for doc in docs:
        page = doc.metadata.get("page", 0)
        parts.append(f"[페이지 {page + 1}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _call_llm(system_prompt: str, context: str, question: str) -> str:
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"컨텍스트:\n{context}\n\n질문: {question}"},
        ],
    )
    answer = response.choices[0].message.content
    if "</think>" in answer:
        answer = answer.split("</think>")[-1].strip()
    return answer


def _calc_trust(filtered_scores: list) -> dict:
    """신뢰도 3지표 계산 (IEP-4006)"""
    relevance_score = round(sum(filtered_scores) / len(filtered_scores), 4)
    coverage_score = round(len(filtered_scores) / TOP_K, 4)
    return {
        "relevance_score": relevance_score,
        "coverage_score": coverage_score,
        "is_in_scope": True,
    }


# ── 공개 함수 ────────────────────────────────────────────────────────────────

def query_simple(question: str) -> dict:
    """
    일반인용 답변 + 신뢰도 지표 반환 (기본 /chat 엔드포인트용).

    Returns:
        {
            "answer_simple": str,
            "sources": List[dict],
            "trust": {"relevance_score": float, "coverage_score": float, "is_in_scope": bool}
        }
    """
    docs, scores, sources = _retrieve(question)

    if not docs:
        return {
            "answer_simple": OUT_OF_SCOPE_ANSWER,
            "sources": [],
            "trust": {
                "relevance_score": 0.0,
                "coverage_score": 0.0,
                "is_in_scope": False,
            },
        }

    context = _build_context(docs)
    answer_simple = _call_llm(SYSTEM_PROMPT_SIMPLE, context, question)
    trust = _calc_trust(scores)

    return {
        "answer_simple": answer_simple,
        "sources": sources,
        "trust": trust,
    }


def query_expert(question: str) -> dict:
    """
    전문가용 답변 반환 (전문가 탭 버튼 클릭 시 /chat/expert 엔드포인트용).
    검색을 재실행합니다 (컨텍스트 재활용 대신 단순성 우선).

    Returns:
        {
            "answer": str
        }
    """
    docs, scores, _ = _retrieve(question)

    if not docs:
        return {"answer": OUT_OF_SCOPE_ANSWER}

    context = _build_context(docs)
    answer = _call_llm(SYSTEM_PROMPT_EXPERT, context, question)

    return {"answer": answer}