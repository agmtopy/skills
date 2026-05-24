#!/usr/bin/env python3
"""PDF 对话音频 — 后处理阶段。

流程:
  1. 解析对话 markdown
  2. 轻声词 + 数字转换
  3. F5-TTS 语音合成（支持断点续传）
  4. ffmpeg 合并为 MP3

前置条件:
  - chapters/ 目录下有章节文件（由 pdf2talk_pre.py 生成）
  - dialogue/ 目录下有对话 md 文件（由 Claude Code 改写生成）

用法:
    python3 pdf2talk_post.py <input.pdf> [--output-dir DIR] [--bubu-speed N] [--yier-speed N]
"""

import argparse
import os
import re
import subprocess
import sys
import time

import numpy as np
import soundfile as sf

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOX2AUDIO_DIR = "/mnt/e/Project/VoiceClone/box2audio-0"
ASSETS_DIR = os.path.join(BOX2AUDIO_DIR, "assets", "audio")
PROJECT_DIR = "/mnt/e/Project/VoiceClone"
OUTPUT_BASE = os.path.join(PROJECT_DIR, "pdf2talk_output")

# 角色音色映射
VOICE_MAP = {
    "布布": {
        "ref_audio": os.path.join(ASSETS_DIR, "bubu_self_introduction.wav"),
        "ref_text": "大家好，我叫布布，上个视频，第二宝做了自我介绍，我也给大家做个自我介绍吧。",
        "speed": 0.6,
    },
    "一二": {
        "ref_audio": os.path.join(ASSETS_DIR, "yier_self_introduction.wav"),
        "ref_text": "大家好，我叫一二。听说大家都在问我，为什么叫一二？下面我来介绍一下我的来历吧。",
        "speed": 0.7,
    },
}

# ==================== 对话解析 ====================

def parse_dialogue(md_text: str) -> list[tuple[str, str]]:
    lines = []
    for line in md_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\*\*(.+?)\*\*[：:]\s*(.+)$", line)
        if m:
            role, text = m.group(1), m.group(2)
            lines.append((role, text))
    return lines


# ==================== 轻声词转换 ====================

sys.path.insert(0, BASE_DIR)
from convert_all import convert_all as do_convert_all


def convert_dialogue(text: str) -> str:
    result = do_convert_all(text)
    print("[轻声词转换] 完成")
    return result


# ==================== TTS 合成 ====================

def patch_pinyin():
    from f5_tts.model.utils import convert_char_to_pinyin as _orig_convert
    from f5_tts.model.utils import get_tokenizer
    from importlib.resources import files as pkg_files

    vocab_file = str(pkg_files("f5_tts").joinpath("infer/examples/vocab.txt"))
    vocab_char_map, _ = get_tokenizer(vocab_file, "custom")

    def _patched_convert(text_list, polyphone=True):
        result = _orig_convert(text_list, polyphone=polyphone)
        fixed_lists = []
        for char_list in result:
            fixed = []
            for p in char_list:
                if p in vocab_char_map:
                    fixed.append(p)
                    continue
                if p.isalpha() and len(p) > 1:
                    for tone in ["5", "4", "3", "2", "1"]:
                        candidate = p + tone
                        if candidate in vocab_char_map:
                            fixed.append(candidate)
                            break
                    else:
                        fixed.append(p)
                else:
                    fixed.append(p)
            fixed_lists.append(fixed)
        return fixed_lists

    import f5_tts.model.utils as _utils_mod
    import f5_tts.infer.utils_infer as _infer_mod
    _utils_mod.convert_char_to_pinyin = _patched_convert
    _infer_mod.convert_char_to_pinyin = _patched_convert
    print("[TTS] pinyin patch applied")


_DIGIT_TO_CHINESE = str.maketrans("0123456789", "零一二三四五六七八九")


# ==================== 停顿优化 ====================

def trim_long_pauses(audio: np.ndarray, sr: int = 24000,
                     max_pause_sec: float = 0.4,
                     target_pause_sec: float = 0.15,
                     threshold_db: float = -30) -> np.ndarray:
    """缩短 TTS 音频中过长的停顿。

    检测音频中的静音区域，将超过 max_pause_sec 的停顿缩短至 target_pause_sec。
    """
    if len(audio) < sr * 0.05:
        return audio

    peak = np.max(np.abs(audio))
    if peak < 1e-10:
        return audio
    threshold = 10 ** (threshold_db / 20) * peak

    frame_len = int(sr * 0.02)
    hop_len = int(sr * 0.01)
    n_frames = max(1, (len(audio) - frame_len) // hop_len + 1)

    energy = np.zeros(n_frames)
    for i in range(n_frames):
        s = i * hop_len
        e = min(s + frame_len, len(audio))
        energy[i] = np.sqrt(np.mean(audio[s:e] ** 2))

    is_silent = energy < threshold

    regions = []
    in_sil = False
    sil_start = 0
    for i in range(n_frames):
        if is_silent[i] and not in_sil:
            sil_start = i * hop_len
            in_sil = True
        elif not is_silent[i] and in_sil:
            regions.append((sil_start, i * hop_len))
            in_sil = False
    if in_sil:
        regions.append((sil_start, len(audio)))

    max_samples = int(max_pause_sec * sr)
    target_samples = int(target_pause_sec * sr)

    parts = []
    prev_end = 0

    for sil_start, sil_end in regions:
        if sil_end - sil_start > max_samples:
            parts.append(audio[prev_end:sil_start])
            half = target_samples // 2
            if half > 0 and sil_start + half <= sil_end - half:
                fade_out = np.linspace(1.0, 0.0, half)
                fade_in = np.linspace(0.0, 1.0, half)
                parts.append(audio[sil_start:sil_start + half] * fade_out)
                parts.append(audio[sil_end - half:sil_end] * fade_in)
            prev_end = sil_end

    parts.append(audio[prev_end:])

    result = np.concatenate([p for p in parts if len(p) > 0])
    return result


def split_text_for_tts(text: str) -> list[tuple[str, float]]:
    """按标点拆分文本为子句，返回 (文本, 段后停顿秒数) 列表。

    拆分规则：
    - 。！？后停顿 0.20-0.25s
    - ，；后停顿 0.10-0.12s
    - 不拆分过短的片段（<5字符合并到前一段）
    """
    PAUSE_MAP = {
        '。': 0.20, '！': 0.25, '？': 0.25,
        '，': 0.10, '；': 0.12, '、': 0.06,
    }

    segments = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in PAUSE_MAP and len(buf.strip()) >= 5:
            segments.append((buf.strip(), PAUSE_MAP[ch]))
            buf = ""

    if buf.strip():
        if segments:
            segments.append((buf.strip(), 0.0))
        else:
            return [(text, 0.0)]

    merged = []
    for seg_text, seg_pause in segments:
        if merged and len(seg_text) < 5:
            prev_text, _ = merged[-1]
            merged[-1] = (prev_text + seg_text, seg_pause)
        else:
            merged.append((seg_text, seg_pause))

    return merged if len(merged) > 1 else [(text, 0.0)]


def synthesize_chapter(dialogue: list[tuple[str, str]], f5tts,
                       max_pause_sec: float = 0.4,
                       target_pause_sec: float = 0.15,
                       inter_line_pause_sec: float = 0.35,
                       split_text: bool = True,
                       trim_enabled: bool = True) -> np.ndarray:
    inter_line_pause = np.zeros(int(24000 * inter_line_pause_sec), dtype=np.float32)
    all_audio = []
    total = len(dialogue)

    for i, (role, text) in enumerate(dialogue):
        voice = VOICE_MAP.get(role)
        if not voice:
            print(f"    [{i+1}/{total}] 跳过未知角色 '{role}'")
            continue

        speed = voice["speed"]
        text = text.translate(_DIGIT_TO_CHINESE)
        print(f"    [{i+1}/{total}] {role}(speed={speed}): {text[:40]}{'...' if len(text) > 40 else ''}")

        if split_text:
            sub_sentences = split_text_for_tts(text)
        else:
            sub_sentences = [(text, 0.0)]

        line_audio = []
        for sub_text, pause_sec in sub_sentences:
            wav, sr, _ = f5tts.infer(
                ref_file=voice["ref_audio"],
                ref_text=voice["ref_text"],
                gen_text=sub_text,
                speed=speed,
                nfe_step=32,
                cfg_strength=2.0,
            )

            if wav is not None and len(wav) > 0:
                if trim_enabled:
                    wav = trim_long_pauses(wav, sr, max_pause_sec, target_pause_sec)
                if line_audio:
                    pause_samples = int(24000 * pause_sec)
                    if pause_samples > 0:
                        line_audio.append(np.zeros(pause_samples, dtype=np.float32))
                line_audio.append(wav)

        if line_audio:
            combined_line = np.concatenate(line_audio)
            if all_audio:
                all_audio.append(inter_line_pause)
            all_audio.append(combined_line)

    if not all_audio:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(all_audio)


# ==================== 主流程 ====================

def main():
    parser = argparse.ArgumentParser(description="PDF 对话音频 — 后处理（对话→TTS→MP3）")
    parser.add_argument("input_pdf", help="输入 PDF 文件路径（用于确定输出目录名）")
    parser.add_argument("--bubu-speed", type=float, default=0.6, help="布布语速（默认 0.6）")
    parser.add_argument("--yier-speed", type=float, default=0.7, help="一二语速（默认 0.7）")
    parser.add_argument("--max-pause", type=float, default=0.4, help="超过此时长的停顿将被缩短（秒，默认 0.4）")
    parser.add_argument("--target-pause", type=float, default=0.15, help="缩短后的目标停顿时长（秒，默认 0.15）")
    parser.add_argument("--inter-line-pause", type=float, default=0.35, help="对话行之间的停顿时长（秒，默认 0.35）")
    parser.add_argument("--no-split", action="store_true", help="禁用文本拆分（整句合成，可能产生过长停顿）")
    parser.add_argument("--no-trim", action="store_true", help="禁用停顿修剪")
    parser.add_argument("--output-dir", default=OUTPUT_BASE, help=f"输出目录（默认 {OUTPUT_BASE}）")
    parser.add_argument("output_mp3", nargs="?", help="输出 MP3 路径（默认在项目输出目录）")
    args = parser.parse_args()

    VOICE_MAP["布布"]["speed"] = args.bubu_speed
    VOICE_MAP["一二"]["speed"] = args.yier_speed

    base_name = os.path.splitext(os.path.basename(args.input_pdf))[0]
    output_dir = os.path.join(args.output_dir, base_name)
    chapters_dir = os.path.join(output_dir, "chapters")
    dialogue_dir = os.path.join(output_dir, "dialogue")
    converted_dir = os.path.join(output_dir, "converted")
    wavs_dir = os.path.join(output_dir, "wavs")
    for d in [converted_dir, wavs_dir]:
        os.makedirs(d, exist_ok=True)

    output_mp3 = args.output_mp3 or os.path.join(output_dir, base_name + ".mp3")

    # 前置检查
    chapter_files = sorted([f for f in os.listdir(chapters_dir) if f.endswith('_raw.txt')]) if os.path.isdir(chapters_dir) else []
    dialogue_files = sorted([f for f in os.listdir(dialogue_dir) if f.endswith('.md')]) if os.path.isdir(dialogue_dir) else []

    if not chapter_files:
        print(f"错误: 未找到章节文件，请先运行 pdf2talk_pre.py")
        sys.exit(1)
    if not dialogue_files:
        print(f"错误: 未找到对话文件，请先将章节改写为对话格式并保存到 {dialogue_dir}")
        sys.exit(1)
    if len(dialogue_files) < len(chapter_files):
        print(f"警告: 对话文件 ({len(dialogue_files)}) 少于章节文件 ({len(chapter_files)})")

    print(f"\n输出目录: {output_dir}")
    print(f"对话文件: {len(dialogue_files)} 个")

    # ====== 加载对话 ======
    dialogue_chapters = []
    for mf in dialogue_files:
        with open(os.path.join(dialogue_dir, mf), 'r', encoding='utf-8') as f:
            dialogue_chapters.append((mf, f.read()))

    # ====== 轻声词转换 ======
    print("\n" + "=" * 60)
    print("Step 1: 轻声词 + 数字转换")
    print("=" * 60)
    converted_chapters = []
    for title, dialogue in dialogue_chapters:
        converted = convert_dialogue(dialogue)
        converted_chapters.append((title, converted))
        # 保存转换后的文件
        converted_path = os.path.join(converted_dir, title)
        with open(converted_path, 'w', encoding='utf-8') as f:
            f.write(converted)
        print(f"  保存: {title}")

    # ====== TTS 合成 ======
    print("\n" + "=" * 60)
    print("Step 2: 语音合成")
    print("=" * 60)

    hf_endpoint = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_ENDPOINT", hf_endpoint)
    patch_pinyin()

    from f5_tts.api import F5TTS
    f5tts = F5TTS()

    all_chapter_audio = []
    chapter_pause = np.zeros(int(24000 * 1.5), dtype=np.float32)
    total_start = time.time()

    total = len(converted_chapters)
    for i, (title, dialogue_text) in enumerate(converted_chapters):
        wav_path = os.path.join(wavs_dir, f"ch{i+1:02d}.wav")

        if os.path.exists(wav_path):
            print(f"\n  [{i+1}/{total}] 已有 WAV，跳过: {title}")
            audio, sr = sf.read(wav_path)
            if len(audio) > 0:
                if all_chapter_audio:
                    all_chapter_audio.append(chapter_pause)
                all_chapter_audio.append(audio.astype(np.float32))
            continue

        print(f"\n  [{i+1}/{total}] 合成: {title}")
        dialogue = parse_dialogue(dialogue_text)
        if not dialogue:
            print(f"    未解析到对话，跳过")
            continue

        chapter_start = time.time()
        audio = synthesize_chapter(
            dialogue, f5tts,
            max_pause_sec=args.max_pause,
            target_pause_sec=args.target_pause,
            inter_line_pause_sec=args.inter_line_pause,
            split_text=not args.no_split,
            trim_enabled=not args.no_trim,
        )
        if len(audio) > 0:
            sf.write(wav_path, audio, 24000)
            if all_chapter_audio:
                all_chapter_audio.append(chapter_pause)
            all_chapter_audio.append(audio)
            duration = len(audio) / 24000
            elapsed = time.time() - chapter_start
            print(f"    完成: {duration:.1f}s (耗时 {elapsed:.0f}s)")

    total_elapsed = time.time() - total_start
    print(f"\n  TTS 总耗时: {total_elapsed/60:.1f} 分钟")

    if not all_chapter_audio:
        print("没有生成任何音频！")
        sys.exit(1)

    # ====== 合并输出 ======
    print("\n" + "=" * 60)
    print("Step 3: 合并输出")
    print("=" * 60)

    final = np.concatenate(all_chapter_audio)
    final_wav = os.path.join(output_dir, base_name + "_full.wav")
    sf.write(final_wav, final, 24000)
    total_duration = len(final) / 24000
    print(f"  WAV: {final_wav} ({total_duration:.1f}s / {total_duration/60:.1f}min)")

    subprocess.run([
        "ffmpeg", "-y", "-i", final_wav,
        "-codec:a", "libmp3lame", "-q:a", "2", output_mp3
    ], check=True, capture_output=True)
    print(f"  MP3: {output_mp3}")
    print(f"\n全部完成！总时长: {total_duration:.1f}s ({total_duration/60:.1f}min)")
    print(f"输出目录: {output_dir}")


if __name__ == "__main__":
    main()
