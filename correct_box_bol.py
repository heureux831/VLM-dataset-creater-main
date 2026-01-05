"""
海运单关键字识别 - 边界框校正脚本
Bill of Lading Keyword Recognition - Bounding Box Correction Script

此脚本将VLM标注结果中的文本框分组转换为YOLO格式的合并边界框，
为海运单关键字识别做准备。
"""

import ast
import numpy as np
import glob
import os
import sys
from config import DEFAULT_CONFIG

def load_boxes(file_path):
    """
    从文件加载文本框坐标

    Args:
        file_path: 文本框坐标文件路径

    Returns:
        dict: {box_id: (x, y, w, h)} 坐标为归一化后的值
    """
    boxes = {}
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            parts = line.strip().split(',')
            if len(parts) >= 5:
                box_id = int(parts[0])
                # 格式: box_id,x_center,y_center,width,height (归一化坐标)
                x = float(parts[1])
                y = float(parts[2])
                w = float(parts[3])
                h = float(parts[4])
                boxes[box_id] = (x, y, w, h)
    return boxes

def load_paragraphs(file_path):
    """
    从文件加载段落分组结果

    Args:
        file_path: 分组标注文件路径

    Returns:
        list: [[box_id1, box_id2], [box_id3], ...]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        return ast.literal_eval(content)

def merge_boxes(boxes, paragraphs):
    """
    合并属于同一段落的文本框

    Args:
        boxes: 文本框字典 {box_id: (x, y, w, h)}
        paragraphs: 分组列表 [[box_id1, box_id2], ...]

    Returns:
        list: [(cls_id, x_center, y_center, width, height), ...]
              所有框的cls_id默认为1（待后续分类）
    """
    merged_boxes = []
    for group in paragraphs:
        if not group:
            continue

        # 获取该组中所有框的坐标
        coords = np.array([boxes[box_id] for box_id in group if box_id in boxes])

        if len(coords) == 0:
            continue

        x_centers, y_centers, widths, heights = coords.T

        # 计算合并后的边界框
        x_min = np.min(x_centers - widths / 2)
        x_max = np.max(x_centers + widths / 2)
        y_min = np.min(y_centers - heights / 2)
        y_max = np.max(y_centers + heights / 2)

        # 计算中心点和尺寸（归一化坐标）
        new_x = (x_min + x_max) / 2
        new_y = (y_min + y_max) / 2
        new_w = x_max - x_min
        new_h = y_max - y_min

        # 所有合并框先标记为待分类（cls_id=27: other）
        merged_boxes.append((27, new_x, new_y, new_w, new_h))

    return merged_boxes

def save_new_boxes(file_path, merged_boxes):
    """
    保存合并后的边界框到文件

    Args:
        file_path: 输出文件路径
        merged_boxes: 合并后的边界框列表
    """
    with open(file_path, 'w') as f:
        for i, (cls_id, x, y, w, h) in enumerate(merged_boxes):
            f.write(f"{cls_id} {x} {y} {w} {h}\n")

def test():
    """测试函数"""
    # 文件路径
    boxes_file = './bol_output/pdf0/1.txt'
    paragraphs_file = './bol_output/pdf0/1_annotated.txt'
    output_file = './bol_output/pdf0/1_merged.txt'

    # 处理数据
    boxes = load_boxes(boxes_file)
    paragraphs = load_paragraphs(paragraphs_file)
    merged_boxes = merge_boxes(boxes, paragraphs)
    save_new_boxes(output_file, merged_boxes)

    print(f"测试完成，结果保存至: {output_file}")

def main():
    """主函数"""
    # 使用配置文件中的默认路径
    folder_path = DEFAULT_CONFIG["output_folder"]

    if len(sys.argv) > 1:
        folder_path = sys.argv[1]

    print(f"{'='*60}")
    print(f"海运单关键字识别 - 边界框校正")
    print(f"{'='*60}")
    print(f"处理文件夹: {folder_path}")
    print(f"{'='*60}\n")

    # 查找所有分组标注文件
    paragraph_file_paths = glob.glob(
        os.path.join(folder_path, '**', '*_annotated.txt'),
        recursive=True
    )

    if not paragraph_file_paths:
        print(f"⚠️  未找到任何标注文件，请检查路径: {folder_path}")
        print("请先运行 vlm_anno_bol.py 进行文本分组标注")
        return

    print(f"找到 {len(paragraph_file_paths)} 个待处理文件\n")

    processed_count = 0
    error_count = 0

    for paragraph_file in paragraph_file_paths:
        try:
            # 构建文件路径
            boxes_file = paragraph_file.replace('_annotated.txt', '.txt')
            output_file = paragraph_file.replace('_annotated.txt', '_merged.txt')

            # 检查必要文件是否存在
            if not os.path.exists(boxes_file):
                print(f"⚠️  文本框文件不存在: {boxes_file}")
                error_count += 1
                continue

            # 处理数据
            boxes = load_boxes(boxes_file)
            paragraphs = load_paragraphs(paragraph_file)
            merged_boxes = merge_boxes(boxes, paragraphs)
            save_new_boxes(output_file, merged_boxes)

            print(f"✅ 已处理: {os.path.basename(paragraph_file)}")
            processed_count += 1

        except Exception as e:
            print(f"❌ 处理 {paragraph_file} 时出错: {str(e)}")
            error_count += 1
            continue

    print(f"\n{'='*60}")
    print(f"处理完成！")
    print(f"{'='*60}")
    print(f"成功处理: {processed_count}")
    print(f"错误数量: {error_count}")
    print(f"\n下一步: 运行 vlm_anno2_bol.py 进行关键字分类")

if __name__ == '__main__':
    main()
    # test()
