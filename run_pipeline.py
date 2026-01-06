#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VLM 数据集创建工具 - 主运行脚本
VLM Dataset Creator - Main Pipeline Runner

运行完整的数据处理流水线：
1. 文档转图片 (step1_doc_to_images.py)
2. 图片OCR (step2_ocr.py)
3. VLM文本分组 (step3_vlm_grouping.py)
4. VLM关键字分类 (step4_vlm_classification.py)
5. 融合生成FUNSD (step5_merge_to_funsd.py)
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from datetime import datetime

from config import PATHS, DEFAULT_CONFIG, ensure_directories

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """打印横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         VLM 数据集创建工具 (VLM Dataset Creator)              ║
║                                                              ║
║    将文档转换为 FUNSD 格式的标注数据集                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_config():
    """检查配置"""
    logger.info("检查配置...")

    errors = []

    # 检查 API 密钥
    if not DEFAULT_CONFIG.get("api_key"):
        errors.append("未配置 API 密钥 (OPENAI_API_KEY)")

    # 检查输入目录
    input_dir = PATHS["input_documents"]
    if not input_dir.exists():
        input_dir.mkdir(parents=True, exist_ok=True)
        logger.warning(f"已创建输入目录: {input_dir}")

    # 检查输入文件
    doc_count = 0
    for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls']:
        doc_count += len(list(input_dir.glob(f"**/*{ext}")))

    if doc_count == 0:
        errors.append(f"输入目录中没有文档文件: {input_dir}")

    if errors:
        for err in errors:
            logger.error(f"❌ {err}")
        return False

    logger.info(f"✅ API 密钥已配置")
    logger.info(f"✅ 找到 {doc_count} 个文档文件")
    logger.info(f"✅ 模型: {DEFAULT_CONFIG.get('model_name')}")
    logger.info(f"✅ API: {DEFAULT_CONFIG.get('base_url')}")

    return True


def run_step(step_name: str, script_name: str, extra_args: list = None) -> bool:
    """运行单个步骤"""
    logger.info("\n" + "=" * 60)
    logger.info(f"🚀 {step_name}")
    logger.info("=" * 60)

    cmd = [sys.executable, script_name]
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(cmd, check=True)
        logger.info(f"✅ {step_name} 完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {step_name} 失败 (错误码: {e.returncode})")
        return False
    except Exception as e:
        logger.error(f"❌ {step_name} 异常: {e}")
        return False


def run_pipeline(
    start_step: int = 1,
    end_step: int = 5,
    visualize: bool = False
):
    """运行流水线"""
    ensure_directories()

    steps = [
        (1, "Step 1: 文档转图片", "step1_doc_to_images.py", []),
        (2, "Step 2: 图片OCR", "step2_ocr.py", ["-v"] if visualize else []),
        (3, "Step 3: VLM文本分组", "step3_vlm_grouping.py", []),
        (4, "Step 4: VLM关键字分类", "step4_vlm_classification.py", []),
        (5, "Step 5: 融合生成FUNSD", "step5_merge_to_funsd.py", ["-v"] if visualize else []),
    ]

    success_count = 0
    failed_count = 0

    for step_num, step_name, script_name, extra_args in steps:
        if step_num < start_step or step_num > end_step:
            continue

        success = run_step(step_name, script_name, extra_args)

        if success:
            success_count += 1
        else:
            failed_count += 1
            # 询问是否继续
            response = input(f"\n{step_name} 失败，是否继续? (y/N): ").strip().lower()
            if response != 'y':
                logger.info("用户取消操作")
                break

    # 打印总结
    logger.info("\n" + "=" * 60)
    logger.info("📊 处理完成总结")
    logger.info("=" * 60)
    logger.info(f"成功步骤: {success_count}")
    logger.info(f"失败步骤: {failed_count}")

    if failed_count == 0:
        logger.info("\n🎉 所有步骤执行成功！")
        logger.info(f"\n输出目录:")
        logger.info(f"  图片:     {PATHS['step1_images']}")
        logger.info(f"  OCR结果:  {PATHS['step2_ocr']}")
        logger.info(f"  分组结果: {PATHS['step3_grouping']}")
        logger.info(f"  分类结果: {PATHS['step4_classification']}")
        logger.info(f"  FUNSD:    {PATHS['step5_funsd']}")
        if visualize:
            logger.info(f"  可视化:   {PATHS['visualizations']}")


def main():
    parser = argparse.ArgumentParser(
        description='VLM 数据集创建工具 - 主运行脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_pipeline.py                  # 运行完整流水线
  python run_pipeline.py --start 2        # 从 Step 2 开始
  python run_pipeline.py --end 3          # 只运行到 Step 3
  python run_pipeline.py --start 3 --end 4  # 只运行 Step 3-4
  python run_pipeline.py -v               # 生成可视化结果

流水线步骤:
  Step 1: 文档转图片     (doc -> png)
  Step 2: 图片OCR        (png -> ocr.json)
  Step 3: VLM文本分组    (ocr + img -> grouping.json)
  Step 4: VLM关键字分类  (grouping + img -> classification.json)
  Step 5: 融合生成FUNSD  (all -> funsd.json)
        """
    )

    parser.add_argument(
        '--start', type=int, default=1,
        help='起始步骤 (1-5，默认: 1)'
    )
    parser.add_argument(
        '--end', type=int, default=5,
        help='结束步骤 (1-5，默认: 5)'
    )
    parser.add_argument(
        '-v', '--visualize', action='store_true',
        help='生成可视化结果'
    )
    parser.add_argument(
        '--check', action='store_true',
        help='仅检查配置，不运行'
    )

    args = parser.parse_args()

    print_banner()

    # 检查配置
    if not check_config():
        logger.error("\n配置检查失败，请修复上述问题后重试")
        sys.exit(1)

    if args.check:
        logger.info("\n配置检查通过")
        sys.exit(0)

    # 确认运行
    print(f"\n将运行 Step {args.start} 到 Step {args.end}")
    response = input("确认开始? (Y/n): ").strip().lower()
    if response == 'n':
        logger.info("已取消")
        sys.exit(0)

    # 运行流水线
    run_pipeline(
        start_step=args.start,
        end_step=args.end,
        visualize=args.visualize
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
        sys.exit(0)
