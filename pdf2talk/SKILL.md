---
name: pdf2talk
description: "PDF 转对话音频。将 PDF 书籍转为布布/一二对话访谈形式的 MP3 音频。当用户提供 PDF 文件并要求生成语音、音频、播客、有声书时激活此 skill。"
license: MIT
metadata:
  version: 0.4.0
---

# PDF 转对话音频

将 PDF 书籍自动转为「布布」（主持人）和「一二」（嘉宾）对话访谈形式的 MP3 音频。

脚本目录：`$SKILLS_PATH/pdf2talk/scripts/`

## 流程

```
PDF → 提取文本 → 分章节 → [Claude Code 对话改写] → 轻声词转换 → F5-TTS 语音合成 → MP3
```

分为三个阶段，由两个脚本 + Claude Code 协作完成：

1. **预处理**（`pdf2talk_pre.py`）：PDF 提取文本 + 分章节
2. **对话改写**（Claude Code）：读取章节内容，改写为布布/一二对话格式
3. **后处理**（`pdf2talk_post.py`）：轻声词转换 + F5-TTS 合成 + ffmpeg 合并 MP3

## 环境依赖

| 环境变量 | 说明 | 必需 |
|---------|------|------|
| `HF_ENDPOINT` | HuggingFace 镜像（国内用户设为 hf-mirror.com） | 推荐 |

| 依赖 | 说明 | 必需 |
|------|------|------|
| `python3` | 运行脚本 | 是 |
| `ffmpeg` | WAV 转 MP3 | 是 |
| `PyMuPDF` | PDF 文本提取 | 是 |
| `F5-TTS` | 语音合成（box2audio-0 venv 中已安装） | 是 |

## 输出目录结构

所有文件输出到 `/mnt/e/Project/VoiceClone/pdf2talk_output/<书名>/`：

```
pdf2talk_output/
└── 西游记（上）/
    ├── txt/                  # 提取的纯文本
    ├── chapters/             # 分章节原始文本
    ├── dialogue/             # 对话格式 md（Claude Code 生成）
    ├── converted/            # 轻声词转换后的对话
    ├── wavs/                 # 各章 WAV（支持断点续传）
    ├── 西游记（上）_full.wav  # 合并 WAV
    └── 西游记（上）.mp3       # 最终 MP3
```

## Skill 工作流程

当用户提供 PDF 文件并要求生成语音时，按以下步骤执行：

### Step 1: 预处理

#### 使用 Claude Code 智能切分

```bash
source /mnt/e/Project/VoiceClone/box2audio-0/venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com

# 1. 只提取文本
python3 $SKILLS_PATH/pdf2talk/scripts/pdf2talk_pre.py input.pdf --extract-only

# 2. 使用 Claude Code 分析文本，生成章节信息 JSON 文件
#    Claude Code 会读取 txt/ 目录下的文本文件，分析章节结构
#    生成 chapters.json 文件

# 3. 使用章节信息切分
python3 $SKILLS_PATH/pdf2talk/scripts/pdf2talk_pre.py input.pdf --chapters-json chapters.json
```

### Step 2: 对话改写（Claude Code 完成）

读取 `chapters/` 目录下每个 `chXX_raw.txt` 文件，将内容改写为布布/一二对话格式，保存到 `dialogue/` 目录，文件名为 `chXX_dialogue.md`。

**改写要求：**
- 布布是主持人，负责提问和引导话题
- 一二是嘉宾，负责讲述内容和回答问题
- 保留原文的核心信息和故事情节，不遗漏重要内容
- 对话自然流畅，像真实的访谈节目
- 每句对话控制在合理长度，不要一句话太长
- 格式：`**布布**：对话内容` / `**一二**：对话内容`，每行一句，行间空一行
- 保留原文中的关键对话和引用
- 章节开头先由布布引入话题，结尾由布布做总结或过渡
- 不要前言、序言、后记的内容，专注于正文部分
- 需要将转换后的文本作为TTS合成材料，以确保对话内容分段适合TTS的合成
- 适当添加一些对于内容的思考作为过渡语句，使对话更自然流畅
- 对轻音字使用拼音替代,例如'了'字的轻声形式改写,需要结合上下文推断是'le'还是'liǎo'，以确保语音合成的自然流畅,主要插入拼音前需要前后有空格分隔,以便于后续的轻声词转换脚本正确识别和处理

**改写时需要：**
1. 读取 `chapters/` 目录下所有 `chXX_raw.txt` 文件
2. 逐章改写为对话格式
3. 将每章对话保存为 `dialogue/chXX_dialogue.md`

### 章节信息 JSON 格式

章节信息 JSON 文件格式如下：

```json
[
  {"title": "第一章 白色的拉布拉多犬", "start_text": "很久很久以前，我就梦想着有一只属于自己的狗"},
  {"title": "第二章 梦想储蓄罐和梦想相册", "start_text": "吉娅，该起床了"}
]
```

- `title`：章节标题（应与书中实际标题一致）
- `start_text`：章节正文的起始文本（用于定位章节位置）

### Step 3: 后处理

```bash
python3 $SKILLS_PATH/pdf2talk/scripts/pdf2talk_post.py input.pdf
```

自定义语速：
```bash
python3 $SKILLS_PATH/pdf2talk/scripts/pdf2talk_post.py input.pdf --bubu-speed 0.7 --yier-speed 0.8
```

停顿控制参数：
```bash
# 调整停顿阈值（超过 0.5s 的停顿会被缩短到 0.2s）
python3 $SKILLS_PATH/pdf2talk/scripts/pdf2talk_post.py input.pdf --max-pause 0.5 --target-pause 0.2

# 调整对话行之间的停顿（默认 0.35s）
python3 $SKILLS_PATH/pdf2talk/scripts/pdf2talk_post.py input.pdf --inter-line-pause 0.4

# 禁用文本拆分（整句合成，可能产生过长停顿）
python3 $SKILLS_PATH/pdf2talk/scripts/pdf2talk_post.py input.pdf --no-split

# 禁用停顿修剪
python3 $SKILLS_PATH/pdf2talk/scripts/pdf2talk_post.py input.pdf --no-trim
```

### 轻声词转换

轻声词转换是将文本中的"们"、"的"、"什么"等词语转换为更适合 TTS 语音合成的版本。

#### 转换规则

| 原词 | 转换后 | 说明 |
|------|--------|------|
| 们 | 门 | 轻声词 |
| 的 | 得 | 轻声词 |
| 什么 | 什摸 | 轻声词 |
| 东西 | 东溪 | 轻声词 |
| 意思 | 意丝 | 轻声词 |
| 12 | 十二 | 数字转换 |

#### 手动执行轻声词转换

```bash
source /mnt/e/Project/VoiceClone/box2audio-0/venv/bin/activate

python3 -c "
import sys
sys.path.insert(0, '$SKILLS_PATH/pdf2talk/scripts')
from convert_all import convert_all as do_convert_all

# 读取原始文件
with open('input.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# 执行轻声词转换
converted = do_convert_all(text)

# 保存转换后的文件
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(converted)

print('轻声词转换完成')
"
```

#### 转换后文件位置

轻声词转换后的文件保存在 `converted/` 目录下，文件名与原始文件相同。

## 断点续传

- 已提取的 TXT 不会重复提取
- 已有的章节文件不会重复生成
- 已合成的 WAV 不会重复合成（删除 wavs/ 目录下对应文件可重新合成）

## 角色

| 角色 | 语音 | 语速 | 身份 |
|------|------|------|------|
| 布布 | bubu_self_introduction.wav | 0.6 | 主持人，提问引导 |
| 一二 | yier_self_introduction.wav | 0.7 | 嘉宾，讲述内容 |

## 对话格式示例

```markdown
**布布**：大家好，今天我们来聊聊这个有趣的故事。

**一二**：好的，这个故事非常精彩。从前有一座山...

**布布**：后来怎么样了？

**一二**：后来啊，山上来了一个猴子...
```

## 注意事项

1. 长书合成时间较长，每章约 3-7 分钟
2. 支持断点续传，中断后重新运行会跳过已完成的步骤
3. 国内用户务必设置 HF_ENDPOINT=https://hf-mirror.com
4. 停顿优化：默认启用文本拆分（按标点拆分长句）+ 停顿修剪（缩短过长静音），可解决 TTS 中"欢迎收听"后等位置停顿过长的问题
