#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
智能天气对比查询工具 - Skill版本
支持动态城市配置和自动依赖安装
"""

import urllib.request
import json
import sys
import logging
import subprocess
import argparse
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 中国主要城市数据库（包含热门旅游城市）
POPULAR_CITIES = {
    # 北京
    "北京": {"lat": 39.90, "lon": 116.41, "cma_id": "101010100"},
    "北京城区": {"lat": 39.90, "lon": 116.41, "cma_id": "101010100"},

    # 上海
    "上海": {"lat": 31.23, "lon": 121.47, "cma_id": "101020100"},
    "上海城区": {"lat": 31.23, "lon": 121.47, "cma_id": "101020100"},

    # 广州、深圳
    "广州": {"lat": 23.13, "lon": 113.26, "cma_id": "101280101"},
    "深圳": {"lat": 22.55, "lon": 114.06, "cma_id": "101280601"},

    # 新疆地区
    "乌鲁木齐": {"lat": 43.82, "lon": 87.62, "cma_id": "101130101"},
    "伊宁": {"lat": 43.9, "lon": 81.27, "cma_id": "101131001"},
    "伊宁市": {"lat": 43.9, "lon": 81.27, "cma_id": "101131001"},
    "库尔德宁": {"lat": 43.48, "lon": 82.23, "cma_id": "101131005"},
    "赛里木湖": {"lat": 44.61, "lon": 81.18, "cma_id": "101131601"},
    "喀什": {"lat": 39.47, "lon": 75.99, "cma_id": "101130901"},
    "吐鲁番": {"lat": 42.95, "lon": 89.20, "cma_id": "101130501"},

    # 西藏地区
    "拉萨": {"lat": 29.65, "lon": 91.13, "cma_id": "101140101"},
    "林芝": {"lat": 29.68, "lon": 94.36, "cma_id": "101140401"},

    # 云南地区
    "昆明": {"lat": 25.04, "lon": 102.71, "cma_id": "101290101"},
    "大理": {"lat": 25.59, "lon": 100.27, "cma_id": "101290201"},
    "丽江": {"lat": 26.87, "lon": 100.23, "cma_id": "101291401"},
    "香格里拉": {"lat": 27.83, "lon": 99.70, "cma_id": "101291301"},

    # 四川地区
    "成都": {"lat": 30.67, "lon": 104.07, "cma_id": "101270101"},
    "九寨沟": {"lat": 33.26, "lon": 103.92, "cma_id": "101271901"},

    # 其他热门城市
    "杭州": {"lat": 30.25, "lon": 120.17, "cma_id": "101210101"},
    "苏州": {"lat": 31.30, "lon": 120.62, "cma_id": "101190401"},
    "南京": {"lat": 32.06, "lon": 118.80, "cma_id": "101190101"},
    "西安": {"lat": 34.26, "lon": 108.95, "cma_id": "101110101"},
    "厦门": {"lat": 24.48, "lon": 118.09, "cma_id": "101230201"},
    "青岛": {"lat": 36.07, "lon": 120.38, "cma_id": "101120201"},
    "三亚": {"lat": 18.25, "lon": 109.51, "cma_id": "101310201"},
    "海口": {"lat": 20.04, "lon": 110.32, "cma_id": "101310101"},
}

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

def ensure_bs4():
    """
    确保 BeautifulSoup 已安装
    尝试自动安装，失败则提示用户手动安装
    """
    try:
        from bs4 import BeautifulSoup
        return True
    except ImportError:
        logger.info("BeautifulSoup 未安装，正在尝试自动安装...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "beautifulsoup4"],
                check=True,
                capture_output=True,
                timeout=60
            )
            logger.info("✓ BeautifulSoup 安装成功")
            return True
        except subprocess.TimeoutExpired:
            logger.error("✗ 安装超时")
            print("\n⚠️  自动安装 BeautifulSoup 超时")
            print("请手动运行: pip install beautifulsoup4")
            print("\n注意：没有 BeautifulSoup 将无法获取中央气象台数据，但仍可查看国际模型数据。")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ 安装失败: {e}")
            print("\n⚠️  自动安装 BeautifulSoup 失败")
            print("请手动运行: pip install beautifulsoup4")
            print("\n注意：没有 BeautifulSoup 将无法获取中央气象台数据，但仍可查看国际模型数据。")
            return False
        except Exception as e:
            logger.error(f"✗ 安装过程发生未知错误: {e}")
            print("\n⚠️  自动安装 BeautifulSoup 时发生错误")
            print("请手动运行: pip install beautifulsoup4")
            print("\n注意：没有 BeautifulSoup 将无法获取中央气象台数据，但仍可查看国际模型数据。")
            return False

# 检查并确保 BeautifulSoup 可用
BS4_AVAILABLE = ensure_bs4()
if BS4_AVAILABLE:
    from bs4 import BeautifulSoup

def get_weather_desc(code):
    """获取天气描述"""
    return WEATHER_CODES.get(code, "未知")

def geocode_city(city_name):
    """
    使用 Open-Meteo Geocoding API 查询城市经纬度
    返回: (lat, lon) 或 None
    """
    try:
        # Open-Meteo Geocoding API（免费，无需API key）
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city_name)}&count=1&language=zh&format=json"

        logger.info(f"正在查询城市 '{city_name}' 的经纬度...")
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.load(resp)

        if data and 'results' in data and len(data['results']) > 0:
            result = data['results'][0]
            lat = result['latitude']
            lon = result['longitude']
            logger.info(f"✓ 找到 '{city_name}': 纬度 {lat}, 经度 {lon}")
            return lat, lon
        else:
            logger.warning(f"✗ 未找到城市 '{city_name}' 的地理信息")
            return None
    except Exception as e:
        logger.error(f"查询城市 '{city_name}' 经纬度失败: {e}")
        return None

def parse_cities(city_input):
    """
    解析城市输入
    支持多种格式：
    - 字符串: "伊宁,库尔德宁,赛里木湖"
    - 列表: ["伊宁", "库尔德宁", "赛里木湖"]
    - JSON字符串: '[{"name":"伊宁","lat":43.9,"lon":81.27}]'
    """
    import urllib.parse

    cities = []

    if isinstance(city_input, str):
        # 尝试解析为 JSON
        try:
            city_list = json.loads(city_input)
            if isinstance(city_list, list):
                # JSON 格式的城市配置
                for city_data in city_list:
                    if isinstance(city_data, dict):
                        cities.append(city_data)
                return cities
        except json.JSONDecodeError:
            # 不是 JSON，按逗号/顿号/空格分割
            city_names = city_input.replace('、', ',').replace(' ', ',').split(',')
            city_names = [name.strip() for name in city_names if name.strip()]

    elif isinstance(city_input, list):
        city_names = city_input
    else:
        logger.error(f"不支持的城市输入格式: {type(city_input)}")
        return []

    # 查找城市配置
    for name in city_names:
        if isinstance(name, dict):
            # 已经是配置对象
            cities.append(name)
        elif isinstance(name, str):
            # 查找预设城市
            if name in POPULAR_CITIES:
                city_config = {"name": name, **POPULAR_CITIES[name]}
                cities.append(city_config)
            else:
                # 自动查询城市经纬度
                print(f"\n🔍 正在查询 '{name}' 的地理信息...")
                coords = geocode_city(name)
                if coords:
                    lat, lon = coords
                    cities.append({
                        "name": name,
                        "lat": lat,
                        "lon": lon,
                        "cma_id": None  # 非预设城市，可能没有中央气象台ID
                    })
                else:
                    print(f"⚠️  无法找到城市 '{name}'，已跳过")

    return cities

def parse_date(date_str):
    """
    解析日期字符串
    支持多种格式：
    - MM-DD: "04-17", "4月17日", "17号"
    - YYYY-MM-DD: "2026-04-17"
    - 相对日期: "今天", "明天", "下周"
    """
    date_str = date_str.strip()
    today = datetime.now()

    # 相对日期
    if date_str in ["今天", "今日"]:
        return today.strftime("%m-%d")
    elif date_str in ["明天", "明日"]:
        return (today + timedelta(days=1)).strftime("%m-%d")
    elif date_str in ["后天"]:
        return (today + timedelta(days=2)).strftime("%m-%d")
    elif "下周" in date_str:
        # 下周一到下周日
        days_ahead = 7 - today.weekday()
        return (today + timedelta(days=days_ahead)).strftime("%m-%d")
    elif "下个月" in date_str:
        return (today + timedelta(days=30)).strftime("%m-%d")

    # MM-DD 格式
    try:
        # 纯数字: "04-17" 或 "4-17"
        if '-' in date_str:
            parts = date_str.split('-')
            if len(parts) == 2:
                month = int(parts[0])
                day = int(parts[1])
                return f"{month:02d}-{day:02d}"
    except (ValueError, IndexError):
        pass

    # 中文格式: "4月17日", "4月17"
    try:
        import re
        match = re.search(r'(\d{1,2})月(\d{1,2})', date_str)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            return f"{month:02d}-{day:02d}"

        # "17号", "17日"
        match = re.search(r'(\d{1,2})[号日]', date_str)
        if match:
            day = int(match.group(1))
            # 假设是当前月份
            month = today.month
            return f"{month:02d}-{day:02d}"
    except (ValueError, AttributeError):
        pass

    # 无法解析
    logger.warning(f"无法解析日期格式: {date_str}")
    return None

def get_ip_location():
    """获取用户位置信息"""
    return {'country': '中国', 'countryCode': 'CN', 'city': '北京'}

def get_official_source_name(country_code):
    """获取官方气象数据源名称"""
    sources = {
        'CN': ('中央气象台', '中国气象局'),
        'US': ('NOAA', '美国国家气象局'),
        'JP': ('JMA', '日本气象厅'),
        'UK': ('Met Office', '英国气象局'),
        'DE': ('DWD', '德国气象局'),
    }
    return sources.get(country_code, ('Open-Meteo', '国际气象数据'))

def get_cma_weather(city_id):
    """获取中央气象台天气数据"""
    if not BS4_AVAILABLE:
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
    except Exception as e:
        logger.error(f"获取中央气象台数据失败 (city_id={city_id}): {e}")
        return None

def get_model_data(lat, lon, days=16):
    """获取国际模型数据"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&timezone=Asia/Shanghai&forecast_days={days}&models=ecmwf_ifs,gfs_seamless"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.load(resp)
    except Exception as e:
        logger.error(f"Open-Meteo API请求失败 (lat={lat}, lon={lon}): {e}")
        return None

def format_weather_report(cities, trip_dates):
    """生成天气对比报告"""
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
    output.append(f"🏙️ 查询城市: {', '.join([c['name'] for c in cities])}")
    output.append("=" * 100)

    for city in cities:
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

            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                today_obj = datetime.strptime(today, "%Y-%m-%d")

                current_year = today_obj.year
                start_obj = datetime.strptime(f"{current_year}-{start_date}", "%Y-%m-%d")
                end_obj = datetime.strptime(f"{current_year}-{end_date}", "%Y-%m-%d")

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

            if i >= len(e_max) or i >= len(e_min) or i >= len(e_precip) or i >= len(e_code):
                logger.warning(f"{city['name']} 第{i}天ECMWF数据不完整")
                e_weather, e_str, e_prec = "-", "-", "-"
            else:
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

            if i >= len(g_max) or i >= len(g_min) or i >= len(g_precip) or i >= len(g_code):
                logger.warning(f"{city['name']} 第{i}天GFS数据不完整")
                g_weather, g_str, g_prec = "-", "-", "-"
            else:
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

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='智能天气对比查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 查询单个城市
  python weather_compare.py --start 04-17 --end 04-21 --cities "伊宁"

  # 查询多个城市
  python weather_compare.py --start 04-17 --end 04-21 --cities "伊宁,库尔德宁,赛里木湖"

  # 使用 JSON 格式传递自定义城市
  python weather_compare.py --start 04-17 --end 04-21 --cities '[{"name":"自定义城市","lat":40.0,"lon":80.0}]'
        """
    )

    parser.add_argument('--start', type=str, required=True, help='开始日期 (MM-DD 或其他支持格式)')
    parser.add_argument('--end', type=str, required=True, help='结束日期 (MM-DD 或其他支持格式)')
    parser.add_argument('--cities', type=str, required=True, help='城市列表 (逗号分隔或JSON格式)')

    args = parser.parse_args()

    # 解析日期
    start_date = parse_date(args.start)
    end_date = parse_date(args.end)

    if not start_date or not end_date:
        print("❌ 错误: 无法解析日期格式")
        print("支持的格式: MM-DD (04-17), 4月17日, 17号, 今天, 明天, 下周")
        sys.exit(1)

    # 解析城市
    cities = parse_cities(args.cities)

    if not cities:
        print("❌ 错误: 未找到有效的城市配置")
        sys.exit(1)

    # 生成报告
    report = format_weather_report(cities, (start_date, end_date))
    print(report)

if __name__ == "__main__":
    main()
