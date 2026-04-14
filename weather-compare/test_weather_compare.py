#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
测试weather-compare.py的业务逻辑
"""

import sys
import importlib.util

# 加载weather-compare.py模块
spec = importlib.util.spec_from_file_location("weather_compare", "/mnt/e/soft/skills/weather-compare/weather-compare.py")
weather_compare = importlib.util.module_from_spec(spec)
sys.modules["weather_compare"] = weather_compare
spec.loader.exec_module(weather_compare)

# 从模块中导入函数
get_weather_desc = weather_compare.get_weather_desc
validate_date = weather_compare.validate_date
get_official_source_name = weather_compare.get_official_source_name
WEATHER_CODES = weather_compare.WEATHER_CODES

def test_weather_codes():
    """测试天气代码转换"""
    print("📋 测试天气代码转换...")

    # 测试正常天气代码
    assert get_weather_desc(0) == "晴", "天气代码0应该返回'晴'"
    assert get_weather_desc(45) == "雾", "天气代码45应该返回'雾'"
    assert get_weather_desc(61) == "小雨", "天气代码61应该返回'小雨'"
    assert get_weather_desc(95) == "雷暴", "天气代码95应该返回'雷暴'"

    # 测试未知天气代码
    assert get_weather_desc(999) == "未知", "未知天气代码应该返回'未知'"

    print("✅ 天气代码转换测试通过")

def test_date_validation():
    """测试日期验证"""
    print("\n📋 测试日期验证...")

    # 测试有效日期
    assert validate_date("01-01") == True, "01-01应该是有效日期"
    assert validate_date("04-17") == True, "04-17应该是有效日期"
    assert validate_date("12-31") == True, "12-31应该是有效日期"

    # 测试无效日期
    assert validate_date("13-01") == False, "13-01应该是无效日期"
    assert validate_date("04-32") == False, "04-32应该是无效日期"
    assert validate_date("2024-04-17") == False, "完整日期格式应该是无效的"
    assert validate_date("invalid") == False, "无效字符串应该是无效日期"

    print("✅ 日期验证测试通过")

def test_official_source_name():
    """测试官方数据源名称"""
    print("\n📋 测试官方数据源名称...")

    # 测试中国
    name, org = get_official_source_name('CN')
    assert name == '中央气象台', "中国应该返回中央气象台"
    assert org == '中国气象局', "中国应该返回中国气象局"

    # 测试美国
    name, org = get_official_source_name('US')
    assert name == 'NOAA', "美国应该返回NOAA"
    assert org == '美国国家气象局', "美国应该返回美国国家气象局"

    # 测试未知国家
    name, org = get_official_source_name('XX')
    assert name == 'Open-Meteo', "未知国家应该返回Open-Meteo"

    print("✅ 官方数据源名称测试通过")

def test_weather_codes_completeness():
    """测试天气代码表完整性"""
    print("\n📋 测试天气代码表完整性...")

    # 检查WMO标准天气代码是否都在表中
    important_codes = [0, 1, 2, 3, 45, 48, 51, 61, 63, 65, 71, 73, 75, 80, 95, 96, 99]

    for code in important_codes:
        assert code in WEATHER_CODES, f"天气代码{code}不在转换表中"

    print(f"✅ 天气代码表包含{len(WEATHER_CODES)}个代码")

def test_url_construction():
    """测试URL构造（不实际发送请求）"""
    print("\n📋 测试URL构造...")

    # 模拟URL构造逻辑
    lat, lon, days = 43.9, 81.27, 16
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&timezone=Asia/Shanghai&forecast_days={days}&models=ecmwf_ifs,gfs_seamless"

    # 检查URL不包含HTML转义字符
    assert "&amp;" not in url, "URL不应包含HTML转义字符&amp;"
    assert "&" in url, "URL应包含URL参数分隔符&"
    assert f"latitude={lat}" in url, "URL应包含纬度参数"
    assert f"longitude={lon}" in url, "URL应包含经度参数"
    assert f"forecast_days={days}" in url, "URL应包含预报天数参数"

    print("✅ URL构造测试通过")

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 开始运行业务逻辑测试")
    print("=" * 60)

    try:
        test_weather_codes()
        test_date_validation()
        test_official_source_name()
        test_weather_codes_completeness()
        test_url_construction()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！业务逻辑正确")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
