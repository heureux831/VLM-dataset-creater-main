#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海运单关键字识别 - 配置检查脚本
Bill of Lading Keyword Recognition - Configuration Check Script

此脚本检查配置文件是否正确设置，帮助用户快速验证配置。
"""

import os
import sys
from pathlib import Path

def check_config():
    """检查配置文件"""
    print("="*60)
    print("海运单关键字识别 - 配置检查")
    print("="*60)
    print()

    # 检查配置文件是否存在
    config_file = "config.py"
    if not os.path.exists(config_file):
        print(f"❌ 错误：配置文件 {config_file} 不存在")
        return False

    print(f"✅ 配置文件存在: {config_file}")
    print()

    # 导入配置
    try:
        sys.path.insert(0, os.getcwd())
        from config import DEFAULT_CONFIG
        print("✅ 配置文件导入成功")
    except Exception as e:
        print(f"❌ 配置文件导入失败: {str(e)}")
        return False

    print()

    # 检查API密钥
    print("1. 检查API密钥...")
    api_key = DEFAULT_CONFIG.get("api_key", "")

    if api_key == "YOUR_API_KEY" or not api_key:
        print("   ❌ API密钥未配置")
        print("   📝 配置步骤:")
        print("      1. 访问 https://aistudio.google.com/apikey")
        print("      2. 使用Google账号登录")
        print("      3. 点击 'Create API key'")
        print("      4. 复制生成的API密钥")
        print("      5. 编辑 config.py 文件")
        print(f"      6. 将第349行的 'YOUR_API_KEY' 替换为您的实际API密钥")
        print()
        return False
    else:
        # 检查API密钥格式（不以"AIza"开头或太短）
        if len(api_key) < 20:
            print(f"   ⚠️  API密钥可能不正确 (长度: {len(api_key)})")
            print("      请确认您复制了完整的API密钥")
            print()
        else:
            print(f"   ✅ API密钥已配置 (长度: {len(api_key)})")
            # 隐藏部分密钥显示
            masked_key = api_key[:8] + "..." + api_key[-4:]
            print(f"      密钥格式: {masked_key}")
        print()

    # 检查输入文件夹
    print("2. 检查输入文件夹...")
    input_folder = DEFAULT_CONFIG.get("input_folder", "./bills_of_lading")

    if not os.path.exists(input_folder):
        print(f"   ⚠️  输入文件夹不存在: {input_folder}")
        print(f"      程序运行时会自动创建此文件夹")
        print(f"      您可以将海运单PDF文件放入此文件夹")
        os.makedirs(input_folder, exist_ok=True)
        print(f"      ✅ 已创建文件夹: {input_folder}")
    else:
        pdf_count = len(list(Path(input_folder).glob("*.pdf")))
        print(f"   ✅ 输入文件夹存在: {input_folder}")
        print(f"      找到 {pdf_count} 个PDF文件")
    print()

    # 检查输出文件夹
    print("3. 检查输出文件夹...")
    output_folder = DEFAULT_CONFIG.get("output_folder", "./bol_output")

    if not os.path.exists(output_folder):
        print(f"   ✅ 输出文件夹将自动创建: {output_folder}")
    else:
        print(f"   ✅ 输出文件夹存在: {output_folder}")
    print()

    # 检查其他配置
    print("4. 其他配置...")
    batch_size = DEFAULT_CONFIG.get("batch_size", 5)
    interval = DEFAULT_CONFIG.get("interval", 15)
    model_name = DEFAULT_CONFIG.get("model_name", "gemini-2.0-flash")

    print(f"   ✅ 批处理大小: {batch_size}")
    print(f"   ✅ API调用间隔: {interval} 秒")
    print(f"   ✅ 模型名称: {model_name}")
    print()

    # 依赖检查
    print("5. 检查依赖包...")
    missing_deps = []

    # 核心依赖
    try:
        import google.genai
        print("   ✅ google-genai 已安装")
    except ImportError:
        print("   ❌ google-genai 未安装")
        missing_deps.append("google-genai")

    try:
        import paddleocr
        print("   ✅ PaddleOCR 已安装")
    except ImportError:
        print("   ❌ PaddleOCR 未安装")
        print("      建议安装: pip install paddlepaddle paddleocr")
        missing_deps.append("paddleocr")

    # 可选依赖 - 多格式文档支持
    print("\n   📄 多格式文档支持:")

    # PDF支持
    try:
        import fitz
        print("   ✅ PyMuPDF (PDF支持) 已安装")
    except ImportError:
        print("   ⚠️  PyMuPDF 未安装 (PDF文档支持需要)")
        print("      安装命令: pip install pymupdf")

    # Excel支持
    try:
        import openpyxl
        print("   ✅ openpyxl (Excel支持) 已安装")
    except ImportError:
        print("   ⚠️  openpyxl 未安装 (Excel文档支持需要)")
        print("      安装命令: pip install openpyxl")

    # Word支持
    try:
        import docx
        print("   ✅ python-docx (Word支持) 已安装")
    except ImportError:
        print("   ⚠️  python-docx 未安装 (Word文档支持需要)")
        print("      安装命令: pip install python-docx")

    try:
        import docx2pdf
        print("   ✅ docx2pdf (.doc转换支持) 已安装")
    except ImportError:
        print("   ⚠️  docx2pdf 未安装 (.doc文件转换支持需要)")
        print("      安装命令: pip install docx2pdf")

    # 图像处理
    try:
        import cv2
        print("   ✅ opencv-python 已安装")
    except ImportError:
        print("   ❌ opencv-python 未安装")
        missing_deps.append("opencv-python")

    try:
        import PIL
        print("   ✅ pillow 已安装")
    except ImportError:
        print("   ❌ pillow 未安装")
        missing_deps.append("pillow")

    try:
        import numpy
        print("   ✅ numpy 已安装")
    except ImportError:
        print("   ❌ numpy 未安装")
        missing_deps.append("numpy")

    print()

    if missing_deps:
        print("❌ 缺少必要依赖包:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print()
        print("请运行以下命令安装依赖:")
        print("  python install_dependencies.py")
        print()
        return False

    # 总结
    print("="*60)
    print("✅ 配置检查完成！")
    print("="*60)
    print()
    print("下一步操作:")
    print("1. 将文档文件放入 ./bills_of_lading/ 文件夹")
    print("   支持格式: PDF, Excel (.xlsx/.xls), Word (.docx/.doc)")
    print()
    print("2. 运行以下命令之一:")
    print("   📄 多格式文档处理 (推荐):")
    print("      python multi_format_to_funsd.py")
    print()
    print("   📄 仅处理PDF文档:")
    print("      python run_all_bol.py")
    print("      (选择选项1)")
    print()
    print("   🖼️  仅处理图像文件:")
    print("      python generate_funsd_format.py")
    print()
    print("3. 查看结果:")
    print("   - 输出目录: ./bol_output/funsd_format/")
    print("   - JSON文件: *.json")
    print("   - 统计报告: statistics.txt")
    print()
    print("如需帮助，请查看:")
    print("  - README.md - 完整文档")
    print("  - QUICKSTART.md - 快速开始")
    print()

    return True

def main():
    """主函数"""
    check_config()

if __name__ == "__main__":
    main()
