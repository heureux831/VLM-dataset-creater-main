#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 5: 融合生成 FUNSD 格式
Merge to FUNSD Format

将 OCR 结果、VLM 分组结果、VLM 分类结果融合，生成标准 FUNSD 格式数据集。

输入:
  - data/02_images/ (图片)
  - data/03_ocr_results/ (OCR结果)
  - data/04_vlm_grouping/ (分组结果)
  - data/05_vlm_classification/ (分类结果)
输出:
  - data/06_funsd_output/ (FUNSD格式数据)
"""

import os
import sys
import json
import shutil
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

from config import PATHS, BILL_OF_LADING_LABELS, LABEL_ID_TO_NAME, ensure_directories

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# FUNSD 标签映射
FUNSD_LABEL_MAPPING = {
    # 标签类别 -> FUNSD 标签
    "role": "answer",
    "geography": "answer",
    "transport": "answer",
    "cargo": "answer",
    "number": "answer",
    "layout": "header",
    "rate": "answer",
    "other": "other"
}


class FUNSDMerger:
    """FUNSD 格式融合器"""

    def __init__(
        self,
        image_dir: Path,
        ocr_dir: Path,
        grouping_dir: Path,
        classification_dir: Path,
        output_dir: Path,
        vis_dir: Optional[Path] = None
    ):
        self.image_dir = Path(image_dir)
        self.ocr_dir = Path(ocr_dir)
        self.grouping_dir = Path(grouping_dir)
        self.classification_dir = Path(classification_dir)
        self.output_dir = Path(output_dir)
        self.vis_dir = Path(vis_dir) if vis_dir else None

        # 创建目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "annotations").mkdir(exist_ok=True)

        if self.vis_dir:
            self.vis_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "total_entities": 0
        }

    def scan_tasks(self) -> List[Dict[str, Path]]:
        """扫描待处理任务"""
        tasks = []

        for classification_file in self.classification_dir.glob("*.json"):
            stem = classification_file.stem

            # 查找对应文件
            image_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                candidate = self.image_dir / f"{stem}{ext}"
                if candidate.exists():
                    image_path = candidate
                    break

            ocr_path = self.ocr_dir / f"{stem}.json"
            grouping_path = self.grouping_dir / f"{stem}.json"

            if image_path and ocr_path.exists() and grouping_path.exists():
                tasks.append({
                    "stem": stem,
                    "image": image_path,
                    "ocr": ocr_path,
                    "grouping": grouping_path,
                    "classification": classification_file
                })

        self.stats["total"] = len(tasks)
        return tasks

    def merge_boxes(self, boxes: List[Dict]) -> Dict:
        """合并多个文本框为一个"""
        if not boxes:
            return None

        # 合并文本
        texts = [b["text"] for b in boxes]
        merged_text = " ".join(texts)

        # 合并边界框
        all_boxes = [b["box"] for b in boxes]
        x_min = min(b[0] for b in all_boxes)
        y_min = min(b[1] for b in all_boxes)
        x_max = max(b[2] for b in all_boxes)
        y_max = max(b[3] for b in all_boxes)

        return {
            "text": merged_text,
            "box": [x_min, y_min, x_max, y_max]
        }

    def get_funsd_label(self, label_id: int) -> str:
        """获取 FUNSD 标签"""
        if label_id in BILL_OF_LADING_LABELS:
            category = BILL_OF_LADING_LABELS[label_id].get("category", "other")
            return FUNSD_LABEL_MAPPING.get(category, "other")
        return "other"

    def split_text_to_words(self, text: str, box: List[int]) -> List[Dict]:
        """将文本拆分为单词"""
        words = []
        x1, y1, x2, y2 = box
        width = x2 - x1

        parts = text.split()
        if not parts:
            return [{"text": "", "box": box}]

        char_width = width / max(len(text), 1)
        current_x = x1

        for part in parts:
            part_width = len(part) * char_width
            words.append({
                "text": part,
                "box": [int(current_x), y1, int(current_x + part_width), y2]
            })
            current_x += part_width + char_width

        return words

    def generate_funsd(
        self,
        image_path: Path,
        ocr_data: Dict,
        grouping_data: Dict,
        classification_data: Dict
    ) -> Dict:
        """生成 FUNSD 格式数据"""

        # 获取图片尺寸
        with Image.open(image_path) as img:
            width, height = img.size

        # 构建文本框映射
        text_boxes = {box["id"]: box for box in ocr_data.get("text_boxes", [])}

        # 获取分组和分类
        groups = grouping_data.get("groups", [])
        classifications = classification_data.get("classifications", {})

        # 构建 FUNSD 实体
        form = []
        entity_id = 0

        for group_idx, group in enumerate(groups):
            # 获取该组的文本框
            group_boxes = [text_boxes[bid] for bid in group if bid in text_boxes]

            if not group_boxes:
                continue

            # 合并文本框
            merged = self.merge_boxes(group_boxes)
            if not merged:
                continue

            # 获取分类标签
            label_id = classifications.get(str(group_idx), 27)  # 默认 other
            if isinstance(label_id, str):
                label_id = int(label_id)

            funsd_label = self.get_funsd_label(label_id)
            bol_label = LABEL_ID_TO_NAME.get(label_id, "other")

            # 构建实体
            entity = {
                "id": entity_id,
                "text": merged["text"],
                "box": merged["box"],
                "label": funsd_label,
                "bol_label": bol_label,  # 保留原始海运单标签
                "bol_label_id": label_id,
                "words": self.split_text_to_words(merged["text"], merged["box"]),
                "linking": []
            }

            form.append(entity)
            entity_id += 1

        return {
            "image": image_path.name,
            "width": width,
            "height": height,
            "form": form
        }

    def draw_funsd_visualization(
        self,
        image_path: Path,
        funsd_data: Dict,
        output_path: Path
    ):
        """绘制 FUNSD 可视化"""
        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font = ImageFont.load_default()

        # 颜色映射
        colors = {
            "header": "blue",
            "answer": "green",
            "question": "orange",
            "other": "gray"
        }

        for entity in funsd_data.get("form", []):
            box = entity["box"]
            label = entity.get("label", "other")
            bol_label = entity.get("bol_label", "")
            color = colors.get(label, "gray")

            # 画框
            draw.rectangle(box, outline=color, width=2)

            # 标注
            label_text = f"{entity['id']}:{bol_label}"
            draw.text((box[0], box[1] - 12), label_text, fill=color, font=font)

        image.save(output_path)

    def process_single(self, task: Dict[str, Path]) -> bool:
        """处理单个任务"""
        try:
            stem = task["stem"]
            image_path = task["image"]
            ocr_path = task["ocr"]
            grouping_path = task["grouping"]
            classification_path = task["classification"]

            logger.info(f"处理: {image_path.name}")

            # 加载数据
            with open(ocr_path, 'r', encoding='utf-8') as f:
                ocr_data = json.load(f)
            with open(grouping_path, 'r', encoding='utf-8') as f:
                grouping_data = json.load(f)
            with open(classification_path, 'r', encoding='utf-8') as f:
                classification_data = json.load(f)

            # 生成 FUNSD 数据
            funsd_data = self.generate_funsd(
                image_path, ocr_data, grouping_data, classification_data
            )

            # 复制图片
            output_image_path = self.output_dir / "images" / image_path.name
            shutil.copy2(image_path, output_image_path)

            # 保存 JSON
            output_json_path = self.output_dir / "annotations" / f"{stem}.json"
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(funsd_data, f, ensure_ascii=False, indent=2)

            # 可视化
            if self.vis_dir:
                vis_path = self.vis_dir / f"{stem}_funsd.png"
                self.draw_funsd_visualization(image_path, funsd_data, vis_path)

            entity_count = len(funsd_data.get("form", []))
            logger.info(f"  ✅ 生成 {entity_count} 个实体")

            self.stats["success"] += 1
            self.stats["total_entities"] += entity_count
            return True

        except Exception as e:
            logger.error(f"  ❌ 失败: {task['stem']} - {e}")
            import traceback
            traceback.print_exc()
            self.stats["failed"] += 1
            return False

    def generate_dataset_info(self):
        """生成数据集信息文件"""
        info = {
            "name": "Bill of Lading FUNSD Dataset",
            "description": "海运单关键字识别数据集（FUNSD格式）",
            "total_images": self.stats["success"],
            "total_entities": self.stats["total_entities"],
            "labels": {
                "funsd_labels": ["header", "question", "answer", "other"],
                "bol_labels": LABEL_ID_TO_NAME
            },
            "structure": {
                "images/": "图片文件",
                "annotations/": "JSON标注文件"
            }
        }

        info_path = self.output_dir / "dataset_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        logger.info(f"数据集信息已保存: {info_path}")

    def run(self):
        """运行融合处理"""
        logger.info("=" * 60)
        logger.info("Step 5: 融合生成 FUNSD 格式")
        logger.info("=" * 60)
        logger.info(f"图片目录: {self.image_dir}")
        logger.info(f"OCR目录: {self.ocr_dir}")
        logger.info(f"分组目录: {self.grouping_dir}")
        logger.info(f"分类目录: {self.classification_dir}")
        logger.info(f"输出目录: {self.output_dir}")

        tasks = self.scan_tasks()
        if not tasks:
            logger.warning("没有待处理的任务")
            return self.stats

        logger.info(f"找到 {len(tasks)} 个待处理任务\n")

        for i, task in enumerate(tasks, 1):
            logger.info(f"[{i}/{len(tasks)}]")
            self.process_single(task)

        # 生成数据集信息
        self.generate_dataset_info()

        # 打印统计
        logger.info("\n" + "=" * 60)
        logger.info("FUNSD 数据集生成完成")
        logger.info("=" * 60)
        logger.info(f"总任务数: {self.stats['total']}")
        logger.info(f"成功: {self.stats['success']}")
        logger.info(f"失败: {self.stats['failed']}")
        logger.info(f"总实体数: {self.stats['total_entities']}")
        logger.info(f"\n输出目录: {self.output_dir}")

        return self.stats


def main():
    parser = argparse.ArgumentParser(description='Step 5: 融合生成 FUNSD 格式')
    parser.add_argument('--image-dir', type=str, help='图片目录')
    parser.add_argument('--ocr-dir', type=str, help='OCR结果目录')
    parser.add_argument('--grouping-dir', type=str, help='分组结果目录')
    parser.add_argument('--classification-dir', type=str, help='分类结果目录')
    parser.add_argument('-o', '--output', type=str, help='输出目录')
    parser.add_argument('-v', '--visualize', action='store_true', help='生成可视化')
    args = parser.parse_args()

    ensure_directories()

    image_dir = Path(args.image_dir) if args.image_dir else PATHS["step1_images"]
    ocr_dir = Path(args.ocr_dir) if args.ocr_dir else PATHS["step2_ocr"]
    grouping_dir = Path(args.grouping_dir) if args.grouping_dir else PATHS["step3_grouping"]
    classification_dir = Path(args.classification_dir) if args.classification_dir else PATHS["step4_classification"]
    output_dir = Path(args.output) if args.output else PATHS["step5_funsd"]
    vis_dir = PATHS["visualizations"] / "funsd" if args.visualize else None

    merger = FUNSDMerger(
        image_dir, ocr_dir, grouping_dir, classification_dir,
        output_dir, vis_dir
    )
    merger.run()


if __name__ == "__main__":
    main()
