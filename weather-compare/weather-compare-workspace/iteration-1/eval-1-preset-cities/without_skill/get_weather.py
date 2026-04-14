#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气预报查询脚本
查询伊宁、库尔德宁、赛里木湖 2026年4月17-21日的天气
"""

import urllib.request
import json
from datetime import datetime, timedelta

# 地点坐标信息
locations = {
    "伊宁市": {"lat": 43.92, "lon": 81.32},
    "库尔德宁": {"lat": 43.43, "lon": 82.45},
    "赛里木湖": {"lat": 44.60, "lon": 81.15}
}

def get_weather_forecast(lat, lon, start_date, end_date):
    """
    使用Open-Meteo API获取天气预报
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_sum,windspeed_10m_max&timezone=Asia/Shanghai&start_date={start_date}&end_date={end_date}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        return {"error": str(e)}

def weather_code_description(code):
    """
    将WMO天气代码转换为中文描述
    """
    weather_codes = {
        0: "晴朗",
        1: "大部晴朗", 2: "多云", 3: "阴天",
        45: "雾", 48: "霜雾",
        51: "小毛毛雨", 53: "中毛毛雨", 55: "大毛毛雨",
        56: "冻毛毛雨", 57: "强冻毛毛雨",
        61: "小雨", 63: "中雨", 65: "大雨",
        66: "冻雨", 67: "强冻雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        77: "雪粒",
        80: "小阵雨", 81: "中阵雨", 82: "大阵雨",
        85: "小阵雪", 86: "大阵雪",
        95: "雷暴", 96: "雷暴伴小冰雹", 99: "雷暴伴大冰雹"
    }
    return weather_codes.get(code, f"未知({code})")

def format_weather_report(location_name, weather_data):
    """
    格式化天气报告
    """
    if "error" in weather_data:
        return f"## {location_name}\n\n错误：无法获取天气数据 - {weather_data['error']}\n"

    daily = weather_data.get("daily", {})
    dates = daily.get("time", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    weather_codes = daily.get("weathercode", [])
    precipitation = daily.get("precipitation_sum", [])
    wind_speed = daily.get("windspeed_10m_max", [])

    report = f"## {location_name}\n\n"
    report += "| 日期 | 天气 | 最高温 | 最低温 | 降水量(mm) | 最大风速(km/h) |\n"
    report += "|------|------|--------|--------|------------|----------------|\n"

    for i in range(len(dates)):
        date = dates[i]
        weather = weather_code_description(weather_codes[i]) if i < len(weather_codes) else "N/A"
        t_max = f"{temp_max[i]:.1f}" if i < len(temp_max) else "N/A"
        t_min = f"{temp_min[i]:.1f}" if i < len(temp_min) else "N/A"
        precip = f"{precipitation[i]:.1f}" if i < len(precipitation) else "N/A"
        wind = f"{wind_speed[i]:.1f}" if i < len(wind_speed) else "N/A"

        report += f"| {date} | {weather} | {t_max} | {t_min} | {precip} | {wind} |\n"

    report += "\n"
    return report

def main():
    """
    主函数
    """
    # 设置日期范围
    start_date = "2026-04-17"
    end_date = "2026-04-21"

    print(f"正在查询天气预报：{start_date} 至 {end_date}")
    print("=" * 60)

    # 生成完整报告
    full_report = f"# 天气预报报告\n\n"
    full_report += f"查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    full_report += f"日期范围：{start_date} 至 {end_date}\n\n"
    full_report += "---\n\n"

    for location_name, coords in locations.items():
        print(f"正在查询：{location_name}...")
        weather_data = get_weather_forecast(
            coords["lat"],
            coords["lon"],
            start_date,
            end_date
        )
        location_report = format_weather_report(location_name, weather_data)
        full_report += location_report + "\n"

    # 保存报告
    output_file = "/mnt/e/soft/skills/weather-compare/weather-compare-workspace/iteration-1/eval-1-preset-cities/without_skill/outputs/weather_report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"\n报告已保存至：{output_file}")
    print("=" * 60)
    print("\n" + full_report)

if __name__ == "__main__":
    main()
