#!/usr/bin/env bash
# QSense 安装脚本
# 用法: bash setup.sh
#
# 要求: Python 3.10+
# 详细安装说明: 参见 skills/qsense/references/install.md

set -euo pipefail
cd "$(dirname "$0")"

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "错误: 需要 Python 3.10+"
    echo "参见 skills/qsense/references/install.md 获取安装指引"
    exit 1
fi

PYTHON=$(command -v python3 || command -v python)
$PYTHON -m venv .venv
# 跨平台 venv 激活脚本检测
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "[qsense] ERROR: could not find venv activate script"
    exit 1
fi
pip install -e .

if [ -n "${QSENSE_API_KEY:-}" ]; then
    mkdir -p ~/.qsense
    cat > ~/.qsense/.env <<EOF
QSENSE_API_KEY=${QSENSE_API_KEY}
QSENSE_BASE_URL=${QSENSE_BASE_URL:-https://api.openai.com/v1}
QSENSE_MODEL=${QSENSE_MODEL:-google/gemini-3-flash-preview}
EOF
fi

echo "完成: source .venv/bin/activate && qsense --help"
