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


class TrustScore(BaseModel):
    """신뢰도 3지표 (IEP-4006)"""
    relevance_score: float   # 근거 일치도: 검색된 청크 similarity 평균 (0~1)
    coverage_score: float    # 출처 충분성: 반환 청크 수 / TOP_K (0~1)
    is_in_scope: bool        # 범위 내 여부: SIMILARITY_THRESHOLD 통과 여부


class ChatResponse(BaseModel):
    answer_simple: str          # 일반인용 답변 (기본 반환)
    sources: List[SourceItem]
    trust: TrustScore


class ExpertRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="질문 (2~500자)",
    )


class ExpertResponse(BaseModel):
    answer: str                 # 전문가용 답변 (버튼 클릭 시 별도 호출)