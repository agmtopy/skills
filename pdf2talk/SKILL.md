---
name: pdf2talk
description: "PDF 转对话音频。将 PDF 书籍转为布布/一二对话访谈形式的 MP3 音频。当用户提供 PDF 文件并要求生成语音、音频、播客、有声书时激活此 skill。"
license: MIT
metadata:
  version: 0.6.0
---

# PDF 转对话音频

将 PDF 书籍自动转为「布布」（主持人）和「一二」（嘉宾）对话访谈形式的 MP3 音频。

脚本目录：`$SKILLS_PATH/pdf2talk/scripts/`

## 流程

```
PDF → 提取文本 → 分章节 → [按章节边界再切分] → [逐段对话改写] → 轻声词转换 → F5-TTS 语音合成 → MP3
```

分为三个阶段，由两个脚本 + Claude Code 协作完成：

1. **预处理**（`pdf2talk_pre.py`）：PDF 提取文本 + 分章节
2. **对话改写**（Claude Code）：逐段改写为布布/一二对话格式
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
    ├── segments/             # 按章节边界二次切分的小段（每个 ≤100 行原文）
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

#### 核心原则：小段处理，逐段转换

**背景**：预处理产生的 `chXX_raw.txt` 文件可能非常大（96KB+），单个 Agent 无法可靠处理。Agent 会倾向于只读取开头然后敷衍总结剩余内容。**必须先将大文件按章节边界切分为小段，再逐段交给 Agent 转换。**

#### 2a: 检查并切分大文件

```bash
# 对每个 raw 文件，检查它包含多少个章节标记
for f in chapters/ch*_raw.txt; do
  count=$(grep -c '第.*章' "$f" || true)
  size=$(wc -c < "$f")
  echo "$(basename $f): ${size}B, ${count} 个章节标记"
done

# 如果任何文件超过 40KB 或包含超过 2 个章节标记，
# 使用 Python 脚本按章节边界进行切分
python3 $SKILLS_PATH/pdf2talk/scripts/split_segments.py chapters/ch01_raw.txt segments/
```

切分规则：
- 在每个「第X章」标记处切分
- 每段包含一个完整章节
- 命名为 `ch01_sec01_raw.txt`, `ch01_sec02_raw.txt` 等

#### 2b: 逐段并行转换

**对每个 segment 文件，启动一个独立 Agent**，每个 Agent 处理一个小段（通常 150-400 行，12-30KB）。

Agent 提示词模板：

```
将以下章节文本改写为布布/一二对话格式：

源文件: {segment_path}
输出: {dialogue_path}

要求：
- 这是 {书名} 的第 {X} 部分，共 {N} 部分
- 将原文**完整**改写为对话，不要跳过或总结
- 格式: **布布**：内容 / **一二**：内容，每行一句，行间空一行
- 布布提问引导，一二讲述内容
```

**关键要求**：
- 每个 Agent 只处理 **一个小段**（≤400行原文），确保 Agent 能完整读取和覆盖
- **严禁总结**：不要在任何位置出现"我们快速过一下"、"简单总结"、"这里就不详细讲了"等跳过内容的表述
- 每个情节、每段对话、每个道理都要转换成实际的布布/一二对话

#### 2c: 合并同一原始文件的小段

转换完成后，将属于同一 `chXX_raw.txt` 的所有 segment 对话文件**按顺序拼接**，保存为 `dialogue/chXX_dialogue.md`。

```bash
# 合并 ch01 的所有 segment 对话
cat segments/dialogue/ch01_sec*.md > dialogue/ch01_dialogue.md
```

#### 2d: 改写质量要求

- 布布是主持人，负责提问和引导话题
- 一二是嘉宾，负责讲述内容和回答问题
- **一句话都不能总结跳过**：原文中每个情节、对话、道理都要在对话中展开
- 对话自然流畅，像真实的访谈节目
- 每句对话控制在合理长度，不要一句话太长
- 格式：`**布布**：对话内容` / `**一二**：对话内容`，每行一句，行间空一行
- 保留原文中的关键对话和引用
- 章节开头先由布布引入话题，结尾由布布做总结或过渡
- 不要前言、序言、后记的内容，专注于正文部分
- 适当添加一些对于内容的思考作为过渡语句，使对话更自然流畅

#### 2e: 改写后验证

```bash
# 对比原文和对话的行数
raw_lines=$(wc -l < chapters/ch01_raw.txt)
dia_lines=$(wc -l < dialogue/ch01_dialogue.md)
echo "原文: ${raw_lines} 行 → 对话: ${dia_lines} 行"

# 检查对话中是否遗漏章节（原文有5章，对话至少应有5段对应内容）
raw_chapters=$(grep -c '第.*章' chapters/ch01_raw.txt)
echo "原文章节数: ${raw_chapters}"

# 检查是否有偷懒总结的迹象
echo "对话最后20行:"
tail -20 dialogue/ch01_dialogue.md
```

如果对话最后20行出现了"总结一下"、"快速过一遍"、"这里就不详细讲了"等词汇，说明 Agent 在敷衍，需要重新生成。

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
- 已合成的 WAV 不会重复合成（删除 wavs/ 目录下对应文件可重新生成）

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
5. **内容完整性是第一优先级**：大文件必须先切分为小段再转换，严禁单个 Agent 处理超过 30KB 的原文
6. **严禁总结跳过**：Agent 提示词中必须明确禁止"我们快速过一下"、"简单总结"等偷懒行为
