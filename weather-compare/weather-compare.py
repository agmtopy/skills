#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
智能天气对比查询工具
根据IP所在地自动选择国家官方气象数据源
对比官方气象数据和ECMWF/GFS国际模型数据
"""

import urllib.request
import json
import sys
import logging
from datetime import datetime

# BeautifulSoup 是可选依赖（用于中央气象台数据）
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 天气代码转换表 (WMO天气代码)
WEATHER_CODES = {
    0: "晴", 1: "晴", 2: "晴", 3: "晴",
    45: "雾", 48: "雾",
    51: "毛毛雨", 53: "毛毛雨", 55: "毛毛雨",
    56: "冻雨", 57: "冻雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    66: "冻雨", 67: "冰雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    77: "雪粒",
    80: "阵雨", 81: "阵雨", 82: "暴雨",
    85: "阵雪", 86: "阵雪",
    95: "雷暴", 96: "雷暴+冰雹", 99: "强雷暴"
}

# 城市配置
CITIES = [
    {"name": "伊宁", "lat": 43.9, "lon": 81.27, "cma_id": "101131001"},
    {"name": "库尔德宁", "lat": 43.48, "lon": 82.23, "cma_id": "101131005"},
    {"name": "赛里木湖", "lat": 44.61, "lon": 81.18, "cma_id": "101131601"},
]

def get_weather_desc(code):
    return WEATHER_CODES.get(code, "未知")

def get_ip_location():
    """
    获取用户位置信息
    由于IP定位API经常受限，直接使用默认位置（中国-北京）
    如需自定义位置，可以修改此函数的返回值
    """
    # 默认位置：中国-北京
    # 如果用户在其他国家，可以修改这里
    # 例如：美国用户可以改为 {'country': '美国', 'countryCode': 'US', 'city': '纽约'}
    return {'country': '中国', 'countryCode': 'CN', 'city': '北京'}

def get_official_source_name(country_code):
    sources = {
        'CN': ('中央气象台', '中国气象局'),
        'US': ('NOAA', '美国国家气象局'),
        'JP': ('JMA', '日本气象厅'),
        'UK': ('Met Office', '英国气象局'),
        'DE': ('DWD', '德国气象局'),
    }
    return sources.get(country_code, ('Open-Meteo', '国际气象数据'))

def get_cma_weather(city_id):
    """获取中央气象台天气数据（需要BeautifulSoup）"""
    if not BS4_AVAILABLE:
        logger.warning("BeautifulSoup未安装，跳过中央气象台数据")
        return None

    url = f"https://www.weather.com.cn/weather/{city_id}.shtml"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            soup = BeautifulSoup(resp.read(), 'html.parser')
        ul = soup.find('ul', class_='t clearfix')
        result = []
        if ul:
            for li in ul.find_all('li')[:7]:
                wea = li.find('p', class_='wea')
                tem = li.find('p', class_='tem')
                result.append({
                    'weather': wea.get('title') or wea.get_text(strip=True) if wea else '',
                    'temp': tem.get_text(strip=True).replace('℃', '') if tem else ''
                })
        return result
    except urllib.error.URLError as e:
        logger.error(f"中央气象台请求失败 (city_id={city_id}): {e}")
        return None
    except Exception as e:
        logger.error(f"解析中央气象台数据失败 (city_id={city_id}): {e}")
        return None

def get_model_data(lat, lon, days=16):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&timezone=Asia/Shanghai&forecast_days={days}&models=ecmwf_ifs,gfs_seamless"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.load(resp)
    except urllib.error.URLError as e:
        logger.error(f"Open-Meteo API请求失败 (lat={lat}, lon={lon}): {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Open-Meteo API数据解析失败: {e}")
        return None
    except Exception as e:
        logger.error(f"获取模型数据未知错误: {e}")
        return None

def format_weather_report(trip_dates=None):
    if trip_dates is None:
        trip_dates = ("04-17", "04-21")

    start_date, end_date = trip_dates
    ip_location = get_ip_location()
    source_name, source_org = get_official_source_name(ip_location['countryCode'])
    today = datetime.now().strftime("%Y-%m-%d")

    output = []
    output.append("=" * 100)
    output.append("🌤️ 智能天气对比查询")
    output.append("=" * 100)
    output.append(f"📍 检测位置: {ip_location['country']} - {ip_location['city']}")
    output.append(f"🏛️ 官方数据源: {source_name} ({source_org})")
    output.append(f"📅 出行日期: {start_date} 至 {end_date}")
    output.append(f"📆 当前日期: {today}")
    output.append("=" * 100)

    for city in CITIES:
        output.append(f"\n📍 {city['name']}")
        output.append("-" * 100)

        if ip_location['countryCode'] == 'CN' and 'cma_id' in city:
            official_data = get_cma_weather(city['cma_id'])
            official_source = "中央气象台"
        else:
            official_data = None
            official_source = source_name

        model_data = get_model_data(city['lat'], city['lon'], days=16)

        if not model_data or 'daily' not in model_data:
            output.append("国际模型数据获取失败或格式错误")
            continue

        # 验证数据结构
        daily = model_data['daily']
        if 'time' not in daily:
            output.append("模型数据缺少时间信息")
            continue

        times = daily['time']

        output.append(f"{'日期':<6} {official_source:^22} {'ECMWF欧洲':^22} {'GFS美国':^22}")
        output.append(f"{'':6} {'天气':<6} {'温度':<12} {'天气':<6} {'温度':<10} {'降水':<6} {'天气':<6} {'温度':<10} {'降水':<6}")
        output.append("-" * 100)

        for i, date in enumerate(times):
            date_short = date[5:]

            # 只显示出行日期范围内的数据
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                today_obj = datetime.strptime(today, "%Y-%m-%d")

                # 解析出行日期（假设当前年份）
                current_year = today_obj.year
                start_obj = datetime.strptime(f"{current_year}-{start_date}", "%Y-%m-%d")
                end_obj = datetime.strptime(f"{current_year}-{end_date}", "%Y-%m-%d")

                # 只保留出行日期范围内的数据
                if not (start_obj <= date_obj <= end_obj):
                    continue

                date_display = date_short
            except ValueError as e:
                logger.warning(f"日期解析错误: {e}")
                continue

            if official_data and i < len(official_data):
                o_weather = official_data[i]['weather']
                o_temp = official_data[i]['temp']
            else:
                o_weather = '-'
                o_temp = '-'

            # ECMWF数据
            e_max = daily.get('temperature_2m_max_ecmwf_ifs', [])
            e_min = daily.get('temperature_2m_min_ecmwf_ifs', [])
            e_precip = daily.get('precipitation_sum_ecmwf_ifs', [])
            e_code = daily.get('weather_code_ecmwf_ifs', [])

            # 检查索引是否有效
            if i >= len(e_max) or i >= len(e_min) or i >= len(e_precip) or i >= len(e_code):
                logger.warning(f"{city['name']} 第{i}天ECMWF数据不完整")
                e_weather, e_str, e_prec = "-", "-", "-"
            else:
                # 类型转换异常处理
                try:
                    e_weather = get_weather_desc(int(e_code[i])) if e_code[i] is not None else "-"
                except (ValueError, TypeError):
                    e_weather = "-"

                e_str = f"{e_max[i]:.0f}/{e_min[i]:.0f}°" if e_max[i] is not None and e_min[i] is not None else "-"
                e_prec = f"{e_precip[i]:.1f}mm" if e_precip[i] is not None else "0mm"

            # GFS数据
            g_max = daily.get('temperature_2m_max_gfs_seamless', [])
            g_min = daily.get('temperature_2m_min_gfs_seamless', [])
            g_precip = daily.get('precipitation_sum_gfs_seamless', [])
            g_code = daily.get('weather_code_gfs_seamless', [])

            # 检查索引是否有效
            if i >= len(g_max) or i >= len(g_min) or i >= len(g_precip) or i >= len(g_code):
                logger.warning(f"{city['name']} 第{i}天GFS数据不完整")
                g_weather, g_str, g_prec = "-", "-", "-"
            else:
                # 类型转换异常处理
                try:
                    g_weather = get_weather_desc(int(g_code[i])) if g_code[i] is not None else "-"
                except (ValueError, TypeError):
                    g_weather = "-"

                g_str = f"{g_max[i]:.0f}/{g_min[i]:.0f}°" if g_max[i] is not None and g_min[i] is not None else "-"
                g_prec = f"{g_precip[i]:.1f}mm" if g_precip[i] is not None else "0mm"

            output.append(f"{date_display:<6} {o_weather:<6} {o_temp:<12} {e_weather:<6} {e_str:<10} {e_prec:<6} {g_weather:<6} {g_str:<10} {g_prec:<6}")

    output.append("\n" + "=" * 100)
    output.append("📊 数据源说明：")
    output.append(f"  • 官方数据: {source_name} - {source_org}")
    output.append("  • ECMWF: Open-Meteo提供的ECMWF IFS模型数据（经过插值处理）")
    output.append("  • GFS: Open-Meteo提供的NOAA GFS模型数据")
    output.append("")
    output.append("⚠️  注意：ECMWF/GFS数据通过Open-Meteo API获取，可能与ECMWF官网显示有差异")
    output.append("   原因：空间插值方式、数据更新时间、坐标点定位不同")
    output.append("   如需ECMWF官方数据，请访问: https://www.ecmwf.int/")
    output.append("=" * 100)

    return "\n".join(output)

def validate_date(date_str):
    """验证日期格式 (MM-DD)"""
    try:
        datetime.strptime(date_str, "%m-%d")
        return True
    except ValueError:
        return False

def main():
    trip_start = "04-17"
    trip_end = "04-21"

    if len(sys.argv) >= 3:
        if validate_date(sys.argv[1]) and validate_date(sys.argv[2]):
            trip_start = sys.argv[1]
            trip_end = sys.argv[2]
        else:
            print("❌ 错误: 日期格式应为 MM-DD (例如: 04-17)")
            print("用法: python weather-compare.py [开始日期] [结束日期]")
            print("示例: python weather-compare.py 04-17 04-21")
            sys.exit(1)

    report = format_weather_report((trip_start, trip_end))
    print(report)

if __name__ == "__main__":
    main()