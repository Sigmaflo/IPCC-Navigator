# Python 3.11 slim — Mac M4(arm64)와 Cloud Run(amd64) 모두 호환
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# torch CPU only 먼저 설치 (GPU 버전 자동 설치 방지, 이미지 크기 최소화)
RUN pip install --no-cache-dir \
    torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# 나머지 패키지 설치
COPY app/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# HuggingFace 모델 사전 다운로드 (빌드 시 캐싱 → 콜드 스타트 방지)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('jhgan/ko-sroberta-multitask')"

# 소스 복사 (chroma_cosine 제외 — GCS에서 런타임에 주입)
COPY app/backend/ .

# Cloud Run 기본 포트
EXPOSE 8080

# 환경변수: Cloud Run은 PORT=8080 자동 주입
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
