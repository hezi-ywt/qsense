# 安装

qsense 不发布到 PyPI,直接从 git 源装。仓库里同时包含 Python 代码、CLI 元数据和 skill 文件 — `git pull` 一般就够了,只有 `pyproject.toml` 改了才需要重装。

支持 macOS / Linux / Windows,核心流程是**先建 venv 再 editable 装**,这样能自然绕开系统 Python 的 PEP 668 保护(macOS brew / Debian / Ubuntu 默认 Python 都会拦截直接 `pip install`)。

## 前置

- **Python >= 3.10**(`python3 --version` / `python --version` 检查)
- **ffmpeg**(可选,仅 `--video-extract` 模式需要):

| 平台 | 安装命令 |
|---|---|
| macOS | `brew install ffmpeg` |
| Debian / Ubuntu | `sudo apt install ffmpeg` |
| Fedora / RHEL | `sudo dnf install ffmpeg` |
| Arch | `sudo pacman -S ffmpeg` |
| Windows (winget) | `winget install --id=Gyan.FFmpeg -e` |
| Windows (choco) | `choco install ffmpeg` |
| Windows (scoop) | `scoop install ffmpeg` |

没装也没关系;qsense 只在调用 `--video-extract` 时才检查,缺了会给平台相关的提示(见 `src/qsense/_deps.py`)。

## 标准安装(venv-first,三平台通用)

```bash
git clone https://github.com/hezi-ywt/qsense.git
cd qsense
```

然后根据平台激活 venv:

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

> 首次执行 `Activate.ps1` 可能被执行策略阻止。以管理员跑 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`,或一次性用 `powershell -ExecutionPolicy Bypass -File .venv\Scripts\Activate.ps1`。

**Windows (CMD):**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -e .
```

装完验证:

```bash
qsense --version
```

### 带视频抽帧扩展(pyav)

```bash
python -m pip install -e ".[video]"
```

Windows PowerShell 里引号可能要改成单引号:`pip install -e '.[video]'`。

## 一键脚本(macOS / Linux / WSL)

仓库根目录的 `setup.sh` 会自动装 `uv`、创建 `.venv`、editable 装,并在设置了 `QSENSE_API_KEY` 的情况下顺手写配置:

```bash
bash setup.sh
# Agent / CI 静默模式:
QSENSE_API_KEY=sk-xxx bash setup.sh
```

Windows 用户如果想一条命令搞定,有两个选项:
1. 在 WSL 里跑 `setup.sh`(推荐,直接兼容)
2. 自己手动走上面的"标准安装"(只是多几行)

## 免安装临时跑(跨平台)

不想装也可以直接把源码当模块跑:

```bash
PYTHONPATH=src python -m qsense --help
# Windows PowerShell:
$env:PYTHONPATH="src"; python -m qsense --help
# Windows CMD:
set PYTHONPATH=src && python -m qsense --help
```

## 首次配置

```bash
qsense init --api-key sk-xxx \
            --base-url https://api.openai.com/v1 \
            --model google/gemini-3-flash-preview
```

配置写到:
- macOS / Linux: `~/.qsense/.env`(chmod 600)
- Windows: `%USERPROFILE%\.qsense\.env`(Windows 不强制 chmod,ACL 建议用户自行检查)

`base-url` 和 `model` 可省略,用默认值。

也可以完全用环境变量,不写文件:

```bash
# macOS / Linux:
export QSENSE_API_KEY=sk-xxx
export QSENSE_BASE_URL=https://your-proxy/v1
export QSENSE_MODEL=google/gemini-3-flash-preview

# Windows PowerShell:
$env:QSENSE_API_KEY="sk-xxx"
$env:QSENSE_BASE_URL="https://your-proxy/v1"
$env:QSENSE_MODEL="google/gemini-3-flash-preview"

# Windows CMD:
set QSENSE_API_KEY=sk-xxx
set QSENSE_BASE_URL=https://your-proxy/v1
set QSENSE_MODEL=google/gemini-3-flash-preview
```

优先级:**CLI flag > 环境变量 > 配置文件**。

## 验证

```bash
qsense --version         # 显示当前版本
qsense models            # 列出支持的模型
qsense config            # 查看当前配置(不打印 API key 全文)
```

## 以前用 pipx 装过的迁移

qsense 从未发布到 PyPI,`pipx install qsense-cli` 其实从来跑不通;如果本机存在这样的条目,要么是装了一份 `pipx install --editable <本地源码>`,要么是残留。清理:

```bash
pipx uninstall qsense-cli
# 然后按上面"标准安装"走
```

如果想定位旧的 pipx editable 指向哪:

```bash
pipx runpip qsense-cli show qsense-cli 2>/dev/null | grep -E "^(Location|Editable project location)"
```

## 常见问题

**`error: externally-managed-environment`(PEP 668)**
系统 Python 被发行版保护(macOS brew / Debian / Ubuntu 常见)。解决:按上面"标准安装"先建 venv 再装,或直接跑 `setup.sh`(自建 venv)。不要加 `--break-system-packages`。

**Windows `Activate.ps1 : 无法加载文件,因为在此系统上禁止运行脚本`**
见上面"标准安装"里的 PowerShell 说明。

**ffmpeg not found(`--video-extract` 模式)**
按前置章节的表装 ffmpeg,或用 `--video-passthrough` / 默认模式(不需要 ffmpeg)。

**`qsense --version` 显示旧版本**
PATH 上有多份 qsense。`which -a qsense`(macOS/Linux)或 `where qsense`(Windows)定位全部副本,激活当前 venv 或移除旧副本。
