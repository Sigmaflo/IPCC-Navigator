import os
from dotenv import load_dotenv

load_dotenv()

# LLM (업스테이지 Solar)
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
UPSTAGE_BASE_URL = "https://api.upstage.ai/v1"
LLM_MODEL = "solar-pro3"

# Embedding
EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"

# ChromaDB
CHROMA_DIR = os.getenv("CHROMA_DIR", "/tmp/chroma_db")
CHROMA_COLLECTION = "ipcc_1001_case3_cosine_v1"  # L2 → cosine 재인덱싱 (2026-04-30)

# RAG
TOP_K = 10  # IEP-1001 Solar v2 측정 기준 (2026-04-30)
SIMILARITY_THRESHOLD = 0.40  # cosine 컬렉션 기준 (관련: 0.62~0.66 / 범위밖: 0.22~0.30)

# API 제한
DAILY_REQUEST_LIMIT = 200
QUESTION_MIN_LENGTH = 2
QUESTION_MAX_LENGTH = 500