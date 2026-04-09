# QSense

Minimal CLI multimodal understanding tool. Send images, audio, and video to multimodal models via OpenAI-compatible APIs.

## Features

- **Image understanding** -- local files and remote URLs, auto-resize, format validation
- **Audio understanding** -- local files and remote URLs, auto-download and base64 encoding
- **Video understanding** -- direct passthrough (default) or ffmpeg frame extraction
- **Multi-model support** -- Gemini, Claude, GPT, Grok, Kimi, Gemma with curated registry
- **Streaming auto-detection** -- models requiring streaming are handled transparently
- **Three-tier config** -- CLI flags > environment variables > `~/.qsense/.env`

## Quick Start

### 一键安装（人工）

```bash
bash setup.sh
source .venv/bin/activate
qsense --prompt "Describe this image" --image photo.png
# 首次运行会交互式引导配置 API key
```

### 一键安装（Agent / CI）

```bash
QSENSE_API_KEY=sk-xxx bash setup.sh
source .venv/bin/activate
```

### 手动安装

```bash
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e .
# 或: pip install -e .
```

## Usage Examples

```bash
# Image
qsense --prompt "What's in this image?" --image screenshot.png
qsense --prompt "Compare these" --image a.png --image b.png
qsense --prompt "Describe" --image https://example.com/photo.jpg

# Audio
qsense --prompt "Transcribe this" --audio recording.wav
qsense --prompt "What genre?" --audio https://example.com/song.mp3

# Video (direct passthrough, default)
qsense --prompt "Summarize this video" --video clip.mp4

# Video (frame extraction, for models without native video)
qsense --prompt "Describe" --video clip.mp4 --video-extract --fps 2

# Mixed
qsense --prompt "Analyze" --image frame.png --audio narration.wav

# Specify model
qsense --model anthropic/claude-opus-4-6 --prompt "Analyze" --image photo.png
```

## Available Models

```bash
qsense models           # List all models
qsense models --detail  # Show limits (formats, max size, etc.)
```

| Model | Vision | Audio | Video | Context |
|-------|--------|-------|-------|---------|
| google/gemini-3-flash-preview | yes | yes | native | 1M |
| google/gemini-3.1-pro-preview | yes | yes | native | 1M |
| gemma-4-31B-it | yes | - | extract | 256K |
| anthropic/claude-opus-4-6 | yes | - | - | 1M |
| anthropic/claude-sonnet-4-6 | yes | - | - | 1M |
| gpt-5.4 | yes | - | - | - |
| grok-4.20-beta | yes | - | - | 256K |
| Kimi-K2.5 | yes | - | native* | 256K |

*experimental

## CLI Reference

```
qsense [OPTIONS] [COMMAND]

Options:
  --prompt TEXT         Text prompt (required for inference)
  --image TEXT          Image path or URL (repeatable)
  --audio TEXT          Audio file path or URL (repeatable)
  --video TEXT          Video file path or URL (repeatable)
  --video-extract       Use ffmpeg frame extraction instead of direct passthrough
  --fps FLOAT           Extraction frame rate (default: 1)
  --max-frames INT      Max extracted frames (default: 30)
  --model TEXT          Override default model
  --timeout INT         Request timeout in seconds
  --max-size INT        Max image longest side in pixels (default: 2048)

Commands:
  config                Show or update configuration
  models                List available models
```

## Configuration

Priority: CLI flags > environment variables > `~/.qsense/.env`

```bash
# Show current config
qsense config

# Update
qsense config --model google/gemini-3.1-pro-preview
qsense config --api-key sk-xxx
qsense config --base-url https://api.openai.com/v1

# Environment variables
export QSENSE_API_KEY=sk-xxx
export QSENSE_BASE_URL=https://api.openai.com/v1
export QSENSE_MODEL=google/gemini-3-flash-preview
```

## Project Structure

```
src/qsense/
  __init__.py       Package metadata
  _util.py          Shared utilities (abort)
  cli.py            Click CLI entry point
  client.py         OpenAI-compatible API client
  config.py         Configuration loading and first-run setup
  image.py          Image validation, resize, encoding
  audio.py          Audio validation, download, encoding
  video.py          Video direct passthrough and frame extraction
  models.py         Model registry loader
  registry.yaml     Curated model list with capabilities
```

## Requirements

- Python >= 3.10
- ffmpeg (only for `--video-extract` mode)
