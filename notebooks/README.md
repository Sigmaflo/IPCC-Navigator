# IEP-1002: 구조 기반 청킹 (Structural Chunking)

IPCC AR6 SYR 한글 번역본(188페이지)을 대상으로 문서 계층 구조를 활용한
구조 기반 청킹을 구현하고, ChromaDB에 저장 후 스모크 테스트를 수행합니다.

## 노트북 구성

| 파일 | Day | 내용 | 주요 산출물 |
| :--- | :---: | :--- | :--- |
| `IEP1002_day1_pdf_parse_heading_detect.ipynb` | Day 1 | PDF 진단 · 텍스트 추출 · 헤딩 패턴 탐지 | `ipcc_raw.txt` `ipcc_pages.json` `ipcc_headings.json` |
| `IEP1002_day2_step1_heading_preprocess.ipynb` | Day 2 | 헤딩 전처리 (목차·러닝헤더·오탐 제거) | `ipcc_headings_clean.json` |
| `IEP1002_day2_step2_structural_chunking.ipynb` | Day 2 | 청킹 로직 구현 · fallback 처리 · 분포 시각화 | `ipcc_chunks_structural.json` `ipcc_headings_final.json` `chunk_dist_structural.png` |
| `IEP1002_day2_step3_chromadb_smoketest.ipynb` | Day 2 | ChromaDB 저장 · 스모크 테스트 | `chroma_db/` `smoke_test_structural.txt` |

## 실행 순서

```
Day 1 → Day 2 Step 1 → Day 2 Step 2 → Day 2 Step 3
```

각 노트북은 이전 노트북의 산출물을 Google Drive에서 로드합니다.
실행 전 `OUTPUT_DIR` 경로(`/content/drive/MyDrive/IPCC_data/parsed`)를 확인하세요.

## 주요 결과

| 항목 | 수치 |
| :--- | :--- |
| 최종 헤딩 수 | 48개 (Day 1 원본 150개에서 전처리) |
| 최종 청크 수 | 284개 |
| 평균 청크 크기 | 1,669자 |
| fallback 비율 | 99.3% (split_max) |
| 임베딩 모델 | `jhgan/ko-sroberta-multitask` |
| 거리 함수 | cosine |
| 스모크 테스트 | 4/4 PASS |

> **fallback 99.3% 원인**: pdfplumber가 절 단위 헤딩(`X.X`, `X.X.X`)을
> 독립된 줄이 아닌 앞뒤 텍스트와 연결해 추출하여 헤딩 탐지 60개 중
> 48개만 확보됨. 실질적으로 헤딩 메타데이터가 붙은 고정 길이 청킹에 가까움.

## 의존성

```
pdfplumber
chromadb>=1.5.0
sentence-transformers>=5.0.0
matplotlib
```

## 관련 문서

- [IEP-1002-structural-chunking.md](../docs/IEP-1002-structural-chunking.md)
- [IEP-1001-simplechunking.md](../docs/IEP-1001-simplechunking.md)
