---
name: qsense
description: "Multimodal perception CLI: send images, audio, or video to an LLM and get text back. Use for image recognition, audio transcription, video understanding, OCR, and any task where a model needs to see or hear something."
metadata:
  requires:
    bins: ["qsense"]
    optional_bins: ["ffmpeg"]
---

# QSense -- Multimodal Perception

One command: files in, text out. QSense is the atomic unit for "let a model see/hear something."

## Setup

```bash
pip install qsense-cli
qsense init            # stderr will tell you what's needed -- ask the user accordingly
```

## Quick Reference

```bash
# Image
qsense --prompt "describe this" --image photo.png
qsense --prompt "OCR" --image https://example.com/doc.jpg

# Audio (Gemini only)
qsense --prompt "transcribe" --audio recording.wav

# Video -- direct (models with native video support)
qsense --prompt "summarize" --video clip.mp4

# Video -- frame extraction (models without native video)
qsense --prompt "describe" --video clip.mp4 --video-extract --fps 1

# Multi-input
qsense --prompt "compare" --image a.png --image b.png
qsense --prompt "match?" --image frame.png --audio narration.wav

# Specify model
qsense --model google/gemini-3-flash-preview --prompt "analyze" --image x.png

# List available models
qsense models --detail
```

## Usage Principles

### Model Selection

Pick the right model for the modality:

| Need | Choose | Why |
|------|--------|-----|
| Audio input | `google/gemini-3-flash-preview` | Only Gemini supports audio |
| Native video | `google/gemini-3-flash-preview` | Most models can't ingest video |
| Deep reasoning on images | `google/gemini-3.1-pro-preview` | Strongest reasoning, 1M context |
| Fast image tasks | default (gemini-3-flash) | Cheapest, fastest |

When unsure, use the default model. Only override `--model` when the task needs a specific capability.

### Cost & Token Awareness

- Large images waste tokens. Use `--max-size 1024` for tasks that don't need full resolution (OCR, layout checks).
- Video is expensive. Prefer `--video-extract --fps 0.5 --max-frames 10` over direct passthrough for quick summaries.
- Multiple `--image` flags = multiple images in one request. Don't loop single-image calls when multi-image works.

### Video Strategy

```
Model supports native video? (check `qsense models --detail`)
  YES  --> direct: qsense --prompt "..." --video clip.mp4
  NO   --> extract: qsense --prompt "..." --video clip.mp4 --video-extract
```

- Direct mode preserves temporal info + audio track -- always prefer when available.
- Video > 20MB: split with `ffmpeg -segment_time 60 -f segment` first, then process segments.
- `--fps` and `--max-frames` control extraction density. Low fps (0.5) for slow-paced content, higher (2-3) for action.

### Audio Notes

- Only Gemini models accept audio. Don't send `--audio` to Claude/GPT/Grok -- it will fail.
- Remote audio is downloaded to memory (limit 20MB). For large files, download and trim first.
- To analyze audio from a video separately: `ffmpeg -i video.mp4 -vn audio.mp3`, then `--audio audio.mp3`.

### Composability

QSense does ONE request per invocation. Batch/pipeline logic belongs to the caller:

```bash
# Batch images
for img in screenshots/*.png; do
  qsense --prompt "any errors?" --image "$img"
done

# Long video: split then analyze
ffmpeg -i long.mp4 -segment_time 60 -f segment seg_%03d.mp4
for seg in seg_*.mp4; do
  qsense --prompt "summarize" --video "$seg"
done

# Capture result for downstream use
result=$(qsense --prompt "extract text" --image doc.png)
```

### Security

- Never read or log `~/.qsense/.env` -- it contains the API key.
- Don't pass API keys via `--prompt` or stdout.
- Config priority: CLI flags > env vars > `~/.qsense/.env`.

## Output Contract

- **stdout**: LLM response text only (pipe-safe)
- **stderr**: `[qsense] ...` errors and warnings
- **exit 0**: success | **exit 1**: failure

## Error Quick Reference

| stderr contains | Cause | Fix |
|----------------|-------|-----|
| `Missing API key` | Not configured | `qsense init` or set `QSENSE_API_KEY` |
| `model not found` | Wrong model id | `qsense models` to list available |
| `too large` | File exceeds limit | `--max-size` for images, split video |
| `ffmpeg is required` | Extract mode needs ffmpeg | `brew install ffmpeg` / `apt install ffmpeg` |
| `HTTP 401` | Invalid API key | `qsense config --api-key <new-key>` |

## Model Capabilities

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

Run `qsense models --detail` for full format/limit info.
