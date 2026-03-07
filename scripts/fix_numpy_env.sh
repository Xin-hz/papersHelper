#!/bin/bash
# 统一为 NumPy 2.x，并强制重装所有依赖 C 扩展的包（解决 Expected 96, got 88）
# 在项目根目录、已激活 .venv 下执行：bash scripts/fix_numpy_env.sh

set -e
cd "$(dirname "$0")/.."

echo ">>> 1. 升级到 NumPy 2.x..."
pip install --upgrade "numpy>=2.0"

echo ">>> 2. 强制重装依赖 C 扩展的包（按 NumPy 2 重新安装）..."
pip install --force-reinstall --no-cache-dir \
  scipy \
  scikit-learn \
  torch \
  sentence-transformers

echo ">>> 3. 安装/补齐其余依赖..."
pip install -r requirements.txt

echo ""
echo ">>> 完成。请重新启动: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
