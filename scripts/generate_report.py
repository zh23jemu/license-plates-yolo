"""根据训练输出生成 Markdown 实验报告。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def format_metric(value: float | None) -> str:
    """格式化报告表格中的指标。"""

    if value is None:
        return "N/A"
    return f"{value:.4f}"


def load_metrics(project_dir: Path) -> list[dict]:
    """读取训练脚本保存的对比指标。"""

    metrics_path = project_dir / "comparison_metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"未找到指标文件：{metrics_path}")
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def decide_winner(metrics: list[dict]) -> str:
    """基于 mAP50-95 判断精度更高的模型。"""

    valid_metrics = [item for item in metrics if item.get("map50_95") is not None]
    if len(valid_metrics) < 2:
        return "当前指标不完整，暂无法判断哪个模型精度更高。"

    ordered = sorted(valid_metrics, key=lambda item: item["map50_95"], reverse=True)
    best = ordered[0]
    second = ordered[1]
    if best["map50_95"] == second["map50_95"]:
        return "两个模型在 mAP50-95 上相同，本次小样本实验未体现明显精度差异。"
    return f"按 mAP50-95 指标，本次实验中 `{best['model']}` 的车牌定位精度更高。"


def build_table(metrics: list[dict]) -> str:
    """生成 Markdown 指标表格。"""

    lines = [
        "| 模型 | Precision | Recall | mAP50 | mAP50-95 | 推理耗时/ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in metrics:
        lines.append(
            "| {model} | {precision} | {recall} | {map50} | {map50_95} | {speed} |".format(
                model=item.get("model", "N/A"),
                precision=format_metric(item.get("precision")),
                recall=format_metric(item.get("recall")),
                map50=format_metric(item.get("map50")),
                map50_95=format_metric(item.get("map50_95")),
                speed=format_metric(item.get("speed_inference_ms")),
            )
        )
    return "\n".join(lines)


def generate_report(project_dir: Path, output_path: Path) -> None:
    """生成完整 Markdown 报告。"""

    metrics = load_metrics(project_dir)
    table = build_table(metrics)
    conclusion = decide_winner(metrics)

    content = f"""# YOLOv8n 与 YOLOv10n 车牌定位对比实验报告

## 1. 实验目的

本实验只研究车牌定位任务，即在图片中检测车牌位置，不进行车牌字符识别。实验使用原始 YOLOv8n 与 YOLOv10n 预训练权重，在相同数据集、训练参数和评价指标下进行对比，判断哪个模型在本次小样本车牌定位实验中精度更高。

## 2. 数据集

实验数据来自 CCPD 公开车牌数据集。CCPD 的车牌框坐标包含在图片文件名中，本项目通过脚本解析文件名中的水平矩形框，并转换为 YOLO 单类别检测标签。类别仅包含：

- `license_plate`

默认抽样规模为 500 张左右，并按 `train/val/test = 70/20/10` 划分。

## 3. 实验设置

- 模型：`yolov8n.pt`、`yolov10n.pt`
- 任务：单类别车牌检测
- 输入尺寸：640
- 训练轮数：100
- Batch：自动估算或按运行命令指定
- 随机种子：42
- 评价集：test

两个模型除初始权重不同外，其余训练和评价参数保持一致。本实验不进行模型结构改进、额外调参搜索、蒸馏或自定义增强策略。

## 4. 评价指标

本实验主要记录以下指标：

- Precision：预测框中正确车牌框的比例。
- Recall：真实车牌框被成功检出的比例。
- mAP50：IoU 阈值为 0.50 时的平均精度。
- mAP50-95：IoU 阈值从 0.50 到 0.95 时的平均精度，更适合作为综合定位精度指标。
- 推理耗时：Ultralytics 验证阶段统计的单图推理时间。

## 5. 实验结果

{table}

训练输出目录：

- `{project_dir}`

预测可视化结果位于各模型对应的 `*_predict` 目录，可从中选取车牌定位效果图放入答辩或提交材料。

## 6. 结论

{conclusion}

需要注意的是，本实验默认只抽取几百张 CCPD 图片，数据规模较小，因此结论仅代表当前小样本实验设置下的结果。
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"实验报告已生成：{output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据训练指标生成 Markdown 实验报告")
    parser.add_argument("--project", type=Path, default=Path("runs/plate_compare"), help="训练输出目录")
    parser.add_argument("--output", type=Path, default=Path("reports/experiment_report.md"), help="报告输出路径")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_report(project_dir=args.project, output_path=args.output)


if __name__ == "__main__":
    main()
