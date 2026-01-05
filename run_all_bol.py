#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海运单关键字识别 - 一键运行脚本
Bill of Lading Keyword Recognition - One-Click Run Script

此脚本自动化整个海运单关键字识别的数据处理流程，
从PDF提取到最终FUNSD格式数据集生成。
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    海运单关键字识别数据集创建工具                             ║
║    Bill of Lading Keyword Recognition Dataset Creator        ║
║                                                              ║
║    版本: v2.1.0 (仅FUNSD格式)                                ║
║    日期: 2025-01-05                                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_config():
    """检查配置文件"""
    print("\n" + "="*60)
    print("📋 检查配置文件...")
    print("="*60)

    from config import DEFAULT_CONFIG, BILL_OF_LADING_LABELS

    # 检查API密钥
    if DEFAULT_CONFIG["api_key"] == "YOUR_API_KEY":
        print("⚠️  警告: 请在 config.py 中设置您的 Gemini 2.0 Flash API 密钥")
        print("   获取地址: https://aistudio.google.com/apikey")
        return False

    print("✅ API密钥已配置")

    # 检查输入文件夹
    input_folder = DEFAULT_CONFIG["input_folder"]
    if not os.path.exists(input_folder):
        print(f"⚠️  警告: 输入文件夹不存在: {input_folder}")
        print(f"   请将海运单PDF文件放入此文件夹")
        os.makedirs(input_folder, exist_ok=True)
        print(f"   已创建文件夹: {input_folder}")

    pdf_count = len([f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')])
    if pdf_count == 0:
        print(f"⚠️  警告: 输入文件夹中没有找到PDF文件")
        return False

    print(f"✅ 找到 {pdf_count} 个PDF文件")

    # 检查输出文件夹
    output_folder = DEFAULT_CONFIG["output_folder"]
    funsd_folder = os.path.join(output_folder, "funsd_format")
    if not os.path.exists(funsd_folder):
        os.makedirs(funsd_folder, exist_ok=True)
        print(f"✅ 已创建输出文件夹: {funsd_folder}")

    print(f"✅ 配置检查完成\n")
    return True

def run_command(script_name, description):
    """运行命令并显示进度"""
    print("\n" + "="*60)
    print(f"🚀 {description}")
    print("="*60)

    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )

        elapsed_time = time.time() - start_time
        print(f"\n✅ {description} 完成 (耗时: {elapsed_time:.2f}秒)")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} 失败 (错误码: {e.returncode})")
        return False
    except Exception as e:
        print(f"\n❌ {description} 出现异常: {str(e)}")
        return False

def main():
    """主函数"""
    print_banner()

    # 检查配置
    if not check_config():
        print("\n❌ 配置检查失败，请检查上述问题后重试")
        sys.exit(1)

    # 定义处理步骤
    print("\n" + "="*60)
    print("⚙️  处理选项")
    print("="*60)
    print("请选择处理方式:")
    print("1. 多格式文档处理 (推荐，支持PDF/Excel/Word)")
    print("2. 分步处理（传统流程）")

    choice = input("\n请选择 (1/2，默认: 1): ").strip()

    if choice == "2":
        # 传统分步流程
        steps = [
            ("vlm_anno_bol.py", "第一次VLM标注（文本分组）"),
            ("correct_format_bol.py", "校正格式"),
            ("correct_box_bol.py", "校正边界框"),
            ("vlm_anno2_bol.py", "第二次VLM标注（关键字分类）"),
            ("convert_label_bol.py", "转换标签格式"),
        ]
        print("\n已选择分步处理流程")
    else:
        # 多格式文档处理（推荐）
        steps = [
            ("multi_format_to_funsd.py", "多格式文档生成FUNSD格式"),
        ]
        print("\n已选择多格式文档处理")

    # 确认继续
    print("\n" + "="*60)
    confirm = input("确认开始处理? (y/N，默认: y): ").strip().lower()
    if confirm in ['n', 'no']:
        print("已取消操作")
        sys.exit(0)

    # 执行步骤
    print("\n" + "="*60)
    print("🎯 开始处理流程")
    print("="*60)

    success_count = 0
    failure_count = 0

    for script_name, description in steps:
        success = run_command(script_name, description)
        if success:
            success_count += 1
        else:
            failure_count += 1

            # 询问是否继续
            print(f"\n⚠️  步骤失败: {description}")
            continue_choice = input("是否继续下一步? (y/N，默认: y): ").strip().lower()
            if continue_choice in ['n', 'no']:
                print("\n用户取消操作")
                break

    # 总结
    print("\n" + "="*60)
    print("📊 处理完成总结")
    print("="*60)
    print(f"✅ 成功步骤: {success_count}")
    print(f"❌ 失败步骤: {failure_count}")

    if failure_count == 0:
        print("\n🎉 所有步骤执行成功！")
        print("\n输出文件位置:")
        from config import DEFAULT_CONFIG
        output_folder = DEFAULT_CONFIG["output_folder"]
        funsd_folder = os.path.join(output_folder, "funsd_format")
        print(f"  - FUNSD格式文件夹: {funsd_folder}")
        print(f"  - JSON标注文件: {funsd_folder}/*.json")
        print(f"  - 统计报告: {funsd_folder}/statistics.txt")
        print(f"  - 使用说明: {funsd_folder}/README.md")

        # 询问是否生成训练命令
        print("\n" + "="*60)
        print("🎯 FUNSD格式数据集可用于训练以下模型:")
        print("="*60)
        print("""
1. LayoutLMv3 (推荐)
   - 微软开源的文档理解模型
   - 支持OCR、视觉和文本多模态理解

2. BERT系列
   - 基于文本内容的分类模型
   - 适合信息抽取任务

3. 自定义Transformer模型
   - 可根据FUNSD格式定制训练
        """)

        print("\n📚 更多信息请查看:")
        print("  - FUNSD_FORMAT_GUIDE.md - FUNSD格式详细说明")
        print("  - README.md - 完整项目文档")
    else:
        print("\n⚠️  部分步骤失败，请检查错误信息后重试")

    print("\n感谢使用海运单关键字识别数据集创建工具！")
    print("如有问题，请查看 README.md 或提交 Issue")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生未处理的异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
