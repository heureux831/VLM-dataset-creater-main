"""
海运单关键字识别 - 文本框提取脚本
Bill of Lading Keyword Recognition - Paragraph Extraction Script

此脚本从海运单PDF中提取文本框并生成可视化图像，
为后续的VLM标注做准备。
"""

import logging
from pathlib import Path
import shutil
import os
import sys

import babeldoc.high_level
import babeldoc.translation_config
import cv2
import numpy as np
import pymupdf
from babeldoc.document_il import il_version_1
from babeldoc.docvision import doclayout
from babeldoc.document_il.midend.detect_scanned_file import DetectScannedFile
from babeldoc.document_il.midend.layout_parser import LayoutParser
from babeldoc.document_il.midend.table_parser import TableParser
from babeldoc.document_il.midend.paragraph_finder import ParagraphFinder
from babeldoc.document_il.utils.layout_helper import get_char_unicode_string
from rich.logging import RichHandler
from babeldoc.docvision.table_detection.rapidocr import RapidOCRModel
from config import DEFAULT_CONFIG

# 加载文档布局模型
logger = logging.getLogger(__name__)
onnx = doclayout.DocLayoutModel.load_available()

def parse_pdf(pdf_path, only_first_page=True) -> il_version_1.Document:
    """
    解析PDF文件并提取文档结构

    Args:
        pdf_path: PDF文件路径
        only_first_page: 是否只处理第一页

    Returns:
        Document: 解析后的文档对象
    """
    translation_config = babeldoc.translation_config.TranslationConfig(
        *[None for _ in range(4)],
        doc_layout_model=onnx,
        table_model=RapidOCRModel(),
    )

    if only_first_page:
        translation_config.page_ranges = [(1, 1)]

    translation_config.progress_monitor = babeldoc.high_level.ProgressMonitor(
        babeldoc.high_level.TRANSLATE_STAGES
    )

    try:
        shutil.copy(pdf_path, translation_config.get_working_file_path("input.pdf"))
        doc = pymupdf.open(pdf_path)
        il_creater = babeldoc.high_level.ILCreater(translation_config)
        il_creater.mupdf = doc

        with open(translation_config.get_working_file_path("input.pdf"), "rb") as f:
            babeldoc.high_level.start_parse_il(
                f,
                doc_zh=doc,
                resfont="test_font",
                il_creater=il_creater,
                translation_config=translation_config,
            )

        il = il_creater.create_il()
        doc.close()
        doc = pymupdf.open(pdf_path)

        DetectScannedFile(translation_config).process(il)
        il = LayoutParser(translation_config).process(il, doc)
        ParagraphFinder(translation_config).process(il)
        il = TableParser(translation_config).process(il, doc)

        return il
    finally:
        translation_config.cleanup_temp_files()

    return None

def extract_paragraph_line(pdf_path, only_first_page=True):
    """
    从PDF中提取段落行和文本框

    Args:
        pdf_path: PDF文件路径
        only_first_page: 是否只处理第一页

    Returns:
        dict: {page_number: [(box, text), ...]}
    """
    il = parse_pdf(pdf_path, only_first_page=only_first_page)

    if il is None:
        return None

    line_boxes = {}
    for page in il.page:
        line_boxes[page.page_number] = []
        for paragraph in page.pdf_paragraph:
            for comp in paragraph.pdf_paragraph_composition:
                if comp.pdf_line:
                    line = comp.pdf_line
                    line_boxes[page.page_number].append(
                        (line.box, get_char_unicode_string(line.pdf_character))
                    )

    return line_boxes

def draw_line_boxes_to_image(pdf_path, line_boxes, output_path):
    """
    将文本框绘制到图像上并保存

    Args:
        pdf_path: PDF文件路径
        line_boxes: 文本框字典
        output_path: 输出目录路径
    """
    doc = pymupdf.open(pdf_path)
    debug_dir = Path(output_path)
    debug_dir.mkdir(parents=True, exist_ok=True)

    for page_number, boxes in line_boxes.items():
        page = doc[page_number]
        pixmap = page.get_pixmap(dpi=DEFAULT_CONFIG.get("image_dpi", 300))
        image_height = pixmap.height
        image_width = pixmap.width

        # 转换PyMuPDF pixmap为numpy数组
        samples = bytearray(pixmap.samples)
        image_array = np.frombuffer(samples, dtype=np.uint8).reshape(
            image_height,
            image_width,
            pixmap.n
        )

        # 转换BGR到RGB
        if pixmap.n == 3 or pixmap.n == 4:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        # 保存原始图像
        cv2.imwrite(str(debug_dir / f"{page_number}.png"), image_array)

        # 创建标注图像的副本
        annotated_image = image_array.copy()

        # 获取页面尺寸
        page_rect = page.rect
        page_height = page_rect.height

        box_id = 0
        for box, text in boxes:
            # PDF坐标（原点左下）
            pdf_x0, pdf_y0, pdf_x1, pdf_y1 = box.x, box.y, box.x2, box.y2

            # 转换为图像坐标（原点左上）
            x_scale = image_width / page_rect.width
            y_scale = image_height / page_height

            # 垂直翻转Y坐标
            img_x0 = int(pdf_x0 * x_scale)
            img_y0 = int(image_height - (pdf_y0 * y_scale))
            img_x1 = int(pdf_x1 * x_scale)
            img_y1 = int(image_height - (pdf_y1 * y_scale))

            x_center = (img_x0 + img_x1) / 2
            y_center = (img_y0 + img_y1) / 2
            width = img_x1 - img_x0
            height = img_y0 - img_y1

            # 归一化坐标
            x_center_norm = x_center / image_width
            y_center_norm = y_center / image_height
            width_norm = width / image_width
            height_norm = height / image_height

            # 更新box对象
            box.x, box.y, box.x2, box.y2 = x_center_norm, y_center_norm, width_norm, height_norm

            # 绘制边界框
            cv2.rectangle(
                annotated_image,
                (img_x0, img_y1),  # 左上
                (img_x1, img_y0),  # 右下
                (0, 255, 0),
                2,
            )

            # 添加文本标签
            cv2.putText(
                annotated_image,
                str(box_id),
                (img_x0 - 35, img_y1 + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # 保存文本框坐标
            txt_path = str(debug_dir / f"{page_number}.txt")
            with open(txt_path, 'a') as f:
                f.write(f"{box_id},{box.x},{box.y},{box.x2},{box.y2}\n")

            box_id += 1

        # 保存标注图像
        cv2.imwrite(str(debug_dir / f"{page_number}_annotated.png"), annotated_image)

    doc.close()

def extract_pdf_img():
    """
    提取PDF图像（备用方法）
    """
    from pdf2image import convert_from_path

    folder_path = DEFAULT_CONFIG["input_folder"]
    paper_num = 0

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                output_path = f'{DEFAULT_CONFIG["output_folder"]}/pdf{str(paper_num)}'
                print(pdf_path)
                images = convert_from_path(pdf_path)
                for i, img in enumerate(images):
                    img.save(f"{output_path}/{i}.png", "PNG")
                paper_num += 1

def main():
    """
    主函数：批量处理海运单PDF文件
    """
    logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])

    folder_path = DEFAULT_CONFIG["input_folder"]
    paper_num = 0
    ONLY_FIRST_PAGE = DEFAULT_CONFIG.get("only_first_page", True)

    print(f"{'='*60}")
    print(f"海运单关键字识别 - 文本框提取")
    print(f"{'='*60}")
    print(f"输入文件夹: {folder_path}")
    print(f"输出文件夹: {DEFAULT_CONFIG['output_folder']}")
    print(f"{'='*60}\n")

    if not os.path.exists(folder_path):
        print(f"❌ 错误：文件夹 {folder_path} 不存在")
        return

    processed_count = 0
    error_count = 0

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                output_path = f'{DEFAULT_CONFIG["output_folder"]}/pdf{str(paper_num)}'

                try:
                    print(f"处理: {pdf_path}")
                    line_boxes = extract_paragraph_line(pdf_path, ONLY_FIRST_PAGE)

                    if line_boxes:
                        draw_line_boxes_to_image(pdf_path, line_boxes, output_path)
                        print(f"✅ 完成: {output_path}")
                        processed_count += 1
                    else:
                        print(f"⚠️  跳过（解析失败）: {pdf_path}")
                        error_count += 1

                except Exception as e:
                    print(f"❌ 错误: {str(e)}")
                    error_count += 1
                    continue

                paper_num += 1

    print(f"\n{'='*60}")
    print(f"处理完成！")
    print(f"{'='*60}")
    print(f"成功处理: {processed_count}")
    print(f"错误数量: {error_count}")
    print(f"\n下一步: 运行 vlm_anno_bol.py 进行文本分组")

if __name__ == "__main__":
    # 允许命令行参数覆盖配置文件
    if len(sys.argv) > 1:
        DEFAULT_CONFIG["input_folder"] = sys.argv[1]
    if len(sys.argv) > 2:
        DEFAULT_CONFIG["output_folder"] = sys.argv[2]

    main()
