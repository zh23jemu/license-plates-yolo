"""为 DOCX 渲染页面生成检查用缩略图拼图。"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    source_dir = Path("reports/rendered_b6b7_report")
    output_path = Path("reports/rendered_b6b7_report_contact_sheet.png")
    files = sorted(source_dir.glob("page-*.png"), key=lambda path: int(path.stem.split("-")[1]))

    thumbs: list[Image.Image] = []
    thumb_width = 360
    for file_path in files:
        image = Image.open(file_path).convert("RGB")
        image.thumbnail((thumb_width, 520))
        canvas = Image.new("RGB", (thumb_width, image.height + 30), "white")
        canvas.paste(image, ((thumb_width - image.width) // 2, 0))
        ImageDraw.Draw(canvas).text((8, image.height + 8), file_path.name, fill=(0, 0, 0))
        thumbs.append(canvas)

    columns = 3
    rows = math.ceil(len(thumbs) / columns)
    cell_height = max(thumb.height for thumb in thumbs)
    sheet = Image.new("RGB", (columns * thumb_width, rows * cell_height), "white")

    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % columns) * thumb_width, (index // columns) * cell_height))

    sheet.save(output_path)
    print(output_path)


if __name__ == "__main__":
    main()
