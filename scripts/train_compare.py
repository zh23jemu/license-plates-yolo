"""同条件训练并评估 YOLOv8n 与 YOLOv10n 车牌定位模型。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from ultralytics import YOLO


DEFAULT_MODELS = ("yolov8n.pt", "yolov10n.pt")


def normalize_batch(batch: str) -> int | float:
    """解析 batch 参数。

    Ultralytics 支持 `batch=-1` 自动估算显存可承受的 batch size。
    为了命令行更直观，这里允许用户传入 `auto`。
    """

    if batch.lower() == "auto":
        return -1
    if "." in batch:
        return float(batch)
    return int(batch)


def metric_to_float(value: Any) -> float | None:
    """把 Ultralytics 返回的指标安全转换为浮点数。"""

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def collect_metrics(metrics: Any) -> dict[str, float | None]:
    """从 Ultralytics 验证结果中提取报告需要的核心指标。"""

    box = getattr(metrics, "box", None)
    speed = getattr(metrics, "speed", None) or {}

    return {
        "precision": metric_to_float(getattr(box, "mp", None)),
        "recall": metric_to_float(getattr(box, "mr", None)),
        "map50": metric_to_float(getattr(box, "map50", None)),
        "map50_95": metric_to_float(getattr(box, "map", None)),
        "speed_preprocess_ms": metric_to_float(speed.get("preprocess")),
        "speed_inference_ms": metric_to_float(speed.get("inference")),
        "speed_postprocess_ms": metric_to_float(speed.get("postprocess")),
    }


def resolve_dataset_root(data_yaml: Path, config: dict[str, Any]) -> Path:
    """解析 `plates.yaml` 中的数据集根目录。"""

    root = Path(config["path"])
    if root.is_absolute():
        return root
    return (data_yaml.parent / root).resolve()


def resolve_predict_source(data_yaml: Path, explicit_source: Path | None) -> Path:
    """确定预测可视化图片来源。

    如果用户显式传入 `--predict-source`，直接使用该目录或图片文件。
    否则读取数据集配置中的 test 图片目录，避免把 YAML 配置文件误传给
    Ultralytics `predict`。
    """

    if explicit_source is not None:
        return explicit_source

    with data_yaml.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    dataset_root = resolve_dataset_root(data_yaml, config)
    test_source = Path(config.get("test", config.get("val", "images/val")))
    if test_source.is_absolute():
        return test_source
    return dataset_root / test_source


def train_one_model(args: argparse.Namespace, model_weight: str) -> dict[str, float | None | str]:
    """训练并验证单个模型。

    两个模型只改变初始权重名称，其余训练参数保持一致，以保证对比公平。
    """

    model_name = Path(model_weight).stem
    model = YOLO(model_weight)

    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=normalize_batch(args.batch),
        project=str(args.project),
        name=model_name,
        seed=args.seed,
        workers=args.workers,
        device=args.device,
        patience=args.patience,
        exist_ok=True,
    )

    best_weight = args.project / model_name / "weights" / "best.pt"
    eval_model = YOLO(str(best_weight))
    predict_source = resolve_predict_source(args.data, args.predict_source)

    val_metrics = eval_model.val(
        data=str(args.data),
        split="test",
        imgsz=args.imgsz,
        batch=normalize_batch(args.batch),
        project=str(args.project),
        name=f"{model_name}_test",
        device=args.device,
        exist_ok=True,
    )

    # 保存一小批测试集预测图，报告中可以直接引用这些可视化结果。
    eval_model.predict(
        source=str(predict_source),
        imgsz=args.imgsz,
        conf=args.conf,
        project=str(args.project),
        name=f"{model_name}_predict",
        device=args.device,
        save=True,
        exist_ok=True,
    )

    result = collect_metrics(val_metrics)
    result["model"] = model_weight
    result["run_dir"] = str(args.project / model_name)
    result["test_dir"] = str(args.project / f"{model_name}_test")
    result["predict_dir"] = str(args.project / f"{model_name}_predict")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="训练并对比 YOLOv8n 与 YOLOv10n 的车牌定位精度")
    parser.add_argument("--data", type=Path, default=Path("data/ccpd_yolo/plates.yaml"), help="Ultralytics 数据集配置")
    parser.add_argument("--project", type=Path, default=Path("runs/plate_compare"), help="训练输出目录")
    parser.add_argument("--models", nargs="+", default=list(DEFAULT_MODELS), help="待对比的模型权重")
    parser.add_argument("--epochs", type=int, default=100, help="训练轮数")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸")
    parser.add_argument("--batch", default="auto", help="batch size，支持整数或 auto")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--workers", type=int, default=8, help="DataLoader worker 数")
    parser.add_argument("--device", default=0, help="训练设备，例如 0、0,1 或 cpu")
    parser.add_argument("--patience", type=int, default=30, help="早停耐心轮数")
    parser.add_argument("--conf", type=float, default=0.25, help="预测可视化置信度阈值")
    parser.add_argument("--predict-source", type=Path, default=None, help="可选预测图片目录；不填则由 Ultralytics 使用数据配置")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.project.mkdir(parents=True, exist_ok=True)

    results = [train_one_model(args, model_weight) for model_weight in args.models]
    metrics_path = args.project / "comparison_metrics.json"
    metrics_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"对比指标已保存：{metrics_path}")


if __name__ == "__main__":
    main()
