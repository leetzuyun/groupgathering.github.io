from flask import Flask, request, jsonify, render_template
import pandas as pd
import re
from datetime import datetime

app = Flask(__name__, template_folder='templates',
            static_folder='static', static_url_path='')


@app.route('/')
def index():
    # 读取CSV文件
    file_path = 'restaurants.csv'
    df = pd.read_csv(file_path)

    # 获取所有的捷运站选项
    mrt_stations = df['鄰近捷運站'].dropna().unique().tolist()

    return render_template('index.html', mrt_stations=mrt_stations)


@app.route('/api/calculate', methods=['POST'])
def calculate():
    # 从请求中获取表单数据
    price = request.form.get('price')
    time = request.form.get('time')
    num_people = request.form.get('num_people')
    station = request.form.get('station')
    days = request.form.getlist('days')  # 因为日期可能是多个值，所以使用 getlist 方法

    # 检查和转换参数
    if price:
        price = int(price)
    if num_people:
        num_people = int(num_people)
    if time and len(time) == 5 and ':' in time:
        time = time[:2] + ':' + time[3:]

    # 调用过滤函数进行处理
    result = filter_restaurants(
        station, price, num_people, days)
    result = filter_by_time(result, time)

    # 将结果转换为字典列表
    result_list = []
    for index, row in result.iterrows():
        formatted_hours = [
            f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')}" for start, end in row['營業時間']]
        formatted_hours_str = ', '.join(formatted_hours)
        website = row['訂位網站'] if pd.notna(row['訂位網站']) else "無"
        result_list.append({
            '餐廳名稱': row['餐廳名稱'],
            '地址': row['地址'],
            '營業時間': formatted_hours_str,
            '鄰近捷運站': row['鄰近捷運站'],
            '電話': row['電話'],
            '訂位網站': website
        })

    # 将结果传递到结果页面
    return render_template('result.html', result=result_list)

# 处理时间值的函数


def extract_time_ranges(time_str):
    # 分割多个时间段
    time_ranges = time_str.split('\n')
    # 提取每个时间段内的开始和结束时间
    parsed_ranges = []
    for time_range in time_ranges:
        match = re.match(r'(\d{2}:\d{2})[–-](\d{2}:\d{2})', time_range)
        if match:
            start_time, end_time = match.groups()
            start_time = datetime.strptime(start_time, '%H:%M').time()
            end_time = datetime.strptime(end_time, '%H:%M').time()
            parsed_ranges.append((start_time, end_time))
    return parsed_ranges


def is_time_in_range(input_time, time_ranges):
    input_time = datetime.strptime(input_time, '%H:%M').time()
    for start, end in time_ranges:
        if start <= end:  # 不跨天的情況
            if start <= input_time < end:
                return True
        else:  # 跨天的情況
            if start <= input_time or input_time < end:
                return True
    return False


def filter_by_time(df, input_time):
    return df[df['營業時間'].apply(lambda x: is_time_in_range(input_time, x))]


def filter_restaurants(station=None, price=None, max_people=None, days=None):
    file_path = 'restaurants.csv'  # 替换成你的 CSV 文件路径
    df = pd.read_csv(file_path)

    # 确保数据类型正确
    df['人均價位下限'] = pd.to_numeric(df['人均價位下限'], errors='coerce')
    df['人均價位上限'] = pd.to_numeric(df['人均價位上限'], errors='coerce')
    df['建議一桌上限人數'] = pd.to_numeric(df['建議一桌上限人數'], errors='coerce')

    # 开始筛选
    filtered_data = df

    # 筛选捷运站
    if station:
        filtered_data = filtered_data[filtered_data['鄰近捷運站'].str.contains(
            station)]

    # 筛选价位范围
    if price is not None:
        filtered_data = filtered_data[(filtered_data['人均價位下限'] <= price) & (
            filtered_data['人均價位上限'] >= price)]

    # 筛选建议一桌上限人数
    if max_people is not None:
        filtered_data = filtered_data[filtered_data['建議一桌上限人數'] >= max_people]

    # 筛选时间_输入星期几(公休日)
    if days:
        day_mapping = {
            "Monday": "一",
            "Tuesday": "二",
            "Wednesday": "三",
            "Thursday": "四",
            "Friday": "五",
            "Saturday": "六",
            "Sunday": "日"
        }
        days_chinese = [day_mapping[day] for day in days if day in day_mapping]
        for day in days_chinese:
            filtered_data = filtered_data[~filtered_data['公休日'].str.contains(
                day, na=False)]

    filtered_data['營業時間'] = filtered_data['營業時間'].apply(
        lambda x: extract_time_ranges(x))

    return filtered_data


if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=True)