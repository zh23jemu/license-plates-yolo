"""调整用户版 Word 报告章节顺序。

目标顺序：
1-7 原实验内容
8 训练曲线与可视化结果
9 结论
10 局限性与后续工作

此前插图脚本将训练曲线追加在结论和后续工作之后，用户要求“结论和后续工作在最后”。
本脚本通过移动 Word OOXML 段落/图片元素完成重排，并同步修正章节编号和图号。
"""

from __future__ import annotations

from pathlib import Path

from docx import Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = PROJECT_ROOT / "reports" / "b6b7cd57_rewritten_2780877452_user_experiment_report.docx"


def paragraph_text(element) -> str:
    """提取段落 XML 元素中的纯文本。"""

    texts = element.xpath(".//w:t")
    return "".join(node.text or "" for node in texts).strip()


def find_paragraph_index(body_elements: list, startswith: str) -> int:
    """查找指定标题所在的 body 元素下标。"""

    for index, element in enumerate(body_elements):
        if element.tag.endswith("}p") and paragraph_text(element).startswith(startswith):
            return index
    raise ValueError(f"未找到标题：{startswith}")


def replace_text_in_element(element, replacements: dict[str, str]) -> None:
    """在元素的所有文本节点中执行简单替换。"""

    for text_node in element.xpath(".//w:t"):
        if not text_node.text:
            continue
        new_text = text_node.text
        for old, new in replacements.items():
            new_text = new_text.replace(old, new)
        text_node.text = new_text


def insert_before_section_properties(body, element) -> None:
    """把元素插入到文档末尾的 sectPr 之前，避免破坏节属性。"""

    section_properties = body.sectPr
    if section_properties is None:
        body.append(element)
    else:
        section_properties.addprevious(element)


def main() -> None:
    document = Document(DOCX_PATH)
    body = document._body._element
    elements = list(body)

    conclusion_start = find_paragraph_index(elements, "8. 结论")
    figures_start = find_paragraph_index(elements, "10. 训练曲线与可视化结果")

    if conclusion_start > figures_start:
        print("章节顺序已经满足要求，无需调整。")
        return

    conclusion_block = elements[conclusion_start:figures_start]

    # 先从原位置移除“结论”和“局限性与后续工作”块。
    for element in conclusion_block:
        body.remove(element)

    replacements_for_existing_body = {
        "10. 训练曲线与可视化结果": "8. 训练曲线与可视化结果",
        "10.1 YOLOv8n 曲线图与结果图": "8.1 YOLOv8n 曲线图与结果图",
        "10.2 YOLOv10n 曲线图与结果图": "8.2 YOLOv10n 曲线图与结果图",
        "10.3 图表结果说明": "8.3 图表结果说明",
        "图 10-": "图 8-",
    }

    replacements_for_conclusion = {
        "8. 结论": "9. 结论",
        "9. 局限性与后续工作": "10. 局限性与后续工作",
    }

    # 更新剩余正文中的训练曲线章节编号和图号。
    for element in list(body):
        replace_text_in_element(element, replacements_for_existing_body)

    # 更新移动块中的结论/后续工作编号，并追加到文档末尾。
    for element in conclusion_block:
        replace_text_in_element(element, replacements_for_conclusion)
        insert_before_section_properties(body, element)

    document.save(DOCX_PATH)
    print(DOCX_PATH)


if __name__ == "__main__":
    main()
