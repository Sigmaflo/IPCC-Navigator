from pydantic import BaseModel, Field
from typing import List


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="질문 (2~500자)",
    )


class SourceItem(BaseModel):
    page: int
    preview: str
    source: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
