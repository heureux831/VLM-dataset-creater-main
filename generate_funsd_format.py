#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海运单关键字识别 - FUNSD格式生成器
Bill of Lading Keyword Recognition - FUNSD Format Generator

此脚本使用OCR提取文本和坐标，然后使用Gemini进行语义分类，
最终生成标准的FUNSD JSON格式数据。
"""

import os
import json
import time
import ast
from pathlib import Path
from PIL import Image
import cv2
import numpy as np
try:
    import google.generativeai as genai
except ImportError:
    try:
        import google.genai as genai
    except ImportError:
        genai = None
from config import BILL_OF_LADING_LABELS, DEFAULT_CONFIG

# FUNSD格式的标签映射
FUNSD_LABEL_MAPPING = {
    # 海运单字段映射到FUNSD标签
    0: "answer",    # shipper -> answer
    1: "answer",    # consignee -> answer
    2: "answer",    # notify_party -> answer
    3: "answer",    # port_of_loading -> answer
    4: "answer",    # port_of_discharge -> answer
    5: "answer",    # port_of_delivery -> answer
    6: "answer",    # place_of_delivery -> answer
    7: "answer",    # place_of_receipt -> answer
    8: "answer",    # vessel -> answer
    9: "answer",    # voyage -> answer
    10: "answer",   # vessel_voyage -> answer
    11: "answer",   # container_no -> answer
    12: "answer",   # seal_no -> answer
    13: "answer",   # description_of_goods -> answer
    14: "answer",   # marks_numbers -> answer
    15: "answer",   # package -> answer
    16: "answer",   # weight -> answer
    17: "answer",   # volume -> answer
    18: "answer",   # bl_no -> answer
    19: "answer",   # freight -> answer
    20: "answer",   # date -> answer
    21: "answer",   # time -> answer
    22: "header",   # header -> header
    23: "other",    # footer -> other
    24: "other",    # company_logo -> other
    25: "answer",   # rate -> answer
    26: "answer",   # total -> answer
    27: "other",    # other -> other
    28: "other",    # abandon -> other
}

# Gemini分类提示词
FUNSD_CLASSIFICATION_PROMPT = """## 任务：海运单文本分类

你是一个专业的海运单（B/L）文档分析专家。请对提供的OCR文本进行分类。

### 海运单字段类型：

**核心角色类：**
0. shipper (托运人): 货物发送方/发货人
1. consignee (收货人): 货物接收方
2. notify_party (通知方): 到货通知接收方

**地理信息类：**
3. port_of_loading (装货港): 货物装载港口
4. port_of_discharge (卸货港): 货物卸载港口
5. port_of_delivery (交货港): 交货地点
6. place_of_delivery (交货地点): 实际交货地点
7. place_of_receipt (收货地点): 货物接收地点

**运输信息类：**
8. vessel (船名): 承运船舶名称
9. voyage (航次): 船舶航次号
10. vessel_voyage (船名航次): 船名和航次组合
11. container_no (集装箱号): 集装箱编号
12. seal_no (封号): 集装箱封条编号

**货物信息类：**
13. description_of_goods (货物描述): 货物详细描述
14. marks_numbers (唛头和编号): 货物包装标记和编号
15. package (包装件数): 货物包装及件数
16. weight (重量): 货物重量
17. volume (体积): 货物体积

**编号日期类：**
18. bl_no (提单号): 提单编号
19. freight (运费): 运输费用
20. date (日期): 各类日期信息
21. time (时间): 时间信息

**特殊标识类：**
22. header (头部信息): 单据头部信息
23. footer (底部信息): 单据底部信息
24. company_logo (公司标志): 公司标志

**费率类：**
25. rate (费率): 单位费率
26. total (总计): 总计金额或数量

**其他：**
27. other (其他信息): 其他重要信息
28. abandon (废弃内容): 需要废弃的内容

### 输出格式：
返回JSON对象：{"文本ID": 类别ID, ...}
只返回JSON，不要其他内容。

### 示例：
输入OCR文本：
- ID 0: "Shipper:"
- ID 1: "ABC Trading Co."
- ID 2: "Shanghai Port"

输出：
{"0": 22, "1": 0, "2": 3}
"""

def ocr_with_paddle(image_path):
    """
    使用PaddleOCR提取图像中的文本和坐标

    Args:
        image_path: 图像文件路径

    Returns:
        list: 包含文本和坐标的列表
    """
    try:
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(use_angle_cls=True, lang="ch", enable_mkldnn=True)
        result = ocr.ocr(image_path, cls=True)

        ocr_results = []
        if result and result[0]:
            for line in result[0]:
                box = line[0]  # 四点坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text = line[1][0]  # 识别文本
                confidence = line[1][1]  # 置信度

                # 计算边界框 (x_min, y_min, x_max, y_max)
                points = np.array(box)
                x_min = int(min(points[:, 0]))
                y_min = int(min(points[:, 1]))
                x_max = int(max(points[:, 0]))
                y_max = int(max(points[:, 1]))

                ocr_results.append({
                    "id": len(ocr_results),
                    "text": text,
                    "box": [x_min, y_min, x_max, y_max],
                    "confidence": confidence
                })

        return ocr_results

    except ImportError:
        print("⚠️  PaddleOCR未安装，请运行: pip install paddlepaddle paddleocr")
        return []
    except Exception as e:
        print(f"❌ OCR识别失败: {str(e)}")
        return []


def classify_with_gemini(ocr_results):
    """
    使用Gemini对OCR结果进行分类

    Args:
        ocr_results: OCR识别结果列表

    Returns:
        dict: 文本ID到类别ID的映射
    """
    if not ocr_results:
        return {}

    try:
        # 检查 genai 是否可用
        if genai is None:
            print("❌ Google Generative AI 库未安装")
            print("   请运行: pip install google-ai-generativelanguage google-auth google-auth-oauthlib google-auth-httplib2")
            return {}

        # 检查 API 密钥
        api_key = DEFAULT_CONFIG.get("api_key", "")
        if not api_key or api_key == "YOUR_API_KEY":
            print("❌ 请在config.py中配置Gemini API密钥")
            return {}

        # 构建输入数据
        input_data = []
        for result in ocr_results:
            input_data.append({
                "id": result["id"],
                "text": result["text"]
            })

        # 尝试新版本API (google.genai)
        try:
            import google.generativeai as genai_new
            genai_new.configure(api_key=api_key)
            model = genai_new.GenerativeModel(DEFAULT_CONFIG["model_name"])
            response = model.generate_content(
                json.dumps(input_data, ensure_ascii=False) + "\n\n" + FUNSD_CLASSIFICATION_PROMPT,
                generation_config={"timeout": 60}
            )
        except (AttributeError, ImportError):
            # 尝试旧版本API (google.generativeai)
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(DEFAULT_CONFIG["model_name"])
                response = model.generate_content(
                    json.dumps(input_data, ensure_ascii=False) + "\n\n" + FUNSD_CLASSIFICATION_PROMPT
                )
            except Exception as e:
                print(f"  ❌ Gemini API调用失败: {str(e)}")
                return {}

        # 解析响应
        if hasattr(response, 'text'):
            result_text = response.text.strip()
        else:
            result_text = str(response).strip()

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
    将文本拆分为单词（用于words字段）

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

        current_x += part_width + char_width  # 加上空格宽度

    return words

def generate_funsd_format(image_path, ocr_results, classification):
    """
    生成FUNSD格式的数据

    Args:
        image_path: 图像路径
        ocr_results: OCR识别结果
        classification: 分类结果

    Returns:
        dict: FUNSD格式的数据
    """
    funsd_data = {
        "form": []
    }

    for result in ocr_results:
        text_id = str(result["id"])
        if text_id not in classification:
            continue

        bol_class_id = classification[text_id]
        funsd_label = FUNSD_LABEL_MAPPING.get(bol_class_id, "other")

        # 构建words字段
        words = split_text_to_words(result["text"], result["box"])

        # 构建实体
        entity = {
            "box": result["box"],
            "text": result["text"],
            "label": funsd_label,
            "words": words,
            "linking": [],
            "id": result["id"]
        }

        funsd_data["form"].append(entity)

    return funsd_data

def process_single_image(image_path, output_dir):
    """
    处理单张图像

    Args:
        image_path: 图像文件路径
        output_dir: 输出目录

    Returns:
        bool: 是否成功
    """
    try:
        print(f"\n处理: {image_path}")

        # 1. OCR识别
        print("  - 进行OCR识别...")
        ocr_results = ocr_with_paddle(image_path)

        if not ocr_results:
            print("  ❌ OCR识别失败")
            return False

        print(f"  ✅ OCR识别到 {len(ocr_results)} 个文本块")

        # 2. Gemini分类
        print("  - 进行语义分类...")
        classification = classify_with_gemini(ocr_results)

        if not classification:
            print("  ❌ 语义分类失败")
            return False

        print(f"  ✅ 完成分类")

        # 3. 生成FUNSD格式
        print("  - 生成FUNSD格式...")
        funsd_data = generate_funsd_format(image_path, ocr_results, classification)

        # 4. 保存结果
        image_name = Path(image_path).stem
        output_path = os.path.join(output_dir, f"{image_name}.json")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(funsd_data, f, ensure_ascii=False, indent=2)

        print(f"  ✅ 已保存: {output_path}")
        return True

    except Exception as e:
        print(f"  ❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

class ImageToFUNSDConverter:
    """图像转FUNSD格式转换器"""

    def __init__(self):
        """初始化转换器"""
        pass

    def convert_image_to_funsd(self, image_path, output_name):
        """
        将图像转换为FUNSD格式

        Args:
            image_path: 图像文件路径
            output_name: 输出名称（不包含扩展名）

        Returns:
            dict: FUNSD格式的数据
        """
        # 1. OCR识别
        ocr_results = ocr_with_paddle(image_path)

        if not ocr_results:
            print(f"  ❌ OCR识别失败: {image_path}")
            return {"form": []}

        # 2. Gemini分类
        classification = classify_with_gemini(ocr_results)

        if not classification:
            print(f"  ❌ 语义分类失败: {image_path}")
            return {"form": []}

        # 3. 生成FUNSD格式
        funsd_data = generate_funsd_format(image_path, ocr_results, classification)

        return funsd_data


def main():
    """主函数"""
    print("="*60)
    print("海运单关键字识别 - FUNSD格式生成器")
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

    # 检查PaddleOCR
    try:
        import paddleocr
        print("✅ PaddleOCR已安装")
    except ImportError:
        print("⚠️  PaddleOCR未安装，将使用BabelDOC作为备用方案")
        print("   建议安装: pip install paddlepaddle paddleocr")

    # 收集所有图像文件
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']:
        image_files.extend(Path(input_dir).glob(ext))

    if not image_files:
        print(f"⚠️  在 {input_dir} 中未找到图像文件")
        return

    print(f"\n找到 {len(image_files)} 个图像文件")
    print(f"输出目录: {output_dir}")

    # 逐个处理图像
    success_count = 0
    failure_count = 0

    for i, image_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}]")
        if process_single_image(str(image_path), output_dir):
            success_count += 1
        else:
            failure_count += 1

        # 避免API限制
        if i < len(image_files):
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
            f.write("FUNSD格式生成统计报告\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"总图像数: {len(image_files)}\n")
            f.write(f"成功处理: {success_count}\n")
            f.write(f"失败数量: {failure_count}\n")
            f.write(f"成功率: {success_count/len(image_files)*100:.2f}%\n\n")

            f.write("类别映射:\n")
            f.write("-" * 60 + "\n")
            for bol_id, funsd_label in FUNSD_LABEL_MAPPING.items():
                if bol_id in BILL_OF_LADING_LABELS:
                    label_info = BILL_OF_LADING_LABELS[bol_id]
                    f.write(f"{bol_id:3d}: {label_info['name']:25s} -> {funsd_label}\n")

        print(f"统计报告: {stats_file}")

if __name__ == "__main__":
    main()
