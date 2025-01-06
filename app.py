import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import griddata
import numpy as np
import time
from matplotlib import font_manager
import streamlit.components.v1 as components

# 设置Matplotlib支持中文字体
font = font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttc')  # Windows下的微软雅黑字体路径
plt.rcParams['font.family'] = font.get_name()

# 加载数据
data = pd.read_csv('清洗后的降雨量数据.csv')

# 数据预处理：将日期列转换为datetime格式，自动推断日期格式
data['日期'] = pd.to_datetime(data['日期'], errors='coerce')

# 数据范围检查
start_date_limit = pd.to_datetime("1981-01-01")
end_date_limit = pd.to_datetime("2023-12-31")

# 过滤数据的函数
def filter_data_by_date(data, start_date=None, end_date=None):
    if start_date:
        data = data[data['日期'] >= pd.to_datetime(start_date)]
    if end_date:
        data = data[data['日期'] <= pd.to_datetime(end_date)]
    return data

# 绘制降雨量热力图
def plot_rainfall_heatmap(data, start_date=None, end_date=None, selected_province=None):
    filtered_data = filter_data_by_date(data, start_date, end_date)
    if selected_province:
        filtered_data = filtered_data[filtered_data['省'] == selected_province]
    if filtered_data.empty or '经度' not in filtered_data or '纬度' not in filtered_data or '降雨量' not in filtered_data:
        return None

    map_center = [35.8617, 104.1954]  # 中国中心位置
    m = folium.Map(location=map_center, zoom_start=5)

    heat_data = [[row['纬度'], row['经度'], row['降雨量']] for _, row in filtered_data.iterrows()]
    HeatMap(heat_data).add_to(m)

    # 将地图转换为HTML并显示
    map_html = m._repr_html_()
    return map_html

# 绘制柱状图
def plot_rainfall_bar(data, time_period, start_date=None, end_date=None, selected_province=None, selected_city=None):
    filtered_data = filter_data_by_date(data, start_date, end_date)

    if filtered_data.empty:
        return None

    # 动态添加时间粒度列
    if time_period == '年':
        filtered_data['Year'] = filtered_data['日期'].dt.year
        group_column = 'Year'
    elif time_period == '月':
        filtered_data['YearMonth'] = filtered_data['日期'].dt.to_period('M').astype(str)
        group_column = 'YearMonth'
    elif time_period == '日':
        filtered_data['Date'] = filtered_data['日期'].dt.date
        group_column = 'Date'
    else:
        return None

    # 按时间粒度和省市分组
    if selected_city:
        time_data = filtered_data[filtered_data['市'] == selected_city].groupby(group_column)['降雨量'].sum().reset_index()
    elif selected_province:
        time_data = filtered_data[filtered_data['省'] == selected_province].groupby(group_column)['降雨量'].sum().reset_index()
    else:
        time_data = filtered_data.groupby(group_column)['降雨量'].sum().reset_index()

    plt.figure(figsize=(12, 6))
    sns.barplot(x=group_column, y='降雨量', data=time_data)

    plt.title(f'{time_period}降雨量柱状图')
    plt.xlabel(f'{time_period}')
    plt.ylabel('降雨量 (mm)')
    plt.xticks(rotation=45)

    return plt

# 绘制折线图
def plot_rainfall_line(data, time_period, start_date=None, end_date=None, selected_province=None, selected_city=None):
    filtered_data = filter_data_by_date(data, start_date, end_date)

    if filtered_data.empty:
        return None

    # 动态添加时间粒度列
    if time_period == '年':
        filtered_data['Year'] = filtered_data['日期'].dt.year
        group_column = 'Year'
    elif time_period == '月':
        filtered_data['YearMonth'] = filtered_data['日期'].dt.to_period('M').astype(str)
        group_column = 'YearMonth'
    elif time_period == '日':
        filtered_data['Date'] = filtered_data['日期'].dt.date
        group_column = 'Date'
    else:
        return None

    # 按时间粒度和省市分组
    if selected_city:
        time_data = filtered_data[filtered_data['市'] == selected_city].groupby(group_column)['降雨量'].sum().reset_index()
    elif selected_province:
        time_data = filtered_data[filtered_data['省'] == selected_province].groupby(group_column)['降雨量'].sum().reset_index()
    else:
        time_data = filtered_data.groupby(group_column)['降雨量'].sum().reset_index()

    plt.figure(figsize=(12, 6))
    sns.lineplot(x=group_column, y='降雨量', data=time_data)

    plt.title(f'{time_period}降雨量折线图')
    plt.xlabel(f'{time_period}')
    plt.ylabel('降雨量 (mm)')
    plt.xticks(rotation=45)

    return plt

# 绘制等值线图
def plot_rainfall_contour(data, start_date=None, end_date=None):
    filtered_data = filter_data_by_date(data, start_date, end_date)

    if filtered_data.empty:
        return None

    lons = filtered_data['经度'].values
    lats = filtered_data['纬度'].values
    rainfall = filtered_data['降雨量'].values

    grid_lon = np.linspace(lons.min(), lons.max(), 100)
    grid_lat = np.linspace(lats.min(), lats.max(), 100)
    grid_rainfall = griddata((lons, lats), rainfall, (grid_lon[None, :], grid_lat[:, None]), method='cubic')

    plt.figure(figsize=(10, 8))
    plt.contourf(grid_lon, grid_lat, grid_rainfall, cmap='coolwarm')
    plt.colorbar(label='降雨量 (mm)')
    plt.title('降雨量等值线图')
    plt.xlabel('经度')
    plt.ylabel('纬度')

    return plt

# 页面显示和交互逻辑
st.title('降雨量数据展示')
query_type = st.radio('查询范围', ['全国', '省', '市'])

# 选择省份或城市
if query_type == '省':
    selected_province = st.selectbox('选择省份', data['省'].unique())
    selected_city = None
elif query_type == '市':
    selected_province = st.selectbox('选择省份', data['省'].unique())
    selected_city = st.selectbox('选择城市', data[data['省'] == selected_province]['市'].unique())
else:
    selected_province = None
    selected_city = None

# 选择时间范围和时间粒度
start_date = st.date_input('开始日期', start_date_limit)
end_date = st.date_input('结束日期', end_date_limit)

time_period = st.selectbox('时间粒度', ['年', '月', '日'])
display_type = st.selectbox('展示方式', ['热力图', '柱状图', '折线图', '等值线图'])

# 查询按钮
query_button = st.button('点击生成')

if query_button:
    with st.spinner('正在生成...'):
        start_time = time.time()

        # 超时检查，查询超时提示
        if time.time() - start_time > 20:
            st.error("查询超时，请稍后重试。")
        else:
            if display_type == '热力图':
                map_html = plot_rainfall_heatmap(data, start_date, end_date, selected_province=selected_province)
                if map_html:
                    components.html(map_html, height=600)
            elif display_type == '柱状图':
                plot = plot_rainfall_bar(data, time_period, start_date, end_date, selected_province=selected_province, selected_city=selected_city)
                if plot:
                    st.pyplot(plot)
            elif display_type == '折线图':
                plot = plot_rainfall_line(data, time_period, start_date, end_date, selected_province=selected_province, selected_city=selected_city)
                if plot:
                    st.pyplot(plot)
            elif display_type == '等值线图':
                plot = plot_rainfall_contour(data, start_date, end_date)
                if plot:
                    st.pyplot(plot)
