import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="서울의 100년 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

# 제목
st.title("🌡️ 서울의 연평균 기온 변화")
st.write("서울의 기상 데이터를 이용해 연도별 연평균 기온의 변화를 나타낸 그래프입니다.")

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


# -----------------------------
# 데이터 불러오기
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 평균기온 숫자 변환
    df["평균기온"] = pd.to_numeric(
        df["평균기온"],
        errors="coerce"
    )

    # 연도 만들기
    df["연도"] = df["날짜"].dt.year

    # 필요한 데이터만 남기기
    df = df.dropna(
        subset=["연도", "평균기온"]
    )

    return df


df = load_data()


# -----------------------------
# 연도별 데이터 계산
# -----------------------------

# 연도별 평균기온 + 관측일수 계산
yearly = (
    df.groupby("연도")
    .agg(
        연평균기온=("평균기온", "mean"),
        관측일수=("평균기온", "count")
    )
    .reset_index()
)

# 1년 동안 충분히 관측된 연도만 사용
# 관측일수가 너무 적은 연도는 비정상적인 평균을 만들 수 있음
yearly = yearly[yearly["관측일수"] >= 300].copy()

# 연도순 정렬
yearly = yearly.sort_values("연도")


# -----------------------------
# 최근 100년 데이터
# -----------------------------

latest_year = int(yearly["연도"].max())
start_year = latest_year - 99

yearly_100 = yearly[
    (yearly["연도"] >= start_year) &
    (yearly["연도"] <= latest_year)
].copy()


# -----------------------------
# 그래프
# -----------------------------

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=yearly_100["연도"],
        y=yearly_100["연평균기온"],
        mode="lines+markers",
        name="연평균 기온",
        line=dict(
            width=2
        ),
        marker=dict(
            size=5
        ),
        hovertemplate=
            "<b>%{x}년</b><br>" +
            "연평균 기온: %{y:.2f} ℃" +
            "<extra></extra>"
    )
)

fig.update_layout(
    title=f"서울 연평균 기온 변화 ({start_year}~{latest_year})",
    xaxis_title="연도",
    yaxis_title="연평균 기온 (℃)",
    hovermode="x unified",

    # 그래프 크기
    height=550,

    # 여백
    margin=dict(
        l=60,
        r=30,
        t=80,
        b=60
    ),

    # 배경
    plot_bgcolor="white",

    # x축 설정
    xaxis=dict(
        tickmode="linear",
        dtick=5,
        showgrid=True
    ),

    # y축 설정
    yaxis=dict(
        showgrid=True,
        zeroline=False
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# -----------------------------
# 간단한 통계
# -----------------------------

first = yearly_100.iloc[0]
last = yearly_100.iloc[-1]

change = last["연평균기온"] - first["연평균기온"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "시작 연도",
        f"{int(first['연도'])}년",
        f"{first['연평균기온']:.1f} ℃"
    )

with col2:
    st.metric(
        "최근 연도",
        f"{int(last['연도'])}년",
        f"{last['연평균기온']:.1f} ℃"
    )

with col3:
    st.metric(
        "기온 변화",
        f"{change:+.1f} ℃"
    )


# -----------------------------
# 설명
# -----------------------------

st.info(
    "💡 관측일수가 300일보다 적은 연도는 제외했습니다. "
    "이렇게 하면 일부 날짜만 관측된 연도 때문에 "
    "그래프가 갑자기 크게 떨어지는 현상을 줄일 수 있습니다."
)


# -----------------------------
# 데이터 표
# -----------------------------

with st.expander("📋 연도별 연평균 기온 보기"):

    table = yearly_100.copy()

    table["연도"] = table["연도"].astype(int)
    table["연평균기온"] = table["연평균기온"].round(2)

    table = table[
        ["연도", "연평균기온", "관측일수"]
    ]

    table.columns = [
        "연도",
        "연평균 기온 (℃)",
        "관측일수"
    ]

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True
    )


st.caption(
    "데이터 출처: 기상청 서울 기상관측 데이터 (seoul.csv)"
)
