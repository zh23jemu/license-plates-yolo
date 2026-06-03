"""打包面向用户交付的车牌定位实验材料。

打包原则：
- 文档只放最终 Word 报告，不放其它 Markdown/中间 Word；
- 额外说明文档只在压缩包内写入一份 README.md；
- 包含可复现实验所需代码、依赖清单、500 张 YOLO 格式数据集压缩包；
- 包含 YOLOv8n/YOLOv10n 的 best/last 权重和关键训练曲线图；
- 不打包完整 runs/、虚拟环境、渲染 QA 图片等本地运行态内容。
"""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ZIP = PROJECT_ROOT / "reports" / "license_plate_yolo_user_delivery.zip"

FINAL_REPORT = PROJECT_ROOT / "reports" / "b6b7cd57_rewritten_2780877452_user_experiment_report.docx"
DATASET_ARCHIVE = PROJECT_ROOT / "reports" / "ccpd_yolo_500_dataset.tar.gz"


README = """# 车牌定位 YOLOv8n 与 YOLOv10n 对比实验交付包

## 程序用途

本项目用于完成车牌定位实验：只检测图片中的车牌位置，不进行车牌字符识别。实验使用 CCPD 数据集中抽取的 500 张图片，对 YOLOv8n 与 YOLOv10n 进行同条件训练和测试，并比较两者定位精度。

## 技术栈

- Python
- Ultralytics YOLO
- PyTorch
- OpenCV
- PyYAML
- Pandas
- Matplotlib

## 目录说明

- `report/user_experiment_report.docx`：最终 Word 实验报告。
- `code/`：数据准备、数据检查、训练对比和报告生成脚本。
- `data/ccpd_yolo_500_dataset.tar.gz`：本次实验使用的 500 张 YOLO 格式车牌定位数据集。
- `models/yolov8n/`：YOLOv8n 的 `best.pt` 和 `last.pt`。
- `models/yolov10n/`：YOLOv10n 的 `best.pt` 和 `last.pt`。
- `figures/yolov8n/`：YOLOv8n 的 F1、PR、P、R 曲线、混淆矩阵和训练结果图。
- `figures/yolov10n/`：YOLOv10n 的 F1、PR、P、R 曲线、混淆矩阵和训练结果图。
- `requirements.txt`：Python 依赖清单。

## 环境要求

建议使用带 NVIDIA GPU 的 Windows 环境，并确保 PyTorch 可以正常访问 GPU。可以用下面命令检查：

```powershell
.venv\\Scripts\\python.exe -c "import torch; print(torch.cuda.is_available())"
```

输出为 `True` 时表示 GPU 可用。

## 启动方法

1. 创建虚拟环境并安装依赖：

```powershell
py -3.10 -m venv .venv
.venv\\Scripts\\python.exe -m pip install -r requirements.txt
```

2. 解压数据集：

```powershell
tar -xf data\\ccpd_yolo_500_dataset.tar.gz
```

3. 检查数据集：

```powershell
.venv\\Scripts\\python.exe code\\check_dataset.py --data-yaml data\\ccpd_yolo\\plates.yaml
```

4. 训练并对比两个模型：

```powershell
.venv\\Scripts\\python.exe code\\train_compare.py --data data\\ccpd_yolo\\plates.yaml --project runs\\plate_compare --epochs 100 --imgsz 640 --batch auto --seed 42 --workers 8 --device 0
```

## 注意事项

- 本实验只做车牌定位，不做车牌字符识别。
- 报告中的结论基于 500 张小样本数据，适合作为本次实验结果，不代表所有车牌场景。
- 如果显存不足，可以把 `--batch auto` 改为较小整数，例如 `--batch 8`。
- 如果只需要查看结果，可直接打开 Word 报告和 `figures/` 中的曲线图。
"""


FILES: list[tuple[Path, str]] = [
    (FINAL_REPORT, "report/user_experiment_report.docx"),
    (DATASET_ARCHIVE, "data/ccpd_yolo_500_dataset.tar.gz"),
    (PROJECT_ROOT / "requirements.txt", "requirements.txt"),
    (PROJECT_ROOT / "scripts" / "prepare_ccpd_dataset.py", "code/prepare_ccpd_dataset.py"),
    (PROJECT_ROOT / "scripts" / "check_dataset.py", "code/check_dataset.py"),
    (PROJECT_ROOT / "scripts" / "train_compare.py", "code/train_compare.py"),
    (PROJECT_ROOT / "scripts" / "generate_report.py", "code/generate_report.py"),
]


def add_directory(zip_file: ZipFile, source_dir: Path, archive_dir: str) -> None:
    """把目录中的文件加入压缩包。"""

    for file_path in sorted(source_dir.rglob("*")):
        if file_path.is_file():
            relative_path = file_path.relative_to(source_dir).as_posix()
            zip_file.write(file_path, f"{archive_dir}/{relative_path}")


def validate_sources() -> None:
    """检查交付包所需文件是否存在。"""

    missing = [str(path) for path, _ in FILES if not path.exists()]
    required_dirs = [
        PROJECT_ROOT / "reports" / "deliverables" / "models",
        PROJECT_ROOT / "reports" / "deliverables" / "figures",
    ]
    missing.extend(str(path) for path in required_dirs if not path.exists())
    if missing:
        raise FileNotFoundError("缺少交付文件：\n" + "\n".join(missing))


def main() -> None:
    validate_sources()
    OUTPUT_ZIP.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(OUTPUT_ZIP, "w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("README.md", README)
        for source_path, archive_path in FILES:
            zip_file.write(source_path, archive_path)
        add_directory(zip_file, PROJECT_ROOT / "reports" / "deliverables" / "models", "models")
        add_directory(zip_file, PROJECT_ROOT / "reports" / "deliverables" / "figures", "figures")

    print(OUTPUT_ZIP)


if __name__ == "__main__":
    main()
