#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海运单关键字识别 - PDF转FUNSD格式
Bill of Lading Keyword Recognition - PDF to FUNSD Format

直接从海运单PDF生成FUNSD格式的数据，结合BabelDOC和Gemini。
"""

import os
import json
import time
import ast
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
from google import genai
import logging
from rich.logging import RichHandler
import babeldoc.high_level
import babeldoc.translation_config
import pymupdf
from babeldoc.document_il import il_version_1
from babeldoc.docvision import doclayout
from babeldoc.document_il.midend.detect_scanned_file import DetectScannedFile
from babeldoc.document_il.midend.layout_parser import LayoutParser
from babeldoc.document_il.midend.table_parser import TableParser
from babeldoc.document_il.midend.paragraph_finder import ParagraphFinder
from babeldoc.document_il.utils.layout_helper import get_char_unicode_string
from babeldoc.docvision.table_detection.rapidocr import RapidOCRModel
from config import BILL_OF_LADING_LABELS, DEFAULT_CONFIG

# 加载文档布局模型
logger = logging.getLogger(__name__)
onnx = doclayout.DocLayoutModel.load_available()

# FUNSD格式的标签映射
FUNSD_LABEL_MAPPING = {
    0: "answer", 1: "answer", 2: "answer",
    3: "answer", 4: "answer", 5: "answer", 6: "answer", 7: "answer",
    8: "answer", 9: "answer", 10: "answer", 11: "answer", 12: "answer",
    13: "answer", 14: "answer", 15: "answer", 16: "answer", 17: "answer",
    18: "answer", 19: "answer", 20: "answer", 21: "answer",
    22: "header", 23: "other", 24: "other",
    25: "answer", 26: "answer",
    27: "other", 28: "other",
}

# Gemini分类提示词
BOL_CLASSIFICATION_PROMPT = """## 任务：海运单文本分类

你是一个专业的海运单（B/L）文档分析专家。请对提供的文本进行分类。

### 海运单字段类型（0-28）：

**核心角色类：**
0. shipper (托运人)
1. consignee (收货人)
2. notify_party (通知方)

**地理信息类：**
3. port_of_loading (装货港)
4. port_of_discharge (卸货港)
5. port_of_delivery (交货港)
6. place_of_delivery (交货地点)
7. place_of_receipt (收货地点)

**运输信息类：**
8. vessel (船名)
9. voyage (航次)
10. vessel_voyage (船名航次)
11. container_no (集装箱号)
12. seal_no (封号)

**货物信息类：**
13. description_of_goods (货物描述)
14. marks_numbers (唛头和编号)
15. package (包装件数)
16. weight (重量)
17. volume (体积)

**编号日期类：**
18. bl_no (提单号)
19. freight (运费)
20. date (日期)
21. time (时间)

**特殊标识类：**
22. header (头部信息)
23. footer (底部信息)
24. company_logo (公司标志)

**费率类：**
25. rate (费率)
26. total (总计)

**其他：**
27. other (其他信息)
28. abandon (废弃内容)

### 输出格式：
返回JSON对象：{"文本ID": 类别ID, ...}
只返回JSON，不要其他内容。

### 示例：
输入：
- 0: "Shipper:"
- 1: "ABC Trading Co."
- 2: "Port of Loading:"

输出：
{"0": 22, "1": 0, "2": 3}
"""

def parse_pdf(pdf_path, only_first_page=True):
    """解析PDF并提取文档结构"""
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
        import shutil
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

def extract_text_blocks(pdf_path, only_first_page=True):
    """
    从PDF中提取文本块

    Args:
        pdf_path: PDF文件路径
        only_first_page: 是否只处理第一页

    Returns:
        list: 包含文本和坐标的列表
    """
    il = parse_pdf(pdf_path, only_first_page=only_first_page)

    if il is None:
        return []

    doc = pymupdf.open(pdf_path)
    page = doc[0]  # 只处理第一页

    # 获取页面尺寸
    page_width = page.rect.width
    page_height = page.rect.height

    text_blocks = []
    for paragraph in il.page[0].pdf_paragraph:
        for comp in paragraph.pdf_paragraph_composition:
            if comp.pdf_line:
                line = comp.pdf_line
                text = get_char_unicode_string(line.pdf_character)

                # 获取边界框（相对坐标）
                box = line.box
                x_center = box.x
                y_center = box.y
                width = box.x2
                height = box.y2

                # 转换为绝对像素坐标（假设图像为1000x1000）
                x1 = int(x_center * page_width - width * page_width / 2)
                y1 = int(y_center * page_height - height * page_height / 2)
                x2 = int(x_center * page_width + width * page_width / 2)
                y2 = int(y_center * page_height + height * page_height / 2)

                # 确保坐标在有效范围内
                x1 = max(0, min(x1, int(page_width)))
                y1 = max(0, min(y1, int(page_height)))
                x2 = max(0, min(x2, int(page_width)))
                y2 = max(0, min(y2, int(page_height)))

                text_blocks.append({
                    "id": len(text_blocks),
                    "text": text,
                    "box": [x1, y1, x2, y2],
                    "confidence": 1.0
                })

    doc.close()
    return text_blocks

def classify_with_gemini(text_blocks):
    """
    使用Gemini对文本块进行分类

    Args:
        text_blocks: 文本块列表

    Returns:
        dict: 文本ID到类别ID的映射
    """
    if not text_blocks:
        return {}

    try:
        client = genai.Client(api_key=DEFAULT_CONFIG["api_key"])

        # 构建输入数据
        input_data = []
        for block in text_blocks:
            input_data.append({
                "id": block["id"],
                "text": block["text"]
            })

        # 发送请求
        response = client.models.generate_content(
            model=DEFAULT_CONFIG["model_name"],
            contents=[json.dumps(input_data, ensure_ascii=False), BOL_CLASSIFICATION_PROMPT],
        )

        # 解析响应
        result_text = response.text.strip()

        # 去除可能的markdown标记
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]

        result_text = result_text.strip()

        # 解析JSON
        classification = ast.literal_eval(result_text)

        return classification

    except Exception as e:
        print(f"❌ Gemini分类失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def split_text_to_words(text, box):
    """
    将文本拆分为单词

    Args:
        text: 文本内容
        box: 边界框 [x1, y1, x2, y2]

    Returns:
        list: 单词列表
    """
    words = []
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1

    # 按空格分割文本
    text_parts = text.split()
    if not text_parts:
        return [{
            "text": "",
            "box": box
        }]

    # 估算每个字符的平均宽度
    char_width = width / max(len(text), 1)

    current_x = x1
    for part in text_parts:
        # 计算该词的宽度
        part_width = len(part) * char_width

        words.append({
            "text": part,
            "box": [int(current_x), y1, int(current_x + part_width), y2]
        })

        current_x += part_width + char_width * 0.5  # 加上空格宽度

    return words

def generate_funsd_format(text_blocks, classification):
    """
    生成FUNSD格式的数据

    Args:
        text_blocks: 文本块列表
        classification: 分类结果

    Returns:
        dict: FUNSD格式的数据
    """
    funsd_data = {
        "form": []
    }

    for block in text_blocks:
        text_id = str(block["id"])
        if text_id not in classification:
            continue

        bol_class_id = classification[text_id]
        funsd_label = FUNSD_LABEL_MAPPING.get(bol_class_id, "other")

        # 构建words字段
        words = split_text_to_words(block["text"], block["box"])

        # 构建实体
        entity = {
            "box": block["box"],
            "text": block["text"],
            "label": funsd_label,
            "words": words,
            "linking": [],
            "id": block["id"]
        }

        funsd_data["form"].append(entity)

    return funsd_data

def process_single_pdf(pdf_path, output_dir):
    """
    处理单个PDF文件

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录

    Returns:
        bool: 是否成功
    """
    try:
        print(f"\n处理: {pdf_path}")

        # 1. 提取文本块
        print("  - 提取文本块...")
        text_blocks = extract_text_blocks(pdf_path)

        if not text_blocks:
            print("  ❌ 未提取到文本块")
            return False

        print(f"  ✅ 提取到 {len(text_blocks)} 个文本块")

        # 2. Gemini分类
        print("  - 进行语义分类...")
        classification = classify_with_gemini(text_blocks)

        if not classification:
            print("  ❌ 语义分类失败")
            return False

        print(f"  ✅ 完成分类")

        # 3. 生成FUNSD格式
        print("  - 生成FUNSD格式...")
        funsd_data = generate_funsd_format(text_blocks, classification)

        # 4. 保存结果
        pdf_name = Path(pdf_path).stem
        output_path = os.path.join(output_dir, f"{pdf_name}.json")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(funsd_data, f, ensure_ascii=False, indent=2)

        print(f"  ✅ 已保存: {output_path}")
        return True

    except Exception as e:
        print(f"  ❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])

    print("="*60)
    print("海运单关键字识别 - PDF转FUNSD格式")
    print("="*60)

    # 输入输出路径
    input_dir = DEFAULT_CONFIG["input_folder"]
    output_dir = os.path.join(DEFAULT_CONFIG["output_folder"], "funsd_format")

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 检查API密钥
    if DEFAULT_CONFIG["api_key"] == "YOUR_API_KEY":
        print("❌ 请在config.py中设置您的Gemini API密钥")
        return

    # 收集所有PDF文件
    pdf_files = list(Path(input_dir).glob("*.pdf"))

    if not pdf_files:
        print(f"⚠️  在 {input_dir} 中未找到PDF文件")
        return

    print(f"\n找到 {len(pdf_files)} 个PDF文件")
    print(f"输出目录: {output_dir}")

    # 逐个处理PDF
    success_count = 0
    failure_count = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}]")
        if process_single_pdf(str(pdf_path), output_dir):
            success_count += 1
        else:
            failure_count += 1

        # 避免API限制
        if i < len(pdf_files):
            print(f"  等待 {DEFAULT_CONFIG['interval']} 秒...")
            time.sleep(DEFAULT_CONFIG['interval'])

    # 总结
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {failure_count}")
    print(f"\nFUNSD格式文件保存在: {output_dir}")

    # 生成统计报告
    if success_count > 0:
        stats_file = os.path.join(output_dir, "statistics.txt")
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("PDF转FUNSD格式统计报告\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"总PDF数: {len(pdf_files)}\n")
            f.write(f"成功处理: {success_count}\n")
            f.write(f"失败数量: {failure_count}\n")
            f.write(f"成功率: {success_count/len(pdf_files)*100:.2f}%\n\n")

            f.write("类别映射 (B/L -> FUNSD):\n")
            f.write("-" * 60 + "\n")
            for bol_id, funsd_label in FUNSD_LABEL_MAPPING.items():
                if bol_id in BILL_OF_LADING_LABELS:
                    label_info = BILL_OF_LADING_LABELS[bol_id]
                    f.write(f"{bol_id:3d}: {label_info['name']:25s} -> {funsd_label}\n")

        print(f"统计报告: {stats_file}")

    # 生成使用说明
    readme_file = os.path.join(output_dir, "README.md")
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("# FUNSD格式数据\n\n")
        f.write("本目录包含使用海运单关键字识别生成的FUNSD格式数据。\n\n")
        f.write("## 文件说明\n\n")
        f.write("- `*.json`: FUNSD格式的标注文件\n")
        f.write("- `statistics.txt`: 处理统计报告\n")
        f.write("- `README.md`: 本说明文件\n\n")
        f.write("## FUNSD格式说明\n\n")
        f.write("每个JSON文件包含以下字段：\n\n")
        f.write("```json\n")
        f.write('{\n')
        f.write('  "form": [\n')
        f.write('    {\n')
        f.write('      "box": [x1, y1, x2, y2],  // 边界框坐标\n')
        f.write('      "text": "文本内容",        // 识别的文本\n')
        f.write('      "label": "标签类型",       // question/answer/header/other\n')
        f.write('      "words": [                // 单词级别的详细信息\n')
        f.write('        {\n')
        f.write('          "text": "单词",        // 单词文本\n')
        f.write('          "box": [x1, y1, x2, y2]  // 单词边界框\n')
        f.write('        }\n')
        f.write('      ],\n')
        f.write('      "linking": [],            // 实体间的关系（可选）\n')
        f.write('      "id": 0                   // 实体ID\n')
        f.write('    }\n')
        f.write('  ]\n')
        f.write('}\n')
        f.write("```\n\n")
        f.write("## 标签类型\n\n")
        f.write("- **answer**: 海运单的关键字段信息（托运人、收货人、港口等）\n")
        f.write("- **header**: 单据头部信息\n")
        f.write("- **question**: 问题标签（本项目中较少使用）\n")
        f.write("- **other**: 其他信息\n")

    print(f"使用说明: {readme_file}")

if __name__ == "__main__":
    main()
