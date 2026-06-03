"""生成 F1-Confidence 曲线示意图。

该图只用于解释“正常 F1 曲线大致长什么样”，不是 YOLOv8n 的真实实验结果。
因此图标题、图例和图下方文字均明确标注 schematic/示意图，避免和真实曲线混淆。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


OUTPUT_PATHS = [
    Path("reports/assets/yolov8n_BoxF1_curve_schematic.png"),
    Path("reports/deliverables/figures/yolov8n/BoxF1_curve_schematic.png"),
]


def main() -> None:
    for output_path in OUTPUT_PATHS:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    x = np.linspace(0, 1, 500)

    # 生成一条“正常示意”的 F1 曲线：低阈值快速上升，中间高位平台，
    # 高阈值区域逐渐下降。该曲线仅用于说明形态，不代表真实训练指标。
    rise = 1 / (1 + np.exp(-45 * (x - 0.035)))
    fall = 1 / (1 + np.exp(38 * (x - 0.92)))
    y = 0.94 * rise * fall
    y = np.clip(y + 0.012 * np.sin(10 * x) * rise * fall, 0, 1)

    best_index = int(np.argmax(y))
    best_x = x[best_index]
    best_y = y[best_index]

    plt.figure(figsize=(12, 8), dpi=200)
    plt.plot(x, y, color="#1f77b4", linewidth=1.8, label="license_plate (schematic)")
    plt.plot(
        x,
        y,
        color="blue",
        linewidth=4.0,
        label=f"all classes {best_y:.2f} at {best_x:.3f} (schematic)",
    )
    plt.title("F1-Confidence Curve (Schematic)", fontsize=20, pad=12)
    plt.xlabel("Confidence", fontsize=16)
    plt.ylabel("F1", fontsize=16)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.grid(False)
    plt.legend(loc="upper left", bbox_to_anchor=(1.03, 1.0), fontsize=14, frameon=True)
    plt.text(
        0.5,
        -0.14,
        "Schematic only: illustrates a normal curve shape, not a real experiment result",
        ha="center",
        va="top",
        transform=plt.gca().transAxes,
        fontsize=12,
        color="crimson",
    )
    plt.tight_layout(rect=[0, 0.04, 0.82, 1])

    for output_path in OUTPUT_PATHS:
        plt.savefig(output_path, bbox_inches="tight")
        print(output_path)

    plt.close()


if __name__ == "__main__":
    main()
