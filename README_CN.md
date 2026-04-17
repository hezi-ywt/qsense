<p align="center">
  <h1 align="center">QSense</h1>
  <p align="center">
    <strong>多模态感知原子技能</strong>
  </p>
  <p align="center">
    <a href="#快速开始">快速开始</a> ·
    <a href="#使用示例">使用示例</a> ·
    <a href="#可用模型">可用模型</a> ·
    <a href="#ai-agent-集成">Agent 集成</a> ·
    <a href="README.md">English</a>
  </p>
</p>

---

一条命令，让模型「看」图像、「听」音频、「看」视频，返回文字。

QSense 不是应用，是给上层 skill、agent、脚本调用的最底层感知能力。它只做一件事：**把多模态输入送给模型，拿回文字结果。** 视频切片、音频分段、批量处理、结果解析——这些都不是 qsense 的事，留给上层组合。

```
┌──────────────────────────────────────────────────────┐
│  上层 Skill / Agent / 脚本                            │
│  视频审核、会议纪要、OCR 流水线、内容分析...              │
├──────────────────────────────────────────────────────┤
│  QSense  ← 你在这里                                  │
│  图像 / 音频 / 视频  →  模型  →  文字                  │
├──────────────────────────────────────────────────────┤
│  OpenAI 兼容 API (Gemini, Claude, GPT, Grok…)         │
└──────────────────────────────────────────────────────┘
```

## 特性

| | 特性 | 说明 |
|---|------|------|
| 🖼 | **图像** | 本地文件自动缩放编码，远程 URL 直接透传 |
| 🎙 | **音频** | 本地/远程文件流式下载编码（OpenAI `input_audio` 格式） |
| 🎬 | **视频** | 直传编码（默认）或 ffmpeg 抽帧 + 音轨分离 |
| 🤖 | **多模型** | Gemini / Claude / GPT / Grok / Kimi / Gemma，YAML 注册表管理 |
| ⚡ | **自动适配** | 流式/非流式自动降级，模型能力自动匹配 |
| 🔌 | **Agent 友好** | 纯文本 stdout，`[qsense]` stderr 错误，exit 0/1，零副作用 |

## 快速开始

qsense 直接从 git 安装(不发 PyPI),跨平台支持 macOS / Linux / Windows。推荐**venv-first**路径,能绕开 brew / Debian 系统 Python 的 PEP 668 保护。

```bash
git clone https://github.com/hezi-ywt/qsense.git
cd qsense
```

**macOS / Linux / WSL:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

验证:`qsense --version`。

**一键脚本(macOS / Linux / WSL / Windows Git Bash,基于 `uv`):**
```bash
bash setup.sh
# Agent / CI 静默:
QSENSE_API_KEY=sk-xxx bash setup.sh
```
脚本自动探测 `Scripts/activate` 或 `bin/activate`,所以 Windows Git Bash 也能直接跑。原生 PowerShell / CMD 没 bash — 用 Git Bash / WSL,或者走上面的标准安装。

**免安装临时跑(跨平台):**
```bash
PYTHONPATH=src python -m qsense --help
```

**ffmpeg(可选,仅 `--video-extract` 需要):** `brew install ffmpeg` / `apt install ffmpeg` / `winget install Gyan.FFmpeg` — 完整多系统表见 [安装参考](skills/qsense/references/install.md#前置)。

**更新:** 在源码目录跑 `git pull`;只有 `pyproject.toml` 变了才需要再 `pip install -e .`。

## 使用示例

```bash
# ── 图像 ───────────────────────────────────────────
qsense --prompt "这张图里有什么？" --image screenshot.png
qsense --prompt "对比这两张图" --image a.png --image b.png
qsense --prompt "描述" --image https://example.com/photo.jpg

# ── 音频 ───────────────────────────────────────────
qsense --prompt "转录这段录音" --audio recording.wav
qsense --prompt "什么音乐风格？" --audio https://example.com/song.mp3

# ── 视频（直传模式）────────────────────────────────
qsense --prompt "总结这个视频" --video clip.mp4

# ── 视频（抽帧模式）────────────────────────────────
qsense --prompt "描述画面" --video clip.mp4 --video-extract --fps 2

# ── 混合输入 ───────────────────────────────────────
qsense --prompt "分析" --image frame.png --audio narration.wav

# ── 指定模型 ───────────────────────────────────────
qsense --model anthropic/claude-opus-4-6 --prompt "分析" --image photo.png
```

## 可用模型

```bash
qsense models           # 列出所有模型
qsense models --detail  # 显示详细限制
```

| 模型 | 视觉 | 音频 | 视频 | 上下文 |
|:-----|:----:|:----:|:----:|------:|
| `google/gemini-3-flash-preview` | ✅ | ✅ | 原生 | 1M |
| `google/gemini-3.1-pro-preview` | ✅ | ✅ | 原生 | 1M |
| `gemma-4-31B-it` | ✅ | — | 抽帧 | 256K |
| `anthropic/claude-opus-4-6` | ✅ | — | — | 1M |
| `anthropic/claude-sonnet-4-6` | ✅ | — | — | 1M |
| `gpt-5.4` | ✅ | — | — | — |
| `grok-4.20-beta` | ✅ | — | — | 256K |
| `Kimi-K2.5` | ✅ | — | 原生* | 256K |

<sup>* 实验性</sup>

## CLI 参考

```
qsense [选项] [命令]

选项:
  --prompt TEXT         文本提示词（推理时必需）
  --image TEXT          图片路径或 URL（可重复）
  --audio TEXT          音频文件路径或 URL（可重复）
  --video TEXT          视频文件路径或 URL（可重复）
  --video-extract       使用 ffmpeg 抽帧模式
  --fps FLOAT           抽帧帧率（默认: 1）
  --max-frames INT      最大抽帧数（默认: 30）
  --model TEXT          覆盖默认模型
  --timeout INT         请求超时秒数
  --max-size INT        图片长边最大像素（默认: 2048）

命令:
  init                  初始化配置
  config                查看或更新配置
  models                列出可用模型
```

## 配置

优先级: CLI 参数 > 环境变量 > `~/.qsense/.env`

```bash
# 查看当前配置
qsense config

# 更新配置
qsense config --model google/gemini-3.1-pro-preview
qsense config --api-key sk-xxx
qsense config --base-url https://api.openai.com/v1

# 环境变量
export QSENSE_API_KEY=sk-xxx
export QSENSE_BASE_URL=https://api.openai.com/v1
export QSENSE_MODEL=google/gemini-3-flash-preview
```

## 设计理念

> QSense 是**原子技能**——不可再分的最小感知单元。

**QSense 做什么** — 把文件送给模型，返回文字。就这样。

**QSense 不做什么** — 视频下载、音频切片、批量遍历、结果解析、对话管理、workflow 编排——全部留给上层 skill 组合。

```bash
# 上层 skill 组合示例：长视频逐段分析
ffmpeg -i long.mp4 -segment_time 60 -f segment chunk_%03d.mp4
for f in chunk_*.mp4; do
  qsense --prompt "总结这一分钟" --video "$f" >> result.txt
done
```

保持原子，才能让上层自由选择策略。详见 [docs/design-rationale.md](docs/design-rationale.md)。

## AI Agent 集成

QSense 采用 **Skill + CLI** 双层设计：CLI 是执行层，Skill 是知识层，教 AI Agent 高效使用这个工具。

### 安装

**项目地址：** https://github.com/hezi-ywt/qsense

复制以下内容发给你的 Agent —— 它知道如何用自己平台的方式安装 skill：

```
安装 qsense 多模态感知技能，项目地址 https://github.com/hezi-ywt/qsense
该 skill 遵循 Agent Skills 标准（https://agentskills.io）。
请使用你所在平台的 skill 安装方式进行安装。
例如: npx skills add hezi-ywt/qsense
```

### 三文件架构

```
skills/qsense/
├── SKILL.md                    # 稳定事实
│                               # 命令语法、输出约定、错误速查
│
└── references/
    ├── models.md               # 模型知识
    │                           # 能力表、限制、视频/音频策略
    │                           # 与 `qsense models --detail` 同步
    │
    └── user-notes.md           # 持续学习记忆
                                # Agent 自动维护：偏好、经验、教训
```

| 文件 | 更新频率 | 谁来维护 |
|------|---------|---------|
| `SKILL.md` | 很少 — CLI 变动时 | 开发者 |
| `models.md` | 新增/更新模型时 | 开发者 + Agent 同步 |
| `user-notes.md` | 使用过程中持续更新 | Agent 自动 |

Agent 每次使用前读取 `user-notes.md`，发现值得记住的事就更新它——模型偏好、失败修复、常用工作流。**用得越多，越好用。**

## 项目结构

```
qsense/
├── src/qsense/
│   ├── cli.py            # Click CLI 入口（main + init / config / models）
│   ├── client.py         # OpenAI SDK 调用、流式自动判断、错误脱敏
│   ├── config.py         # 三级配置: CLI > 环境变量 > ~/.qsense/.env
│   ├── image.py          # Pillow 缩放 + base64（远程 URL 直接透传）
│   ├── audio.py          # 流式下载 + base64 input_audio
│   ├── video.py          # 直传 / 下载编码 / 抽帧调度
│   ├── models.py         # Registry 加载（registry.yaml）
│   ├── registry.yaml     # 模型能力与行为开关注册表
│   └── _*.py             # 内部 helper：_util、_deps、_download、_extract、__main__
└── skills/qsense/        # 面向 agent 的 skill（SKILL.md + references/）
```

新增模型 = 只改 `registry.yaml`（不改代码）。完整架构说明见 [CLAUDE.md](CLAUDE.md)。

## 环境要求

- Python >= 3.10
- ffmpeg（仅 `--video-extract` 模式需要）

## 许可证

MIT
