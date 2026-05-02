# IEP-4003: GCP Cloud Run 배포

| 항목 | 내용 |
| :--- | :--- |
| **상태** | `Completed` |
| **작성일** | 2026-05-01 |

---

## 동기

IEP-4002에서 Docker 이미지를 로컬에서 검증했다. 이 이미지를 GCP Cloud Run에 배포하여 **실제 URL**을 확보하는 것이 이 단계의 목표다. 실제 URL이 있어야 GitHub README에 데모 링크를 포함할 수 있고, 외부에서 접근 가능한 서비스로서 완성도를 갖출 수 있다.

---

## 진행

### 배포 스택

| 항목 | 값 |
| :--- | :--- |
| 프로젝트 ID | `ipcc-rag` |
| 프로젝트 번호 | `[PROJECT_NUMBER]` |
| 리전 | `asia-northeast3` (서울) |
| 이미지 레지스트리 | GCR (`gcr.io/ipcc-rag/ipcc-rag`) |
| 서비스명 | `ipcc-rag` |
| 서비스 URL | `https://[CLOUD_RUN_URL]` |

### 사전 준비

```bash
# gcloud CLI 설치
brew install --cask google-cloud-sdk

# PATH 설정
echo 'export PATH=/opt/homebrew/share/google-cloud-sdk/bin:"$PATH"' >> ~/.zshrc
source ~/.zshrc

# 초기화 및 로그인
gcloud init

# 프로젝트 설정
gcloud config set project ipcc-rag
```

### GCR 인증 및 이미지 푸시

```bash
# GCR 인증
gcloud auth configure-docker

# Artifact Registry API 활성화
gcloud services enable artifactregistry.googleapis.com

# amd64로 빌드 + GCR 푸시 (Mac M4 arm64 → Cloud Run amd64)
docker buildx build \
  --platform linux/amd64 \
  -t gcr.io/ipcc-rag/ipcc-rag:latest \
  --push \
  .
```

### Cloud Run 배포

```bash
# Cloud Run API 활성화
gcloud services enable run.googleapis.com

# 배포 (환경변수 포함)
gcloud run deploy ipcc-rag \
  --image gcr.io/ipcc-rag/ipcc-rag:latest \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 60 \
  --min-instances 0 \
  --max-instances 1 \
  --concurrency 10 \
  --cpu-throttling \
  --set-env-vars "UPSTAGE_API_KEY=<your_key>,GCS_BUCKET=[GCS_BUCKET],CHROMA_DIR=/tmp/chroma_cosine,DEVICE=cpu"
```

### 배포 옵션 설계 근거

| 옵션 | 값 | 근거 |
| :--- | :--- | :--- |
| `--memory 2Gi` | 2GB | jhgan 모델(~500MB) + ChromaDB(~200MB) + FastAPI + 연산 여유분 |
| `--cpu 2` | 2코어 | CPU 임베딩 추론 속도 확보 |
| `--min-instances 0` | 0 | 유휴 비용 없음 (콜드 스타트 허용) |
| `--max-instances 1` | 1 | 과도한 스케일아웃 방지 |
| `--concurrency 10` | 10 | 인스턴스당 최대 10개 동시 요청 |
| `--cpu-throttling` | — | 요청 없을 때 CPU 제한 → 비용 절감 |

> **콜드 스타트 트레이드오프**: `--min-instances 0`이면 유휴 인스턴스 비용이 없는 대신 첫 요청 시 GCS 다운로드 + 모델 로드로 30~60초 지연 발생. 데모 용도로 감수 가능한 수준.

### 주요 트러블슈팅

#### 1. exec format error (아키텍처 불일치)

**증상**: 첫 배포 시 `failed to load /usr/bin/sh: exec format error`.

**원인**: Mac M4(arm64) 로컬 빌드 이미지를 Cloud Run(amd64)에 배포.

**해결**: `docker buildx build --platform linux/amd64`로 재빌드.

#### 2. Application startup failed

**증상**: 재빌드 후에도 `Application startup failed. Exiting.`

**원인**: 환경변수(`UPSTAGE_API_KEY`, `GCS_BUCKET`, `CHROMA_DIR`) 미주입 상태로 배포. `rag` 모듈 임포트 시 ChromaDB 경로를 찾지 못해 실패.

**해결**: `--set-env-vars`로 환경변수 포함하여 재배포.

#### 3. Artifact Registry API 미활성화

**증상**: `docker push` 시 `denied: Artifact Registry API has not been used`.

**해결**: `gcloud services enable artifactregistry.googleapis.com`

#### 4. 결제 계정 미연결

**증상**: GCS 버킷 생성 시 `AccessDeniedException: 403 billing account disabled`.

**해결**: Google Cloud Console에서 결제 계정 연결 후 재시도.

---

## 검증 결과

**서비스 URL**: `https://[CLOUD_RUN_URL]`

| 테스트 | 결과 |
| :--- | :--- |
| `GET /health` → 200 OK | ✅ |
| 관련 질문 → 한글 답변 + 출처 10개 | ✅ |
| 범위 밖 질문 → 거절 메시지 | ✅ |
| GCS → `/tmp/chroma_cosine` 자동 다운로드 | ✅ |

**검증 명령어**:

```bash
# 헬스체크
curl https://[CLOUD_RUN_URL]/health

# 관련 질문 (한글 출력)
curl -s -X POST https://[CLOUD_RUN_URL]/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "기후변화의 주요 원인은 무엇인가요?"}' \
  | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))"

# 범위 밖 질문
curl -s -X POST https://[CLOUD_RUN_URL]/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "오늘 날씨가 어때?"}' \
  | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))"
```

---

## 분석

### GCS 마운트 방식의 장단점

| 항목 | 내용 |
| :--- | :--- |
| **장점** | 이미지 크기 최소화, ChromaDB 업데이트 시 재빌드 불필요 |
| **단점** | 콜드 스타트 시 GCS 다운로드 지연 (10.2MB, 약 2~5초) |

ChromaDB(10.2MB)는 크기가 작아 다운로드 지연이 크지 않다. 모델 로드(jhgan, ~1초)가 실제 콜드 스타트의 주요 지연 원인.

### 비용 구조

| 항목 | 내용 |
| :--- | :--- |
| 유휴 비용 | 없음 (`--min-instances 0`) |
| 요청당 과금 | Cloud Run 무료 티어: 월 200만 요청 / 360,000 vCPU-초 / 180,000 GiB-초 |
| 예상 비용 | 데모 서비스 수준에서 **무료 티어 내 운영 가능** |

---

## 미해결 질문

- 콜드 스타트 실제 지연 시간은? (GCS 다운로드 + 모델 로드 합산)
- `--min-instances 1`로 항상 켜두면 월 비용이 얼마나 발생하는가?
- IEP-4005(실시간 로그) 추가 시 Cloud Run 재배포 전략은?

---

## 계획

- **GitHub README 업데이트**: 실제 URL 반영
- **IEP-4005·4006**: Streamlit UI와 함께 실시간 로그 + 신뢰도 점수 통합 구현 후 재배포
- **Phase 3 진입**: 하이브리드 방법E cosine 컬렉션 기준 재실험 후 rag.py 반영

---

## 참고자료

- [IEP-4001: FastAPI 서비스화](./IEP-4001-fastapi.md)
- [IEP-4002: Docker 컨테이너화](./IEP-4002-docker.md)
- [GCP Cloud Run 공식 문서](https://cloud.google.com/run/docs)
- 사용 환경 (2026-05-01)
  - gcloud CLI: 566.0.0
  - Docker: 28.5.2 (OrbStack)
  - 리전: asia-northeast3 (서울)
  - 이미지: `gcr.io/ipcc-rag/ipcc-rag:latest` (linux/amd64)