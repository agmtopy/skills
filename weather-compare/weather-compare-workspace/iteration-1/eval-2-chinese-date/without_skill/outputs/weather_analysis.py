#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气数据分析脚本
解析Open-Meteo API返回的天气数据并生成可读报告
"""

import json

# WMO天气代码解释
WEATHER_CODES = {
    0: "晴天",
    1: "晴间多云",
    2: "晴间多云",
    3: "多云",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "中毛毛雨",
    55: "大毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "小阵雨",
    81: "中阵雨",
    82: "大阵雨",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "雷暴伴大冰雹"
}

def parse_weather_data(json_str, city_name):
    """解析天气数据"""
    data = json.loads(json_str)
    daily = data['daily']

    report = []
    report.append(f"\n{'='*60}")
    report.append(f"{city_name}天气预报 (2026年4月20日-4月25日)")
    report.append(f"{'='*60}\n")

    for i in range(len(daily['time'])):
        date = daily['time'][i]
        max_temp = daily['temperature_2m_max'][i]
        min_temp = daily['temperature_2m_min'][i]
        weather_code = daily['weather_code'][i]
        weather_desc = WEATHER_CODES.get(weather_code, f"未知({weather_code})")

        # 转换日期格式
        date_parts = date.split('-')
        formatted_date = f"{date_parts[1]}月{date_parts[2]}日"

        report.append(f"📅 {formatted_date}")
        report.append(f"   天气: {weather_desc}")
        report.append(f"   温度: {min_temp}°C ~ {max_temp}°C")
        report.append(f"")

    return '\n'.join(report)

def generate_travel_advice(beijing_data, shanghai_data):
    """生成旅行建议"""
    advice = []
    advice.append(f"\n{'='*60}")
    advice.append("旅行建议")
    advice.append(f"{'='*60}\n")

    # 分析北京天气
    beijing_json = json.loads(beijing_data)
    beijing_rain_days = sum(1 for code in beijing_json['daily']['weather_code'] if code in [51, 53, 55, 61, 63, 65, 80, 81, 82])

    # 分析上海天气
    shanghai_json = json.loads(shanghai_data)
    shanghai_rain_days = sum(1 for code in shanghai_json['daily']['weather_code'] if code in [51, 53, 55, 61, 63, 65, 80, 81, 82])

    advice.append("🎒 行李准备:")
    advice.append("")

    if beijing_rain_days > 0 or shanghai_rain_days > 0:
        advice.append("  ✓ 建议携带雨伞或雨衣")
        advice.append("  ✓ 准备防水鞋或雨靴")

    # 温度建议
    beijing_max = max(beijing_json['daily']['temperature_2m_max'])
    beijing_min = min(beijing_json['daily']['temperature_2m_min'])
    shanghai_max = max(shanghai_json['daily']['temperature_2m_max'])
    shanghai_min = min(shanghai_json['daily']['temperature_2m_min'])

    advice.append(f"  ✓ 北京气温范围: {beijing_min}°C ~ {beijing_max}°C")
    advice.append(f"  ✓ 上海气温范围: {shanghai_min}°C ~ {shanghai_max}°C")
    advice.append("  ✓ 建议准备春季服装，早晚温差较大，需带外套")
    advice.append("")

    # 详细建议
    advice.append("📍 城市建议:")
    advice.append("")
    advice.append(f"  北京: {beijing_rain_days}天有降水可能")
    if beijing_rain_days > 2:
        advice.append("    → 较多雨天，建议多准备室内活动备选方案")

    advice.append(f"  上海: {shanghai_rain_days}天有降水可能")
    if shanghai_rain_days > 2:
        advice.append("    → 较多雨天，建议多准备室内活动备选方案")

    advice.append("")
    advice.append("🌡️ 温馨提示:")
    advice.append("  - 早晚温差较大，注意增减衣物")
    advice.append("  - 春季干燥，注意补水保湿")
    advice.append("  - 建议查看实时天气更新")

    return '\n'.join(advice)

# 北京天气数据
beijing_data = '''{"latitude":39.875,"longitude":116.375,"generationtime_ms":0.22041797637939453,"utc_offset_seconds":28800,"timezone":"Asia/Shanghai","timezone_abbreviation":"GMT+8","elevation":47.0,"daily_units":{"time":"iso8601","temperature_2m_max":"°C","temperature_2m_min":"°C","weather_code":"wmo code"},"daily":{"time":["2026-04-20","2026-04-21","2026-04-22","2026-04-23","2026-04-24","2026-04-25"],"temperature_2m_max":[22.7,24.4,17.0,20.7,27.8,18.7],"temperature_2m_min":[10.7,11.6,9.8,9.6,14.5,9.2],"weather_code":[3,0,3,3,51,51]}}'''

# 上海天气数据
shanghai_data = '''{"latitude":31.25,"longitude":121.5,"generationtime_ms":36.632418632507324,"utc_offset_seconds":28800,"timezone":"Asia/Shanghai","timezone_abbreviation":"GMT+8","elevation":5.0,"daily_units":{"time":"iso8601","temperature_2m_max":"°C","temperature_2m_min":"°C","weather_code":"wmo code"},"daily":{"time":["2026-04-20","2026-04-21","2026-04-22","2026-04-23","2026-04-24","2026-04-25"],"temperature_2m_max":[24.4,14.7,20.4,18.3,26.7,31.9],"temperature_2m_min":[14.1,12.0,11.6,12.2,13.0,17.5],"weather_code":[45,61,61,3,3,2]}}'''

# 生成报告
report_lines = []
report_lines.append("北京和上海天气预报报告")
report_lines.append("查询日期: 2026年4月15日")
report_lines.append("预报时段: 2026年4月20日 - 4月25日")
report_lines.append("数据来源: Open-Meteo API")

# 添加北京天气
report_lines.append(parse_weather_data(beijing_data, "北京"))

# 添加上海天气
report_lines.append(parse_weather_data(shanghai_data, "上海"))

# 添加旅行建议
report_lines.append(generate_travel_advice(beijing_data, shanghai_data))

# 保存报告
final_report = '\n'.join(report_lines)

with open('/mnt/e/soft/skills/weather-compare/weather-compare-workspace/iteration-1/eval-2-chinese-date/without_skill/outputs/weather_report.txt', 'w', encoding='utf-8') as f:
    f.write(final_report)

print("天气报告已生成！")
print(final_report)
