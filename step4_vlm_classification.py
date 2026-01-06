#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 4: VLM 关键字分类标注
VLM Keyword Classification Annotation

使用 VLM 对分组后的文本框进行语义分类，识别每个组对应的海运单字段类型。

输入:
  - data/02_images/ (图片)
  - data/03_ocr_results/ (OCR结果)
  - data/04_vlm_grouping/ (分组结果)
输出:
  - data/05_vlm_classification/ (分类结果)
"""

import os
import sys
import json
import base64
import argparse
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import BytesIO
from PIL import Image

from config import PATHS, DEFAULT_CONFIG, BILL_OF_LADING_LABELS, LABEL_ID_TO_NAME, ensure_directories

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI 库未安装")


# 生成标签说明
def _generate_label_description():
    lines = []
    for label_id, info in BILL_OF_LADING_LABELS.items():
        lines.append(f"{label_id}. {info['name']} ({info['name_cn']})")
    return "\n".join(lines)


CLASSIFICATION_PROMPT = """## 任务：海运单关键字分类

你是一个专业的海运单（B/L）文档分析专家。请分析图片中已分组的文本框，为每个组分配对应的海运单字段类型。

### 海运单字段类型：
{label_description}

### 已分组的文本信息：
{grouped_info}

### 输出格式：
返回 JSON 对象，键为组ID（字符串），值为对应的标签ID（整数）：
```json
{{"0": 0, "1": 3, "2": 18, ...}}
```

请仅返回 JSON 对象，不要包含其他内容。"""


class VLMClassificationProcessor:
    """VLM 分类处理器"""

    def __init__(
        self,
        image_dir: Path,
        ocr_dir: Path,
        grouping_dir: Path,
        output_dir: Path
    ):
        self.image_dir = Path(image_dir)
        self.ocr_dir = Path(ocr_dir)
        self.grouping_dir = Path(grouping_dir)
        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # API 配置
        self.api_key = DEFAULT_CONFIG.get("api_key")
        self.base_url = DEFAULT_CONFIG.get("base_url")
        self.model_name = DEFAULT_CONFIG.get("model_name")
        self.batch_size = DEFAULT_CONFIG.get("batch_size", 5)
        self.interval = DEFAULT_CONFIG.get("interval", 15)

        self.client = None
        self.label_description = _generate_label_description()

        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0
        }

    def _init_client(self):
        if not HAS_OPENAI:
            raise ImportError("OpenAI 库未安装")
        if not self.api_key:
            raise ValueError("未配置 API 密钥")

        if self.client is None:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _encode_image(self, image_path: Path) -> str:
        with Image.open(image_path) as img:
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def scan_tasks(self) -> List[Dict[str, Path]]:
        """扫描待处理任务"""
        tasks = []
        for grouping_file in self.grouping_dir.glob("*.json"):
            stem = grouping_file.stem

            # 查找图片
            image_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                candidate = self.image_dir / f"{stem}{ext}"
                if candidate.exists():
                    image_path = candidate
                    break

            # 查找 OCR 文件
            ocr_path = self.ocr_dir / f"{stem}.json"

            if image_path and ocr_path.exists():
                output_path = self.output_dir / f"{stem}.json"
                if not output_path.exists():
                    tasks.append({
                        "image": image_path,
                        "ocr": ocr_path,
                        "grouping": grouping_file,
                        "output": output_path
                    })

        self.stats["total"] = len(tasks)
        return tasks

    def call_vlm(self, image_path: Path, ocr_data: Dict, grouping_data: Dict) -> Dict[str, int]:
        """调用 VLM 进行分类"""
        self._init_client()

        # 构建分组信息
        text_boxes = {box["id"]: box for box in ocr_data.get("text_boxes", [])}
        groups = grouping_data.get("groups", [])

        grouped_info_lines = []
        for group_idx, group in enumerate(groups):
            texts = []
            for box_id in group:
                if box_id in text_boxes:
                    texts.append(text_boxes[box_id]["text"])
            combined_text = " ".join(texts)
            grouped_info_lines.append(f"组 {group_idx}: \"{combined_text}\"")

        grouped_info = "\n".join(grouped_info_lines)

        prompt = CLASSIFICATION_PROMPT.format(
            label_description=self.label_description,
            grouped_info=grouped_info
        )

        base64_image = self._encode_image(image_path)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            max_tokens=4096
        )

        result_text = response.choices[0].message.content.strip()

        # 解析 JSON
        if result_text.startswith("```"):
            lines = result_text.split("\n")
            result_text = "\n".join(lines[1:-1])

        return json.loads(result_text)

    def process_single(self, task: Dict[str, Path]) -> bool:
        """处理单个任务"""
        try:
            image_path = task["image"]
            ocr_path = task["ocr"]
            grouping_path = task["grouping"]
            output_path = task["output"]

            logger.info(f"处理: {image_path.name}")

            # 加载数据
            with open(ocr_path, 'r', encoding='utf-8') as f:
                ocr_data = json.load(f)
            with open(grouping_path, 'r', encoding='utf-8') as f:
                grouping_data = json.load(f)

            # 调用 VLM
            classifications = self.call_vlm(image_path, ocr_data, grouping_data)

            # 构建输出数据
            output_data = {
                "image_name": image_path.name,
                "ocr_file": ocr_path.name,
                "grouping_file": grouping_path.name,
                "classifications": classifications,
                "label_mapping": {
                    str(k): v["name"] for k, v in BILL_OF_LADING_LABELS.items()
                }
            }

            # 保存结果
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            logger.info(f"  ✅ 分类完成: {len(classifications)} 个组")
            self.stats["success"] += 1
            return True

        except Exception as e:
            logger.error(f"  ❌ 失败: {task['image'].name} - {e}")
            self.stats["failed"] += 1
            return False

    def run(self):
        """运行分类处理"""
        logger.info("=" * 60)
        logger.info("Step 4: VLM 关键字分类标注")
        logger.info("=" * 60)
        logger.info(f"图片目录: {self.image_dir}")
        logger.info(f"OCR目录: {self.ocr_dir}")
        logger.info(f"分组目录: {self.grouping_dir}")
        logger.info(f"输出目录: {self.output_dir}")
        logger.info(f"模型: {self.model_name}")

        tasks = self.scan_tasks()
        if not tasks:
            logger.warning("没有待处理的任务")
            return self.stats

        logger.info(f"找到 {len(tasks)} 个待处理任务\n")

        for i, task in enumerate(tasks, 1):
            logger.info(f"[{i}/{len(tasks)}]")
            self.process_single(task)

            if i % self.batch_size == 0 and i < len(tasks):
                logger.info(f"⏳ 等待 {self.interval} 秒...")
                time.sleep(self.interval)

        # 打印统计
        logger.info("\n" + "=" * 60)
        logger.info("分类处理完成")
        logger.info("=" * 60)
        logger.info(f"总任务数: {self.stats['total']}")
        logger.info(f"成功: {self.stats['success']}")
        logger.info(f"失败: {self.stats['failed']}")

        return self.stats


def main():
    parser = argparse.ArgumentParser(description='Step 4: VLM 关键字分类标注')
    parser.add_argument('--image-dir', type=str, help='图片目录')
    parser.add_argument('--ocr-dir', type=str, help='OCR结果目录')
    parser.add_argument('--grouping-dir', type=str, help='分组结果目录')
    parser.add_argument('-o', '--output', type=str, help='输出目录')
    args = parser.parse_args()

    ensure_directories()

    image_dir = Path(args.image_dir) if args.image_dir else PATHS["step1_images"]
    ocr_dir = Path(args.ocr_dir) if args.ocr_dir else PATHS["step2_ocr"]
    grouping_dir = Path(args.grouping_dir) if args.grouping_dir else PATHS["step3_grouping"]
    output_dir = Path(args.output) if args.output else PATHS["step4_classification"]

    processor = VLMClassificationProcessor(image_dir, ocr_dir, grouping_dir, output_dir)
    processor.run()


if __name__ == "__main__":
    main()
