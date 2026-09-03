import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

# 제목
st.title("🌡️ 서울의 100년 기온 변화")
st.write(
    "서울의 일별 기온 데이터를 이용해 연평균 기온의 변화를 살펴봅니다."
)

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


# ==================================================
# 데이터 불러오기
# ==================================================

@st.cache_data
def load_data():

    df = pd.read_csv(
        DATA_URL,
        encoding="utf-8-sig"
    )

    # 날짜 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"],
        errors="coerce"
    )

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    # 기온 숫자 변환
    df["평균기온"] = pd.to_numeric(
        df["평균기온"],
        errors="coerce"
    )

    df["최저기온"] = pd.to_numeric(
        df["최저기온"],
        errors="coerce"
    )

    df["최고기온"] = pd.to_numeric(
        df["최고기온"],
        errors="coerce"
    )

    return df


try:

    df = load_data()

    # ==================================================
    # 원본 데이터 요약
    # ==================================================

    st.subheader("📊 원본 데이터 요약")

    total_count = len(df)

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
            if pd.notna(start_date)
            else "-"
        )

    with col3:
        st.metric(
            "관측 종료",
            end_date.strftime("%Y-%m-%d")
            if pd.notna(end_date)
            else "-"
        )

    # 요약통계
    summary = df[
        ["평균기온", "최저기온", "최고기온"]
    ].describe().T

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

    summary = summary.round(2)

    summary.index = [
        "평균기온 (℃)",
        "최저기온 (℃)",
        "최고기온 (℃)"
    ]

    st.dataframe(
        summary,
        use_container_width=True
    )

    # 결측값
    st.write("**🔍 결측값 개수**")

    missing = df[
        ["날짜", "평균기온", "최저기온", "최고기온"]
    ].isnull().sum()

    st.dataframe(
        missing.to_frame("결측값 개수"),
        use_container_width=True
    )


    # ==================================================
    # 연도별 평균기온 계산
    # ==================================================

    temperature_data = df.dropna(
        subset=["연도", "평균기온"]
    )

    yearly = (
        temperature_data
        .groupby("연도")
        .agg(
            연평균기온=("평균기온", "mean"),
            관측일수=("평균기온", "count")
        )
        .reset_index()
    )

    yearly["연도"] = yearly["연도"].astype(int)


    # ==================================================
    # 최근 100년
    # ==================================================

    latest_year = int(
        yearly["연도"].max()
    )

    start_year = latest_year - 99

    yearly_100 = yearly[
        (yearly["연도"] >= start_year) &
        (yearly["연도"] <= latest_year)
    ].copy()


    # ==================================================
    # 데이터가 없는 연도 찾기
    # ==================================================

    all_years = pd.DataFrame({
        "연도": range(
            start_year,
            latest_year + 1
        )
    })

    yearly_full = all_years.merge(
        yearly_100,
        on="연도",
        how="left"
    )


    # ==================================================
    # 유난히 낮은 연도 찾기
    # ==================================================

    valid_temps = yearly_100[
        "연평균기온"
    ].dropna()

    # 사분위수를 이용해서 매우 낮은 값을 찾음
    Q1 = valid_temps.quantile(0.25)
    Q3 = valid_temps.quantile(0.75)

    IQR = Q3 - Q1

    # Q1보다 1.5*IQR 이상 낮으면 이상값으로 판단
    low_limit = Q1 - 1.5 * IQR

    yearly_full["이상하게낮음"] = (
        yearly_full["연평균기온"] < low_limit
    )


    # ==================================================
    # 그래프
    # ==================================================

    st.subheader(
        f"📈 {start_year}년 ~ {latest_year}년 "
        "서울 연평균 기온"
    )

    fig = go.Figure()


    # -----------------------------------------------
    # 정상적인 연평균 기온
    # -----------------------------------------------

    normal = yearly_full[
        (~yearly_full["이상하게낮음"]) &
        (yearly_full["연평균기온"].notna())
    ]

    fig.add_trace(
        go.Scatter(
            x=normal["연도"],
            y=normal["연평균기온"],
            mode="lines+markers",
            name="연평균 기온",
            line=dict(
                width=2
            ),
            marker=dict(
                size=5
            ),
            connectgaps=False,
            hovertemplate=
                "<b>%{x}년</b><br>" +
                "연평균 기온: %{y:.2f} ℃" +
                "<extra></extra>"
        )
    )


    # -----------------------------------------------
    # 유난히 낮은 연도
    # -----------------------------------------------

    low_years = yearly_full[
        yearly_full["이상하게낮음"]
    ]

    if len(low_years) > 0:

        fig.add_trace(
            go.Scatter(
                x=low_years["연도"],
                y=low_years["연평균기온"],
                mode="markers+text",
                name="유난히 낮은 연도",
                text=[
                    f"{int(year)}년<br>이상하게 낮음"
                    for year in low_years["연도"]
                ],
                textposition="top center",
                marker=dict(
                    size=12,
                    symbol="circle"
                ),
                hovertemplate=
                    "<b>%{x}년</b><br>" +
                    "연평균 기온: %{y:.2f} ℃<br>" +
                    "⚠️ 평소보다 유난히 낮은 값" +
                    "<extra></extra>"
            )
        )


    # -----------------------------------------------
    # 데이터가 없는 연도
    # -----------------------------------------------

    missing_years = yearly_full[
        yearly_full["연평균기온"].isna()
    ]

    if len(missing_years) > 0:

        # 그래프 아래쪽에 표시하기 위한 위치
        min_temp = yearly_100["연평균기온"].min()

        missing_y = min_temp - 0.8

        fig.add_trace(
            go.Scatter(
                x=missing_years["연도"],
                y=[missing_y] * len(missing_years),
                mode="markers+text",
                name="데이터 없음",
                text=[
                    f"{int(year)}년<br>데이터 없음"
                    for year in missing_years["연도"]
                ],
                textposition="bottom center",
                marker=dict(
                    size=12,
                    symbol="x"
                ),
                hovertemplate=
                    "<b>%{x}년</b><br>" +
                    "❌ 연평균 기온 데이터 없음" +
                    "<extra></extra>"
            )
        )


    # -----------------------------------------------
    # 그래프 설정
    # -----------------------------------------------

    fig.update_layout(

        title="서울 연도별 연평균 기온",

        xaxis_title="연도",

        yaxis_title="연평균 기온 (℃)",

        height=600,

        hovermode="x unified",

        plot_bgcolor="white",

        xaxis=dict(
            tickmode="linear",
            dtick=5,
            showgrid=True
        ),

        yaxis=dict(
            showgrid=True,
            zeroline=False
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # ==================================================
    # 이상한 데이터 요약
    # ==================================================

    st.subheader("🔎 그래프에서 확인된 이상 데이터")


    col1, col2 = st.columns(2)


    # 데이터가 없는 연도
    with col1:

        st.write("### ❌ 데이터가 없는 연도")

        if len(missing_years) == 0:

            st.success(
                "데이터가 없는 연도가 없습니다."
            )

        else:

            missing_list = [
                str(int(x))
                for x in missing_years["연도"]
            ]

            st.warning(
                ", ".join(missing_list)
            )


    # 유난히 낮은 연도
    with col2:

        st.write("### ⚠️ 유난히 낮은 연도")

        if len(low_years) == 0:

            st.success(
                "통계적으로 유난히 낮은 연도가 없습니다."
            )

        else:

            for _, row in low_years.iterrows():

                st.error(
                    f"{int(row['연도'])}년 : "
                    f"{row['연평균기온']:.2f} ℃"
                )


    # ==================================================
    # 기준 설명
    # ==================================================

    with st.expander("📌 이상값을 판단한 기준"):

        st.write(
            f"""
            **유난히 낮은 연도**는 모든 연도의 연평균 기온을
            이용해 통계적으로 판단했습니다.

            - 1사분위수(Q1): {Q1:.2f} ℃
            - 3사분위수(Q3): {Q3:.2f} ℃
            - IQR: {IQR:.2f} ℃
            - 이상값 판단 기준: {low_limit:.2f} ℃보다 낮은 경우

            따라서 이 기준보다 낮은 연도는 그래프에서
            **⚠️ 유난히 낮은 연도**로 표시됩니다.

            데이터가 하나도 존재하지 않는 연도는
            **❌ 데이터 없음**으로 따로 표시됩니다.
            """
        )


    # ==================================================
    # 간단한 통계
    # ==================================================

    st.subheader("📌 100년간 기온 변화")

    first_year = yearly_100.iloc[0]
    last_year = yearly_100.iloc[-1]

    temperature_change = (
        last_year["연평균기온"]
        - first_year["연평균기온"]
    )

    col1, col2, col3 = st.columns(3)

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
    # 연도별 데이터
    # ==================================================

    with st.expander("📋 연도별 연평균 기온 데이터 보기"):

        display_data = yearly_full.copy()

        display_data["연평균기온"] = (
            display_data["연평균기온"].round(2)
        )

        display_data["연도"] = (
            display_data["연도"].astype(int)
        )

        display_data["상태"] = "정상"

        display_data.loc[
            display_data["연평균기온"].isna(),
            "상태"
        ] = "❌ 데이터 없음"

        display_data.loc[
            display_data["이상하게낮음"],
            "상태"
        ] = "⚠️ 유난히 낮음"

        display_data = display_data[
            ["연도", "연평균기온", "관측일수", "상태"]
        ]

        display_data.columns = [
            "연도",
            "연평균 기온 (℃)",
            "관측일수",
            "상태"
        ]

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )


    # 출처
    st.caption(
        "데이터 출처: 기상청 서울 기상관측 데이터 (seoul.csv)"
    )


except Exception as e:

    st.error(
        "데이터를 불러오는 중 문제가 발생했습니다."
    )

    st.write("오류 내용:", e)
