# IEP-4002: Docker 컨테이너화

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `Completed` |
| **작성일** | 2026-05-01 |

---

## 동기

IEP-4001에서 FastAPI 서비스를 Mac 로컬에서 검증했다. 이를 GCP Cloud Run에 배포하려면 Docker 이미지로 패키징하는 단계가 필요하다. 단순히 동작하는 이미지를 만드는 것이 아니라, **Cloud Run(amd64) 환경과 Mac M4(arm64) 환경의 아키텍처 차이를 고려한 빌드 전략**과 **GCS 마운트 방식의 ChromaDB 주입**이 핵심이다.

---

## 진행

### 설계 원칙

- ChromaDB 폴더는 이미지에 포함하지 않음 — GCS에서 런타임에 주입
- `jhgan/ko-sroberta-multitask` 모델은 빌드 시 캐싱 — 콜드 스타트 방지
- `torch` CPU only 버전으로 이미지 크기 최소화
- Cloud Run 기본 포트 `8080` 사용

### requirements.txt 정리

| 변경 항목 | 내용 |
| :--- | :--- |
| `torch==2.2.2` 제거 | Dockerfile에서 CPU only로 별도 설치 |
| `transformers==4.47.1` 제거 | sentence-transformers가 자동으로 당김 |
| `httpx==0.28.1` 제거 | openai가 자동으로 당김 |
| `google-cloud-storage==2.19.0` 추가 | GCS 다운로드용 |
| `numpy==1.26.4%` 오타 수정 | `%` 제거 |

### rag.py 수정

`import torch` 및 디바이스 감지 로직 제거. 환경변수로 단순화:

```python
# 변경 전
import torch
if torch.backends.mps.is_available():
    device = "mps"
elif torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

# 변경 후
device = os.environ.get("DEVICE", "cpu")
```

로컬 Mac: `DEVICE=mps`, 컨테이너: 환경변수 없이 `cpu` 자동 적용.

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# torch CPU only (CVE-2025-32434 대응: 2.6+ 필요)
RUN pip install --no-cache-dir \
    torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu

COPY app/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# HuggingFace 모델 사전 다운로드 (빌드 시 캐싱 → 콜드 스타트 방지)
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('jhgan/ko-sroberta-multitask')"

COPY app/backend/ .

EXPOSE 8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

### 주요 트러블슈팅

#### 1. torch 버전 문제 (CVE-2025-32434)

**증상**: 빌드 중 모델 다운로드 단계에서 `ValueError` 발생.

**원인**: CVE-2025-32434 보안 취약점으로 `transformers`가 `torch 2.6+` 강제 요구.

**해결**: `torch==2.2.2` → `torch==2.6.0`으로 버전 업.

#### 2. 아키텍처 불일치 (exec format error)

**증상**: Cloud Run 배포 후 `failed to load /usr/bin/sh: exec format error`.

**원인**: Mac M4(arm64)로 빌드한 이미지를 Cloud Run(amd64)에 배포.

**해결**: `--platform linux/amd64` 명시하여 재빌드.

```bash
docker buildx build \
  --platform linux/amd64 \
  -t gcr.io/ipcc-rag/ipcc-rag:latest \
  --push \
  .
```

### GCS 업로드

```bash
# 버킷 생성 (서울 리전, Cloud Run과 동일)
gsutil mb -l asia-northeast3 gs://ipcc-rag-chromadb

# chroma_cosine 업로드
gsutil -m cp -r /Volumes/T7_Storage/chroma_cosine gs://ipcc-rag-chromadb/
```

| 항목 | 내용 |
| :--- | :--- |
| 버킷명 | `ipcc-rag-chromadb` |
| 업로드 파일 | 5개 / 10.2 MiB |
| 컬렉션 경로 | `gs://ipcc-rag-chromadb/chroma_cosine/` |

### main.py — GCS 다운로드 로직

앱 기동 시 GCS에서 `/tmp/chroma_cosine`으로 자동 다운로드하는 lifespan 이벤트 추가.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # GCS_BUCKET 환경변수가 있을 때만 다운로드 (로컬 실행 시 스킵)
    if os.environ.get("GCS_BUCKET"):
        _download_chromadb()

    from rag import query as _query
    app.state.query = _query
    yield
```

**설계 포인트**:
- `GCS_BUCKET` 없으면 스킵 → 로컬 실행 호환
- `rag` 모듈을 ChromaDB 다운로드 완료 후 임포트 — 순서 보장
- deprecated `@app.on_event` 대신 FastAPI 권장 `lifespan` 사용

---

## 검증 결과

**빌드 환경**: OrbStack (Docker 28.5.2, Mac M4)

| 테스트 | 결과 |
| :--- | :--- |
| `docker build` 에러 없이 완료 | ✅ |
| 이미지 크기 | ✅ 2.62GB (목표 3GB 이하) |
| `curl /health` → 200 OK | ✅ |
| 관련 질문 → 답변 + 출처 반환 | ✅ |
| 범위 밖 질문 → 거절 메시지 | ✅ |

**로컬 테스트 실행 방법** (볼륨 마운트로 GCS 다운로드 대체):

```bash
docker run -p 8080:8080 \
  -e UPSTAGE_API_KEY=<your_key> \
  -e DEVICE=cpu \
  -e CHROMA_DIR=/tmp/chroma_cosine \
  -v /Volumes/T7_Storage/chroma_cosine:/tmp/chroma_cosine \
  ipcc-rag:local
```

---

## 분석

### 이미지 크기 구성

| 항목 | 크기 |
| :--- | :--- |
| torch CPU only | ~700MB (GPU 버전 ~2GB 대비 절감) |
| jhgan 모델 | ~300MB |
| 나머지 패키지 | ~500MB |
| **총합** | **~2.62GB** |

### 로컬 vs 컨테이너 디바이스 전략

| 환경 | DEVICE 환경변수 | 적용값 |
| :--- | :--- | :--- |
| 로컬 Mac M4 | `DEVICE=mps` | mps |
| 컨테이너 (Cloud Run) | 없음 | cpu (기본값) |

환경변수 한 줄로 코드 분기 없이 처리. `import torch` 의존성 완전 제거.

---

## 미해결 질문

- 콜드 스타트 시 GCS 다운로드 + 모델 로드 시간이 실제로 얼마나 걸리는가? → IEP-4003 배포 후 실측
- 이미지 크기 2.62GB를 더 줄일 수 있는가? (`python:3.11-slim` 대신 `distroless` 시도 가능)

---

## 계획

- **IEP-4003**: GCP Cloud Run 배포 → 실제 URL 확보 ✅ 완료
- **IEP-4005·4006**: Streamlit UI와 함께 실시간 로그 + 신뢰도 점수 통합 구현 후 재배포
- **Phase 3 진입 전**: 하이브리드 방법E(BM25 + Vector)를 cosine 컬렉션 기준으로 재실험 후 rag.py 반영

---

## 참고자료

- [IEP-4001: FastAPI 서비스화](./IEP-4001-fastapi.md)
- [CVE-2025-32434 취약점 보고서](https://nvd.nist.gov/vuln/detail/CVE-2025-32434)
- 사용 환경 (2026-05-01)
  - 플랫폼: Mac Mini M4 / OrbStack Docker 28.5.2
  - Python: 3.11-slim (컨테이너)
  - torch: 2.6.0 CPU only
  - 이미지: `gcr.io/ipcc-rag/ipcc-rag:latest`
