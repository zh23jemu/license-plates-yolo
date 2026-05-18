# YOLOv8n 与 YOLOv10n 车牌定位对比实验

本项目用于完成一个最小可复现的车牌定位实验：使用 CCPD 公开数据集抽取几百张图片，转换为 YOLO 单类别检测格式，然后在相同训练参数下对比 `yolov8n.pt` 与 `yolov10n.pt` 的定位精度。

## 环境准备

始终使用项目本地虚拟环境：

```powershell
py -3.10 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux 或 Slurm 环境：

```bash
python3.10 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 数据准备

先将 CCPD 原始图片放到 `data/raw/ccpd`，然后生成 YOLO 格式子集：

```bash
.venv/bin/python scripts/prepare_ccpd_dataset.py \
  --source data/raw/ccpd \
  --output data/ccpd_yolo \
  --sample-size 500 \
  --seed 42
```

Windows 本地调试时使用：

```powershell
.venv\Scripts\python.exe scripts\prepare_ccpd_dataset.py --source data\raw\ccpd --output data\ccpd_yolo --sample-size 500 --seed 42
```

生成后可检查数据一致性：

```bash
.venv/bin/python scripts/check_dataset.py --data-yaml data/ccpd_yolo/plates.yaml
```

## 训练与对比

本地或交互式 GPU 环境运行：

```bash
.venv/bin/python scripts/train_compare.py \
  --data data/ccpd_yolo/plates.yaml \
  --project runs/plate_compare \
  --epochs 100 \
  --imgsz 640 \
  --batch auto
```

Slurm 集群运行：

```bash
sbatch slurm/train_compare.sbatch
```

如果需要临时覆盖分区：

```bash
sbatch --partition=目标分区 slurm/train_compare.sbatch
```

## 生成报告

训练完成后汇总指标并生成报告：

```bash
.venv/bin/python scripts/generate_report.py \
  --project runs/plate_compare \
  --output reports/experiment_report.md
```

报告会根据训练输出中的 `results.csv` 和验证指标自动生成对比表，并在结论中按实际 `mAP50-95` 判断哪个模型精度更高。
