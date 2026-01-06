#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 3: VLM 文本分组标注
VLM Text Grouping Annotation

使用 VLM (Vision Language Model) 对 OCR 识别的文本框进行语义分组。
将属于同一语义单元的文本框合并为一组。

输入:
  - data/02_images/ (图片)
  - data/03_ocr_results/ (OCR结果)
输出:
  - data/04_vlm_grouping/ (分组结果)
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
import concurrent.futures
from PIL import Image

from config import PATHS, DEFAULT_CONFIG, ensure_directories

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenAI API
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("OpenAI 库未安装。请运行: pip install openai")


# 分组提示词
GROUPING_PROMPT = """## 任务：海运单文本框语义分组

你是一个专业的海运单（B/L）文档分析专家。请分析图片中的文本框（已用红框标出并标注ID），将属于同一语义单元的文本框进行分组。

### 分组原则：
1. **同一字段合并**：如公司名+地址+联系方式应合并
2. **数值+单位合并**：如 "1000" + "KGS" 应合并
3. **港口信息合并**：港口名+城市+国家应合并
4. **表格同行合并**：表格中同一行的相关字段应合并

### 不应合并的情况：
- 完全独立的字段（托运人 vs 收货人）
- 标题与正文（"Shipper:" 标签 vs 实际公司名）
- 表格不同行的数据

### 输入的OCR文本框信息：
{ocr_info}

### 输出格式：
返回 JSON 格式的分组列表，每个子列表包含应合并的文本框ID：
```json
[[0, 1, 2], [3], [4, 5], ...]
```

请仅返回 JSON 数组，不要包含其他内容。"""


class VLMGroupingProcessor:
    """VLM 分组处理器"""

    def __init__(
        self,
        image_dir: Path,
        ocr_dir: Path,
        output_dir: Path,
        vis_dir: Optional[Path] = None
    ):
        self.image_dir = Path(image_dir)
        self.ocr_dir = Path(ocr_dir)
        self.output_dir = Path(output_dir)
        self.vis_dir = Path(vis_dir) if vis_dir else None

        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.vis_dir:
            self.vis_dir.mkdir(parents=True, exist_ok=True)

        # API 配置
        self.api_key = DEFAULT_CONFIG.get("api_key")
        self.base_url = DEFAULT_CONFIG.get("base_url")
        self.model_name = DEFAULT_CONFIG.get("model_name")
        self.batch_size = DEFAULT_CONFIG.get("batch_size", 5)
        self.interval = DEFAULT_CONFIG.get("interval", 15)

        self.client = None

        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "total_groups": 0
        }

    def _init_client(self):
        """初始化 OpenAI 客户端"""
        if not HAS_OPENAI:
            raise ImportError("OpenAI 库未安装")
        if not self.api_key:
            raise ValueError("未配置 API 密钥")

        if self.client is None:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _encode_image(self, image_path: Path) -> str:
        """将图片编码为 base64"""
        with Image.open(image_path) as img:
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def scan_tasks(self) -> List[Dict[str, Path]]:
        """扫描待处理任务"""
        tasks = []
        for ocr_file in self.ocr_dir.glob("*.json"):
            # 查找对应的图片
            stem = ocr_file.stem
            image_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                candidate = self.image_dir / f"{stem}{ext}"
                if candidate.exists():
                    image_path = candidate
                    break

            if image_path:
                # 检查是否已处理
                output_path = self.output_dir / f"{stem}.json"
                if not output_path.exists():
                    tasks.append({
                        "image": image_path,
                        "ocr": ocr_file,
                        "output": output_path
                    })

        self.stats["total"] = len(tasks)
        return tasks

    def call_vlm(self, image_path: Path, ocr_data: Dict) -> List[List[int]]:
        """调用 VLM 进行分组"""
        self._init_client()

        # 构建 OCR 信息文本
        ocr_info_lines = []
        for box in ocr_data.get("text_boxes", []):
            ocr_info_lines.append(f"ID {box['id']}: \"{box['text']}\"")
        ocr_info = "\n".join(ocr_info_lines)

        prompt = GROUPING_PROMPT.format(ocr_info=ocr_info)
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
            output_path = task["output"]

            logger.info(f"处理: {image_path.name}")

            # 加载 OCR 数据
            with open(ocr_path, 'r', encoding='utf-8') as f:
                ocr_data = json.load(f)

            # 调用 VLM
            groups = self.call_vlm(image_path, ocr_data)

            # 构建输出数据
            output_data = {
                "image_name": image_path.name,
                "ocr_file": ocr_path.name,
                "groups": groups,
                "total_groups": len(groups),
                "total_boxes": ocr_data.get("total_boxes", 0)
            }

            # 保存结果
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            logger.info(f"  ✅ 分组完成: {len(groups)} 个组")
            self.stats["success"] += 1
            self.stats["total_groups"] += len(groups)
            return True

        except Exception as e:
            logger.error(f"  ❌ 失败: {task['image'].name} - {e}")
            self.stats["failed"] += 1
            return False

    def run(self):
        """运行分组处理"""
        logger.info("=" * 60)
        logger.info("Step 3: VLM 文本分组标注")
        logger.info("=" * 60)
        logger.info(f"图片目录: {self.image_dir}")
        logger.info(f"OCR目录: {self.ocr_dir}")
        logger.info(f"输出目录: {self.output_dir}")
        logger.info(f"模型: {self.model_name}")
        logger.info(f"API: {self.base_url}")

        tasks = self.scan_tasks()
        if not tasks:
            logger.warning("没有待处理的任务")
            return self.stats

        logger.info(f"找到 {len(tasks)} 个待处理任务\n")

        # 批量处理
        for i, task in enumerate(tasks, 1):
            logger.info(f"[{i}/{len(tasks)}]")
            self.process_single(task)

            # 批次间隔
            if i % self.batch_size == 0 and i < len(tasks):
                logger.info(f"⏳ 等待 {self.interval} 秒...")
                time.sleep(self.interval)

        # 打印统计
        logger.info("\n" + "=" * 60)
        logger.info("分组处理完成")
        logger.info("=" * 60)
        logger.info(f"总任务数: {self.stats['total']}")
        logger.info(f"成功: {self.stats['success']}")
        logger.info(f"失败: {self.stats['failed']}")
        logger.info(f"总分组数: {self.stats['total_groups']}")

        return self.stats


def main():
    parser = argparse.ArgumentParser(description='Step 3: VLM 文本分组标注')
    parser.add_argument('--image-dir', type=str, help='图片目录')
    parser.add_argument('--ocr-dir', type=str, help='OCR结果目录')
    parser.add_argument('-o', '--output', type=str, help='输出目录')
    args = parser.parse_args()

    ensure_directories()

    image_dir = Path(args.image_dir) if args.image_dir else PATHS["step1_images"]
    ocr_dir = Path(args.ocr_dir) if args.ocr_dir else PATHS["step2_ocr"]
    output_dir = Path(args.output) if args.output else PATHS["step3_grouping"]

    processor = VLMGroupingProcessor(image_dir, ocr_dir, output_dir)
    processor.run()


if __name__ == "__main__":
    main()
