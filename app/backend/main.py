from datetime import date
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from models import ChatRequest, ChatResponse
from rag import query
from config import DAILY_REQUEST_LIMIT

app = FastAPI(title="IPCC Navigator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 일일 요청 카운터 (인메모리, Cloud Run 재시작 시 초기화)
_counter: dict = {"date": str(date.today()), "count": 0}


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


@app.get("/health")
def health():
    return {
        "status": "ok",
        "requests_today": _counter["count"],
        "limit": DAILY_REQUEST_LIMIT,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
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

    result = query(request.question)
    return ChatResponse(**result)
