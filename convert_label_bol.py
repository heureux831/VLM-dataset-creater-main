"""
海运单关键字识别 - 标签转换脚本
Bill of Lading Keyword Recognition - Label Conversion Script

此脚本将VLM分类结果转换为最终的YOLO格式标签文件，
为训练海运单关键字检测模型做准备。
"""

import os
import ast
import shutil
from pathlib import Path
from tqdm import tqdm
from config import DEFAULT_CONFIG

def convert_classification_to_yolo(folder_path):
    """
    将分类结果转换为YOLO标签格式

    Args:
        folder_path: 包含分类结果的文件夹路径
    """
    # 查找所有分类文件
    classified_files = list(Path(folder_path).rglob("*_classified.txt"))

    if not classified_files:
        print(f"⚠️  未找到任何分类文件: {folder_path}")
        return

    print(f"{'='*60}")
    print(f"海运单关键字识别 - 标签转换")
    print(f"{'='*60}")
    print(f"处理文件夹: {folder_path}")
    print(f"找到 {len(classified_files)} 个分类文件")
    print(f"{'='*60}\n")

    converted_count = 0
    error_count = 0

    for classified_file in tqdm(classified_files, desc="转换进度"):
        try:
            # 构建文件路径
            classified_path = str(classified_file)
            merged_txt_path = classified_path.replace('_classified.txt', '_merged.txt')
            output_yolo_path = classified_path.replace('_classified.txt', '.txt')

            # 检查必要文件是否存在
            if not os.path.exists(merged_txt_path):
                print(f"⚠️  合并文件不存在: {merged_txt_path}")
                error_count += 1
                continue

            # 读取分类结果
            with open(classified_path, 'r', encoding='utf-8') as f:
                classification_result = ast.literal_eval(f.read().strip())

            # 读取合并后的文本框坐标
            yolo_labels = []
            with open(merged_txt_path, 'r') as f_merged:
                for line_idx, line in enumerate(f_merged):
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        # 获取分类结果中的类别ID
                        cls_id = classification_result.get(str(line_idx), 27)  # 默认使用"other"类别

                        # 提取坐标
                        x_center = float(parts[1])
                        y_center = float(parts[2])
                        width = float(parts[3])
                        height = float(parts[4])

                        # 写入YOLO格式
                        yolo_labels.append(f"{cls_id} {x_center} {y_center} {width} {height}")

            # 保存YOLO标签文件
            with open(output_yolo_path, 'w') as f_out:
                f_out.write('\n'.join(yolo_labels))

            converted_count += 1

        except Exception as e:
            print(f"❌ 处理 {classified_file} 时出错: {str(e)}")
            error_count += 1
            continue

    print(f"\n{'='*60}")
    print(f"转换完成！")
    print(f"{'='*60}")
    print(f"成功转换: {converted_count}")
    print(f"错误数量: {error_count}")

def create_label_mapping_file(folder_path):
    """
    创建标签映射文件

    Args:
        folder_path: 输出文件夹路径
    """
    from config import BILL_OF_LADING_LABELS

    mapping_file = os.path.join(folder_path, "label_mapping.txt")

    with open(mapping_file, 'w', encoding='utf-8') as f:
        f.write("海运单关键字识别 - 标签映射\n")
        f.write("=" * 60 + "\n\n")

        # 按类别分组
        categories = {
            "Core Roles (核心角色)": [0, 1, 2],
            "Geographic Information (地理信息)": [3, 4, 5, 6, 7],
            "Transportation Info (运输信息)": [8, 9, 10, 11, 12],
            "Cargo Information (货物信息)": [13, 14, 15, 16, 17],
            "Number & Date (编号日期)": [18, 19, 20, 21],
            "Layout Elements (布局元素)": [22, 23, 24],
            "Rate & Total (费率总计)": [25, 26],
            "Other (其他)": [27, 28]
        }

        for category_name, class_ids in categories.items():
            f.write(f"\n{category_name}:\n")
            f.write("-" * 60 + "\n")
            for cls_id in class_ids:
                if cls_id in BILL_OF_LADING_LABELS:
                    label_info = BILL_OF_LADING_LABELS[cls_id]
                    f.write(f"{cls_id:3d}: {label_info['name']:25s} | {label_info['name_cn']:15s} | {label_info['description']}\n")

    print(f"✅ 已创建标签映射文件: {mapping_file}")

def generate_training_commands(output_dir):
    """
    生成训练命令示例

    Args:
        output_dir: 输出目录
    """
    commands_file = os.path.join(output_dir, "training_commands.txt")

    with open(commands_file, 'w', encoding='utf-8') as f:
        f.write("海运单关键字识别 - 模型训练命令\n")
        f.write("=" * 60 + "\n\n")

        f.write("1. 使用Ultralytics YOLO训练:\n")
        f.write("-" * 60 + "\n")
        f.write("yolo task=detect mode=train \\\n")
        f.write(f"  data={output_dir}/dataset_info.yaml \\\n")
        f.write("  model=yolov10n.pt \\\n")
        f.write("  epochs=100 \\\n")
        f.write("  imgsz=640 \\\n")
        f.write("  batch=16 \\\n")
        f.write("  name=bol_keyword_detection\n\n")

        f.write("2. 使用自定义配置训练:\n")
        f.write("-" * 60 + "\n")
        f.write("yolo task=detect mode=train \\\n")
        f.write(f"  data={output_dir}/dataset_info.yaml \\\n")
        f.write("  model=yolov10s.pt \\\n")
        f.write("  epochs=200 \\\n")
        f.write("  imgsz=1024 \\\n")
        f.write("  batch=8 \\\n")
        f.write("  lr0=0.01 \\\n")
        f.write("  name=bol_keyword_detection_v2\n\n")

        f.write("3. 验证模型:\n")
        f.write("-" * 60 + "\n")
        f.write("yolo task=detect mode=val \\\n")
        f.write(f"  data={output_dir}/dataset_info.yaml \\\n")
        f.write("  model=runs/detect/bol_keyword_detection/weights/best.pt\n\n")

        f.write("4. 预测新图像:\n")
        f.write("-" * 60 + "\n")
        f.write("yolo task=detect mode=predict \\\n")
        f.write("  model=runs/detect/bol_keyword_detection/weights/best.pt \\\n")
        f.write("  source=test_images/ \\\n")
        f.write("  conf=0.5 \\\n")
        f.write("  save=True\n\n")

        f.write("5. 导出模型:\n")
        f.write("-" * 60 + "\n")
        f.write("yolo task=detect mode=export \\\n")
        f.write("  model=runs/detect/bol_keyword_detection/weights/best.pt \\\n")
        f.write("  format=onnx \\\n")
        f.write("  dynamic=True\n\n")

    print(f"✅ 已生成训练命令文件: {commands_file}")

def main():
    """主函数"""
    import sys

    # 使用配置文件中的路径
    folder_path = DEFAULT_CONFIG["output_folder"]

    if len(sys.argv) > 1:
        folder_path = sys.argv[1]

    if not os.path.exists(folder_path):
        print(f"❌ 文件夹不存在: {folder_path}")
        print("请先运行数据处理和标注脚本")
        return

    # 转换标签
    convert_classification_to_yolo(folder_path)

    # 创建标签映射文件
    print("\n创建标签映射文件...")
    create_label_mapping_file(folder_path)

    # 生成训练命令
    print("\n生成训练命令...")
    generate_training_commands(folder_path)

    print(f"\n{'='*60}")
    print(f"✅ 所有转换完成！")
    print(f"{'='*60}")
    print(f"输出文件夹: {folder_path}")
    print(f"\n下一步: 运行 vlmdata2yolo_bol.py 生成最终数据集")

if __name__ == '__main__':
    main()
