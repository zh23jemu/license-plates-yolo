"""将 CCPD 车牌图片转换为 YOLO 单类别检测数据集。

CCPD 数据集的车牌标注通常写在图片文件名中，常见格式为：
    area-tilt-bbox-points-plate-brightness-blur.jpg

其中第 3 段 bbox 形如：
    left&top_right&bottom

本脚本只使用水平矩形框作为检测标签，不解析车牌字符，也不使用角点 OBB。
"""

from __future__ import annotations

import argparse
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

import cv2
import yaml


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}
SPLITS = {"train": 0.7, "val": 0.2, "test": 0.1}


@dataclass(frozen=True)
class PlateBox:
    """保存 CCPD 文件名中解析出的车牌水平矩形框。"""

    left: int
    top: int
    right: int
    bottom: int

    def to_yolo(self, image_width: int, image_height: int) -> tuple[float, float, float, float]:
        """将像素坐标转换为 YOLO 归一化格式。

        YOLO 检测标签需要使用中心点坐标和宽高，且全部归一化到 0 到 1。
        这里会先把坐标裁剪到图片边界内，避免少量异常文件名导致标签越界。
        """

        left = max(0, min(self.left, image_width - 1))
        right = max(0, min(self.right, image_width - 1))
        top = max(0, min(self.top, image_height - 1))
        bottom = max(0, min(self.bottom, image_height - 1))

        if right <= left or bottom <= top:
            raise ValueError("车牌框宽高无效，无法转换为 YOLO 标签")

        box_width = right - left
        box_height = bottom - top
        x_center = left + box_width / 2
        y_center = top + box_height / 2

        return (
            x_center / image_width,
            y_center / image_height,
            box_width / image_width,
            box_height / image_height,
        )


def parse_ccpd_bbox(image_path: Path) -> PlateBox:
    """从 CCPD 图片文件名中解析车牌框。

    CCPD 文件名以短横线分隔多段信息，第 3 段通常是矩形框坐标。
    如果文件名不符合预期，调用方会记录并跳过该图片，保证数据集构建不中断。
    """

    parts = image_path.stem.split("-")
    if len(parts) < 3:
        raise ValueError(f"文件名段数不足，无法解析 CCPD 标注：{image_path.name}")

    bbox_part = parts[2]
    points = bbox_part.split("_")
    if len(points) != 2:
        raise ValueError(f"车牌框字段格式异常：{image_path.name}")

    left_top = points[0].split("&")
    right_bottom = points[1].split("&")
    if len(left_top) != 2 or len(right_bottom) != 2:
        raise ValueError(f"车牌框坐标格式异常：{image_path.name}")

    left, top = int(left_top[0]), int(left_top[1])
    right, bottom = int(right_bottom[0]), int(right_bottom[1])
    return PlateBox(left=left, top=top, right=right, bottom=bottom)


def collect_images(source_dir: Path) -> list[Path]:
    """递归收集 CCPD 原始图片。"""

    return sorted(path for path in source_dir.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)


def split_images(images: list[Path], seed: int) -> dict[str, list[Path]]:
    """按固定随机种子划分 train/val/test，确保实验可复现。"""

    shuffled = images[:]
    random.Random(seed).shuffle(shuffled)

    train_end = int(len(shuffled) * SPLITS["train"])
    val_end = train_end + int(len(shuffled) * SPLITS["val"])

    return {
        "train": shuffled[:train_end],
        "val": shuffled[train_end:val_end],
        "test": shuffled[val_end:],
    }


def write_label(image_path: Path, label_path: Path) -> None:
    """读取图片尺寸并写出单类别 YOLO 标签。"""

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"OpenCV 无法读取图片：{image_path}")

    image_height, image_width = image.shape[:2]
    plate_box = parse_ccpd_bbox(image_path)
    x_center, y_center, box_width, box_height = plate_box.to_yolo(image_width, image_height)

    label_path.parent.mkdir(parents=True, exist_ok=True)
    label_path.write_text(
        f"0 {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}\n",
        encoding="utf-8",
    )


def copy_image(source: Path, target: Path) -> None:
    """复制图片到目标数据集目录。

    使用复制而不是软链接，便于在 Slurm 节点、共享文件系统和 Windows 本地之间迁移。
    如果目标文件已存在，覆盖复制可以保证重复运行脚本后数据内容与当前抽样一致。
    """

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def build_dataset(source_dir: Path, output_dir: Path, sample_size: int, seed: int) -> None:
    """构建 YOLO 数据集目录和 `plates.yaml`。"""

    images = collect_images(source_dir)
    if not images:
        raise FileNotFoundError(f"未在目录中找到图片：{source_dir}")

    if sample_size > 0:
        images = images[:]
        random.Random(seed).shuffle(images)
        images = images[: min(sample_size, len(images))]

    split_map = split_images(images, seed)
    skipped: list[str] = []
    written_count = 0

    for split_name, split_images_list in split_map.items():
        for source_image in split_images_list:
            target_image = output_dir / "images" / split_name / source_image.name
            target_label = output_dir / "labels" / split_name / f"{source_image.stem}.txt"

            try:
                write_label(source_image, target_label)
                copy_image(source_image, target_image)
                written_count += 1
            except Exception as exc:  # noqa: BLE001
                # 少量异常图片不应阻断整个小样本实验，统一记录后跳过。
                skipped.append(f"{source_image}: {exc}")

    data_yaml = {
        "path": str(output_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {0: "license_plate"},
    }
    (output_dir / "plates.yaml").write_text(
        yaml.safe_dump(data_yaml, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    if skipped:
        log_dir = output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "skipped_files.txt").write_text("\n".join(skipped) + "\n", encoding="utf-8")

    print(f"已写入 {written_count} 张图片及标签，输出目录：{output_dir}")
    if skipped:
        print(f"跳过 {len(skipped)} 个异常文件，详情见：{output_dir / 'logs' / 'skipped_files.txt'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 CCPD 原始图片转换为 YOLO 车牌定位数据集")
    parser.add_argument("--source", type=Path, required=True, help="CCPD 原始图片目录")
    parser.add_argument("--output", type=Path, default=Path("data/ccpd_yolo"), help="YOLO 数据集输出目录")
    parser.add_argument("--sample-size", type=int, default=500, help="抽样图片数量，设为 0 表示使用全部图片")
    parser.add_argument("--seed", type=int, default=42, help="随机种子，用于抽样和数据集划分")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_dataset(
        source_dir=args.source,
        output_dir=args.output,
        sample_size=args.sample_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
