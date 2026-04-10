<p align="center">
  <h1 align="center">QSense</h1>
  <p align="center">
    <strong>Multimodal Perception Atomic Skill</strong><br>
    多模态感知原子技能
  </p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> ·
    <a href="#usage-examples">Examples</a> ·
    <a href="#available-models">Models</a> ·
    <a href="#ai-agent-integration">Agent Integration</a>
  </p>
</p>

---

One command. Files in, text out.

一条命令，让模型「看」图像、「听」音频、「看」视频，返回文字。

QSense is not an app — it's the lowest-level perception primitive for skills, agents, and scripts. It does one thing: **send multimodal input to an LLM, get text back.** Video splitting, audio segmentation, batch processing, result parsing — all belong to the caller.

QSense 不是应用，是给上层 skill、agent、脚本调用的最底层感知能力。它只做一件事：**把多模态输入送给模型，拿回文字结果。**

```
┌──────────────────────────────────────────────────────┐
│  Skills / Agents / Scripts                           │
│  video review, meeting notes, OCR pipeline, ...      │
├──────────────────────────────────────────────────────┤
│  QSense  ← you are here                             │
│  image / audio / video  →  LLM  →  text             │
├──────────────────────────────────────────────────────┤
│  OpenAI-compatible API (Gemini, Claude, GPT, Grok…)  │
└──────────────────────────────────────────────────────┘
```

## Features

| | Feature | Detail |
|---|---------|--------|
| 🖼 | **Image** | Auto-resize & encode local files; passthrough remote URLs |
| 🎙 | **Audio** | Streaming download & base64 encode (OpenAI `input_audio` format) |
| 🎬 | **Video** | Direct encode (default) or ffmpeg frame extraction + audio track |
| 🤖 | **Multi-model** | Gemini / Claude / GPT / Grok / Kimi / Gemma — YAML registry |
| ⚡ | **Auto-adapt** | Stream/non-stream fallback, model capability matching |
| 🔌 | **Agent-ready** | Plain text stdout, `[qsense]` stderr errors, exit 0/1, zero side effects |

## Quick Start

**One-line install / 一键安装：**

```bash
bash setup.sh && source .venv/bin/activate
qsense --prompt "Describe this image" --image photo.png
# First run will interactively guide API key setup
# 首次运行会交互式引导配置 API key
```

**For agents / CI：**

```bash
QSENSE_API_KEY=sk-xxx bash setup.sh
source .venv/bin/activate
```

**Manual install / 手动安装：**

```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e .
# or: pip install -e .
```

## Usage Examples

```bash
# ── Image ──────────────────────────────────────────
qsense --prompt "What's in this image?" --image screenshot.png
qsense --prompt "Compare these" --image a.png --image b.png
qsense --prompt "Describe" --image https://example.com/photo.jpg

# ── Audio ──────────────────────────────────────────
qsense --prompt "Transcribe this" --audio recording.wav
qsense --prompt "What genre?" --audio https://example.com/song.mp3

# ── Video (direct passthrough) ─────────────────────
qsense --prompt "Summarize this video" --video clip.mp4

# ── Video (frame extraction) ──────────────────────
qsense --prompt "Describe" --video clip.mp4 --video-extract --fps 2

# ── Mixed modalities ──────────────────────────────
qsense --prompt "Analyze" --image frame.png --audio narration.wav

# ── Model override ────────────────────────────────
qsense --model anthropic/claude-opus-4-6 --prompt "Analyze" --image photo.png
```

## Available Models

```bash
qsense models           # List all models / 列出所有模型
qsense models --detail  # Show limits / 显示详细限制
```

| Model | Vision | Audio | Video | Context |
|:------|:------:|:-----:|:-----:|--------:|
| `google/gemini-3-flash-preview` | ✅ | ✅ | native | 1M |
| `google/gemini-3.1-pro-preview` | ✅ | ✅ | native | 1M |
| `gemma-4-31B-it` | ✅ | — | extract | 256K |
| `anthropic/claude-opus-4-6` | ✅ | — | — | 1M |
| `anthropic/claude-sonnet-4-6` | ✅ | — | — | 1M |
| `gpt-5.4` | ✅ | — | — | — |
| `grok-4.20-beta` | ✅ | — | — | 256K |
| `Kimi-K2.5` | ✅ | — | native* | 256K |

<sup>* experimental</sup>

## CLI Reference

```
qsense [OPTIONS] [COMMAND]

Options:
  --prompt TEXT         Text prompt (required for inference)
  --image TEXT          Image path or URL (repeatable)
  --audio TEXT          Audio file path or URL (repeatable)
  --video TEXT          Video file path or URL (repeatable)
  --video-extract       Use ffmpeg frame extraction
  --fps FLOAT           Extraction frame rate (default: 1)
  --max-frames INT      Max extracted frames (default: 30)
  --model TEXT          Override default model
  --timeout INT         Request timeout in seconds
  --max-size INT        Max image longest side in px (default: 2048)

Commands:
  init                  Initialize configuration
  config                Show or update configuration
  models                List available models
```

## Configuration

Priority / 优先级: CLI flags > environment variables > `~/.qsense/.env`

```bash
# Show current config / 查看当前配置
qsense config

# Update / 更新配置
qsense config --model google/gemini-3.1-pro-preview
qsense config --api-key sk-xxx
qsense config --base-url https://api.openai.com/v1

# Environment variables / 环境变量
export QSENSE_API_KEY=sk-xxx
export QSENSE_BASE_URL=https://api.openai.com/v1
export QSENSE_MODEL=google/gemini-3-flash-preview
```

## Design Philosophy

> QSense is an **atomic skill** — the smallest indivisible unit of perception.
>
> QSense 是**原子技能**——不可再分的最小感知单元。

**What QSense does** — send files to a model, return text. That's it.

**What QSense does NOT do** — video download, audio slicing, batch iteration, result parsing, conversation management, workflow orchestration. All left to the caller.

**QSense 做什么** — 把文件送给模型，返回文字。就这样。

**QSense 不做什么** — 视频下载、音频切片、批量遍历、结果解析、对话管理、workflow 编排——全部留给上层组合。

```bash
# Compose with higher-level skills / 上层 skill 组合示例
ffmpeg -i long.mp4 -segment_time 60 -f segment chunk_%03d.mp4
for f in chunk_*.mp4; do
  qsense --prompt "Summarize this minute" --video "$f" >> result.txt
done
```

Stay atomic, stay composable. See [docs/design-rationale.md](docs/design-rationale.md) for the full story.

## AI Agent Integration

QSense ships with [Agent Skills](https://agentskills.io) support — a standard format recognized by Claude Code, OpenCode, Codex, and more.

QSense 提供标准 Agent Skills 格式的 Skill，支持主流 AI 编程助手。

**Copy this to your agent / 复制以下命令发给你的 Agent：**

```
Install the qsense multimodal perception skill:
npx skills add hezi-ywt/qsense
```

The skill includes:
- **`SKILL.md`** — command reference, output contract, error guide
- **`references/models.md`** — model capabilities, limits, selection strategy
- **`references/user-notes.md`** — agent-maintained learning log that improves over time

```
skills/qsense/
├── SKILL.md
└── references/
    ├── models.md
    └── user-notes.md
```

## Project Structure

```
src/qsense/
  cli.py            Click CLI entry point
  client.py         OpenAI-compatible API client
  config.py         Three-tier config: CLI > env > file
  image.py          Image validation, resize, encoding
  audio.py          Audio validation, download, encoding
  video.py          Video passthrough and frame extraction
  models.py         Model registry loader
  registry.yaml     Curated model capabilities database
```

## Requirements

- Python >= 3.10
- ffmpeg (only for `--video-extract` mode)

## License

MIT
