# pdf2talk - PDF 转对话音频 Skill

将 PDF 书籍自动转为「布布」（主持人）和「一二」（嘉宾）对话访谈形式的 MP3 音频。

## 流程

```
PDF → 提取文本 → 分章节 → [Claude Code 对话改写] → 轻声词转换 → F5-TTS 语音合成 → MP3
```

## 安装

将 `pdf2talk` 目录复制到 `~/.claude/skills/` 下：

```bash
cp -r pdf2talk ~/.claude/skills/
```

## 依赖

- Python 3.10+
- ffmpeg
- PyMuPDF (`pip install pymupdf`)
- F5-TTS（需要 box2audio-0 项目）
- anthropic 或 openai（可选，用于 LLM 章节切分）

## 使用

### Step 1: 预处理

```bash
source /path/to/box2audio-0/venv/bin/activate
export HF_ENDPOINT=https://hf-mirror.com

python3 ~/.claude/skills/pdf2talk/scripts/pdf2talk_pre.py input.pdf
```

### Step 2: 对话改写

由 Claude Code 读取 `chapters/` 目录下的章节文件，改写为对话格式，保存到 `dialogue/` 目录。

### Step 3: 后处理

```bash
python3 ~/.claude/skills/pdf2talk/scripts/pdf2talk_post.py input.pdf
```

## 输出

所有文件输出到 `/mnt/e/Project/VoiceClone/pdf2talk_output/<书名>/`：

```
pdf2talk_output/
└── 书名/
    ├── txt/           # 提取的纯文本
    ├── chapters/      # 分章节原始文本
    ├── dialogue/      # 对话格式 md（Claude Code 生成）
    ├── converted/     # 轻声词转换后的对话
    ├── wavs/          # 各章 WAV（支持断点续传）
    └── 书名.mp3       # 最终 MP3
```

## 角色

| 角色 | 语速 | 身份 |
|------|------|------|
| 布布 | 0.6 | 主持人，提问引导 |
| 一二 | 0.7 | 嘉宾，讲述内容 |

## 许可证

MIT
