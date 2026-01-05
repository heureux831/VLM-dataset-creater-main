#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海运单关键字识别 - 依赖安装脚本
Bill of Lading Keyword Recognition - Dependency Installation Script

此脚本自动安装运行海运单关键字识别工具所需的所有依赖。
"""

import subprocess
import sys
import os

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    海运单关键字识别 - 依赖安装脚本                            ║
║    B/L Keyword Recognition - Dependency Installer            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def run_command(command, description):
    """运行命令"""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    print(f"命令: {command}\n")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败")
        print(f"错误信息: {e.stderr}")
        return False

def check_python_version():
    """检查Python版本"""
    print("\n" + "="*60)
    print("🔍 检查Python版本...")
    print("="*60)

    version = sys.version_info
    print(f"当前Python版本: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ 错误: 需要Python 3.7或更高版本")
        print("请升级Python版本后重试")
        return False

    print("✅ Python版本符合要求")
    return True

def install_core_dependencies():
    """安装核心依赖"""
    print("\n" + "="*60)
    print("📦 安装核心依赖...")
    print("="*60)

    packages = [
        "pip install -q -U google-genai",
        "pip install paddlepaddle paddleocr",
    ]

    success_count = 0
    for package in packages:
        if run_command(package, f"安装 {package.split()[-1]}"):
            success_count += 1

    return success_count == len(packages)

def install_optional_dependencies():
    """安装可选依赖"""
    print("\n" + "="*60)
    print("📦 安装可选依赖...")
    print("="*60)

    packages = [
        "pip install pymupdf",
        "pip install opencv-python",
        "pip install pillow",
        "pip install numpy",
        "pip install tqdm",
        "pip install rich",
        "pip install openpyxl",
        "pip install python-docx",
        "pip install docx2pdf",
    ]

    success_count = 0
    for package in packages:
        if run_command(package, f"安装 {package.split()[-1]}"):
            success_count += 1

    print(f"\n成功安装 {success_count}/{len(packages)} 个可选依赖")
    return True

def install_ml_dependencies():
    """安装机器学习相关依赖（可选）"""
    print("\n" + "="*60)
    print("📦 安装机器学习相关依赖（可选）...")
    print("="*60)
    print("注意: 这些依赖仅在需要时安装，用于模型训练")

    packages = [
        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu",
    ]

    success_count = 0
    for package in packages:
        if run_command(package, f"安装 {package.split()[-1]}"):
            success_count += 1

    print(f"\n成功安装 {success_count}/{len(packages)} 个机器学习依赖")
    return True

def verify_installation():
    """验证安装"""
    print("\n" + "="*60)
    print("✅ 验证安装...")
    print("="*60)

    # 核心依赖
    try:
        import google.genai
        print("✅ google-genai 已安装")
    except ImportError:
        print("❌ google-genai 未安装")

    try:
        import paddleocr
        print("✅ PaddleOCR 已安装")
    except ImportError:
        print("❌ PaddleOCR 未安装")

    # PDF处理
    try:
        import fitz
        print("✅ PyMuPDF 已安装")
    except ImportError:
        print("⚠️  PyMuPDF 未安装 (用于PDF文档处理)")

    # 可选依赖 - 文档格式支持
    try:
        import openpyxl
        print("✅ openpyxl 已安装 (Excel支持)")
    except ImportError:
        print("⚠️  openpyxl 未安装 (Excel支持需要)")

    try:
        import docx
        print("✅ python-docx 已安装 (Word支持)")
    except ImportError:
        print("⚠️  python-docx 未安装 (Word支持需要)")

    try:
        import docx2pdf
        print("✅ docx2pdf 已安装 (.doc转换支持)")
    except ImportError:
        print("⚠️  docx2pdf 未安装 (.doc转换支持需要)")

    # 图像处理
    try:
        import cv2
        print("✅ opencv-python 已安装")
    except ImportError:
        print("❌ opencv-python 未安装")

    try:
        import PIL
        print("✅ pillow 已安装")
    except ImportError:
        print("❌ pillow 未安装")

    try:
        import numpy
        print("✅ numpy 已安装")
    except ImportError:
        print("❌ numpy 未安装")

    try:
        import tqdm
        print("✅ tqdm 已安装")
    except ImportError:
        print("❌ tqdm 未安装")

    print("\n" + "="*60)
    print("📝 说明:")
    print("   ✅ 核心依赖 (必需)")
    print("   ⚠️  可选依赖 (支持更多文档格式)")
    print("="*60)

def print_next_steps():
    """打印后续步骤"""
    print("\n" + "="*60)
    print("📋 后续步骤")
    print("="*60)
    print("""
1. 获取Gemini 2.0 Flash API密钥:
   - 访问: https://aistudio.google.com/apikey
   - 使用Google账号登录
   - 创建新的API密钥

2. 配置API密钥:
   - 编辑 config.py 文件
   - 将 "YOUR_API_KEY" 替换为您的实际API密钥

3. 准备文档文件:
   - 支持格式: PDF, Excel (.xlsx/.xls), Word (.docx/.doc)
   - 将文档文件放入 ./bills_of_lading 文件夹
   - 或者修改 config.py 中的 input_folder 路径

4. 运行数据处理:

   📄 处理多格式文档 (推荐):
     python multi_format_to_funsd.py

   📄 仅处理PDF文档:
     python pdf_to_funsd.py

   📄 处理图像文件:
     python generate_funsd_format.py

   📄 一键运行 (包含配置检查):
     python run_all_bol.py

5. 查看结果:
   - 输出目录: ./bol_output/funsd_format/
   - 包含JSON标注文件、统计报告和使用说明

6. 训练模型 (可选):
   - 参考 https://huggingface.co/microsoft/layoutlmv3-base
   - 或使用其他支持FUNSD格式的模型
    """)

def main():
    """主函数"""
    print_banner()

    # 检查Python版本
    if not check_python_version():
        sys.exit(1)

    # 询问用户要安装的依赖类型
    print("\n" + "="*60)
    print("⚙️  安装选项")
    print("="*60)
    print("请选择要安装的依赖类型:")
    print("1. 核心依赖 (必需)")
    print("2. 核心依赖 + 可选依赖 (支持多格式文档)")
    print("3. 核心依赖 + 可选依赖 + 机器学习依赖 (全部)")
    print("4. 自定义安装")

    choice = input("\n请选择 (1/2/3/4，默认: 2): ").strip()

    if choice == "1":
        install_core_dependencies()
        verify_installation()
    elif choice == "2":
        install_core_dependencies()
        install_optional_dependencies()
        verify_installation()
    elif choice == "4":
        # 自定义安装
        print("\n请选择要安装的依赖包:")
        packages = {
            "1": ("google-genai", "pip install -q -U google-genai"),
            "2": ("PaddleOCR", "pip install paddlepaddle paddleocr"),
            "3": ("PyMuPDF", "pip install pymupdf"),
            "4": ("OpenCV", "pip install opencv-python"),
            "5": ("Pillow", "pip install pillow"),
            "6": ("NumPy", "pip install numpy"),
            "7": ("tqdm", "pip install tqdm"),
            "8": ("rich", "pip install rich"),
            "9": ("openpyxl", "pip install openpyxl"),
            "10": ("python-docx", "pip install python-docx"),
            "11": ("docx2pdf", "pip install docx2pdf"),
            "12": ("PyTorch", "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"),
        }

        selected = input("请输入包编号 (用逗号分隔，如: 1,2,3): ").strip()
        for pkg_num in selected.split(","):
            pkg_num = pkg_num.strip()
            if pkg_num in packages:
                _, command = packages[pkg_num]
                run_command(command, f"安装 {packages[pkg_num][0]}")

        verify_installation()
    else:
        # 默认安装选项2 (核心 + 可选)
        install_core_dependencies()
        install_optional_dependencies()
        verify_installation()

    print_next_steps()

    print("\n" + "="*60)
    print("✅ 安装完成！")
    print("="*60)
    print("感谢使用海运单关键字识别数据集创建工具！")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  安装被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 安装过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
