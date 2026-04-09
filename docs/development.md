# QSense 开发文档

## 开发环境

```bash
# 克隆项目后
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .

# 验证
qsense --help

# 可选：安装 ffmpeg（视频抽帧功能）
brew install ffmpeg  # macOS
```

## 项目结构

```
基础设施/
├── pyproject.toml              包配置、依赖、入口点
├── CLAUDE.md                   Agent 上下文（Claude Code 自动加载）
├── README.md                   项目介绍
├── .gitignore
├── docs/
│   ├── usage.md                使用指南
│   ├── development.md          本文件
│   └── superpowers/specs/      设计规格文档
├── scripts/
│   └── probe_audio_format.py   音频格式探测脚本
└── src/qsense/
    ├── __init__.py              版本号
    ├── _util.py                 公共工具（abort）
    ├── cli.py                   CLI 入口（Click group）
    ├── client.py                API 客户端
    ├── config.py                配置加载 + 首次设置
    ├── image.py                 图像处理
    ├── audio.py                 音频处理
    ├── video.py                 视频处理
    ├── models.py                模型注册表加载器
    └── registry.yaml            模型注册表数据
```

## 模块职责

### `_util.py`
唯一导出 `abort(message)` -- 统一的错误退出函数。格式 `[qsense] message` 到 stderr，exit 1。三个处理模块（image/audio/video）都 import 它。

### `config.py`
- `Config` dataclass: api_key, base_url, model, timeout
- `load_config()`: 合并三层配置（CLI > env > file）
- `run_first_time_setup()`: 交互式引导，写入 `~/.qsense/.env`
- `show_config()` / `update_config()`: 配置查看和修改

### `image.py`
- `prepare_image(source)` / `prepare_images(sources)`
- 远程 URL: 直接透传（`image_url` 字段）
- 本地文件: Pillow 打开 → 校验尺寸 → `_fit_to_limit()` 等比缩小 → `_encode_to_data_url()` base64 编码
- 类型: `ImageContentPart` (TypedDict)

### `audio.py`
- `prepare_audio(source)` / `prepare_audios(sources)`
- 远程 URL: httpx 下载 → Content-Type/扩展名推断格式 → base64
- 本地文件: 读取 → 校验 → base64
- 输出格式: `input_audio`（OpenAI 标准，无 `audio_url` 类型）
- 类型: `AudioContentPart` (TypedDict)

### `video.py`
- `encode_video_direct(source)`: 整个视频 base64 → `image_url` data URL
- `extract_frames_and_audio(source)`: ffmpeg 抽帧 + 音轨提取
  - 帧: 复用 `image.prepare_images()`
  - 音轨: 复用 `audio.prepare_audio()`
  - 返回 `(images, audio_or_None)`

### `client.py`
- `chat(config, prompt, images, audios, extras)`: 构建 message content → 调用 OpenAI SDK
- 流式处理: 检查注册表 `stream_only` → 直接 stream；否则先 non-stream，失败降级 stream
- `_strip_thinking()`: 去除推理模型的 `<think>` 块
- `_collect_stream()`: 消费 stream chunks 拼接完整文本

### `models.py`
- `ModelInfo` dataclass: id, name, vision, audio, video, native_video, stream_only, limits...
- 从 `registry.yaml` 加载，构建 `_INDEX` 字典
- `get_model()` / `list_models()` / `is_registered()`

### `cli.py`
- `main`: Click group（`invoke_without_command=True`），无子命令时执行推理
- `config`: 子命令，查看/修改持久化配置
- `models`: 子命令，列出注册表模型

## 添加新模型

编辑 `src/qsense/registry.yaml`，追加一条：

```yaml
- id: provider/model-name        # API 使用的确切模型 ID
  name: Display Name
  vision: true
  audio: false
  video: false
  native_video: false
  stream_only: false              # 如果模型要求 stream=true 就设 true
  context_tokens: 128000
  max_image_size_mb: 10
  max_image_resolution: null      # 如 "8000x8000"，未知填 null
  max_images_per_request: null
  max_audio_duration_min: 0
  max_video_duration_min: 0
  image_formats: [jpeg, png, webp]
  audio_formats: []
  video_formats: []
  description: 一句话描述
```

不需要改任何 Python 代码。重新 `pip install -e .` 后生效。

## 添加新模态

以添加 "PDF 理解" 为例：

1. 创建 `src/qsense/pdf.py`
   - 定义 `prepare_pdf(source)` → 返回 content part dict
   - 参考 `image.py` 的模式
2. 修改 `cli.py`
   - 添加 `--pdf` option
   - 调用 `prepare_pdf()` 处理
3. 修改 `client.py`
   - `chat()` 参数增加 `pdfs` 或放入 `extras`
4. 修改 `registry.yaml`
   - 给支持 PDF 的模型添加 `pdf: true`
5. 修改 `models.py`
   - `ModelInfo` 增加 `pdf` 字段

## 设计原则

### OpenAI 兼容
所有 API 调用统一走 `openai` Python SDK 的 `chat.completions.create()`。不引入任何 provider 特定 SDK。通过 `base_url` 参数适配不同代理。

### 三层配置
CLI flags > 环境变量 > `~/.qsense/.env`。确保交互式使用和 agent 自动化场景都能工作。

### 流式降级
默认 `stream=False`。注册表标记 `stream_only: true` 的模型直接走流式。未注册模型如果 non-stream 请求失败且错误含 "stream"，自动重试 stream。

### 最小依赖
运行时依赖仅 6 个包。ffmpeg 是可选的外部依赖（仅 `--video-extract` 需要）。

### 错误优先
所有用户可触发的错误路径都有明确的 `[qsense] ...` 格式消息和 exit 1。不吞异常，不静默失败。

## 已知限制

- 音频 `input_audio` 格式并非所有代理都支持转发（GPT 系列通过部分代理会 500）
- 视频直传依赖代理对 `data:video/*` 的处理能力
- 注册表是静态的，不会自动从 API `/models` 端点同步
- 没有 JSON 结构化输出模式
- 不支持对话上下文/多轮
