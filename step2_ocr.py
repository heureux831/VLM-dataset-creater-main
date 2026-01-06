#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2: 图片 OCR 识别
Image OCR Recognition

使用 PaddleOCR 对图片进行文字识别，输出文本框坐标和内容。
输入: data/02_images/
输出: data/03_ocr_results/
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from config import PATHS, DEFAULT_CONFIG, ensure_directories

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 检查 PaddleOCR
try:
    from paddleocr import PaddleOCR
    HAS_PADDLEOCR = True
except ImportError:
    HAS_PADDLEOCR = False
    logger.warning("PaddleOCR 未安装。请运行: pip install paddlepaddle paddleocr")


class OCRProcessor:
    """OCR 处理器"""

    def __init__(self, input_dir: Path, output_dir: Path, vis_dir: Optional[Path] = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.vis_dir = Path(vis_dir) if vis_dir else None

        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.vis_dir:
            self.vis_dir.mkdir(parents=True, exist_ok=True)

        self.lang = DEFAULT_CONFIG.get("ocr_lang", "ch")
        self.ocr = None  # 延迟初始化

        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "total_text_boxes": 0
        }

    def _init_ocr(self):
        """初始化 PaddleOCR"""
        if not HAS_PADDLEOCR:
            raise ImportError("PaddleOCR 未安装")

        if self.ocr is None:
            logger.info(f"初始化 PaddleOCR (语言: {self.lang})")
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                show_log=False
            )

    def scan_images(self) -> List[Path]:
        """扫描目录下的所有图片"""
        images = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff']:
            images.extend(self.input_dir.glob(f"**/{ext}"))
        images.sort()
        self.stats["total"] = len(images)
        return images

    def ocr_image(self, image_path: Path) -> List[Dict[str, Any]]:
        """对单张图片进行 OCR 识别"""
        self._init_ocr()

        result = self.ocr.ocr(str(image_path), cls=True)

        ocr_results = []
        if result and result[0]:
            for idx, line in enumerate(result[0]):
                box = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text = line[1][0]
                confidence = float(line[1][1])

                # 计算边界框 [x_min, y_min, x_max, y_max]
                points = np.array(box)
                x_min = int(min(points[:, 0]))
                y_min = int(min(points[:, 1]))
                x_max = int(max(points[:, 0]))
                y_max = int(max(points[:, 1]))

                ocr_results.append({
                    "id": idx,
                    "text": text,
                    "box": [x_min, y_min, x_max, y_max],
                    "polygon": [[int(p[0]), int(p[1])] for p in box],
                    "confidence": round(confidence, 4)
                })

        return ocr_results

    def draw_ocr_results(self, image_path: Path, ocr_results: List[Dict], output_path: Path):
        """在图片上绘制 OCR 结果"""
        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font = ImageFont.load_default()

        for item in ocr_results:
            box = item["box"]
            text_id = item["id"]

            # 画框
            draw.rectangle(box, outline="red", width=2)

            # 标注ID
            draw.text((box[0], box[1] - 15), str(text_id), fill="blue", font=font)

        image.save(output_path)

    def process_single(self, image_path: Path) -> bool:
        """处理单张图片"""
        try:
            logger.info(f"处理: {image_path.name}")

            # OCR 识别
            ocr_results = self.ocr_image(image_path)

            if not ocr_results:
                logger.warning(f"  未识别到文本: {image_path.name}")

            # 构建输出数据
            output_data = {
                "image_name": image_path.name,
                "image_path": str(image_path),
                "text_boxes": ocr_results,
                "total_boxes": len(ocr_results)
            }

            # 保存 JSON 结果
            output_name = f"{image_path.stem}.json"
            output_path = self.output_dir / output_name
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            logger.info(f"  ✅ 识别到 {len(ocr_results)} 个文本框 -> {output_name}")

            # 可视化
            if self.vis_dir:
                vis_path = self.vis_dir / f"{image_path.stem}_ocr.png"
                self.draw_ocr_results(image_path, ocr_results, vis_path)
                logger.info(f"  📊 可视化: {vis_path.name}")

            self.stats["success"] += 1
            self.stats["total_text_boxes"] += len(ocr_results)
            return True

        except Exception as e:
            logger.error(f"  ❌ 失败: {image_path.name} - {e}")
            self.stats["failed"] += 1
            return False

    def run(self):
        """运行 OCR 处理"""
        logger.info("=" * 60)
        logger.info("Step 2: 图片 OCR 识别")
        logger.info("=" * 60)
        logger.info(f"输入目录: {self.input_dir}")
        logger.info(f"输出目录: {self.output_dir}")
        if self.vis_dir:
            logger.info(f"可视化目录: {self.vis_dir}")

        images = self.scan_images()
        if not images:
            logger.warning("未找到任何图片文件")
            return self.stats

        logger.info(f"找到 {len(images)} 张图片\n")

        for i, image_path in enumerate(images, 1):
            logger.info(f"[{i}/{len(images)}]")
            self.process_single(image_path)

        # 打印统计
        logger.info("\n" + "=" * 60)
        logger.info("OCR 处理完成")
        logger.info("=" * 60)
        logger.info(f"总图片数: {self.stats['total']}")
        logger.info(f"成功: {self.stats['success']}")
        logger.info(f"失败: {self.stats['failed']}")
        logger.info(f"总文本框数: {self.stats['total_text_boxes']}")

        return self.stats


def main():
    parser = argparse.ArgumentParser(description='Step 2: 图片 OCR 识别')
    parser.add_argument('-i', '--input', type=str, help='输入目录')
    parser.add_argument('-o', '--output', type=str, help='输出目录')
    parser.add_argument('-v', '--visualize', action='store_true', help='生成可视化结果')
    args = parser.parse_args()

    ensure_directories()

    input_dir = Path(args.input) if args.input else PATHS["step1_images"]
    output_dir = Path(args.output) if args.output else PATHS["step2_ocr"]
    vis_dir = PATHS["visualizations"] / "ocr" if args.visualize else None

    processor = OCRProcessor(input_dir, output_dir, vis_dir)
    processor.run()


if __name__ == "__main__":
    main()
