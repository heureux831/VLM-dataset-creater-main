#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多格式文档解析器测试脚本
Multi-Format Document Parser Test Script

此脚本用于测试 document_parser.py 的功能
"""

import os
import sys
from pathlib import Path

def test_imports():
    """测试所需库的导入"""
    print("="*60)
    print("测试库导入...")
    print("="*60)

    missing_libs = []

    # 核心依赖
    try:
        import google.genai
        print("✅ google-genai")
    except ImportError as e:
        print(f"❌ google-genai: {e}")
        missing_libs.append("google-genai")

    try:
        import paddleocr
        print("✅ paddleocr")
    except ImportError as e:
        print(f"❌ paddleocr: {e}")
        missing_libs.append("paddleocr")

    # PDF支持
    try:
        import fitz
        print("✅ PyMuPDF (fitz)")
    except ImportError as e:
        print(f"⚠️  PyMuPDF (fitz): 未安装 (PDF支持需要)")
        print(f"   安装命令: pip install pymupdf")

    # Excel支持
    try:
        import openpyxl
        print("✅ openpyxl")
    except ImportError as e:
        print(f"⚠️  openpyxl: 未安装 (Excel支持需要)")
        print(f"   安装命令: pip install openpyxl")

    # Word支持
    try:
        import docx
        print("✅ python-docx")
    except ImportError as e:
        print(f"⚠️  python-docx: 未安装 (Word支持需要)")
        print(f"   安装命令: pip install python-docx")

    try:
        import docx2pdf
        print("✅ docx2pdf")
    except ImportError as e:
        print(f"⚠️  docx2pdf: 未安装 (.doc转换支持需要)")
        print(f"   安装命令: pip install docx2pdf")

    # 图像处理
    try:
        from PIL import Image
        print("✅ Pillow")
    except ImportError as e:
        print(f"❌ Pillow: {e}")
        missing_libs.append("Pillow")

    try:
        import cv2
        print("✅ opencv-python")
    except ImportError as e:
        print(f"❌ opencv-python: {e}")
        missing_libs.append("opencv-python")

    try:
        import numpy
        print("✅ numpy")
    except ImportError as e:
        print(f"❌ numpy: {e}")
        missing_libs.append("numpy")

    print()
    if missing_libs:
        print(f"❌ 缺少核心依赖: {', '.join(missing_libs)}")
        print("请运行: python install_dependencies.py")
        return False
    else:
        print("✅ 所有核心依赖已安装")
        return True


def test_document_parser():
    """测试文档解析器"""
    print("\n" + "="*60)
    print("测试文档解析器...")
    print("="*60)

    try:
        from document_parser import DocumentParser
        print("✅ DocumentParser 导入成功")
    except ImportError as e:
        print(f"❌ DocumentParser 导入失败: {e}")
        return False

    # 创建解析器实例
    try:
        parser = DocumentParser(temp_dir="./test_temp")
        print("✅ DocumentParser 实例化成功")
    except Exception as e:
        print(f"❌ DocumentParser 实例化失败: {e}")
        return False

    # 检查支持的格式
    print("\n支持的文档格式:")
    for ext, desc in parser.SUPPORTED_FORMATS.items():
        print(f"  {ext}: {desc}")

    print("\n✅ 文档解析器测试通过")
    return True


def test_config():
    """测试配置"""
    print("\n" + "="*60)
    print("测试配置文件...")
    print("="*60)

    try:
        from config import DEFAULT_CONFIG, BILL_OF_LADING_LABELS
        print("✅ 配置文件导入成功")

        # 检查API密钥
        api_key = DEFAULT_CONFIG.get("api_key", "")
        if api_key == "YOUR_API_KEY" or not api_key:
            print("⚠️  警告: API密钥未配置")
            print("请编辑 config.py 文件，设置您的 Gemini API密钥")
        else:
            print(f"✅ API密钥已配置")

        # 检查标签数量
        label_count = len(BILL_OF_LADING_LABELS)
        print(f"✅ 海运单标签类别数量: {label_count}")

        return True

    except ImportError as e:
        print(f"❌ 配置文件导入失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("多格式文档解析器测试")
    print("="*60)
    print()

    # 运行测试
    tests = [
        ("库导入测试", test_imports),
        ("文档解析器测试", test_document_parser),
        ("配置测试", test_config),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 出现异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")

    # 检查是否所有测试通过
    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 所有测试通过！")
        print("\n下一步:")
        print("1. 准备测试文档 (PDF/Excel/Word)")
        print("2. 将文档放入 ./bills_of_lading 文件夹")
        print("3. 运行: python multi_format_to_funsd.py")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息")
        print("\n建议:")
        print("1. 运行: python install_dependencies.py")
        print("2. 检查 config.py 中的API密钥配置")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
