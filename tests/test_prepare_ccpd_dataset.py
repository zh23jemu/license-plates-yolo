from pathlib import Path

from scripts.prepare_ccpd_dataset import PlateBox, parse_ccpd_bbox


def test_parse_ccpd_bbox_from_filename() -> None:
    """验证能从 CCPD 文件名第 3 段解析出水平矩形框。"""

    image_path = Path("025-95_113-154&383_386&473-386&473_177&454_154&383_363&402-0_0_22_27_27_33_16-37-15.jpg")

    plate_box = parse_ccpd_bbox(image_path)

    assert plate_box == PlateBox(left=154, top=383, right=386, bottom=473)


def test_plate_box_to_yolo_normalized_values() -> None:
    """验证像素框会被转换为 YOLO 所需的归一化中心点和宽高。"""

    plate_box = PlateBox(left=100, top=50, right=300, bottom=150)

    x_center, y_center, width, height = plate_box.to_yolo(image_width=400, image_height=200)

    assert x_center == 0.5
    assert y_center == 0.5
    assert width == 0.5
    assert height == 0.5
