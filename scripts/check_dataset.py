"""检查 YOLO 车牌定位数据集的基本一致性。"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def read_yaml(data_yaml: Path) -> dict:
    """读取 Ultralytics 数据集配置文件。"""

    with data_yaml.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def resolve_dataset_root(data_yaml: Path, config: dict) -> Path:
    """解析数据集根目录。

    Ultralytics 的 `path` 字段既可能是绝对路径，也可能是相对 `plates.yaml`
    所在目录的路径。这里兼容两种写法，方便用户迁移数据集目录。
    """

    root = Path(config["path"])
    if root.is_absolute():
        return root
    return (data_yaml.parent / root).resolve()


def check_label_file(label_path: Path) -> list[str]:
    """检查单个 YOLO 标签文件是否合法。"""

    errors: list[str] = []
    lines = label_path.read_text(encoding="utf-8").strip().splitlines()
    if len(lines) != 1:
        errors.append(f"{label_path} 应只有 1 个车牌框，实际为 {len(lines)} 行")
        return errors

    parts = lines[0].split()
    if len(parts) != 5:
        errors.append(f"{label_path} 标签列数不是 5")
        return errors

    class_id = parts[0]
    if class_id != "0":
        errors.append(f"{label_path} 类别 id 应为 0，实际为 {class_id}")

    for value in parts[1:]:
        number = float(value)
        if number < 0 or number > 1:
            errors.append(f"{label_path} 归一化坐标越界：{value}")

    return errors


def check_split(dataset_root: Path, split_name: str, image_rel_dir: str) -> list[str]:
    """检查一个数据划分中的图片与标签是否一一对应。"""

    errors: list[str] = []
    image_dir = dataset_root / image_rel_dir
    label_dir = dataset_root / "labels" / split_name

    if not image_dir.exists():
        return [f"图片目录不存在：{image_dir}"]
    if not label_dir.exists():
        return [f"标签目录不存在：{label_dir}"]

    images = sorted(path for path in image_dir.iterdir() if path.is_file())
    if not images:
        errors.append(f"{split_name} 划分没有图片")

    for image_path in images:
        label_path = label_dir / f"{image_path.stem}.txt"
        if not label_path.exists():
            errors.append(f"缺少标签：{label_path}")
            continue
        errors.extend(check_label_file(label_path))

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查 YOLO 车牌定位数据集")
    parser.add_argument("--data-yaml", type=Path, required=True, help="数据集 plates.yaml 路径")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = read_yaml(args.data_yaml)
    dataset_root = resolve_dataset_root(args.data_yaml, config)

    errors: list[str] = []
    for split_name in ("train", "val", "test"):
        errors.extend(check_split(dataset_root, split_name, config[split_name]))

    if errors:
        print("数据集检查失败：")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"数据集检查通过：{args.data_yaml}")


if __name__ == "__main__":
    main()
