import os
from datetime import date
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from models import ChatRequest, ChatResponse, ExpertRequest, ExpertResponse
from config import DAILY_REQUEST_LIMIT, LLM_MODEL, CHROMA_COLLECTION, SIMILARITY_THRESHOLD, TOP_K

# 일일 요청 카운터 (인메모리, Cloud Run 재시작 시 초기화)
# /chat과 /chat/expert 각각 카운트 (1 질문 세션 = 최대 2 카운트)
_counter: dict = {"date": str(date.today()), "count": 0}


def _download_chromadb():
    """GCS에서 ChromaDB를 /tmp/chroma_cosine으로 다운로드합니다."""
    bucket_name = os.environ.get("GCS_BUCKET", "ipcc-rag-chromadb")
    gcs_prefix = "chroma_cosine/"
    local_base = "/tmp"

    print(f"[startup] ChromaDB 다운로드 시작: gs://{bucket_name}/{gcs_prefix}")

    try:
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=gcs_prefix))

        for blob in blobs:
            local_path = os.path.join(local_base, blob.name)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            blob.download_to_filename(local_path)
            print(f"[startup] 다운로드 완료: {blob.name}")

        print(f"[startup] ChromaDB 다운로드 완료 ({len(blobs)}개 파일)")

    except Exception as e:
        print(f"[startup] ChromaDB 다운로드 실패: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # GCS_BUCKET 환경변수가 있을 때만 다운로드 (로컬 실행 시 스킵)
    if os.environ.get("GCS_BUCKET"):
        _download_chromadb()

    # rag 모듈은 ChromaDB 다운로드 후에 임포트
    from rag import query_simple, query_expert
    app.state.query_simple = query_simple
    app.state.query_expert = query_expert

    yield


app = FastAPI(title="IPCC Navigator API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_and_increment() -> bool:
    """오늘 날짜 기준 카운트를 확인하고 증가시킵니다. 한도 초과 시 False 반환."""
    today = str(date.today())
    if _counter["date"] != today:
        _counter["date"] = today
        _counter["count"] = 0
    if _counter["count"] >= DAILY_REQUEST_LIMIT:
        return False
    _counter["count"] += 1
    return True


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "requests_today": _counter["count"],
        "limit": DAILY_REQUEST_LIMIT,
    }


@app.get("/info")
def info():
    """투명성 조치 (IEP-4006) — UI에서 모델·설정 정보를 표시하기 위한 엔드포인트."""
    return {
        "llm_model": LLM_MODEL,
        "embedding_model": "jhgan/ko-sroberta-multitask",
        "chroma_collection": CHROMA_COLLECTION,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "top_k": TOP_K,
        "document": "IPCC AR6 종합보고서 (한글 번역본, 188페이지)",
        "note": "이 챗봇은 위 문서에 기반한 답변만 제공합니다.",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """일반인용 답변 + 신뢰도 지표 (기본 엔드포인트)."""
    if not _check_and_increment():
        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    f"일일 요청 한도({DAILY_REQUEST_LIMIT}건)에 도달했습니다. "
                    "내일 다시 시도해주세요."
                )
            },
        )

    result = app.state.query_simple(request.question)
    return ChatResponse(**result)


@app.post("/chat/expert", response_model=ExpertResponse)
async def chat_expert(request: ExpertRequest):
    """전문가용 답변 (전문가 탭 버튼 클릭 시 호출)."""
    if not _check_and_increment():
        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    f"일일 요청 한도({DAILY_REQUEST_LIMIT}건)에 도달했습니다. "
                    "내일 다시 시도해주세요."
                )
            },
        )

    result = app.state.query_expert(request.question)
    return ExpertResponse(**result)