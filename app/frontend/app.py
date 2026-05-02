import streamlit as st
import requests

# ── 설정 ─────────────────────────────────────────────────────────────────────

API_BASE = st.secrets.get("API_BASE", "https://ipcc-rag-917731718328.asia-northeast3.run.app")

# ── 페이지 설정 ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="IPCC Navigator",
    page_icon="🌍",
    layout="centered",
)

# ── 스타일 ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600;700&family=Noto+Sans+KR:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

/* 헤더 */
.ipcc-header {
    text-align: center;
    padding: 2.5rem 0 1.5rem;
    border-bottom: 2px solid #1a3a2a;
    margin-bottom: 1.5rem;
}
.ipcc-header h1 {
    font-family: 'Noto Serif KR', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #1a3a2a;
    margin: 0 0 0.3rem;
    letter-spacing: -0.5px;
}
.ipcc-header p {
    font-size: 0.85rem;
    color: #5a7a6a;
    margin: 0;
}

/* 고지 배너 */
.notice-banner {
    background: #f0f7f2;
    border-left: 4px solid #2d6a4f;
    padding: 0.75rem 1rem;
    border-radius: 0 6px 6px 0;
    font-size: 0.82rem;
    color: #2d4a3a;
    margin-bottom: 1.5rem;
}

/* 신뢰도 카드 */
.trust-card {
    background: #f8faf9;
    border: 1px solid #d0e4d8;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-top: 1.2rem;
}
.trust-card h4 {
    font-size: 0.78rem;
    font-weight: 500;
    color: #5a7a6a;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 0 0 0.8rem;
}
.trust-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.5rem;
    font-size: 0.83rem;
}
.trust-label { color: #3a5a4a; width: 90px; flex-shrink: 0; }
.trust-bar-wrap {
    flex: 1;
    background: #e0ede6;
    border-radius: 99px;
    height: 7px;
    overflow: hidden;
}
.trust-bar {
    height: 7px;
    border-radius: 99px;
    background: #2d6a4f;
    transition: width 0.6s ease;
}
.trust-num { color: #2d6a4f; font-weight: 500; width: 34px; text-align: right; }
.trust-tag {
    font-size: 0.72rem;
    padding: 1px 7px;
    border-radius: 99px;
    font-weight: 500;
}
.tag-high { background: #d1f0e0; color: #1a5c38; }
.tag-mid  { background: #fef3cd; color: #7a5a00; }
.tag-low  { background: #fde8e8; color: #7a2020; }
.tag-in   { background: #d1f0e0; color: #1a5c38; }
.tag-out  { background: #fde8e8; color: #7a2020; }

/* 출처 카드 */
.source-card {
    background: #f8faf9;
    border: 1px solid #d0e4d8;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.82rem;
}
.source-page {
    font-weight: 600;
    color: #2d6a4f;
    margin-bottom: 0.2rem;
    font-size: 0.78rem;
}
.source-preview { color: #4a6a5a; line-height: 1.5; }
.source-file {
    font-size: 0.72rem;
    color: #8aaa9a;
    margin-top: 0.3rem;
}

/* 전문가 버튼 */
.stButton > button {
    background: #1a3a2a;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1.2rem;
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background 0.2s;
}
.stButton > button:hover { background: #2d6a4f; }

/* 답변 영역 */
.answer-box {
    background: white;
    border: 1px solid #d0e4d8;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    line-height: 1.8;
    font-size: 0.93rem;
    color: #1a2a22;
}
</style>
""", unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="ipcc-header">
    <h1>🌍 IPCC Navigator</h1>
    <p>IPCC AR6 기후변화 종합보고서 질문 답변 시스템</p>
</div>
""", unsafe_allow_html=True)

# 고지 문구 (투명성 ①)
st.markdown("""
<div class="notice-banner">
    ⚠️ 이 챗봇은 <strong>IPCC AR6 종합보고서(한글 번역본, 188페이지)</strong>에 기반한 답변만 제공합니다.
    보고서 범위를 벗어난 질문에는 답변하지 않습니다.
</div>
""", unsafe_allow_html=True)

# 모델 정보 (투명성 ③)
with st.expander("🔧 시스템 정보", expanded=False):
    try:
        info = requests.get(f"{API_BASE}/info", timeout=5).json()
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"**LLM 모델** {info.get('llm_model', '-')}")
            st.caption(f"**임베딩** {info.get('embedding_model', '-')}")
            st.caption(f"**벡터 DB** ChromaDB · {info.get('chroma_collection', '-')}")
        with col2:
            st.caption(f"**검색 방식** 벡터 검색 (cosine)")
            st.caption(f"**유사도 임계값** {info.get('similarity_threshold', '-')}")
            st.caption(f"**검색 청크 수(TOP_K)** {info.get('top_k', '-')}")
    except Exception:
        st.caption("시스템 정보를 불러올 수 없습니다.")

st.divider()

# ── 질문 입력 ─────────────────────────────────────────────────────────────────

question = st.text_area(
    "질문을 입력하세요",
    placeholder="예) 지구 온도가 1.5°C 상승하면 어떤 일이 일어나나요?",
    height=90,
    label_visibility="collapsed",
)

ask_btn = st.button("질문하기 →", use_container_width=True)

# ── 세션 상태 초기화 ──────────────────────────────────────────────────────────

if "result" not in st.session_state:
    st.session_state.result = None
if "last_question" not in st.session_state:
    st.session_state.last_question = ""
if "expert_answer" not in st.session_state:
    st.session_state.expert_answer = None

# ── 질문 실행 ─────────────────────────────────────────────────────────────────

if ask_btn and question.strip():
    # 새 질문이면 전문가 답변 및 토글 초기화
    if question.strip() != st.session_state.last_question:
        st.session_state.expert_answer = None

    with st.status("답변을 생성하고 있습니다...", expanded=True) as status:
        st.write("🔍 질문 임베딩 중...")
        st.write("📚 관련 문서 검색 중...")
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={"question": question.strip()},
                timeout=60,
            )
            st.write("✍️ 답변 생성 중...")

            if response.status_code == 429:
                st.error("일일 요청 한도에 도달했습니다. 내일 다시 시도해주세요.")
                st.session_state.result = None
            elif response.status_code != 200:
                st.error(f"오류가 발생했습니다. (상태 코드: {response.status_code})")
                st.session_state.result = None
            else:
                st.session_state.result = response.json()
                st.session_state.last_question = question.strip()
                status.update(label="완료 ✅", state="complete", expanded=False)

        except requests.exceptions.Timeout:
            st.error("응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
            st.session_state.result = None
        except Exception as e:
            st.error(f"연결 오류: {e}")
            st.session_state.result = None

elif ask_btn and not question.strip():
    st.warning("질문을 입력해주세요.")

# ── 결과 표시 ─────────────────────────────────────────────────────────────────

if st.session_state.result:
    result = st.session_state.result
    trust = result.get("trust", {})
    sources = result.get("sources", [])

    st.divider()

    # ── 일반인용 답변 ─────────────────────────────────────────────────────────
    st.markdown("##### 🙋 일반인용 답변")
    st.markdown(
        f'<div class="answer-box">{result.get("answer_simple", "")}</div>',
        unsafe_allow_html=True,
    )

    # ── 전문가용 답변 ────────────────────────────────────────────────────────
    st.markdown("---")
    if not st.session_state.expert_answer:
        if st.button("🔬 전문가용 답변 보기", use_container_width=False):
            with st.spinner("전문가용 답변 생성 중..."):
                try:
                    exp_response = requests.post(
                        f"{API_BASE}/chat/expert",
                        json={"question": st.session_state.last_question},
                        timeout=60,
                    )
                    if exp_response.status_code == 200:
                        st.session_state.expert_answer = exp_response.json().get("answer", "")
                        st.rerun()
                    elif exp_response.status_code == 429:
                        st.error("일일 요청 한도에 도달했습니다.")
                    else:
                        st.error(f"오류: {exp_response.status_code}")
                except Exception as e:
                    st.error(f"연결 오류: {e}")
    else:
        st.markdown("##### 🔬 전문가용 답변")
        st.caption("원문 수치·신뢰 수준·섹션 맥락을 포함합니다.")
        st.markdown(
            f'<div class="answer-box">{st.session_state.expert_answer}</div>',
            unsafe_allow_html=True,
        )

    # ── 신뢰도 지표 (IEP-4006) ────────────────────────────────────────────────

    def _label(score: float) -> str:
        if score >= 0.7:
            return '<span class="trust-tag tag-high">높음</span>'
        elif score >= 0.4:
            return '<span class="trust-tag tag-mid">중간</span>'
        else:
            return '<span class="trust-tag tag-low">낮음</span>'

    rel = trust.get("relevance_score", 0.0)
    cov = trust.get("coverage_score", 0.0)
    in_scope = trust.get("is_in_scope", False)

    scope_tag = (
        '<span class="trust-tag tag-in">✅ 범위 내</span>'
        if in_scope
        else '<span class="trust-tag tag-out">❌ 범위 밖</span>'
    )

    st.markdown(f"""
<div class="trust-card">
    <h4>답변 신뢰도</h4>
    <div class="trust-row">
        <span class="trust-label">근거 일치도</span>
        <div class="trust-bar-wrap"><div class="trust-bar" style="width:{rel*100:.0f}%"></div></div>
        <span class="trust-num">{rel:.2f}</span>
        {_label(rel)}
    </div>
    <div class="trust-row">
        <span class="trust-label">출처 충분성</span>
        <div class="trust-bar-wrap"><div class="trust-bar" style="width:{cov*100:.0f}%"></div></div>
        <span class="trust-num">{cov:.2f}</span>
        {_label(cov)}
    </div>
    <div class="trust-row">
        <span class="trust-label">범위 내 여부</span>
        <div style="flex:1"></div>
        {scope_tag}
    </div>
</div>
""", unsafe_allow_html=True)

    # ── 출처 ──────────────────────────────────────────────────────────────────

    if sources:
        st.markdown("##### 📄 출처")
        for src in sources:
            st.markdown(f"""
<div class="source-card">
    <div class="source-page">p. {src['page']}</div>
    <div class="source-preview">{src['preview']}</div>
    <div class="source-file">{src['source']}</div>
</div>
""", unsafe_allow_html=True)

# ── 푸터 ─────────────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.caption("데이터 출처: IPCC AR6 종합보고서 한글 번역본 · Powered by Upstage Solar")