#!/usr/bin/env python3
"""PDF 对话音频 — 预处理阶段。

流程:
  1. PDF 提取文本
  2. 使用 LLM 模型智能切分章节（通过 Claude Code 会话）

用法:
    python3 pdf2talk_pre.py <input.pdf> [--output-dir DIR] [--extract-only]

输出:
    <output_dir>/<书名>/txt/       — 提取的纯文本
    <output_dir>/<书名>/chapters/  — 分章节原始文本

说明:
    默认模式会输出 JSON 格式的章节信息，供 Claude Code 解析后切分
    使用 --extract-only 只提取文本，不切分章节
"""

import argparse
import json
import os
import re
import sys

import fitz  # PyMuPDF

# ==================== 路径配置 ====================
PROJECT_DIR = "/mnt/e/Project/VoiceClone"
OUTPUT_BASE = os.path.join(PROJECT_DIR, "pdf2talk_output")


# ==================== Step 1: PDF → TXT ====================

def pdf_to_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text.strip())
    doc.close()
    content = "\n\n".join(pages)
    print(f"[Step 1] 提取 {len(pages)} 页，共 {len(content)} 字")
    return content


# ==================== Step 2: 分章节 ====================

def get_chapter_info_for_llm(text: str) -> str:
    """获取供 LLM 分析的章节信息，返回 JSON 字符串"""
    # 如果文本太长，只取前面部分给 LLM 分析章节结构
    max_sample_len = 15000
    sample_text = text[:max_sample_len] if len(text) > max_sample_len else text

    return json.dumps({
        "task": "请分析书籍文本，识别出所有章节的标题和起始位置",
        "requirements": [
            "只识别正文章节，忽略目录、版权页、前言、附录等非正文内容",
            "返回章节标题列表",
            "每个章节标题应该是书中实际使用的标题文本（精确匹配）"
        ],
        "sample_text": sample_text
    }, ensure_ascii=False, indent=2)


def split_chapters_with_chapter_list(text: str, chapters_info: list[dict], target_duration_minutes: int = 20) -> list[tuple[str, str]]:
    """根据 Claude Code 返回的章节信息切分文本，返回 [(章节标题, 章节内容), ...]

    Args:
        text: 原始文本
        chapters_info: 章节信息列表
        target_duration_minutes: 目标时长（分钟），默认20分钟
    """

    if not chapters_info:
        print("[Step 2] 章节信息为空")
        return []

    # 首先找到每个章节标题在文本中的位置
    chapter_positions = []
    for ch_info in chapters_info:
        title = ch_info["title"]
        start_text = ch_info.get("start_text", "")

        # 查找章节起始位置
        pos = -1
        if start_text:
            # 先尝试精确匹配
            pos = text.find(start_text)
            if pos == -1:
                # 尝试模糊匹配（前20个字符）
                for i in range(len(text) - 20):
                    if text[i:i+20] == start_text[:20]:
                        pos = i
                        break

        if pos != -1:
            chapter_positions.append({"title": title, "pos": pos})

    # 按位置排序
    chapter_positions.sort(key=lambda x: x["pos"])

    # 计算目标字符数
    # 基于之前的数据：108.4分钟音频 = 约181920字符原始文本
    # 所以每分钟约1678字符，每20分钟约33560字符
    target_chars = target_duration_minutes * 1678  # 约1678字符/分钟

    # 根据位置和目标时长切分文本
    chapters = []
    current_start = 0
    current_title_idx = 0

    while current_start < len(text):
        # 计算当前段的结束位置
        # 优先在章节标题处切分，如果章节标题距离太远，则按目标字符数切分
        end = min(current_start + target_chars, len(text))

        # 查找最近的章节标题
        next_chapter_pos = None
        for i in range(current_title_idx, len(chapter_positions)):
            if chapter_positions[i]["pos"] > current_start:
                # 如果章节标题在目标范围内，使用它作为切分点
                if chapter_positions[i]["pos"] <= end:
                    next_chapter_pos = chapter_positions[i]
                    current_title_idx = i + 1
                else:
                    # 章节标题超出范围，但不要切分到重要内容中间
                    # 检查是否有重要内容（如"第X章"、"布布"、"一二"等）
                    break
                break

        if next_chapter_pos and next_chapter_pos["pos"] - current_start > target_chars * 0.5:
            # 如果找到合适的章节标题，使用它
            end = next_chapter_pos["pos"]
            title = next_chapter_pos["title"]
        else:
            # 没有找到合适的章节标题，按目标字符数切分
            # 但要确保不在句子中间切分
            # 寻找最近的句号、感叹号、问号等
            search_range = min(500, len(text) - end)
            for offset in range(search_range):
                if end + offset < len(text) and text[end + offset] in '。！？\n':
                    end = end + offset + 1
                    break

            # 生成标题
            title = f"第{len(chapters) + 1}部分"

        # 提取内容
        content = text[current_start:end].strip()
        if content:
            chapters.append((title, content))

        current_start = end

    print(f"[Step 2] 按{target_duration_minutes}分钟时长切分为 {len(chapters)} 个部分")
    return chapters


# ==================== 主流程 ====================

def main():
    parser = argparse.ArgumentParser(description="PDF 对话音频 — 预处理（PDF→TXT→分章节）")
    parser.add_argument("input_pdf", help="输入 PDF 文件路径")
    parser.add_argument("--output-dir", default=OUTPUT_BASE, help=f"输出目录（默认 {OUTPUT_BASE}）")
    parser.add_argument("--extract-only", action="store_true", help="只提取文本，不切分章节")
    parser.add_argument("--chapters-json", help="章节信息 JSON 文件路径（由 Claude Code 生成）")
    parser.add_argument("--target-duration", type=int, default=20, help="目标时长（分钟），默认20分钟")
    args = parser.parse_args()

    pdf_path = args.input_pdf
    if not os.path.isfile(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = os.path.join(args.output_dir, base_name)
    txt_dir = os.path.join(output_dir, "txt")
    chapters_dir = os.path.join(output_dir, "chapters")
    for d in [txt_dir, chapters_dir]:
        os.makedirs(d, exist_ok=True)

    print(f"\n输入: {pdf_path}")
    print(f"输出目录: {output_dir}")
    print(f"目标时长: {args.target_duration} 分钟/部分")

    # Step 1
    print("\n" + "=" * 60)
    print("Step 1: PDF 提取文本")
    print("=" * 60)
    txt_path = os.path.join(txt_dir, base_name + ".txt")
    if os.path.exists(txt_path):
        print(f"  已有 TXT，跳过: {txt_path}")
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = pdf_to_text(pdf_path)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  保存到: {txt_path}")

    # 如果只是提取文本，到此结束
    if args.extract_only:
        print(f"\n文本提取完成！")
        print(f"文本文件: {txt_path}")
        print(f"\n下一步：请使用 Claude Code 分析章节结构，然后运行：")
        print(f"  python3 {sys.argv[0]} {pdf_path} --chapters-json <章节信息.json>")
        return

    # Step 2: 分章节
    print("\n" + "=" * 60)
    print("Step 2: 分章节")
    print("=" * 60)

    # 如果提供了章节信息 JSON 文件
    if args.chapters_json:
        if not os.path.isfile(args.chapters_json):
            print(f"章节信息文件不存在: {args.chapters_json}")
            sys.exit(1)
        with open(args.chapters_json, 'r', encoding='utf-8') as f:
            chapters_info = json.load(f)
        chapters = split_chapters_with_chapter_list(text, chapters_info, args.target_duration)
    else:
        # 默认使用硬切分
        print("  使用硬切分模式（如需 LLM 切分，请先运行 --extract-only）")
        # 由于已删除硬切分函数，这里提示用户使用 --chapters-json
        print("  错误：请提供 --chapters-json 参数")
        sys.exit(1)

    for i, (title, content) in enumerate(chapters):
        ch_path = os.path.join(chapters_dir, f"ch{i+1:02d}_raw.txt")
        with open(ch_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  保存: ch{i+1:02d}_raw.txt — {title}")

    print(f"\n预处理完成！")
    print(f"章节文件: {chapters_dir}")
    print(f"\n下一步：请将章节内容改写为对话格式，保存到 {os.path.join(output_dir, 'dialogue/')}")


if __name__ == "__main__":
    main()
