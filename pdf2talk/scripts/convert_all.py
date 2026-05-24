#!/usr/bin/env python3
"""轻声词 + 数字转换 — 用于 F5-TTS 语音合成。

将文本中的轻声词替换为谐音、阿拉伯数字替换为中文，
避免 TTS 吞音或错误发音。

用法:
    python convert_all.py <input.txt> <output.txt>
"""

import re
import sys

# ==================== 轻声词映射表 ====================
LIGHT_TONE_MAP = {
    # 用户提供的示例
    '意思': '意丝',
    '告诉': '告苏',
    '东西': '东溪',
    '漂亮': '漂两',
    '暖和': '暖活',
    '热闹': '热脑',
    '大方': '大放',
    '干净': '干静',
    '窗户': '窗呼',
    '钥匙': '药师',

    # 称谓和人称
    '先生': '先声',
    '朋友': '朋有',
    '亲戚': '亲七',
    '师父': '师付',
    '徒弟': '徒地',
    '丫头': '丫投',
    '小伙子': '小伙紫',
    '姑娘': '姑酿',
    '老太太': '老太态',
    '老爷爷': '老爷业',

    # 代词+们
    '他们': '他门',
    '她们': '她门',
    '它们': '它门',
    '我们': '我门',
    '你们': '你门',
    '人们': '人门',

    # 代词+的
    '我的': '我得',
    '你的': '你得',
    '他的': '他得',
    '她的': '她得',
    '它的': '它得',

    # 疑问词和指示词
    '什么': '什摸',
    '怎么': '怎摸',
    '那么': '那摸',
    '这么': '这摸',
    '多么': '多摸',

    # 动词+着
    '看着': '看哲',
    '拿着': '拿哲',
    '听着': '听哲',
    '说着': '说哲',
    '坐着': '坐哲',
    '站着': '站哲',
    '笑着': '笑哲',
    '哭着': '哭哲',
    '跑着': '跑哲',
    '飞着': '飞哲',
    '写着': '写哲',
    '读着': '读哲',
    '走着': '走哲',
    '做着': '做哲',

    # 动词+了
    '走了': '走乐',
    '来了': '来乐',
    '去了': '去乐',
    '吃了': '吃乐',
    '喝了': '喝乐',
    '看了': '看乐',
    '说了': '说乐',
    '想了': '想乐',
    '做了': '做乐',
    '买了': '买乐',
    '卖了': '卖乐',
    '给了': '给乐',
    '拿了': '拿乐',
    '跑了': '跑乐',
    '飞了': '飞乐',
    '坐了': '坐乐',
    '站了': '站乐',
    '笑了': '笑乐',
    '哭了': '哭乐',
    '写了': '写乐',
    '读了': '读乐',
    '学了': '学乐',
    '教了': '教乐',
    '问了': '问乐',
    '答了': '答乐',
    '叫了': '叫乐',

    # 动词+过
    '看过': '看个',
    '说过': '说个',
    '想过': '想个',
    '做过': '做个',
    '来过': '来个',
    '去过': '去个',
    '吃过': '吃个',
    '喝过': '喝个',
    '买过': '买个',
    '卖过': '卖个',

    # 名词+子
    '桌子': '桌紫',
    '椅子': '椅紫',
    '杯子': '杯紫',
    '瓶子': '瓶紫',
    '盒子': '盒紫',
    '袋子': '袋紫',
    '箱子': '箱紫',
    '包子': '包紫',
    '饺子': '饺紫',
    '馒头': '馒投',
    '筷子': '筷紫',
    '勺子': '勺紫',
    '叉子': '叉紫',
    '刀子': '刀紫',
    '锤子': '锤紫',
    '钉子': '钉紫',
    '绳子': '绳紫',
    '棍子': '棍紫',
    '棒子': '棒紫',
    '管子': '管紫',
    '轮子': '轮紫',
    '镜子': '镜紫',
    '扇子': '扇紫',
    '帘子': '帘紫',
    '垫子': '垫紫',
    '褥子': '褥紫',
    '被子': '被紫',
    '毯子': '毯紫',
    '枕头': '枕投',
    '梳子': '梳紫',
    '刷子': '刷紫',
    '院子': '院紫',
    '名字': '名紫',

    # 身体部位
    '耳朵': '耳躲',
    '眼睛': '眼精',
    '鼻子': '鼻紫',
    '舌头': '舌投',
    '脖子': '脖紫',
    '胳膊': '胳搏',
    '肚子': '肚紫',
    '肠子': '肠紫',

    # 时间词
    '早上': '早尚',
    '晚上': '晚尚',
    '夜里': '夜厘',

    # 其他高频词
    '知道': '知到',
    '觉得': '觉德',
    '认识': '认十',
    '地方': '地芳',
    '事情': '事清',
    '舒服': '舒付',
    '笑话': '笑化',

    # 形容词+的
    '好的': '好得',
    '坏的': '坏得',
    '大的': '大得',
    '小的': '小得',
    '多的': '多得',
    '少的': '少得',
    '长的': '长得',
    '短的': '短得',
    '高的': '高得',
    '低的': '低得',
    '快的': '快得',
    '慢的': '慢得',
    '新的': '新得',
    '旧的': '旧得',
    '老的': '老得',
    '年轻的': '年轻得',
    '漂亮的': '漂亮得',
    '干净的': '干净得',
    '热闹的': '热闹得',
    '安静的': '安静得',
    '快乐的': '快乐得',
    '幸福的': '幸福得',
    '聪明的': '聪明得',
    '勇敢的': '勇敢得',
    '善良的': '善良得',
    '诚实的': '诚实得',
    '勤劳的': '勤劳得',
}

SORTED_LIGHT_TONE_WORDS = sorted(LIGHT_TONE_MAP.keys(), key=len, reverse=True)

DIGITS = '零一二三四五六七八九'
UNITS = ['', '十', '百', '千']
BIG_UNITS = ['', '万', '亿', '兆']


def number_to_chinese(num_str):
    if '.' in num_str:
        parts = num_str.split('.')
        integer_part = int(parts[0]) if parts[0] else 0
        decimal_part = parts[1]
        result = int_to_chinese(integer_part) + '点'
        for digit in decimal_part:
            result += DIGITS[int(digit)]
        return result
    return int_to_chinese(int(num_str))


def int_to_chinese(num):
    if num == 0:
        return '零'
    if num >= 100000000:
        return int_to_chinese(num // 100000000) + '亿' + (int_to_chinese(num % 100000000) if num % 100000000 != 0 else '')
    if num >= 10000:
        return int_to_chinese(num // 10000) + '万' + (int_to_chinese(num % 10000) if num % 10000 != 0 else '')
    result = ''
    unit_index = 0
    while num > 0:
        digit = num % 10
        if digit != 0:
            result = DIGITS[digit] + UNITS[unit_index] + result
        elif result and not result.startswith('零'):
            result = '零' + result
        num //= 10
        unit_index += 1
    result = result.rstrip('零')
    if result.startswith('一十'):
        result = result[1:]
    return result


def convert_percentage(match):
    return '百分之' + number_to_chinese(match.group(1))


def convert_number(match):
    num_str = match.group(0)
    if len(num_str) > 10:
        return num_str
    return number_to_chinese(num_str)


def convert_light_tone(text):
    result = text
    for word in SORTED_LIGHT_TONE_WORDS:
        replacement = LIGHT_TONE_MAP[word]
        if word != replacement:
            result = result.replace(word, replacement)
    return result


def convert_numbers_in_text(text):
    result = text
    result = re.sub(r'(\d+(?:\.\d+)?)\s*%', convert_percentage, result)
    result = re.sub(r'(?<![一二三四五六七八九十百千万亿兆])\d+(?:\.\d+)?(?![一二三四五六七八九十百千万亿兆])', convert_number, result)
    return result


def convert_all(text):
    # 清理系统 artifacts（如 </parameter>、<parameter name= 等 XML 标签残留）
    result = re.sub(r'</?parameter[^>]*>', '', text)
    # 也处理不完整的标签（如 </parameter 或 <parameter name=）
    result = re.sub(r'</?parameter\s*[^>]*', '', result)
    result = convert_numbers_in_text(result)
    result = convert_light_tone(result)
    return result


def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    converted = convert_all(content)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(converted)
    return converted != content


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python convert_all.py <input.txt> [output.txt]")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path
    changed = process_file(input_path, output_path)
    status = "已转换" if changed else "无变化"
    print(f"{status}: {input_path} -> {output_path}")
