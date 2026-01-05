#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多格式文档转FUNSD格式脚本
Multi-Format Document to FUNSD Format Script

支持处理PDF、Excel、Word文档，统一转换为FUNSD格式数据集
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import logging

# 导入自定义模块
from config import DEFAULT_CONFIG, BILL_OF_LADING_LABELS
from document_parser import DocumentParser
from generate_funsd_format import ImageToFUNSDConverter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiFormatToFUNSD:
    """多格式文档转FUNSD格式处理器"""

    def __init__(self):
        """初始化"""
        self.config = DEFAULT_CONFIG
        self.labels = BILL_OF_LADING_LABELS
        self.parser = DocumentParser()
        self.converter = ImageToFUNSDConverter()

        # 创建输出目录
        self.output_dir = Path(self.config["output_folder"]) / "funsd_format"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"输出目录: {self.output_dir}")

    def process_directory(self, input_dir: str) -> Dict[str, Any]:
        """
        批量处理目录中的所有文档

        Args:
            input_dir: 输入目录路径

        Returns:
            处理统计信息
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")

        # 获取所有支持的文档文件
        supported_ext = ['.pdf', '.xlsx', '.xls', '.docx', '.doc']
        doc_files = []
        for ext in supported_ext:
            doc_files.extend(input_path.glob(f"*{ext}"))
            doc_files.extend(input_path.glob(f"**/*{ext}"))

        if not doc_files:
            logger.warning(f"在 {input_dir} 中未找到支持的文档文件")
            return {
                "total_files": 0,
                "processed_files": 0,
                "failed_files": 0,
                "total_pages": 0,
                "results": []
            }

        logger.info(f"找到 {len(doc_files)} 个文档文件")

        # 统计信息
        stats = {
            "total_files": len(doc_files),
            "processed_files": 0,
            "failed_files": 0,
            "total_pages": 0,
            "results": []
        }

        # 处理每个文档
        for doc_file in doc_files:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"处理文档: {doc_file.name}")
                logger.info(f"{'='*60}")

                result = self.process_single_document(doc_file)
                stats["processed_files"] += 1
                stats["total_pages"] += result["pages"]
                stats["results"].append({
                    "file": str(doc_file),
                    "status": "success",
                    "pages": result["pages"],
                    "annotations": result["annotations"]
                })

                logger.info(f"✅ 文档处理成功: {doc_file.name}")
                logger.info(f"   页数: {result['pages']}")
                logger.info(f"   标注数: {result['annotations']}")

            except Exception as e:
                logger.error(f"❌ 文档处理失败: {doc_file.name}")
                logger.error(f"   错误: {str(e)}")
                stats["failed_files"] += 1
                stats["results"].append({
                    "file": str(doc_file),
                    "status": "failed",
                    "error": str(e)
                })

        return stats

    def process_single_document(self, doc_path: Path) -> Dict[str, Any]:
        """
        处理单个文档

        Args:
            doc_path: 文档路径

        Returns:
            处理结果字典
        """
        # 解析文档
        pages = self.parser.parse_document(doc_path)

        if not pages:
            raise ValueError("文档解析后没有获取到内容")

        logger.info(f"文档解析完成，共 {len(pages)} 页")

        # 为每页生成FUNSD格式
        all_annotations = 0
        page_results = []

        for page_num, (text, image) in enumerate(pages):
            logger.info(f"\n处理第 {page_num + 1} 页...")

            # 保存临时图像
            temp_img_path = self.parser.temp_dir / f"{doc_path.stem}_page_{page_num + 1}.png"
            image.save(temp_img_path)

            # 转换为FUNSD格式
            funsd_data = self.converter.convert_image_to_funsd(
                str(temp_img_path),
                f"{doc_path.stem}_page_{page_num + 1}"
            )

            # 保存单独的JSON文件
            page_json_path = self.output_dir / f"{doc_path.stem}_page_{page_num + 1}.json"
            with open(page_json_path, 'w', encoding='utf-8') as f:
                json.dump(funsd_data, f, ensure_ascii=False, indent=2)

            annotations_count = len(funsd_data.get("form", []))
            all_annotations += annotations_count

            page_results.append({
                "page": page_num + 1,
                "image_path": str(temp_img_path),
                "json_path": str(page_json_path),
                "annotations": annotations_count
            })

            logger.info(f"   ✅ 第 {page_num + 1} 页完成，{annotations_count} 个标注")

        return {
            "pages": len(pages),
            "annotations": all_annotations,
            "page_results": page_results
        }

    def generate_statistics(self, stats: Dict[str, Any]) -> None:
        """生成统计报告"""
        stats_file = self.output_dir / "statistics.txt"

        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("多格式文档转FUNSD格式 - 统计报告\n")
            f.write("="*60 + "\n\n")

            f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"输入目录: {self.config['input_folder']}\n")
            f.write(f"输出目录: {self.output_dir}\n\n")

            f.write("-"*60 + "\n")
            f.write("处理统计\n")
            f.write("-"*60 + "\n")
            f.write(f"总文件数:     {stats['total_files']}\n")
            f.write(f"成功处理:     {stats['processed_files']}\n")
            f.write(f"处理失败:     {stats['failed_files']}\n")
            f.write(f"总页数:       {stats['total_pages']}\n\n")

            f.write("-"*60 + "\n")
            f.write("详细结果\n")
            f.write("-"*60 + "\n")

            for result in stats['results']:
                f.write(f"\n文件: {Path(result['file']).name}\n")
                f.write(f"状态: {result['status']}\n")

                if result['status'] == 'success':
                    f.write(f"页数: {result['pages']}\n")
                    f.write(f"标注数: {result['annotations']}\n")
                else:
                    f.write(f"错误: {result.get('error', 'N/A')}\n")

            f.write("\n" + "="*60 + "\n")
            f.write("支持格式说明\n")
            f.write("="*60 + "\n")
            f.write("本工具支持以下文档格式:\n")
            f.write("  1. PDF文档 (.pdf)\n")
            f.write("  2. Excel工作簿 (.xlsx, .xls)\n")
            f.write("  3. Word文档 (.docx, .doc)\n\n")
            f.write("所有文档都将转换为图像，然后使用PaddleOCR进行文本识别，\n")
            f.write("最后通过Gemini 2.0 Flash进行语义分类和标注。\n")

        logger.info(f"统计报告已生成: {stats_file}")

    def generate_readme(self) -> None:
        """生成使用说明"""
        readme_file = self.output_dir / "README.md"

        readme_content = """# FUNSD格式数据集

本目录包含从多格式文档转换而来的FUNSD格式数据集。

## 文件说明

- `*.json`: FUNSD格式的标注文件
- `statistics.txt`: 处理统计报告
- `README.md`: 本说明文件

## FUNSD格式说明

FUNSD (Form Understanding in Noisy Scanned Documents) 是一个用于表单理解的标注格式。

### JSON结构

```json
{
  "image": "图像文件名",
  "width": 图像宽度,
  "height": 图像高度,
  "form": [
    {
      "text": "文本内容",
      "label": "标签类别",
      "bbox": [x1, y1, x2, y2],
      "linking": [],
      "id": 唯一标识符
    }
  ]
}
```

### 标签类别

本项目定义了29种海运单关键字类别:

**核心角色类 (3种)**
- shipper: 托运人
- consignee: 收货人
- notify_party: 通知方

**地理信息类 (5种)**
- port_of_loading: 装货港
- port_of_discharge: 卸货港
- port_of_delivery: 交货港
- place_of_delivery: 交货地点
- place_of_receipt: 收货地点

**运输信息类 (5种)**
- vessel: 船名
- voyage: 航次
- vessel_voyage: 船名航次
- container_no: 集装箱号
- seal_no: 封号

**货物信息类 (5种)**
- description_of_goods: 货物描述
- marks_numbers: 唛头和编号
- package: 包装件数
- weight: 重量
- volume: 体积

**编号日期类 (4种)**
- bl_no: 提单号
- freight: 运费
- date: 日期
- time: 时间

**特殊标识类 (3种)**
- header: 头部信息
- footer: 底部信息
- company_logo: 公司标志

**费率类 (2种)**
- rate: 费率
- total: 总计

**其他 (2种)**
- other: 其他信息
- abandon: 废弃内容

## 使用方法

### 1. 训练模型

可以使用以下框架训练模型:

**LayoutLMv3 (推荐)**
```python
from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Processor

# 加载模型
model = LayoutLMv3ForTokenClassification.from_pretrained("microsoft/layoutlmv3-base")
processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")
```

**自定义Transformer**
```python
import torch
from torch.utils.data import Dataset, DataLoader

# 自定义数据集类
class BOLDataset(Dataset):
    def __init__(self, json_files, processor):
        self.json_files = json_files
        self.processor = processor

    def __len__(self):
        return len(self.json_files)

    def __getitem__(self, idx):
        # 加载和处理数据
        pass
```

### 2. 推理预测

```python
import json
from PIL import Image

# 加载训练好的模型
model = load_trained_model()

# 加载图像和JSON
image = Image.open("test_image.jpg")
with open("test_annotation.json", 'r') as f:
    annotation = json.load(f)

# 推理
predictions = model.predict(image, annotation)
```

### 3. 评估指标

常用评估指标:
- 精确率 (Precision)
- 召回率 (Recall)
- F1分数 (F1-Score)
- 准确率 (Accuracy)

## 注意事项

1. 所有文档在处理前都会被转换为图像
2. 图像分辨率为300 DPI以确保OCR准确率
3. 使用Gemini 2.0 Flash进行语义分类，需要配置API密钥
4. 支持的文档格式: PDF, Excel, Word

## 更多信息

- FUNSD格式: https://guillaume-bellafronte.medium.com/funsd-a-guide-to-this-dataset-for-form-understanding-e9cf84adedc4
- LayoutLMv3: https://huggingface.co/microsoft/layoutlmv3-base
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
"""

        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        logger.info(f"使用说明已生成: {readme_file}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("多格式文档转FUNSD格式工具")
    print("="*60)
    print("\n支持的文档格式:")
    print("  1. PDF文档 (.pdf)")
    print("  2. Excel工作簿 (.xlsx, .xls)")
    print("  3. Word文档 (.docx, .doc)")
    print()

    # 检查配置
    if DEFAULT_CONFIG["api_key"] == "YOUR_API_KEY":
        print("❌ 错误: 请先在config.py中配置Gemini API密钥")
        print("   获取地址: https://aistudio.google.com/apikey")
        sys.exit(1)

    # 检查输入目录
    input_dir = DEFAULT_CONFIG["input_folder"]
    if not os.path.exists(input_dir):
        print(f"⚠️  警告: 输入目录不存在: {input_dir}")
        os.makedirs(input_dir, exist_ok=True)
        print(f"   已创建目录: {input_dir}")
        print(f"   请将文档文件放入此目录后重新运行")
        sys.exit(1)

    # 检查输出目录
    output_dir = DEFAULT_CONFIG["output_folder"]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ 已创建输出目录: {output_dir}")

    # 获取文档文件列表
    supported_ext = ['.pdf', '.xlsx', '.xls', '.docx', '.doc']
    doc_files = []
    for ext in supported_ext:
        doc_files.extend(Path(input_dir).glob(f"*{ext}"))
        doc_files.extend(Path(input_dir).glob(f"**/*{ext}"))

    if not doc_files:
        print(f"❌ 在 {input_dir} 中未找到支持的文档文件")
        print("   支持格式: PDF, Excel, Word")
        sys.exit(1)

    print(f"✅ 找到 {len(doc_files)} 个文档文件\n")

    # 确认继续
    confirm = input("确认开始处理? (y/N，默认: y): ").strip().lower()
    if confirm in ['n', 'no']:
        print("已取消操作")
        sys.exit(0)

    # 开始处理
    try:
        processor = MultiFormatToFUNSD()
        stats = processor.process_directory(input_dir)

        # 生成报告
        processor.generate_statistics(stats)
        processor.generate_readme()

        # 打印总结
        print("\n" + "="*60)
        print("处理完成总结")
        print("="*60)
        print(f"总文件数:   {stats['total_files']}")
        print(f"成功处理:   {stats['processed_files']}")
        print(f"处理失败:   {stats['failed_files']}")
        print(f"总页数:     {stats['total_pages']}")
        print(f"\n输出目录:   {processor.output_dir}")
        print(f"统计报告:   {processor.output_dir}/statistics.txt")
        print(f"使用说明:   {processor.output_dir}/README.md")
        print("\n✅ 所有文档处理完成！")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理临时文件
        try:
            processor.parser.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
