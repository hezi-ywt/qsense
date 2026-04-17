# 安装

qsense 不发布到 PyPI,直接从 git 源装。仓库里同时包含 Python 代码、CLI 元数据和 skill 文件 — `git pull` 一般就够了,只有 `pyproject.toml` 改了才需要重装。

## 前置

- Python >= 3.10
- (可选) ffmpeg — 只有需要 `--video-extract` 模式时才用

## 标准安装

```bash
git clone https://github.com/hezi-ywt/qsense.git
cd qsense
python -m pip install -e .
qsense --help
```

带视频抽帧扩展(pyav):

```bash
python -m pip install -e '.[video]'
```

## 一键脚本(推荐)

仓库根目录的 `setup.sh` 会自动装 `uv`、创建 `.venv`、编辑安装,并在设置了 `QSENSE_API_KEY` 的情况下顺手写配置:

```bash
bash setup.sh
# Agent / CI 静默模式:
QSENSE_API_KEY=sk-xxx bash setup.sh
```

## 免安装临时跑

不想装也可以直接把源码当模块跑:

```bash
PYTHONPATH=src python -m qsense --help
```

## 首次配置

```bash
qsense init --api-key sk-xxx \
            --base-url https://api.openai.com/v1 \
            --model google/gemini-3-flash-preview
```

配置写到 `~/.qsense/.env`(chmod 600)。`base-url` 和 `model` 可省略,用默认值。

也可以完全用环境变量,不写文件:

```bash
export QSENSE_API_KEY=sk-xxx
export QSENSE_BASE_URL=https://your-proxy/v1
export QSENSE_MODEL=google/gemini-3-flash-preview
```

优先级:**CLI flag > 环境变量 > `~/.qsense/.env`**。

## 验证

```bash
qsense --version         # 显示当前版本
qsense models            # 列出支持的模型
qsense config            # 查看当前配置(不打印 API key)
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
