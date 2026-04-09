# QSense -- Agent Context

## What This Is

QSense (`qsense`) is a CLI tool that sends images, audio, and video to multimodal LLMs via OpenAI-compatible chat completions APIs. It outputs the model's text response to stdout.

Package name: `qsense-cli`. Binary: `qsense`.

## Code Layout

```
src/qsense/
  _util.py          abort() -- shared error handler, prints "[qsense] ..." to stderr, exits 1
  config.py         Config dataclass + load_config() -- three-tier priority: CLI > env > ~/.qsense/.env
  image.py          prepare_image(s)() -- validate, Pillow resize, base64 data URL. Remote URLs pass through.
  audio.py          prepare_audio(s)() -- validate, httpx download if remote, base64 input_audio format.
  video.py          encode_video_direct() -- base64 data URL via image_url field.
                    extract_frames_and_audio() -- ffmpeg frames + audio track extraction.
  client.py         chat() -- builds message content, calls OpenAI SDK. Handles streaming auto-detection.
  models.py         ModelInfo dataclass + registry loader from registry.yaml.
  registry.yaml     Curated model list with capabilities (vision/audio/video/stream_only) and limits.
  cli.py            Click group: main command (inference), config subcommand, models subcommand.
```

## Key Design Decisions

- **OpenAI-compatible only**: All API calls go through the `openai` Python SDK. No provider-specific SDKs.
- **Audio uses `input_audio` format**: OpenAI API has no `audio_url` type. All audio (local and remote) must be base64-encoded inline. Remote audio is downloaded client-side via httpx.
- **Images use `image_url` format**: Local images become `data:` URLs. Remote URLs pass through directly.
- **Video default is direct passthrough**: Whole video base64-encoded as `data:video/mp4;base64,...` in an `image_url` field. Works with Gemini and Kimi. For models without native video, use `--video-extract` (ffmpeg).
- **Streaming fallback**: Some models/proxies require `stream=True`. Registry has `stream_only` flag. Client tries non-stream first, falls back to stream if error contains "stream".
- **`<think>` stripping**: Reasoning models (Grok) emit `<think>...</think>` blocks. Client strips these automatically.

## Setup

```bash
# One-liner (auto-config with env var)
QSENSE_API_KEY=sk-xxx bash setup.sh && source .venv/bin/activate

# Or manual
uv venv --python 3.12 && source .venv/bin/activate && uv pip install -e .
```

setup.sh handles: uv install, venv creation, dependency install, config file creation.
If QSENSE_API_KEY is set, config is written automatically (no interactive prompts).
If not set, first `qsense` run will prompt interactively (requires TTY).

## Registry Format (registry.yaml)

```yaml
- id: google/gemini-3-flash-preview    # exact API model ID
  name: Gemini 3 Flash                 # display name
  vision: true
  audio: true
  video: true
  native_video: true                   # server handles video natively
  stream_only: false                   # requires streaming API
  context_tokens: 1048576
  max_image_size_mb: 7
  max_images_per_request: 3000
  max_audio_duration_min: 504
  max_video_duration_min: 45
  image_formats: [jpeg, png, webp]
  audio_formats: [mp3, wav, flac]
  video_formats: [mp4, mov, webm]
  description: 快速多模态模型
```

To add a new model: append an entry to `src/qsense/registry.yaml`. No code changes needed.

## Conventions

- Errors: call `_abort(message)` from `_util.py`. Format: `[qsense] message` to stderr, exit 1.
- Public functions: `prepare_*` for input processing, `chat` for API calls, `load_config` / `update_config` / `show_config` for config.
- TypedDicts: `ImageContentPart`, `AudioContentPart` define payload shapes. Client accepts `list[dict]` for flexibility.
- Constants: module-scoped, prefixed for image module (`IMAGE_MAX_LONG_SIDE`), unprefixed for audio/video.

## Config File

`~/.qsense/.env`:
```
QSENSE_API_KEY=sk-xxx
QSENSE_BASE_URL=https://api.openai.com/v1
QSENSE_MODEL=google/gemini-3-flash-preview
```

## Dependencies

Runtime: click, openai, httpx, python-dotenv, Pillow, PyYAML.
Optional: ffmpeg (for `--video-extract`).
