# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 **Claude Code Skills 单体仓库**，包含可复用的 Claude Code 技能（skills）。每个 skill 是一个独立目录，遵循 `SKILL.md` + `scripts/` 的结构约定。

当前包含的 skills：

| Skill | 用途 | 核心依赖 |
|-------|------|----------|
| `pdf2talk` | PDF 转布布/一二对话音频 MP3 | PyMuPDF, F5-TTS, ffmpeg |
| `weather-compare` | 旅行天气多源对比查询 | Open-Meteo API, BeautifulSoup |

## 仓库结构

```
skills/
├── pdf2talk/
│   ├── SKILL.md            # Skill 元数据与使用说明（YAML frontmatter + 文档）
│   ├── README.md           # 安装与快速上手
│   └── scripts/
│       ├── pdf2talk_pre.py   # 预处理：PDF→TXT→分章节
│       ├── pdf2talk_post.py  # 后处理：对话解析→TTS→MP3
│       ├── pdf2txt.py        # PDF 文本提取（独立工具）
│       └── convert_all.py    # 轻声词+数字转换（TTS 优化）
│
└── weather-compare/
    └── weather-compare-skill/
        ├── SKILL.md          # Skill 元数据与使用说明
        ├── scripts/
        │   └── weather_compare.py  # 天气查询主脚本
        └── evals/
            └── evals.json          # Skill 评测用例
```

## Skill 开发约定

### SKILL.md 格式

每个 skill 必须有 `SKILL.md`，使用 YAML frontmatter：

```yaml
---
name: skill-name
description: "一句话描述，用于 Claude Code 触发匹配"
---
```

### 脚本约定

- 所有 Python 脚本使用 `#!/usr/bin/env python3` shebang
- 脚本应可独立运行（`python3 script.py`），不依赖 skill 框架
- 环境变量通过 `os.environ` 读取，不硬编码密钥

### 安装方式

Skill 安装到 `~/.claude/skills/` 下：

```bash
cp -r pdf2talk ~/.claude/skills/
```

## 关键路径与配置

### pdf2talk

- 音色文件位于 `/mnt/e/Project/VoiceClone/box2audio-0/assets/audio/`
- 输出目录固定为 `/mnt/e/Project/VoiceClone/pdf2talk_output/<书名>/`
- 运行前需激活 box2audio venv：`source /mnt/e/Project/VoiceClone/box2audio-0/venv/bin/activate`
- 国内环境设置 `HF_ENDPOINT=https://hf-mirror.com`
- 章节切分支持两种方式：
  - 使用 `--extract-only` 提取文本，然后由 Claude Code 分析章节结构并生成 `chapters.json`
  - 使用 `--chapters-json chapters.json` 参数切分章节
  - 使用 `--no-llm` 参数使用硬切分（备用方案）
- 轻声词转换：将"们"、"的"、"什么"等词语转换为更适合 TTS 语音合成的版本
- 停顿优化：默认启用文本拆分（按标点拆分长句）+ 停顿修剪（缩短过长静音），可通过 `--no-split` / `--no-trim` 禁用

### weather-compare

- 数据源：Open-Meteo API（免费，无需 API key）
- 官方数据抓取需要 BeautifulSoup（脚本会自动尝试安装）
- 预设城市数据库硬编码在 `weather_compare.py` 的 `POPULAR_CITIES` 字典中
- 最大预报范围：16 天

## 开发命令

```bash
# pdf2talk - 预处理（PDF→TXT→分章节）
source /mnt/e/Project/VoiceClone/box2audio-0/venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com
python3 pdf2talk/scripts/pdf2talk_pre.py input.pdf

# pdf2talk - 后处理（对话→TTS→MP3），需先完成对话改写
python3 pdf2talk/scripts/pdf2talk_post.py input.pdf

# pdf2talk - 单步调试
python3 pdf2talk/scripts/pdf2txt.py input.pdf output.txt
python3 pdf2talk/scripts/convert_all.py input.md output.md

# weather-compare - 查询天气
python3 weather-compare/weather-compare-skill/scripts/weather_compare.py --start 05-20 --end 05-25 --cities '["北京","上海"]'
```

## .gitignore 说明

以下文件被排除在版本控制外：
- `**/test_*.py`, `**/verify_*.py` — 测试和验证脚本
- `**/*-workspace/` — 迭代工作区
- `**/REPAIR_SUMMARY.md` — 修复记录
- `__pycache__/`, `*.pyc` — Python 缓存
