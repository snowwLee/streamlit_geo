import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.map import Marker
from folium.plugins import MarkerCluster
import plotly.express as px
import json
from streamlit_option_menu import option_menu
import base64
import io
from io import BytesIO
import tempfile
from collections import Counter
from streamlit_folium import folium_static
import matplotlib.colors as mcolors
import branca.colormap as cm
import matplotlib.pyplot as plt
#--------------------------------------------------------------------------------

# streamlit화면을 전체로 사용
st.set_page_config(layout="wide")

# streamlit의 title
st.title('대일항쟁기 강제동원 희생자 지도')
st.markdown('<hr style="bosrder-top: 3px solid #89a5ea; border-radius: 3px;">', unsafe_allow_html=True)

# 데이터 불러오기
# 엑셀파일 변경시
df = pd.read_excel('0. streamlit_데이터(08.14).xlsx', sheet_name='Sheet1')



#--------------------------------------------------------------------------------

# 탭 생성
with st.sidebar:
    tabs = option_menu("MENU", ["전체분포 확인", "유해봉환 확인", "동원 지역", "접수번호 조회","통합"],menu_icon="app-indicator")
#---------------------------------------------------------------------------------


#--------------전체 분포 지도 페이지 지도 시작점 -------------------------------------------------------------------
if tabs == "전체분포 확인":
    st.subheader('전체 분포 확인 지도')
    info1, info2, info3 = st.columns(3)
    with info1 :
        st.info('1순위 지역')
    with info2:
        st.error('2순위 지역')
    with info3:    
        st.success('3순위 지역')
    # Folium을 사용하여 지도 생성
    m1 = folium.Map(location=[34.61292748985476, 22.350872041599875], zoom_start=2,tiles='cartodbpositron')


    # 같은 위치의 좌표들을 하나로 묶어서 사용하기 위해 사용
    marker_cluster = MarkerCluster().add_to(m1)

    # 좌표 빈도 계산
    coordinates = [(row['위도'], row['경도']) for index, row in df.iterrows() if pd.notnull(row['위도']) and pd.notnull(row['경도'])]
    coordinate_counts = Counter(coordinates)

    # 가장 많은 좌표 상위 3개 찾기
    most_common_coordinates = coordinate_counts.most_common(3)


    # 클러스터 그리기
    for index, row in df.iterrows():
        local_name = row['동원지역명 수정']
        lat = row['위도']
        lng = row['경도']
        if isinstance(lat, str) or isinstance(lng, str):
            continue
        if pd.notnull(lat) and pd.notnull(lng):
            folium.Marker([lat, lng], tooltip=local_name).add_to(marker_cluster)

    # 상위 3개 좌표에 동그라미 그리기
    colors = ['#0100FF', '#FF007F', '#41FF3A']
    for i, (coordinate, count) in enumerate(most_common_coordinates):
        folium.Circle(
            location=coordinate,
            radius=25000,
            color=colors[i],
            fill=True,
            fill_color=colors[i]
        ).add_to(m1)

    # 지도 출력하기
    st_folium(m1, width=2000)

    st.write(' ')
    st.markdown('---')
    st.write(' ')
    st.subheader('작업장 육/해 구분 파이차트')

    # 육해구분을 위한 데이터 프레임 만들기
    dist_count = df[['육해구분','육해구분완료']]
    dist_counts = df['육해구분완료'].value_counts().sort_values(ascending=False)
    dist_count_df = pd.DataFrame({'육/해구분':dist_counts.index, 'count':dist_counts.values})

    # 상단 텍스트 출력
    st.markdown(f"**{dist_counts.index[0]}     {dist_counts.values[0]}건 / " \
                f"{dist_counts.index[2]}     {dist_counts.values[2]}건 / " \
                f"{dist_counts.index[1]}     {dist_counts.values[1]}건**")
    dist_col1_1, dist_col1_2= st.columns([3,2])

    with dist_col1_1 : 


        # 파이차트 그리기
        # 파이차트 컬러 지정
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']

        dist_count_fig = px.pie(dist_count_df, values='count',
                            names='육/해구분',
                            title=' ',
                            hole=0.3,
                            color_discrete_sequence = colors)

        # 범례 위치 설정
        dist_count_fig.update_layout(legend=dict(
            orientation="h",  # 범례의 방향 (수평)
            xanchor="left",   # 범례의 x축 기준 위치 (왼쪽)
            yanchor="top",    # 범례의 y축 기준 위치 (상단)
            x=0,              # x축 위치 (0은 왼쪽 맨 끝)
            y=1.3             # y축 위치 (1.1은 상단에서 약간 내린 곳)
        ))

        st.plotly_chart(dist_count_fig, use_container_width=True)
    with dist_col1_2 :
        # 육해구분 대한 데이터프레임 출력
        st.write(' ')
        st.write(dist_count)
        
#--------------지도 페이지 지도 끝점 -----------------------------------------------------------------------

#--------------유해봉환여부 시작점 -----------------------------------------------------------------------
if tabs == "유해봉환 확인":
    st.subheader('확인 지도')

    # '지역명 수정' 갯수를 계산하여 딕셔너리에 저장
    location_counts = df['동원지역명 수정'].value_counts().to_dict()

    # 색상 구간 정의
    def get_color(count):
        if count <= 10:
            return '#A5DF00'
        elif count <= 100:
            return '#74DF00'
        elif count <= 200:
            return '#01A9DB'
        elif count <= 300:
            return '#0174DF'
        elif count <= 400:
            return '#0101DF'
        elif count <= 500:
            return '#A225BB'
        elif count <= 600:
            return '#7E15A3'
        elif count <= 700:
            return '#622197'
        elif count <= 800:
            return '#B40431'
        else:
            return '#000000'

    # 지도 객체 생성
    m2 = folium.Map(location=[34.61292748985476, 22.350872041599875], zoom_start=2, tiles='cartodbpositron')

    # 데이터프레임을 순회하며 각 '수정' 원을 생성
    for name, group in df.groupby('동원지역명 수정'):
        latitude = group['위도'].iloc[0] 
        longitude = group['경도'].iloc[0]
        num_locations = len(group)  # 그룹의 행 수 가져오기
        num_count_1 = sum(group['유골봉환여부'] == '봉환')  # 각 group의 봉환 갯수 가져오기
        num_count_2 = sum(group['유골봉환여부'] == '불상')  # 각 group의 봉환 갯수 가져오기
        num_count_3 = sum(group['유골봉환여부'] == '미봉환 및 행불')  # 각 group의 봉환 갯수 가져오기
        num_count_4 = sum(group['유골봉환여부'] == '기타')  # 각 group의 봉환 갯수 가져오기
        color = get_color(location_counts[name])  # 지정한 색상 구간에 따라 색상 결정
        
        # 위도 경도가 없을 경우에는 넘어가기
        if pd.isnull(latitude) or pd.isnull(longitude):
            continue
        
        # Tooltip 텍스트 생성
        tooltip_text = f"{name} <br> 총 합 : {num_locations} <br>봉환 : {num_count_1} <br>불상 : {num_count_2} <br>미봉환 및 행불 : {num_count_3} <br>기타 : {num_count_4} <br>",

        # HTML 및 CSS를 사용하여 숫자와 색상을 모두 포함하는 DivIcon 생성
        icon_html = f'''
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                width: 25px;
                height: 25px;
                border-radius: 50%;
                background-color: {color};
                font-size: 10pt;
                color: white;">
                {int(num_locations)}
            </div>
        '''

        # Marker 생성하여 지도에 추가
        folium.Marker(
            location=[latitude, longitude],
            icon=folium.DivIcon(html=icon_html),
            tooltip=tooltip_text
        ).add_to(m2)

    # 지도 저장 및 렌더링
    m2.save('map_with_colormap.html')

    with open('map_with_colormap.html', 'r', encoding='utf-8') as file:
        st.components.v1.html(file.read(), height=700)
    #---------- 유해봉환여부 파이차트그리기 ---------------
    # 유해봉환여부 파이차트 columns 나누기
    st.write(' ')
    st.markdown('---')
    st.write(' ')
    st.subheader('봉환여부 파이차트')
    pie_col1_1, pie_col1_2= st.columns([4,1])

    with pie_col1_1 : 

        # 각 지역의 갯수 세기
        region_counts = df['유골봉환여부'].value_counts().sort_values(ascending=False)

        # 파이차트 그리기
        # 파이차트 컬러 지정
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
        pie_count = df['유골봉환여부'].value_counts()
        pie_count_df = pd.DataFrame({'유골봉환여부':pie_count.index, 'count':pie_count.values})
        pie_count_fig = px.pie(pie_count_df, values='count',
                            names='유골봉환여부',
                            title=' ',
                            hole=0.3,
                            color_discrete_sequence = colors)

        # 범례 위치 설정
        pie_count_fig.update_layout(legend=dict(
            orientation="h",  # 범례의 방향 (수평)
            xanchor="left",   # 범례의 x축 기준 위치 (왼쪽)
            yanchor="top",    # 범례의 y축 기준 위치 (상단)
            x=0,              # x축 위치 (0은 왼쪽 맨 끝)
            y=1.3             # y축 위치 (1.1은 상단에서 약간 내린 곳)
        ))

        st.plotly_chart(pie_count_fig, use_container_width=True)
    with pie_col1_2 :
        # 유해봉환여부에 대한 데이터프레임 출력
        st.write(' ')
        st.write(pie_count_df)
        
#--------------유해 봉환 여부 끝점 ---------------------------------------------






    
#--------------동원 지역 시작점 ------------------------------------------------

elif tabs == "동원 지역":
    # 두 번째 탭 첫번째 컬럼 생성
    tabs2_col1_1, tabs2_col1_2= st.columns([4,1])

    st.markdown('---')

    #지역의 갯수
    # 지역명의 수를 count 한 다음 데이터 프레임으로 만들기
    local_count = df['동원지역명 수정'].value_counts()
    local_count = pd.DataFrame({'동원지역명': local_count.index, 'count': local_count.values})

    # 데이터프레임 열의 고유값들을 리스트로 가져오기
    options = local_count['동원지역명'].unique().tolist()

    # multiselect로 선택한 값을 저장할 리스트
    selected_options = st.multiselect(' ' ,options)

    # 선택한 값에 해당하는 행만 필터링
    filtered_df = local_count[local_count['동원지역명'].isin(selected_options)]

    # 두 번째 탭 두번째 컬럼 생성
    tabs2_col2_1, tabs2_col2_2= st.columns([4,1])

    st.markdown('---')

    # 두 번째 탭 세번째 컬럼 생성
    tabs2_col3_1, tabs2_col3_2= st.columns([4,1])

    with tabs2_col1_1:
        fig = px.bar(local_count, x='동원지역명', y='count', title='전체 동원 지역 그래프')
        fig.update_traces(marker_color='#ffb6c1')
        st.plotly_chart(fig, use_container_width=True)

    with tabs2_col1_2:
        # 전체 데이터 프레임 출력
        st.write(local_count[['동원지역명','count']])

    with tabs2_col2_1:
        # 선택한 데이터프레임을 막대그래프로 표시
        f_fig = px.bar(filtered_df, x='동원지역명', y='count', title='선택 동원 지역 그래프')
        f_fig.update_traces(marker_color='#c71585')
        st.plotly_chart(f_fig, use_container_width=True)
    with tabs2_col2_2:
        # 선택한 데이터프레임 출력
        st.write(filtered_df[['동원지역명','count']])

    with tabs2_col3_1:
        #상위 선택 슬라이더
        top_count = st.slider(' ', min_value=0, max_value=len(local_count), value=10)
        top_df = local_count.nlargest(top_count, 'count')
        top_fig = px.bar(top_df, x='동원지역명', y='count', title=f'상위 {top_count}개 동원 지역 그래프')
        top_fig.update_traces(marker_color='#8b008b')
        st.plotly_chart(top_fig, use_container_width=True)
        
        
    with tabs2_col3_2:
        #상위 데이터프레임 출력
        st.write(top_df[['동원지역명','count']])

#--------------동원 지역 끝점 ---------------------------------------------

#--------------접수번호 조회 시작점 ------------------------------------------------

elif tabs == "접수번호 조회":

    #접수번호 조회를 위해 사용할 지도 생성
    application_map = folium.Map(location=[-3.0511135,132.2798922], zoom_start=3,tiles='cartodbpositron')
    
    # 나중에는 text_input으로 바꿔야함
    application_num = st.text_input('접수번호를 입력하세요')

    # input값에 대한 조건 조회
    if application_num:
        result = df[df['접수번호'] == application_num]
        if not result.empty:
            st.write('동원지역명은 **{}** 입니다.'.format(result.iloc[0]['동원지역명 수정']))
            st.dataframe(result)
            if pd.notnull([result['위도']]) and pd.notnull([result['경도']]):
                folium.Marker([result['위도'],result['경도']],
                            tooltip=result.iloc[0]['동원지역명 수정'],
                            icon=folium.Icon(icon='star', color='green')).add_to(application_map)
            st_application = st_folium(application_map, width=2000)
        else:
            st.write('입력한 접수번호를 찾을 수 없습니다.')
    

#--------------접수번호 조회 끝점 ------------------------------------------------
#--------------통합분석 시작점 ------------------------------------------------
elif tabs == "통합":
    st.header('통합분석')
    st.write(' ')
    st.write(' ')

    #df를 total_data로 복사
    total_data = df

    #국가 필터링--------------------------------------------------------------------------------
    #totdat_data['동원국가 - 수정']의 고유값들을 리스트로 만들어 total_option에 저장
    total_option1 = total_data['동원국가 - 수정'].unique().tolist()

    # multiselect로 선택한 값을 total_selected_options에 저장
    total_selected_options1 = st.multiselect('동원국가 선택' ,total_option1)

    # 선택한 값에 해당하는 행만 필터링
    total_filtered1 = total_data[total_data['동원국가 - 수정'].isin(total_selected_options1)]

    #지역 필터링--------------------------------------------------------------------------------
    total_option2 = total_filtered1['동원지역명 수정'].unique().tolist()

    total_selected_options2 = st.multiselect('동원지역 선택' ,total_option2)
    
    total_filtered2 = total_filtered1[total_filtered1['동원지역명 수정'].isin(total_selected_options2)]
    
    #비율 데이터 프레임 만들기--------------------------------------------------------------------------------
    total_filtered2_count = total_filtered2['동원지역명 수정'].value_counts()
    total_filtered2_count = pd.DataFrame({'선택 동원지역': total_filtered2_count.index, 'count': total_filtered2_count.values})


    #필터링 좌표를 찍을 map선언
    total_filtered2_map = folium.Map(location=[-3.0511135,132.2798922], zoom_start=3,tiles='cartodbpositron')

    #필터링 좌표의 cluster 선언
    total_filtered2_marker_cluster = MarkerCluster().add_to(total_filtered2_map)

    for index, row in total_filtered2.iterrows():
        local_name = row['동원지역명 수정']
        lat = row['위도']
        lng = row['경도']
        if isinstance(lat, str) or isinstance(lng, str):
            continue
        if pd.notnull(lat) and pd.notnull(lng):
            folium.Marker([lat, lng], tooltip=local_name).add_to(total_filtered2_marker_cluster)
        
    #streamlit에 folium을 출력하기 위해 사용
    st_total_filtered2_map = st_folium(total_filtered2_map, width=2000)

    tabs4_col1_1, tabs4_col1_2 = st.columns([7,3])
    tabs4_col2_1, tabs4_col2_2 = st.columns(2)

    with tabs4_col1_1:
        # 선택한 데이터프레임을 막대그래프로 표시
        total_filtered2_count_fig = px.bar(total_filtered2_count, x='선택 동원지역', y='count', title='선택 동원 지역 그래프')
        total_filtered2_count_fig.update_traces(marker_color='#7fffd4')
        st.plotly_chart(total_filtered2_count_fig, use_container_width=True)
        
    with tabs4_col1_2 : 
        st.dataframe(total_filtered2)

    with tabs4_col2_1 :

        #엑셀파일 저장 임시 공간 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            total_filtered2.to_excel(writer, index=False, sheet_name='Sheet1')


        # 엑셀 파일 다운로드 버튼 만들기
        output.seek(0)  # 파일의 시작 지점으로 커서 이동1t
        st.download_button(
            label="엑셀 다운로드",
            data=output,
            file_name='data.xlsx',
            #mime옵션 : 확장자를 명시해줌 
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    with tabs4_col2_2 :
        # 지도 저장 임시 공간 만들기
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
            total_filtered2_map.save(tmp_file.name)
            tmp_file.seek(0)  # 파일 포인터를 시작 위치로 이동
            file_data = tmp_file.read()

        # 지도 html 다운로드 버튼 만들기
        st.download_button(
        label='지도(HTML) 다운로드',
        data=file_data,
        file_name='map.html',
        mime='text/html')   
#--------------통합분석 끝점 ------------------------------------------------
