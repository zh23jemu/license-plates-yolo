#!/bin/bash
#SBATCH --job-name=plate-yolo-compare
#SBATCH --partition=aws
#SBATCH --account=gpo-ifv7xx
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --gres=gpu:1
#SBATCH --time=08:00:00
#SBATCH --output=slurm_logs/%x-%j.out
#SBATCH --error=slurm_logs/%x-%j.err

# 本脚本用于在 Slurm GPU 节点上运行 YOLOv8n 与 YOLOv10n 车牌定位对比实验。
# 默认 GPU 分区为 aws；如需改分区，可以提交时覆盖：
#   sbatch --partition=目标分区 slurm/train_compare.sbatch

set -euo pipefail

# 切换到提交作业时所在的项目根目录，保证使用共享文件系统中的代码和 `.venv`。
# Slurm 可能会把脚本复制到 `/var/spool/...` 后再执行，如果用 `BASH_SOURCE[0]`
# 反推路径，就会误指向计算节点临时目录，导致找不到项目虚拟环境。
PROJECT_DIR="${SLURM_SUBMIT_DIR:-$(pwd)}"
cd "${PROJECT_DIR}"

# Slurm 日志目录由 #SBATCH --output/--error 使用。
# 注意：部分集群会在作业启动前创建日志文件，但计算节点对项目目录的
# 目录创建权限更严格，因此不要在作业内部再次创建该目录。

# 始终使用项目本地虚拟环境，不依赖系统 Python 或 shell 激活状态。
PYTHON="${PROJECT_DIR}/.venv/bin/python"

if [ ! -x "${PYTHON}" ]; then
  echo "未找到项目虚拟环境：${PYTHON}"
  echo "请先运行：python3.10 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
  exit 1
fi

# 先检查数据集配置和标签一致性，避免占用 GPU 后才发现数据路径错误。
"${PYTHON}" scripts/check_dataset.py --data-yaml data/ccpd_yolo/plates.yaml

# 两个模型使用同一入口训练，除模型权重外训练参数保持一致。
"${PYTHON}" scripts/train_compare.py \
  --data data/ccpd_yolo/plates.yaml \
  --project runs/plate_compare \
  --epochs 100 \
  --imgsz 640 \
  --batch auto \
  --seed 42 \
  --workers 8 \
  --device 0

# 训练完成后自动生成 Markdown 实验报告。
"${PYTHON}" scripts/generate_report.py \
  --project runs/plate_compare \
  --output reports/experiment_report.md
