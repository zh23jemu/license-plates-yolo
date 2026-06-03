"""向用户版 Word 实验报告中插入训练曲线、混淆矩阵和说明文字。

该脚本专门处理已经生成好的 Word 报告：
`reports/b6b7cd57_rewritten_2780877452_user_experiment_report.docx`。

新增内容放在文档末尾，作为“训练曲线与可视化结果”章节，包含：
- YOLOv8n 与 YOLOv10n 的 F1 曲线、PR 曲线、P 曲线、R 曲线；
- YOLOv8n 与 YOLOv10n 的混淆矩阵；
- YOLOv8n 与 YOLOv10n 的训练结果曲线；
- 每类图对应的中文说明，便于用户理解这些图表示什么。
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = PROJECT_ROOT / "reports" / "b6b7cd57_rewritten_2780877452_user_experiment_report.docx"
FIGURE_ROOT = PROJECT_ROOT / "reports" / "deliverables" / "figures"

CHINESE_BODY_FONT = "宋体"
CHINESE_HEADING_FONT = "黑体"
ENGLISH_FONT = "Times New Roman"


FIGURES = [
    (
        "YOLOv8n",
        [
            ("BoxF1_curve.png", "图 10-1 YOLOv8n 的 F1 曲线", "F1 曲线反映不同置信度阈值下 Precision 与 Recall 的综合表现，曲线越高表示模型在该阈值范围内综合检测效果越好。"),
            ("BoxPR_curve.png", "图 10-2 YOLOv8n 的 PR 曲线", "PR 曲线展示 Precision 与 Recall 之间的关系，可用于观察模型在提高召回率时精确率的变化情况。"),
            ("BoxP_curve.png", "图 10-3 YOLOv8n 的 Precision 曲线", "Precision 曲线反映不同置信度阈值下预测框的准确程度，数值越高说明误检越少。"),
            ("BoxR_curve.png", "图 10-4 YOLOv8n 的 Recall 曲线", "Recall 曲线反映不同置信度阈值下真实车牌被检出的比例，数值越高说明漏检越少。"),
            ("confusion_matrix.png", "图 10-5 YOLOv8n 的混淆矩阵", "混淆矩阵用于观察预测类别与真实类别之间的对应关系。本实验只有 license_plate 一个类别，因此主要用于检查车牌目标是否被正确归入唯一类别。"),
            ("results.png", "图 10-6 YOLOv8n 的训练结果曲线", "训练结果曲线展示 box loss、cls loss、dfl loss 以及验证集 mAP 等指标随 epoch 的变化，可用于观察模型收敛趋势。"),
        ],
    ),
    (
        "YOLOv10n",
        [
            ("BoxF1_curve.png", "图 10-7 YOLOv10n 的 F1 曲线", "F1 曲线用于综合比较模型在不同阈值下的查准率和查全率表现，能直观看出模型整体检测稳定性。"),
            ("BoxPR_curve.png", "图 10-8 YOLOv10n 的 PR 曲线", "PR 曲线越靠近右上方，说明模型在较高召回率下仍能保持较高精确率，检测质量更好。"),
            ("BoxP_curve.png", "图 10-9 YOLOv10n 的 Precision 曲线", "Precision 曲线用于观察模型在不同置信度阈值下的误检控制能力。"),
            ("BoxR_curve.png", "图 10-10 YOLOv10n 的 Recall 曲线", "Recall 曲线用于观察模型在不同置信度阈值下的目标检出能力。"),
            ("confusion_matrix.png", "图 10-11 YOLOv10n 的混淆矩阵", "混淆矩阵可以辅助判断模型是否能将车牌目标稳定识别为 license_plate 类别。"),
            ("results.png", "图 10-12 YOLOv10n 的训练结果曲线", "训练结果曲线展示训练损失和验证指标变化，可用于判断 YOLOv10n 在本实验数据上的收敛情况。"),
        ],
    ),
]


def set_run_font(run, chinese_font: str, english_font: str, size: Pt, bold: bool = False) -> None:
    """设置中英文混排字体。"""

    run.font.name = english_font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), chinese_font)
    run.font.size = size
    run.bold = bold


def set_body_paragraph(paragraph, first_line_indent: bool = True) -> None:
    """设置正文段落格式：宋体小四、首行缩进、1.5 倍行距。"""

    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)
    if first_line_indent:
        paragraph.paragraph_format.first_line_indent = Pt(24)


def add_text(document: Document, text: str, *, bold: bool = False, first_line_indent: bool = True) -> None:
    """添加正文说明文字。"""

    paragraph = document.add_paragraph()
    set_body_paragraph(paragraph, first_line_indent=first_line_indent)
    run = paragraph.add_run(text)
    set_run_font(run, CHINESE_BODY_FONT, ENGLISH_FONT, Pt(12), bold=bold)


def add_heading(document: Document, text: str, level: int) -> None:
    """添加符合报告格式的标题。"""

    paragraph = document.add_paragraph()
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    paragraph.paragraph_format.space_before = Pt(12 if level == 1 else 6)
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.first_line_indent = None
    run = paragraph.add_run(text)
    set_run_font(run, CHINESE_HEADING_FONT, ENGLISH_FONT, Pt(14 if level == 1 else 12), bold=True)


def add_caption(document: Document, caption: str) -> None:
    """添加居中的图片题注。"""

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run(caption)
    set_run_font(run, CHINESE_BODY_FONT, ENGLISH_FONT, Pt(10.5))


def add_picture_block(document: Document, image_path: Path, caption: str, note: str) -> None:
    """添加一张图片、题注和解释说明。"""

    if not image_path.exists():
        raise FileNotFoundError(f"缺少图片文件：{image_path}")

    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(0)
    run = paragraph.add_run()
    run.add_picture(str(image_path), width=Cm(13.5))
    add_caption(document, caption)
    add_text(document, note)


def add_page_break(document: Document) -> None:
    """添加分页符，避免图片章节与前文挤在同一页。"""

    paragraph = document.add_paragraph()
    run = paragraph.add_run()
    run.add_break()


def remove_empty_last_paragraph(document: Document) -> None:
    """减少保存过程中可能留下的末尾空段落。"""

    if document.paragraphs and not document.paragraphs[-1].text.strip():
        paragraph = document.paragraphs[-1]._element
        paragraph.getparent().remove(paragraph)


def append_figures() -> None:
    """向目标 Word 文档追加图表章节。"""

    document = Document(DOCX_PATH)

    add_page_break(document)
    add_heading(document, "10. 训练曲线与可视化结果", level=1)
    add_text(
        document,
        "训练完成后，Ultralytics 会在每个模型的输出目录中自动生成 F1 曲线、PR 曲线、Precision 曲线、Recall 曲线、混淆矩阵和训练结果曲线。"
        "这些图可以从不同角度辅助分析模型的检测效果和训练收敛情况。",
    )

    for model_name, model_figures in FIGURES:
        add_heading(document, f"10.{1 if model_name == 'YOLOv8n' else 2} {model_name} 曲线图与结果图", level=2)
        model_dir = FIGURE_ROOT / model_name.lower()
        for file_name, caption, note in model_figures:
            add_picture_block(document, model_dir / file_name, caption, note)

    add_heading(document, "10.3 图表结果说明", level=2)
    add_text(
        document,
        "从曲线图可以看出，两个模型在本次 500 张 CCPD 小样本车牌定位实验中均能完成收敛，并在验证指标上取得较高表现。"
        "其中，PR 曲线和 F1 曲线用于观察不同置信度阈值下的综合检测效果；Precision 和 Recall 曲线分别反映误检控制能力与漏检控制能力；"
        "混淆矩阵用于检查类别预测是否稳定；results 曲线用于观察训练损失和验证指标随 epoch 的变化。"
    )
    add_text(
        document,
        "结合前文指标表，YOLOv10n 在 mAP50 和 mAP50-95 上略高于 YOLOv8n，因此本实验最终认为 YOLOv10n 在该小样本车牌定位任务中的综合定位精度更高。"
    )

    remove_empty_last_paragraph(document)
    document.save(DOCX_PATH)
    print(DOCX_PATH)


if __name__ == "__main__":
    append_figures()
