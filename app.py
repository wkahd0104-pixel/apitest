import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------------------------
# 1. Google Apps Script Web App URL 설정 (사용자 환경에 맞게 변경 필수)
# ----------------------------------------------------------------------
# 아래 URL은 Google Apps Script 배포 후 생성된 "웹앱 URL"로 교체해야 합니다.
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwle7KC-foFS2Z3JeyQK02HOMqYz7CZ9OY2-_DbHZzPaZvr95xJbMmCEOyxn6GWjc7o/exec" 

st.set_page_config(page_title="팀 예산 관리 시스템", page_icon="📊", layout="wide")

# 커스텀 CSS
st.markdown("""
<style>
    .reportview-container .main .block-container{
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        color: #64748b;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        color: #1e293b;
        font-size: 1.5rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=60) # 1분마다 캐시 갱신 (선택 사항)
def load_data():
    """Apps Script API를 통해 데이터를 가져옵니다."""
    if APPS_SCRIPT_URL == "YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL_HERE":
        st.warning("⚠️ Apps Script URL이 설정되지 않았습니다. 샘플 데이터를 사용합니다.")
        return get_sample_data()
        
    try:
        response = requests.get(APPS_SCRIPT_URL)
        if response.status_code == 200:
            data = response.json()
            if not data:
                return pd.DataFrame(columns=["id", "date", "member", "month", "category", "amount"])
            
            df = pd.DataFrame(data)
            # 날짜 형식 변환 및 금액 숫자 변환 등 전처리
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
            return df
        else:
            st.error(f"데이터 로드 실패: API 응답 오류 (Status Code: {response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

def save_data(entry_data):
    """Apps Script API를 통해 데이터를 저장(추가)합니다."""
    if APPS_SCRIPT_URL == "YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL_HERE":
        st.error("Apps Script URL이 설정되지 않아 데이터를 저장할 수 없습니다.")
        return False
        
    try:
        # Apps Script는 기본적으로 POST 요청 본문을 파싱하는데 제한이 있을 수 있어,
        # URL 파라미터나 json payload 형태로 전송 방식 맞춤 설정 필요
        headers = {'Content-Type': 'application/json'}
        response = requests.post(APPS_SCRIPT_URL, data=json.dumps(entry_data), headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                st.cache_data.clear() # 새 데이터 추가 후 캐시 삭제
                return True
            else:
                st.error(f"저장 실패: {result.get('message')}")
                return False
        else:
            st.error(f"API 요청 실패 (Status: {response.status_code})")
            return False
    except Exception as e:
        st.error(f"데이터 저장 중 예외 발생: {e}")
        return False

def ask_llm(prompt):
    """Apps Script API를 통해 mygemini 함수를 호출합니다."""
    if APPS_SCRIPT_URL == "YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL_HERE":
        return "Apps Script URL이 설정되지 않았습니다."
        
    try:
        headers = {'Content-Type': 'application/json'}
        payload = {"action": "ask_llm", "prompt": prompt}
        response = requests.post(APPS_SCRIPT_URL, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                return result.get("answer")
            else:
                return f"오류 발생: {result.get('message')}"
        else:
            return f"API 연결 실패 (Status Code: {response.status_code})"
    except Exception as e:
        return f"예외 발생: {e}"

def get_sample_data():
    """URL 설정 전 테스트용 샘플 데이터"""
    data = [
        {"id": 1, "date": "2026-07-29T10:00:00", "member": "팀원1", "month": "2026-07", "category": "비품", "amount": 50000},
        {"id": 2, "date": "2026-07-28T14:30:00", "member": "부장님", "month": "2026-07", "category": "수선유지비", "amount": 150000},
        {"id": 3, "date": "2026-06-15T09:00:00", "member": "팀원2", "month": "2026-06", "category": "개량공사", "amount": 500000},
    ]
    return pd.DataFrame(data)


st.title("📊 팀 예산 관리 시스템 (Streamlit + Sheets)")
st.caption("Google Spreadsheet DB 연동 대시보드")

# AI 어시스턴트 영역 추가
st.markdown("### 🤖 AI 예산 어시스턴트")
with st.container(border=True):
    llm_query = st.text_input("질문을 입력하면 mygemini가 답변해 드립니다.", placeholder="예: 이번 달 지출 중 수선유지비 비중이 어떻게 돼?")
    
    if st.button("질문하기", type="primary"):
        if llm_query:
            with st.spinner("AI가 답변을 생성하고 있습니다..."):
                # LLM 함수 호출
                llm_answer = ask_llm(llm_query)
                st.success(llm_answer)
        else:
            st.warning("질문을 먼저 입력해주세요.")
            
st.divider() # 시각적 분리선

# 탭 구성
tab_input, tab_dashboard = st.tabs(["📝 데이터 입력", "📈 전체 대시보드"])

# 데이터 로드
df = load_data()

with tab_input:
    st.header("내역 입력")
    
    with st.form("budget_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            member = st.selectbox("팀원 선택", ["부장님", "팀원1", "팀원2", "팀원3", "팀원4"])
            # 현재 연월 기본값
            current_month = datetime.now().strftime("%Y-%m")
            # Streamlit은 month picker가 없어서 text input이나 selectbox 조합 사용
            # 여기서는 편의상 최근 12개월 목록 제공
            months_list = [(datetime.now() - pd.DateOffset(months=i)).strftime("%Y-%m") for i in range(12)]
            month = st.selectbox("해당 월", months_list)
            
        with col2:
            category = st.selectbox("예산 항목", ["수선유지비", "비품", "개량공사"])
            amount = st.number_input("사용 금액 (원)", min_value=0, step=1000)
            
        submit_button = st.form_submit_button(label="기록 저장하기")
        
        if submit_button:
            if amount <= 0:
                st.warning("금액은 0원보다 커야 합니다.")
            else:
                new_entry = {
                    "action": "insert", # Apps script에서 동작 구분을 위한 필드
                    "id": datetime.now().timestamp(),
                    "date": datetime.now().isoformat(),
                    "member": member,
                    "month": month,
                    "category": category,
                    "amount": amount
                }
                
                with st.spinner("저장 중..."):
                    if save_data(new_entry):
                        st.success("예산 데이터가 성공적으로 저장되었습니다.")
                        st.rerun() # 화면 새로고침하여 데이터 반영
                    else:
                        if APPS_SCRIPT_URL == "YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL_HERE":
                             st.info("현재 샘플 모드입니다. 실제 저장을 위해서는 URL을 설정하세요.")
    
    st.divider()
    
    st.header("최근 입력 내역")
    if not df.empty:
        # 최신 데이터가 위로 오도록 정렬 (id 역순 또는 date 역순)
        display_df = df.sort_values(by="id", ascending=False).head(10)
        
        # 표시용 데이터프레임 포맷팅
        format_dict = {'amount': '{:,.0f} 원'}
        st.dataframe(
            display_df[['month', 'member', 'category', 'amount', 'date']].style.format(format_dict),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("등록된 데이터가 없습니다.")

with tab_dashboard:
    if df.empty:
         st.warning("분석할 데이터가 없습니다.")
    else:
        # 요약 통계
        total_amount = df['amount'].sum()
        record_count = len(df)
        
        # 이번 달 최대 사용 항목 계산
        current_month_str = datetime.now().strftime("%Y-%m")
        current_month_df = df[df['month'] == current_month_str]
        
        top_category_text = "-"
        if not current_month_df.empty:
            cat_sum = current_month_df.groupby('category')['amount'].sum()
            if not cat_sum.empty:
                top_cat = cat_sum.idxmax()
                top_val = cat_sum.max()
                top_category_text = f"{top_cat} ({top_val:,.0f}원)"
        
        # Metric Cards 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">전체 누적 사용액</div>
                <div class="metric-value" style="color: #2563eb;">{total_amount:,.0f}원</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">이번 달 최대 사용 항목 ({current_month_str})</div>
                <div class="metric-value" style="color: #16a34a;">{top_category_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">총 데이터 건수</div>
                <div class="metric-value" style="color: #9333ea;">{record_count}건</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("") # 여백
        
        # 차트 영역
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("🏠 항목별 예산 분포")
            cat_data = df.groupby('category')['amount'].sum().reset_index()
            fig_pie = px.pie(cat_data, values='amount', names='category', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with chart_col2:
            st.subheader("👥 팀원별 누적 사용액")
            member_data = df.groupby('member')['amount'].sum().reset_index()
            fig_bar = px.bar(member_data, x='member', y='amount', text='amount',
                             color_discrete_sequence=['#60a5fa'])
            fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_bar.update_layout(yaxis_title="금액 (원)", xaxis_title="팀원")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        st.subheader("📅 월별/항목별 요약 테이블 (취합본)")
        
        # Pivot Table 생성
        pivot_df = pd.pivot_table(
            df, 
            values='amount', 
            index='month', 
            columns='category', 
            aggfunc='sum',
            fill_value=0
        )
        
        # '합계' 열 추가
        pivot_df['합계'] = pivot_df.sum(axis=1)
        
        # 필요한 열(항목)이 데이터에 없을 경우 빈 열 추가 (포맷팅 유지를 위해)
        for cat in ["수선유지비", "비품", "개량공사"]:
            if cat not in pivot_df.columns:
                 pivot_df[cat] = 0
                 
        # 열 순서 정렬
        pivot_df = pivot_df[["수선유지비", "비품", "개량공사", "합계"]]
        
        # 월별 내림차순 정렬
        pivot_df = pivot_df.sort_index(ascending=False)
        
        # 데이터프레임 스타일링 표시
        st.dataframe(
            pivot_df.style.format("{:,.0f}"),
            use_container_width=True
        )

# 설정 안내 메시지 (디버깅 용도)
if APPS_SCRIPT_URL == "YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL_HERE":
    st.sidebar.title("설정 안내")
    st.sidebar.info("""
    **Google Sheets 연동 방법:**
    1. 새 구글 스프레드시트를 생성합니다.
    2. A1:F1에 헤더를 입력합니다: `id, date, member, month, category, amount`
    3. `확장 프로그램` > `Apps Script`를 엽니다.
    4. 제공된 `Code.gs` 스크립트를 붙여넣고 배포합니다(웹앱, 접근 권한: 모든 사용자).
    5. 발급된 **웹앱 URL**을 복사하여 `app.py` 12번째 줄의 `APPS_SCRIPT_URL` 변수에 붙여넣으세요.
    """)
