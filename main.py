import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

# 제목
st.title("🌡️ 서울의 100년 기온 변화")
st.write("서울의 일별 기온 데이터를 이용해 연평균 기온의 변화를 살펴봅니다.")

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    # 기온 데이터를 숫자로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")
    df["최저기온"] = pd.to_numeric(df["최저기온"], errors="coerce")
    df["최고기온"] = pd.to_numeric(df["최고기온"], errors="coerce")

    return df


try:
    # 원본 데이터
    df = load_data()

    # ==================================================
    # 원본 데이터 요약
    # ==================================================

    st.subheader("📊 원본 데이터 요약")

    # 전체 데이터 개수
    total_count = len(df)

    # 관측 기간
    start_date = df["날짜"].min()
    end_date = df["날짜"].max()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "전체 데이터 개수",
            f"{total_count:,}개"
        )

    with col2:
        st.metric(
            "관측 시작",
            start_date.strftime("%Y-%m-%d")
            if pd.notna(start_date) else "-"
        )

    with col3:
        st.metric(
            "관측 종료",
            end_date.strftime("%Y-%m-%d")
            if pd.notna(end_date) else "-"
        )

    # 요약통계
    summary = df[
        ["평균기온", "최저기온", "최고기온"]
    ].describe().T

    # 보기 좋은 한글 이름으로 변경
    summary = summary.rename(
        columns={
            "count": "개수",
            "mean": "평균",
            "std": "표준편차",
            "min": "최솟값",
            "25%": "25%",
            "50%": "중앙값",
            "75%": "75%",
            "max": "최댓값"
        }
    )

    # 소수점 정리
    summary = summary.round(2)

    # 행 이름 변경
    summary.index = [
        "평균기온 (℃)",
        "최저기온 (℃)",
        "최고기온 (℃)"
    ]

    st.dataframe(
        summary,
        use_container_width=True
    )

    # 결측값 확인
    st.write("**🔍 결측값 개수**")

    missing = df[
        ["날짜", "평균기온", "최저기온", "최고기온"]
    ].isnull().sum()

    missing = missing.rename(
        {
            "날짜": "날짜",
            "평균기온": "평균기온",
            "최저기온": "최저기온",
            "최고기온": "최고기온"
        }
    )

    st.dataframe(
        missing.to_frame("결측값 개수"),
        use_container_width=True
    )

    # ==================================================
    # 연평균 기온 계산
    # ==================================================

    # 평균기온이 없는 데이터는 연평균 계산에서 제외
    temperature_data = df.dropna(
        subset=["연도", "평균기온"]
    )

    # 연도별 평균기온 계산
    yearly = (
        temperature_data
        .groupby("연도")["평균기온"]
        .mean()
        .reset_index()
        .rename(
            columns={
                "평균기온": "연평균기온"
            }
        )
    )

    # 데이터가 존재하는 가장 최근 100년 선택
    latest_year = int(yearly["연도"].max())
    start_year = latest_year - 99

    yearly_100 = yearly[
        (yearly["연도"] >= start_year) &
        (yearly["연도"] <= latest_year)
    ].copy()

    # ==================================================
    # 그래프
    # ==================================================

    st.subheader(
        f"📈 {int(yearly_100['연도'].min())}년 ~ "
        f"{int(yearly_100['연도'].max())}년 "
        "서울 연평균 기온"
    )

    chart_data = yearly_100.set_index("연도")

    st.line_chart(
        chart_data["연평균기온"],
        x_label="연도",
        y_label="연평균 기온 (℃)",
        use_container_width=True
    )

    # ==================================================
    # 간단한 통계
    # ==================================================

    col1, col2, col3 = st.columns(3)

    first_year = yearly_100.iloc[0]
    last_year = yearly_100.iloc[-1]

    temperature_change = (
        last_year["연평균기온"]
        - first_year["연평균기온"]
    )

    with col1:
        st.metric(
            "시작 연도",
            f"{int(first_year['연도'])}년",
            f"{first_year['연평균기온']:.1f} ℃"
        )

    with col2:
        st.metric(
            "최근 연도",
            f"{int(last_year['연도'])}년",
            f"{last_year['연평균기온']:.1f} ℃"
        )

    with col3:
        st.metric(
            "100년 동안 변화",
            f"{temperature_change:+.1f} ℃"
        )

    # ==================================================
    # 설명
    # ==================================================

    st.info(
        "💡 그래프에서 연도별 연평균 기온의 흐름을 확인할 수 있습니다. "
        "값이 높아질수록 서울의 연평균 기온이 높았다는 의미입니다."
    )

    # ==================================================
    # 연도별 데이터
    # ==================================================

    with st.expander("📋 연도별 연평균 기온 데이터 보기"):

        display_data = yearly_100.copy()

        display_data["연도"] = (
            display_data["연도"].astype(int)
        )

        display_data["연평균기온"] = (
            display_data["연평균기온"].round(2)
        )

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )

    # 출처
    st.caption(
        "데이터 출처: 기상청 서울 기상관측 데이터(seoul.csv)"
    )


except Exception as e:

    st.error(
        "데이터를 불러오는 중 문제가 발생했습니다."
    )

    st.write("오류 내용:", e)
