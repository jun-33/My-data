import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 페이지 설정
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울의 100년 연평균 기온 변화")
st.write("서울의 기온 데이터를 이용해 연도별 연평균 기온을 불연속적인 점으로 나타낸 그래프입니다.")

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    # 평균기온 숫자 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 결측값 제거
    df = df.dropna(subset=["연도", "평균기온"])

    return df


try:
    df = load_data()

    # 연도별 연평균 기온 계산
    yearly = (
        df.groupby("연도")["평균기온"]
        .mean()
        .reset_index()
    )

    # 최근 100년
    latest_year = int(yearly["연도"].max())
    start_year = latest_year - 99

    yearly_100 = yearly[
        (yearly["연도"] >= start_year) &
        (yearly["연도"] <= latest_year)
    ].copy()

    # 제목
    st.subheader(
        f"📊 {int(yearly_100['연도'].min())}년 ~ "
        f"{int(yearly_100['연도'].max())}년"
    )

    # -----------------------------
    # 불연속 그래프
    # -----------------------------
    fig, ax = plt.subplots(figsize=(14, 6))

    # 연도별 점만 표시
    ax.scatter(
        yearly_100["연도"],
        yearly_100["평균기온"],
        s=25
    )

    # 각 연도 값을 세로선으로 표시하여
    # 연도별 값이 서로 연결되지 않은 것처럼 표현
    for _, row in yearly_100.iterrows():
        ax.vlines(
            row["연도"],
            0,
            row["평균기온"],
            alpha=0.12
        )

    ax.set_title(
        "서울 연도별 연평균 기온",
        fontsize=18
    )

    ax.set_xlabel(
        "연도",
        fontsize=13
    )

    ax.set_ylabel(
        "연평균 기온 (℃)",
        fontsize=13
    )

    ax.grid(
        True,
        alpha=0.25
    )

    # x축 연도 표시
    ax.set_xticks(
        range(
            int(yearly_100["연도"].min()),
            int(yearly_100["연도"].max()) + 1,
            10
        )
    )

    plt.tight_layout()

    st.pyplot(fig)

    # -----------------------------
    # 통계
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    first_temp = yearly_100.iloc[0]["평균기온"]
    last_temp = yearly_100.iloc[-1]["평균기온"]

    change = last_temp - first_temp

    with col1:
        st.metric(
            "100년 전 연평균 기온",
            f"{first_temp:.1f} ℃"
        )

    with col2:
        st.metric(
            "최근 연평균 기온",
            f"{last_temp:.1f} ℃"
        )

    with col3:
        st.metric(
            "기온 변화",
            f"{change:+.1f} ℃"
        )

    # 설명
    st.info(
        "💡 각 점은 해당 연도의 연평균 기온을 나타냅니다. "
        "점과 점을 선으로 연결하지 않아 연도별 기온을 "
        "불연속적인 값으로 확인할 수 있습니다."
    )

    # 데이터 표
    with st.expander("📋 연도별 데이터 보기"):
        result = yearly_100.copy()
        result["연도"] = result["연도"].astype(int)
        result["평균기온"] = result["평균기온"].round(2)

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "데이터 출처: 기상청 서울 기상관측 데이터 (seoul.csv)"
    )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.write("오류 내용:", e)
