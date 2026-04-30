import os
import torch
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

# 디바이스 설정 (Mac M4: mps / Colab: cuda / 그 외: cpu)
if torch.backends.mps.is_available():
    device = "mps"
elif torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

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

SYSTEM_PROMPT = """당신은 IPCC AR6 종합보고서(한글 번역본) 전문 도우미입니다.
반드시 제공된 컨텍스트만 참고하여 답변하세요.
컨텍스트에 없는 내용은 추측하지 말고 모른다고 답하세요.
답변은 한국어로 작성하세요."""


def query(question: str) -> dict:
    """
    질문을 받아 RAG 파이프라인으로 답변과 출처를 반환합니다.

    Returns:
        {
            "answer": str,
            "sources": [{"page": int, "preview": str, "source": str}, ...]
        }
    """
    # cosine distance → similarity 변환: 1 - distance
    # ipcc_1001_case3_cosine_v1 컬렉션 기준 (hnsw:space=cosine)
    # 관련 질문: 0.62~0.66 / 범위 밖: 0.22~0.30
    raw_results = vectorstore.similarity_search_with_score(
        question, k=TOP_K
    )
    results = [(doc, 1 - score) for doc, score in raw_results]

    # Similarity Threshold 필터
    filtered = [
        (doc, score) for doc, score in results if score >= SIMILARITY_THRESHOLD
    ]

    if not filtered:
        return {
            "answer": (
                "죄송합니다. 해당 질문은 IPCC AR6 보고서 범위를 벗어난 것 같습니다. "
                "기후변화 관련 질문을 해주세요."
            ),
            "sources": [],
        }

    # 컨텍스트 + 출처 구성
    context_parts = []
    sources = []

    for doc, _score in filtered:
        # ChromaDB 메타데이터 키: page(int, 0-indexed), source(PDF 경로 전체)
        page = doc.metadata.get("page", 0)
        source = doc.metadata.get("source", "")
        preview = doc.page_content[:200].replace("\n", " ")

        context_parts.append(f"[페이지 {page + 1}]\n{doc.page_content}")
        sources.append({
            "page": page + 1,
            "preview": preview,
            "source": os.path.basename(source),  # 파일명만 추출
        })

    context = "\n\n---\n\n".join(context_parts)

    # Solar API 호출
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"컨텍스트:\n{context}\n\n질문: {question}",
            },
        ],
    )

    answer = response.choices[0].message.content
    if "</think>" in answer:
        answer = answer.split("</think>")[-1].strip()

    return {
        "answer": answer,
        "sources": sources,
    }