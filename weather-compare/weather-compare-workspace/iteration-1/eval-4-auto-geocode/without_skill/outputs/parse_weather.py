#!/usr/bin/env python3
"""
天气数据解析脚本
解析Open-Meteo API返回的JSON格式天气数据
"""

import json
import sys

# 天气代码对应的天气描述
WEATHER_CODES = {
    0: "晴朗",
    1: "晴朗",
    2: "晴朗",
    3: "多云",
    45: "雾",
    48: "霜雾",
    51: "毛毛雨",
    53: "毛毛雨",
    55: "毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小雨",
    81: "中雨",
    82: "大雨",
    85: "小雪",
    86: "大雪",
    95: "雷暴",
    96: "雷暴伴冰雹",
    99: "强雷暴伴冰雹"
}

def parse_weather_data(json_file, city_name):
    """解析天气数据并生成报告"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'daily' not in data:
        print(f"错误：{json_file} 中没有找到天气数据")
        return

    print(f"\n{city_name}天气预报")
    print("=" * 70)
    print(f"{'日期':<12} {'最低温':<8} {'最高温':<8} {'天气':<12} {'降水概率':<8}")
    print("-" * 70)

    for i in range(len(data['daily']['time'])):
        date = data['daily']['time'][i]
        temp_min = data['daily']['temperature_2m_min'][i]
        temp_max = data['daily']['temperature_2m_max'][i]
        weather_code = data['daily']['weathercode'][i]
        precip_prob = data['daily']['precipitation_probability_max'][i]

        weather_desc = WEATHER_CODES.get(weather_code, f"代码{weather_code}")

        print(f"{date:<12} {temp_min:>5.1f}°C {temp_max:>5.1f}°C {weather_desc:<12} {precip_prob:>5.0f}%")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python parse_weather.py <json_file> <city_name>")
        sys.exit(1)

    parse_weather_data(sys.argv[1], sys.argv[2])
