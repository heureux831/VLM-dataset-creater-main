"""
海运单关键字识别 - 格式校正脚本
Bill of Lading Keyword Recognition - Format Correction Script

此脚本用于校正VLM标注结果的格式，
去除不必要的markdown标记，只保留纯JSON或列表数据。
"""

import os
import sys
from config import DEFAULT_CONFIG

def process_txt_files(folder_path):
    """
    处理指定文件夹中的所有标注文件，校正格式

    Args:
        folder_path: 文件夹路径
    """
    processed_count = 0
    error_count = 0

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 处理两种类型的文件：分组标注和分类标注
            if file.lower().endswith("_annotated.txt") or file.lower().endswith("_classified.txt"):
                txt_path = os.path.join(root, file)
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()

                    # 处理可能包含markdown标记的内容
                    lines = content.split('\n')
                    if len(lines) >= 1:
                        # 去除可能的markdown代码块标记
                        first_line = lines[0].strip()
                        if first_line.startswith('```'):
                            # 跳过markdown标记，使用第二行
                            if len(lines) >= 2:
                                corrected_content = lines[1].strip()
                                with open(txt_path, 'w', encoding='utf-8') as fw:
                                    fw.write(corrected_content)
                                print(f'✅ 已处理: {txt_path}')
                                processed_count += 1
                            else:
                                print(f'⚠️  文件格式异常: {txt_path}')
                                error_count += 1
                        elif first_line.startswith('```json'):
                            # 跳过```json标记，使用第二行
                            if len(lines) >= 2:
                                corrected_content = lines[1].strip()
                                with open(txt_path, 'w', encoding='utf-8') as fw:
                                    fw.write(corrected_content)
                                print(f'✅ 已处理: {txt_path}')
                                processed_count += 1
                            else:
                                print(f'⚠️  文件格式异常: {txt_path}')
                                error_count += 1
                        else:
                            # 检查是否已经是正确格式（列表或字典）
                            if content.startswith('[') or content.startswith('{'):
                                print(f'✓  格式正确，跳过: {txt_path}')
                            else:
                                print(f'⚠️  格式可能不正确: {txt_path}')
                                error_count += 1

                except Exception as e:
                    print(f'❌ 处理 {txt_path} 时出错: {str(e)}')
                    error_count += 1
                    continue

    print(f"\n{'='*60}")
    print(f"处理完成！")
    print(f"{'='*60}")
    print(f"已处理文件: {processed_count}")
    print(f"错误文件: {error_count}")

def main():
    """主函数"""
    # 使用配置文件中的默认路径，或使用命令行参数
    folder_path = DEFAULT_CONFIG["output_folder"]

    if len(sys.argv) > 1:
        folder_path = sys.argv[1]

    if not os.path.exists(folder_path):
        print(f'❌ 错误：文件夹 {folder_path} 不存在')
        print(f'请检查路径是否正确，或先运行数据处理脚本')
        return

    print(f"{'='*60}")
    print(f"海运单关键字识别 - 格式校正")
    print(f"{'='*60}")
    print(f"处理文件夹: {folder_path}")
    print(f"{'='*60}\n")

    process_txt_files(folder_path)

if __name__ == '__main__':
    main()
