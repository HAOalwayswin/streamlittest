import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import xmltodict
import json
import plotly.graph_objects as go

st.set_page_config(
    page_title="서울 주요상권 인구 및 상권정보 ",
    page_icon=":tada:",
    layout="wide",
)

API_KEY = "77576c4366676b77313033484a544654"

st.title("서울 주요상권 인구 및 상권정보")

tab1, tab4, tab7, tab10 = st.tabs(["광화문·덕수궁", "여의도", "DMC", "용리단길"])

#1. 광화문·덕수궁
url = f'http://openapi.seoul.go.kr:8088/{API_KEY}/xml/citydata/1/5/광화문·덕수궁'
g_response = requests.get(url)

#2. 여의도
url = f'http://openapi.seoul.go.kr:8088/{API_KEY}/xml/citydata/1/5/여의도'
y_response = requests.get(url)

#3. DMC(디지털미디어시티)
url = f'http://openapi.seoul.go.kr:8088/{API_KEY}/xml/citydata/1/5/DMC(디지털미디어시티)'
d_response = requests.get(url)

#4. 용리단길
url = f'http://openapi.seoul.go.kr:8088/{API_KEY}/xml/citydata/1/5/용리단길'
u_response = requests.get(url)


#광화문 탭
with tab1:
    st.title("광화문·덕수궁")
    tab2, tab3 = st.tabs(["인구현황", "상권정보"])
    
    with tab2 :
        if g_response.status_code == 200:
            # XML 데이터를 딕셔너리로 변환
            xml_data = xmltodict.parse(g_response.text)
            
            # JSON으로 변환
            json_data = json.dumps(xml_data, indent=4, ensure_ascii=False)
            parsed_data = json.loads(json_data)  # JSON String -> Dictionary

            # 안전하게 키 접근
            city_data = parsed_data.get("SeoulRtd.citydata", {}).get("CITYDATA", {})
            if city_data:
                # 실시간 인구 상태 (live_ppltn_stts)
                live_ppltn_stts = city_data["LIVE_PPLTN_STTS"]["LIVE_PPLTN_STTS"]

                # 실시간 인구 데이터를 DataFrame으로 변환
                live_ppltn_df = pd.DataFrame([{
                    "구역 이름": live_ppltn_stts["AREA_NM"],
                    "혼잡도": live_ppltn_stts["AREA_CONGEST_LVL"],
                    "혼잡 메시지": live_ppltn_stts["AREA_CONGEST_MSG"],
                    "최소 인구": live_ppltn_stts["AREA_PPLTN_MIN"],
                    "최대 인구": live_ppltn_stts["AREA_PPLTN_MAX"],
                    "남성 비율": live_ppltn_stts["MALE_PPLTN_RATE"],
                    "여성 비율": live_ppltn_stts["FEMALE_PPLTN_RATE"],
                    "거주자 비율": live_ppltn_stts["RESNT_PPLTN_RATE"],
                    "비거주자 비율": live_ppltn_stts["NON_RESNT_PPLTN_RATE"]
                }])
                col1, col2 = st.columns([1, 1.5], border=True)    
                with col1:
                    st.title("광화문 실시간 인구현황",)
                    st.write(live_ppltn_df)
                    # 예측 인구 데이터 (fcst_ppltn)
                    fcst_ppltn = live_ppltn_stts["FCST_PPLTN"]["FCST_PPLTN"]

                    # 예측 인구 데이터를 DataFrame으로 변환
                    fcst_ppltn_df = pd.DataFrame([
                        {
                            "시간": item["FCST_TIME"],
                            "혼잡도": item["FCST_CONGEST_LVL"],
                            "최소 인구": item["FCST_PPLTN_MIN"],
                            "최대 인구": item["FCST_PPLTN_MAX"],
                        }
                        for item in fcst_ppltn
                    ])

                    st.subheader("인구 데이터 예측")
                    st.dataframe(fcst_ppltn_df, height=600)
                    
                with col2:
                    st.title("유동인구 예측 시각화")
                    with st.container():
                        # 예측 인구 데이터 시각화 (라인 차트)
                        st.line_chart(fcst_ppltn_df.set_index("시간")[["최소 인구", "최대 인구"]].astype(float))
                        st.bar_chart(live_ppltn_df[["남성 비율", "여성 비율"]].astype(float), x_label="성별", y_label="비율")
                        st.bar_chart(live_ppltn_df[["거주자 비율", "비거주자 비율"]].astype(float), x_label="거주자/비거주자", y_label="비율")
                    # with st.container():
                    #     st.write("This is a container2.")
                    #     st.bar_chart(data)
                    # with st.container():
                    #     st.write("This is a container3.")
                    #     st.line_chart(data)
            else:
                st.warning("실시간 인구 데이터가 없습니다.")
        else:
            st.error("Failed to fetch data from the API.")
            
    with tab3:
        g_cmrcl_stts_time = city_data['LIVE_CMRCL_STTS']['CMRCL_TIME']
        st.title(f"광화문 상권정보 : {g_cmrcl_stts_time.split(' ')[1]}에 갱신")
        g_cmrcl_stts = city_data['LIVE_CMRCL_STTS']
        # 주요 상권 정보 테이블
        main_info = {
            "상권 혼잡도": g_cmrcl_stts["AREA_CMRCL_LVL"],
            "결제 건수": g_cmrcl_stts["AREA_SH_PAYMENT_CNT"],
            "최소 결제 금액": g_cmrcl_stts["AREA_SH_PAYMENT_AMT_MIN"],
            "최대 결제 금액": g_cmrcl_stts["AREA_SH_PAYMENT_AMT_MAX"]
        }

        # 상권 RSB 데이터프레임
        cmrcl_rsb_data = [
            {
                "대분류": rsb["RSB_LRG_CTGR"],
                "중분류": rsb["RSB_MID_CTGR"],
                "결제 수준": rsb["RSB_PAYMENT_LVL"],
                "결제 건수": rsb["RSB_SH_PAYMENT_CNT"],
                "최소 결제 금액": rsb["RSB_SH_PAYMENT_AMT_MIN"],
                "최대 결제 금액": rsb["RSB_SH_PAYMENT_AMT_MAX"],
                "가맹점 수": rsb["RSB_MCT_CNT"],
                "가맹점 수 업데이트 월": rsb["RSB_MCT_TIME"]
            }
            for rsb in g_cmrcl_stts["CMRCL_RSB"]["CMRCL_RSB"]
        ]
        cmrcl_rsb_df = pd.DataFrame(cmrcl_rsb_data)

        # 성별 및 연령대 비율 데이터
        gender_data = {
            "남성 비율": float(g_cmrcl_stts["CMRCL_MALE_RATE"]),
            "여성 비율": float(g_cmrcl_stts["CMRCL_FEMALE_RATE"])
        }

        age_data = {
            "10대": float(g_cmrcl_stts["CMRCL_10_RATE"]),
            "20대": float(g_cmrcl_stts["CMRCL_20_RATE"]),
            "30대": float(g_cmrcl_stts["CMRCL_30_RATE"]),
            "40대": float(g_cmrcl_stts["CMRCL_40_RATE"]),
            "50대": float(g_cmrcl_stts["CMRCL_50_RATE"]),
            "60대 이상": float(g_cmrcl_stts["CMRCL_60_RATE"])
        }
        col1, col2 = st.columns([1, 1.5], border=True)
        with col1:
            st.header("상권 주요 정보")
            st.table(main_info)
            st.subheader("성별 비율")
            st.bar_chart(pd.DataFrame(gender_data, index=["비율"]).T)
            st.subheader("연령대 비율")
            st.bar_chart(pd.DataFrame(age_data, index=["비율"]).T)
                # 데이터 준비
        bar_data = cmrcl_rsb_df.set_index("중분류")[["결제 건수"]].astype(float)
        line_data = cmrcl_rsb_df.set_index("중분류")[["최소 결제 금액", "최대 결제 금액"]].astype(float)

        # Plotly Figure 생성
        fig = go.Figure()

        # 결제 건수를 바 차트로 추가 (주축)
        fig.add_trace(go.Bar(
            x=bar_data.index,
            y=bar_data["결제 건수"].astype(float),
            name="결제 건수",
            marker_color='darkblue',
            yaxis="y1",  # 주축
        ))

        # 최소 결제 금액을 라인 차트로 추가 (보조축)
        fig.add_trace(go.Scatter(
            x=line_data.index,
            y=line_data["최소 결제 금액"].astype(float),
            mode='lines+markers',
            name="최소 결제 금액",
            line=dict(color='green', width=2),
            yaxis="y2"  # 보조축
        ))

        # 최대 결제 금액을 라인 차트로 추가 (보조축)
        fig.add_trace(go.Scatter(
            x=line_data.index,
            y=line_data["최대 결제 금액"].astype(float),
            mode='lines+markers',
            name="최대 결제 금액",
            line=dict(color='red', width=2),
            yaxis="y2"  # 보조축
        ))

        # 레이아웃 설정
        fig.update_layout(
            title="결제 건수 및 금액 분포",
            xaxis=dict(title="업종 중분류"),
            yaxis=dict(
                title="결제 건수",
                titlefont=dict(color="white"),
                tickfont=dict(color="white"),
            ),
            yaxis2=dict(
                title="결제 금액",
                titlefont=dict(color="green"),
                tickfont=dict(color="green"),
                overlaying="y",
                side="right"  # 보조축을 오른쪽에 표시
            ),
            legend=dict(title="항목"),
            template="plotly_white",
            barmode='group'
        )

        # Streamlit에 표시
        with col2:
            st.header("상권 세부 정보")
            st.dataframe(cmrcl_rsb_df)
            st.subheader("결제 건수 및 금액 분포")
            st.plotly_chart(fig, use_container_width=True)

#여의도 탭
with tab4:
    st.title("여의도")
    tab5, tab6 = st.tabs(["인구현황", "상권정보"])
    
    #여의도 인구정보
    with tab5:
        if y_response.status_code == 200:
            # XML 데이터를 딕셔너리로 변환
            xml_data2 = xmltodict.parse(y_response.text)
            
            # JSON으로 변환
            json_data2 = json.dumps(xml_data2, indent=4, ensure_ascii=False)
            parsed_data2 = json.loads(json_data2)  # JSON String -> Dictionary

            # 안전하게 키 접근
            city_data2 = parsed_data2.get("SeoulRtd.citydata", {}).get("CITYDATA", {})

            if city_data2:
                # 실시간 인구 상태 (live_ppltn_stts)
                live_ppltn_stts2 = city_data2["LIVE_PPLTN_STTS"]["LIVE_PPLTN_STTS"]

                # 실시간 인구 데이터를 DataFrame으로 변환
                live_ppltn_df2 = pd.DataFrame([{
                    "구역 이름": live_ppltn_stts2["AREA_NM"],
                    "혼잡도": live_ppltn_stts2["AREA_CONGEST_LVL"],
                    "혼잡 메시지": live_ppltn_stts2["AREA_CONGEST_MSG"],
                    "최소 인구": live_ppltn_stts2["AREA_PPLTN_MIN"],
                    "최대 인구": live_ppltn_stts2["AREA_PPLTN_MAX"],
                    "남성 비율": live_ppltn_stts2["MALE_PPLTN_RATE"],
                    "여성 비율": live_ppltn_stts2["FEMALE_PPLTN_RATE"],
                    "거주자 비율": live_ppltn_stts2["RESNT_PPLTN_RATE"],
                    "비거주자 비율": live_ppltn_stts2["NON_RESNT_PPLTN_RATE"]
                }])

                col1, col2 = st.columns([1, 1.5], border=True)
                with col1:
                    st.title("여의도 실시간 인구현황",)
                    st.write(live_ppltn_df2)
                    # 예측 인구 데이터 (fcst_ppltn)
                    fcst_ppltn2 = live_ppltn_stts2["FCST_PPLTN"]["FCST_PPLTN"]

                    # 예측 인구 데이터를 DataFrame으로 변환
                    fcst_ppltn_df2 = pd.DataFrame([
                        {
                            "시간": item["FCST_TIME"],
                            "혼잡도": item["FCST_CONGEST_LVL"],
                            "최소 인구": item["FCST_PPLTN_MIN"],
                            "최대 인구": item["FCST_PPLTN_MAX"],
                        }
                        for item in fcst_ppltn2
                    ])

                    st.subheader("인구 데이터 예측")
                    st.dataframe(fcst_ppltn_df2.sort_values(by="시간"), height=600)
                    
                with col2:
                    st.title("유동인구 예측 시각화")
                    with st.container():
                        # 예측 인구 데이터 시각화 (라인 차트)
                        st.line_chart(fcst_ppltn_df2.set_index("시간")[["최소 인구", "최대 인구"]].astype(float))
                        st.bar_chart(live_ppltn_df2[["남성 비율", "여성 비율"]].astype(float), x_label="성별", y_label="비율")
                        st.bar_chart(live_ppltn_df2[["거주자 비율", "비거주자 비율"]].astype(float), x_label="거주자/비거주자", y_label="비율")
                    # with st.container():
                    #     st.write("This is a container2.")
                    #     st.bar_chart(data)
                    # with st.container():
                    #     st.write("This is a container3.")
                    #     st.line_chart(data)
            else:
                st.warning("실시간 인구 데이터가 없습니다.")
        else:
            st.error("Failed to fetch data from the API.")
    
    #여의도 상권정보        
    with tab6:
        y_cmrcl_stts_time = city_data2['LIVE_CMRCL_STTS']['CMRCL_TIME']
        st.title(f"여의도 상권정보 : {y_cmrcl_stts_time.split(' ')[1]}에 갱신")
        y_cmrcl_stts = city_data2['LIVE_CMRCL_STTS']
        # 주요 상권 정보 테이블
        main_info = {
            "상권 혼잡도": y_cmrcl_stts["AREA_CMRCL_LVL"],
            "결제 건수": y_cmrcl_stts["AREA_SH_PAYMENT_CNT"],
            "최소 결제 금액": y_cmrcl_stts["AREA_SH_PAYMENT_AMT_MIN"],
            "최대 결제 금액": y_cmrcl_stts["AREA_SH_PAYMENT_AMT_MAX"]
        }

        # 상권 RSB 데이터프레임
        y_cmrcl_rsb_data = [
            {
                "대분류": rsb["RSB_LRG_CTGR"],
                "중분류": rsb["RSB_MID_CTGR"],
                "결제 수준": rsb["RSB_PAYMENT_LVL"],
                "결제 건수": rsb["RSB_SH_PAYMENT_CNT"],
                "최소 결제 금액": rsb["RSB_SH_PAYMENT_AMT_MIN"],
                "최대 결제 금액": rsb["RSB_SH_PAYMENT_AMT_MAX"],
                "가맹점 수": rsb["RSB_MCT_CNT"],
                "가맹점 수 업데이트 월": rsb["RSB_MCT_TIME"]
            }
            for rsb in y_cmrcl_stts["CMRCL_RSB"]["CMRCL_RSB"]
        ]
        y_cmrcl_rsb_df = pd.DataFrame(y_cmrcl_rsb_data)

        # 성별 및 연령대 비율 데이터
        y_gender_data = {
            "남성 비율": float(y_cmrcl_stts["CMRCL_MALE_RATE"]),
            "여성 비율": float(y_cmrcl_stts["CMRCL_FEMALE_RATE"])
        }

        y_age_data = {
            "10대": float(y_cmrcl_stts["CMRCL_10_RATE"]),
            "20대": float(y_cmrcl_stts["CMRCL_20_RATE"]),
            "30대": float(y_cmrcl_stts["CMRCL_30_RATE"]),
            "40대": float(y_cmrcl_stts["CMRCL_40_RATE"]),
            "50대": float(y_cmrcl_stts["CMRCL_50_RATE"]),
            "60대 이상": float(y_cmrcl_stts["CMRCL_60_RATE"])
        }
        col1, col2 = st.columns([1, 1.5], border=True)
        with col1:
            st.header("상권 주요 정보")
            st.table(main_info)
            st.subheader("성별 비율")
            st.bar_chart(pd.DataFrame(y_gender_data, index=["비율"]).T)
            st.subheader("연령대 비율")
            st.bar_chart(pd.DataFrame(y_age_data, index=["비율"]).T)
                # 데이터 준비
        y_bar_data = y_cmrcl_rsb_df.set_index("중분류")[["결제 건수"]].astype(float)
        y_line_data = y_cmrcl_rsb_df.set_index("중분류")[["최소 결제 금액", "최대 결제 금액"]].astype(float)

        # Plotly Figure 생성
        fig = go.Figure()

        # 결제 건수를 바 차트로 추가 (주축)
        fig.add_trace(go.Bar(
            x=y_bar_data.index,
            y=y_bar_data["결제 건수"].astype(float),
            name="결제 건수",
            marker_color='darkblue',
            yaxis="y1",  # 주축
        ))

        # 최소 결제 금액을 라인 차트로 추가 (보조축)
        fig.add_trace(go.Scatter(
            x=y_line_data.index,
            y=y_line_data["최소 결제 금액"].astype(float),
            mode='lines+markers',
            name="최소 결제 금액",
            line=dict(color='green', width=2),
            yaxis="y2"  # 보조축
        ))

        # 최대 결제 금액을 라인 차트로 추가 (보조축)
        fig.add_trace(go.Scatter(
            x=y_line_data.index,
            y=y_line_data["최대 결제 금액"].astype(float),
            mode='lines+markers',
            name="최대 결제 금액",
            line=dict(color='red', width=2),
            yaxis="y2"  # 보조축
        ))

        # 레이아웃 설정
        fig.update_layout(
            title="결제 건수 및 금액 분포",
            xaxis=dict(title="업종 중분류"),
            yaxis=dict(
                title="결제 건수",
                titlefont=dict(color="black"),
                tickfont=dict(color="black"),
            ),
            yaxis2=dict(
                title="결제 금액",
                titlefont=dict(color="green"),
                tickfont=dict(color="green"),
                overlaying="y",
                side="right"  # 보조축을 오른쪽에 표시
            ),
            legend=dict(title="항목"),
            template="plotly_white",
            barmode='group'
        )

        # Streamlit에 표시
        with col2:
            st.header("상권 세부 정보")
            st.dataframe(y_cmrcl_rsb_df)
            st.subheader("결제 건수 및 금액 분포")
            st.plotly_chart(fig, use_container_width=True)
            
#DMC 탭
with tab7 :
    st.title("DMC(디지털미디어시티)")
    tab8, tab9 = st.tabs(["인구현황", "상권정보"])
    
    with tab8:
        if d_response.status_code == 200 :
            # XML 데이터를 딕셔너리로 변환
            xml_data3 = xmltodict.parse(d_response.text)
            
            # JSON으로 변환
            json_data3 = json.dumps(xml_data3, indent=4, ensure_ascii=False)
            parsed_data3 = json.loads(json_data3)  # JSON String -> Dictionary
            
            # 안전하게 키 접근
            city_data3 = parsed_data3.get("SeoulRtd.citydata", {}).get("CITYDATA", {})
            
            if city_data3:
                # 실시간 인구 상태 (live_ppltn_stts)
                live_ppltn_stts3 = city_data3["LIVE_PPLTN_STTS"]["LIVE_PPLTN_STTS"]

                # 실시간 인구 데이터를 DataFrame으로 변환
                live_ppltn_df3 = pd.DataFrame([{
                    "구역 이름": live_ppltn_stts3["AREA_NM"],
                    "혼잡도": live_ppltn_stts3["AREA_CONGEST_LVL"],
                    "혼잡 메시지": live_ppltn_stts3["AREA_CONGEST_MSG"],
                    "최소 인구": live_ppltn_stts3["AREA_PPLTN_MIN"],
                    "최대 인구": live_ppltn_stts3["AREA_PPLTN_MAX"],
                    "남성 비율": live_ppltn_stts3["MALE_PPLTN_RATE"],
                    "여성 비율": live_ppltn_stts3["FEMALE_PPLTN_RATE"],
                    "거주자 비율": live_ppltn_stts3["RESNT_PPLTN_RATE"],
                    "비거주자 비율": live_ppltn_stts3["NON_RESNT_PPLTN_RATE"]
                }])

                col1, col2 = st.columns([1, 1.5], border=True)
                with col1:
                    st.title("DMC 실시간 인구현황",)
                    st.write(live_ppltn_df3)
                    # 예측 인구 데이터 (fcst_ppltn)
                    fcst_ppltn3 = live_ppltn_stts3["FCST_PPLTN"]["FCST_PPLTN"]

                    # 예측 인구 데이터를 DataFrame으로 변환
                    fcst_ppltn_df3 = pd.DataFrame([
                        {
                            "시간": item["FCST_TIME"],
                            "혼잡도": item["FCST_CONGEST_LVL"],
                            "최소 인구": item["FCST_PPLTN_MIN"],
                            "최대 인구": item["FCST_PPLTN_MAX"],
                        }
                        for item in fcst_ppltn3
                    ])

                    st.subheader("인구 데이터 예측")
                    st.dataframe(fcst_ppltn_df3.sort_values(by="시간"), height=600)
                    
                with col2:
                    st.title("유동인구 예측 시각화")
                    with st.container():
                        # 예측 인구 데이터 시각화 (라인 차트)
                        st.line_chart(fcst_ppltn_df3.set_index("시간")[["최소 인구", "최대 인구"]].astype(float))
                        st.bar_chart(live_ppltn_df3[["남성 비율", "여성 비율"]].astype(float), x_label="성별", y_label="비율")
                        st.bar_chart(live_ppltn_df3[["거주자 비율", "비거주자 비율"]].astype(float), x_label="거주자/비거주자", y_label="비율")
                    # with st.container():
                    #     st.write("This is a container2.")
                    #     st.bar_chart(data)
                    # with st.container():
                    #     st.write("This is a container3.")
                    #     st.line_chart(data)
            else:
                st.warning("실시간 인구 데이터가 없습니다.")
        else:
            st.error("Failed to fetch data from the API.")
    
    # with tab9:
    with tab9:
        d_cmrcl_stts_time = city_data3['LIVE_CMRCL_STTS']['CMRCL_TIME']
        st.title(f"DMC 상권정보 : {d_cmrcl_stts_time.split(' ')[1]}에 갱신")
        d_cmrcl_stts = city_data3['LIVE_CMRCL_STTS']
        # 주요 상권 정보 테이블
        main_info = {
            "상권 혼잡도": d_cmrcl_stts["AREA_CMRCL_LVL"],
            "결제 건수": d_cmrcl_stts["AREA_SH_PAYMENT_CNT"],
            "최소 결제 금액": d_cmrcl_stts["AREA_SH_PAYMENT_AMT_MIN"],
            "최대 결제 금액": d_cmrcl_stts["AREA_SH_PAYMENT_AMT_MAX"]
        }

        # 상권 RSB 데이터프레임
        d_cmrcl_rsb_data = [
            {
                "대분류": rsb["RSB_LRG_CTGR"],
                "중분류": rsb["RSB_MID_CTGR"],
                "결제 수준": rsb["RSB_PAYMENT_LVL"],
                "결제 건수": rsb["RSB_SH_PAYMENT_CNT"],
                "최소 결제 금액": rsb["RSB_SH_PAYMENT_AMT_MIN"],
                "최대 결제 금액": rsb["RSB_SH_PAYMENT_AMT_MAX"],
                "가맹점 수": rsb["RSB_MCT_CNT"],
                "가맹점 수 업데이트 월": rsb["RSB_MCT_TIME"]
            }
            for rsb in d_cmrcl_stts["CMRCL_RSB"]["CMRCL_RSB"]
        ]
        d_cmrcl_rsb_df = pd.DataFrame(d_cmrcl_rsb_data)

        # 성별 및 연령대 비율 데이터
        d_gender_data = {
            "남성 비율": float(d_cmrcl_stts["CMRCL_MALE_RATE"]),
            "여성 비율": float(d_cmrcl_stts["CMRCL_FEMALE_RATE"])
        }

        d_age_data = {
            "10대": float(d_cmrcl_stts["CMRCL_10_RATE"]),
            "20대": float(d_cmrcl_stts["CMRCL_20_RATE"]),
            "30대": float(d_cmrcl_stts["CMRCL_30_RATE"]),
            "40대": float(d_cmrcl_stts["CMRCL_40_RATE"]),
            "50대": float(d_cmrcl_stts["CMRCL_50_RATE"]),
            "60대 이상": float(d_cmrcl_stts["CMRCL_60_RATE"])
        }
        col1, col2 = st.columns([1, 1.5], border=True)
        with col1:
            st.header("상권 주요 정보")
            st.table(main_info)
            st.subheader("성별 비율")
            st.bar_chart(pd.DataFrame(d_gender_data, index=["비율"]).T)
            st.subheader("연령대 비율")
            st.bar_chart(pd.DataFrame(d_age_data, index=["비율"]).T)
        # 데이터 준비
        d_bar_data = d_cmrcl_rsb_df.set_index("중분류")[["결제 건수"]].astype(float)
        d_line_data = d_cmrcl_rsb_df.set_index("중분류")[["최소 결제 금액", "최대 결제 금액"]].astype(float)

        # Plotly Figure 생성
        fig = go.Figure()

        # 결제 건수를 바 차트로 추가 (주축)
        fig.add_trace(go.Bar(
            x=d_bar_data.index,
            y=d_bar_data["결제 건수"].astype(float),
            name="결제 건수",
            marker_color='darkblue',
            yaxis="y1",  # 주축
        ))

        # 최소 결제 금액을 라인 차트로 추가 (보조축)
        fig.add_trace(go.Scatter(
            x=d_line_data.index,
            y=d_line_data["최소 결제 금액"].astype(float),
            mode='lines+markers',
            name="최소 결제 금액",
            line=dict(color='green', width=2),
            yaxis="y2"  # 보조축
        ))

        # 최대 결제 금액을 라인 차트로 추가 (보조축)
        fig.add_trace(go.Scatter(
            x=d_line_data.index,
            y=d_line_data["최대 결제 금액"].astype(float),
            mode='lines+markers',
            name="최대 결제 금액",
            line=dict(color='red', width=2),
            yaxis="y2"  # 보조축
        ))

        # 레이아웃 설정
        fig.update_layout(
            title="결제 건수 및 금액 분포",
            xaxis=dict(title="업종 중분류"),
            yaxis=dict(
                title="결제 건수",
                titlefont=dict(color="white"),
                tickfont=dict(color="white"),
            ),
            yaxis2=dict(
                title="결제 금액",
                titlefont=dict(color="green"),
                tickfont=dict(color="green"),
                overlaying="y",
                side="right"  # 보조축을 오른쪽에 표시
            ),
            legend=dict(title="항목"),
            template="plotly_white",
            barmode='group'
        )

        # Streamlit에 표시
        with col2:
            st.header("상권 세부 정보")
            st.dataframe(d_cmrcl_rsb_df)
            st.subheader("결제 건수 및 금액 분포")
            st.plotly_chart(fig, use_container_width=True)
            
#용리단길 탭
with tab10:
    st.title("용리단길")
    tab11, tab12 = st.tabs(["인구현황", "상권정보"])
    
    with tab11:
        if u_response.status_code == 200:
            # XML 데이터를 딕셔너리로 변환
            xml_data4 = xmltodict.parse(u_response.text)
            
            # JSON으로 변환
            json_data4 = json.dumps(xml_data4, indent=4, ensure_ascii=False)
            parsed_data4 = json.loads(json_data4)  # JSON String -> Dictionary

            # 안전하게 키 접근
            city_data4 = parsed_data4.get("SeoulRtd.citydata", {}).get("CITYDATA", {})
            if city_data4:
                # 실시간 인구 상태 (live_ppltn_stts)
                live_ppltn_stts4 = city_data4["LIVE_PPLTN_STTS"]["LIVE_PPLTN_STTS"]

                # 실시간 인구 데이터를 DataFrame으로 변환
                live_ppltn_df4 = pd.DataFrame([{
                    "구역 이름": live_ppltn_stts4["AREA_NM"],
                    "혼잡도": live_ppltn_stts4["AREA_CONGEST_LVL"],
                    "혼잡 메시지": live_ppltn_stts4["AREA_CONGEST_MSG"],
                    "최소 인구": live_ppltn_stts4["AREA_PPLTN_MIN"],
                    "최대 인구": live_ppltn_stts4["AREA_PPLTN_MAX"],
                    "남성 비율": live_ppltn_stts4["MALE_PPLTN_RATE"],
                    "여성 비율": live_ppltn_stts4["FEMALE_PPLTN_RATE"],
                    "거주자 비율": live_ppltn_stts4["RESNT_PPLTN_RATE"],
                    "비거주자 비율": live_ppltn_stts4["NON_RESNT_PPLTN_RATE"]
                }])
                col1, col2 = st.columns([1, 1.5], border=True)
                with col1:
                    st.title("용리단길 실시간 인구현황",)
                    st.write(live_ppltn_df4)
                    # 예측 인구 데이터 (fcst_ppltn)
                    fcst_ppltn4 = live_ppltn_stts4["FCST_PPLTN"]["FCST_PPLTN"]

                    # 예측 인구 데이터를 DataFrame으로 변환
                    fcst_ppltn_df4 = pd.DataFrame([
                        {
                            "시간": item["FCST_TIME"],
                            "혼잡도": item["FCST_CONGEST_LVL"],
                            "최소 인구": item["FCST_PPLTN_MIN"],
                            "최대 인구": item["FCST_PPLTN_MAX"],
                        }
                        for item in fcst_ppltn4
                    ])

                    st.subheader("인구 데이터 예측")
                    st.dataframe(fcst_ppltn_df4.sort_values(by="시간"), height=600)
                
                with col2:
                    st.title("유동인구 예측 시각화")
                    with st.container():
                        # 예측 인구 데이터 시각화 (라인 차트)
                        st.line_chart(fcst_ppltn_df4.set_index("시간")[["최소 인구", "최대 인구"]].astype(float))
                        st.bar_chart(live_ppltn_df4[["남성 비율", "여성 비율"]].astype(float), x_label="성별", y_label="비율")
                        st.bar_chart(live_ppltn_df4[["거주자 비율", "비거주자 비율"]].astype(float), x_label="거주자/비거주자", y_label="비율")
                    # with st.container():
                    #     st.write("This is a container2.")
                    #     st.bar_chart(data)
                    # with st.container():
                    #     st.write("This is a container3.")
                    #     st.line_chart(data)
            else:
                st.warning("실시간 인구 데이터가 없습니다.")
        else:
            st.error("Failed to fetch data from the API.")
    
    with tab12:
        u_cmrcl_stts_time = city_data4['LIVE_CMRCL_STTS']['CMRCL_TIME']
        st.title(f"용리단길 상권정보 : {u_cmrcl_stts_time.split(' ')[1]}에 갱신")
        u_cmrcl_stts = city_data4['LIVE_CMRCL_STTS']
        # 주요 상권 정보 테이블
        main_info = {
            "상권 혼잡도": u_cmrcl_stts["AREA_CMRCL_LVL"],
            "결제 건수": u_cmrcl_stts["AREA_SH_PAYMENT_CNT"],
            "최소 결제 금액": u_cmrcl_stts["AREA_SH_PAYMENT_AMT_MIN"],
            "최대 결제 금액": u_cmrcl_stts["AREA_SH_PAYMENT_AMT_MAX"]
        }

        # 상권 RSB 데이터프레임
        u_cmrcl_rsb_data = [
            {
                "대분류": rsb["RSB_LRG_CTGR"],
                "중분류": rsb["RSB_MID_CTGR"],
                "결제 수준": rsb["RSB_PAYMENT_LVL"],
                "결제 건수": rsb["RSB_SH_PAYMENT_CNT"],
                "최소 결제 금액": rsb["RSB_SH_PAYMENT_AMT_MIN"],
                "최대 결제 금액": rsb["RSB_SH_PAYMENT_AMT_MAX"],
                "가맹점 수": rsb["RSB_MCT_CNT"],
                "가맹점 수 업데이트 월": rsb["RSB_MCT_TIME"]
            }
            for rsb in u_cmrcl_stts["CMRCL_RSB"]["CMRCL_RSB"]
        ]
        u_cmrcl_rsb_df = pd.DataFrame(u_cmrcl_rsb_data)

        # 성별 및 연령대 비율 데이터
        u_gender_data = {
            "남성 비율": float(u_cmrcl_stts["CMRCL_MALE_RATE"]),
            "여성 비율": float(u_cmrcl_stts["CMRCL_FEMALE_RATE"])
        }
        
        u_age_data = {
            "10대": float(u_cmrcl_stts["CMRCL_10_RATE"]),
            "20대": float(u_cmrcl_stts["CMRCL_20_RATE"]),
            "30대": float(u_cmrcl_stts["CMRCL_30_RATE"]),
            "40대": float(u_cmrcl_stts["CMRCL_40_RATE"]),
            "50대": float(u_cmrcl_stts["CMRCL_50_RATE"]),
            "60대 이상": float(u_cmrcl_stts["CMRCL_60_RATE"])
        }
        col1, col2 = st.columns([1, 1.5], border=True)
        with col1:
            st.header("상권 주요 정보")
            st.table(main_info)
            st.subheader("성별 비율")
            st.bar_chart(pd.DataFrame(u_gender_data, index=["비율"]).T)
            st.subheader("연령대 비율")
            st.bar_chart(pd.DataFrame(u_age_data, index=["비율"]).T)
                # 데이터 준비
        u_bar_data = u_cmrcl_rsb_df.set_index("중분류")[["결제 건수"]].astype(float)
        u_line_data = u_cmrcl_rsb_df.set_index("중분류")[["최소 결제 금액", "최대 결제 금액"]].astype(float)
        
        #Plotly Figure 생성
        fig = go.Figure()
        
        #결제 건수르 바 차트로 추가 (주축)
        fig.add_trace(go.Bar(
            x=u_bar_data.index,
            y=u_bar_data["결제 건수"].astype(float),
            name="결제 건수",
            marker_color='darkblue',
            yaxis="y1", #주축
        ))
        
        #최소 결제 금액을 라인 차트로 추가 (보조축)
        fig.add_trace(go.Scatter(
            x=u_line_data.index,
            y=u_line_data["최소 결제 금액"].astype(float),
            mode='lines+markers',
            name="최소 결제 금액",
            line=dict(color='green', width=2),
            yaxis="y2" #보조축
        ))
        
        #최대 결제 금액을 라인 차트로 추가 (보조축)
        fig.add_trace(go.Scatter(
            x=u_line_data.index,
            y=u_line_data["최대 결제 금액"].astype(float),
            mode='lines+markers',
            name="최대 결제 금액",
            line=dict(color='red', width=2),
            yaxis="y2" #보조축
        ))
        
        #레이아웃 설정
        fig.update_layout(
            title="결제 건수 및 금액 분포",
            xaxis=dict(title="업종 중분류"),
            yaxis=dict(
                title="결제 건수",
                titlefont=dict(color="white"),
                tickfont=dict(color="white"),
            ),
            yaxis2=dict(
                title="결제 금액",
                titlefont=dict(color="green"),
                tickfont=dict(color="green"),
                overlaying="y",
                side="right" #보조축을 오른쪽에 표시
            ),
            legend=dict(title="항목"),
            template="plotly_white",
            barmode='group'
        )
        
        #Streamlit에 표시
        with col2:
            st.header("상권 세부 정보")
            st.dataframe(u_cmrcl_rsb_df)
            st.subheader("결제 건수 및 금액 분포")
            st.plotly_chart(fig, use_container_width=True)