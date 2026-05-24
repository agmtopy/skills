#!/usr/bin/env python3
"""按章节边界切分 raw 文本文件为小段。

用法:
    python3 split_segments.py <input_raw.txt> [output_dir]

在每个「第X章」标记处切分，每段包含一个完整章节。
前言的章节标题行会被跳过（只切分正文中的章节标记）。
"""

import os, re, sys

CHAPTER_PAT = re.compile(r'^第[一二三四五六七八九十百千]+章')


def split_raw(input_path, output_dir="segments"):
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.basename(input_path)
    match = re.match(r'ch(\d+)', base)
    prefix = match.group(1) if match else "00"

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find all chapter boundaries
    boundaries = []
    toc_started = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if CHAPTER_PAT.match(stripped):
            # Skip TOC entries (chapters in table of contents before first story)
            # A real chapter start has substantial text after it, TOC entries don't
            if not toc_started and i > 0:
                # Check if this is near the beginning (likely TOC)
                # TOC entries: short lines with just chapter names, close together
                pass
            boundaries.append((i, stripped))
        # Detect when TOC ends and actual content begins
        if not toc_started and len(stripped) > 80 and not stripped.startswith('童话') and not stripped.startswith('前言'):
            toc_started = True

    if len(boundaries) <= 1:
        print(f"  {base}: only {len(boundaries)} chapter markers, no split needed")
        return []

    # The first few chapter markers in the file are from the TOC.
    # Skip TOC entries: collect boundaries that appear twice (TOC + actual)
    # The actual chapter starts are the second occurrence of each chapter title.

    # Build title -> [positions] map
    title_positions = {}
    for pos, title in boundaries:
        if title not in title_positions:
            title_positions[title] = []
        title_positions[title].append(pos)

    # For titles that appear twice, use the second occurrence (actual content)
    # For titles that appear once, use it if it's after content has started
    actual_boundaries = []
    for title, positions in title_positions.items():
        if len(positions) >= 2:
            # Use the second occurrence (after TOC)
            actual_boundaries.append((positions[1], title))
        elif positions[0] > 100:  # Single occurrence, far from start - likely real
            actual_boundaries.append((positions[0], title))
        # else: single occurrence near start, likely TOC-only, skip

    actual_boundaries.sort()

    if len(actual_boundaries) <= 1:
        print(f"  {base}: only {len(actual_boundaries)} actual chapters after dedup, skipping")
        return []

    # Split at chapter boundaries
    seg_files = []
    for idx in range(len(actual_boundaries)):
        start_line = actual_boundaries[idx][0]
        title = actual_boundaries[idx][1]
        end_line = actual_boundaries[idx + 1][0] if idx + 1 < len(actual_boundaries) else len(lines)

        seg_lines = lines[start_line:end_line]
        seg_name = f"ch{prefix}_sec{idx + 1:02d}_raw.txt"
        seg_path = os.path.join(output_dir, seg_name)
        with open(seg_path, 'w', encoding='utf-8') as f:
            f.writelines(seg_lines)
        seg_files.append((seg_name, len(seg_lines), title))
        print(f"  {seg_name}: {len(seg_lines)} lines, {sum(len(l) for l in seg_lines)} bytes → {title}")

    return seg_files


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'segments'
    split_raw(input_path, output_dir)
