# 海运单关键字识别数据集创建工具
# Bill of Lading Keyword Recognition Dataset Creator

一个基于Gemini 2.0 Flash API的专业工具，专门用于从海运单（Bill of Lading, B/L）文档中自动提取和识别关键信息字段，生成适用于训练文档理解模型的FUNSD格式数据集。

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 目录

- [功能特性](#功能特性)
- [完整处理流程](#完整处理流程)
  - [流程概述](#流程概述)
  - [脚本功能详解](#脚本功能详解)
- [支持的标签类别](#支持的标签类别)
- [环境要求](#环境要求)
- [安装依赖](#安装依赖)
- [快速开始](#快速开始)
- [工作流程](#工作流程)
- [项目结构](#项目结构)
- [详细使用说明](#详细使用说明)
  - [配置文件说明](#配置文件说明)
  - [性能优化建议](#性能优化建议)
  - [常见错误处理](#常见错误处理)
- [FUNSD格式详细说明](#funsd格式详细说明)
  - [标准格式](#标准格式)
  - [标签类型](#标签类型)
  - [输出示例](#输出示例)
- [训练模型](#训练模型)
- [海运单关键字详解](#海运单关键字详解)
- [迁移指南](#迁移指南)
- [FUNSD格式生成指南](#funsd格式生成指南)
  - [核心原理](#核心原理)
  - [脚本说明](#脚本说明)
  - [处理流程详解](#处理流程详解)
  - [高级配置](#高级配置)
  - [性能优化](#性能优化)
  - [故障排除](#故障排除)
- [常见问题](#常见问题)
- [许可证](#许可证)
- [更新日志](#更新日志)

## ✨ 功能特性

- 🚢 **海运单专业处理**：专门针对海运单（B/L）文档结构优化
- 📄 **多格式文档支持**：支持PDF、Excel (.xlsx/.xls)、Word (.docx/.doc) 多种文档格式
- 🎯 **智能关键字识别**：自动识别托运人、收货人、港口、船名等29种关键字段
- 🤖 **VLM辅助标注**：使用Gemini 2.0 Flash进行智能语义分组和分类
- 📦 **文本框智能合并**：将相关文本框合并为逻辑文本块
- 🔄 **FUNSD格式输出**：生成标准FUNSD JSON格式数据集
- 📊 **结构化数据**：保留完整的文本内容和字段类型信息
- ⚡ **高效批处理**：支持批量处理，提高工作效率

## 🔄 完整处理流程

### 流程概述

本项目采用"**OCR提供坐标 + Gemini提供标签**"的混合模式，整个流程包括4个关键步骤：

```
海运单PDF → 文本提取 → Gemini语义分类 → FUNSD格式输出
```

### 步骤详解

#### 第1步：文件转图片（PDF转换）
**脚本**: `pdf_to_funsd.py`

**功能说明**:
- 将PDF文档转换为图像
- 为OCR识别做准备
- 支持多页处理

**关键代码**:
```python
# 使用PyMuPDF将PDF转换为图像
import pymupdf

doc = pymupdf.open(pdf_path)
page = doc[0]  # 获取第一页
pixmap = page.get_pixmap(dpi=300)
image = pixmap.tobytes("png")
```

**输出**: 图像文件，用于OCR识别

#### 第2步：图片OCR（文本识别）
**脚本**: `generate_funsd_format.py` 和 `pdf_to_funsd.py`

**功能说明**:
- **引擎**: PaddleOCR
  - 提取图像中的文本和精确边界框
  - 支持多语言识别
  - 自动文本分词
  - 高精度文本检测

**关键代码**:
```python
# 使用PaddleOCR提取文本和坐标
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang="ch", enable_mkldnn=True)
result = ocr.ocr(image_path, cls=True)

for line in result[0]:
    box = line[0]  # 四点坐标
    text = line[1][0]  # 识别文本
    confidence = line[1][1]  # 置信度
```

**输出**: OCR结果列表，包含文本内容、边界框坐标、置信度

#### 第3步：Gemini标注（语义分类）
**脚本**: `vlm_anno_bol.py`、`vlm_anno2_bol.py`、`pdf_to_funsd.py`、`generate_funsd_format.py`

**功能说明**:
- 使用Gemini 2.0 Flash对文本进行语义分类
- 识别海运单字段类型（29种分类）
- 将结果映射为FUNSD格式标签

**两次标注流程**:

**第一次 - 文本分组** (`vlm_anno_bol.py`):
```python
# 将相关文本框合并为逻辑文本块
prompt = """
## 任务：海运单文本框语义分组
将属于同一海运单字段的文本框进行语义分组。
例如：公司名、地址、联系方式应合并为一个托运人信息。
"""
```

**第二次 - 关键字分类** (`vlm_anno2_bol.py`):
```python
# 识别每个文本块对应的海运单字段类型
prompt = """
## 任务：海运单关键字分类
对提供的文本块进行分类：
0. shipper (托运人)
1. consignee (收货人)
...
28. abandon (废弃内容)
"""
```

**输出**: 文本ID到类别ID的映射字典

#### 第4步：汇总为FUNSD（格式转换）
**脚本**: `pdf_to_funsd.py`、`generate_funsd_format.py`、`convert_label_bol.py`

**功能说明**:
- 将OCR坐标和Gemini分类结果整合
- 转换为标准FUNSD JSON格式
- 生成层级结构的文本和边界框信息

**关键代码**:
```python
def generate_funsd_format(ocr_results, classification):
    funsd_data = {"form": []}

    for result in ocr_results:
        text_id = str(result["id"])
        if text_id in classification:
            bol_class_id = classification[text_id]
            funsd_label = FUNSD_LABEL_MAPPING[bol_class_id]

            entity = {
                "box": result["box"],
                "text": result["text"],
                "label": funsd_label,
                "words": split_text_to_words(result["text"], result["box"]),
                "linking": [],
                "id": result["id"]
            }
            funsd_data["form"].append(entity)

    return funsd_data
```

**输出**: 标准FUNSD JSON文件

### 脚本功能详解

| 脚本名称 | 功能 | 适用场景 | 输出格式 |
|---------|------|----------|----------|
| **pdf_to_funsd.py** | 直接从PDF生成FUNSD | 推荐使用，最简单 | JSON |
| **generate_funsd_format.py** | 从图像生成FUNSD | 处理已有图像文件 | JSON |
| **extract_paragraph_bol.py** | PDF文本框提取 | 分步处理第一步 | 文本框坐标 |
| **vlm_anno_bol.py** | VLM文本分组 | 分步处理第二步 | 分组结果 |
| **vlm_anno2_bol.py** | VLM关键字分类 | 分步处理第五步 | 分类结果 |
| **convert_label_bol.py** | 标签格式转换 | 分步处理第六步 | 标签文件 |
| **correct_format_bol.py** | 校正格式 | 清理VLM输出 | 修正文件 |
| **correct_box_bol.py** | 校正边界框 | 合并文本框 | 合并框 |
| **run_all_bol.py** | 一键运行 | 自动化流程 | 交互式选择 |
| **check_config.py** | 配置检查 | 验证环境 | 状态报告 |
| **install_dependencies.py** | 安装依赖 | 环境搭建 | 自动安装 |

## 🏷️ 支持的标签类别

本项目支持29种海运单关键字段的识别与标注，最终映射为FUNSD格式的4种标签类型：

### 核心角色类（3种）
| 标签ID | 类别名称 | 英文标识 | 描述 | FUNSD映射 |
|--------|----------|----------|------|-----------|
| 0 | shipper | 托运人 | 货物发送方 | answer |
| 1 | consignee | 收货人 | 货物接收方 | answer |
| 2 | notify_party | 通知方 | 到货通知接收方 | answer |

### 地理信息类（5种）
| 标签ID | 类别名称 | 英文标识 | 描述 | FUNSD映射 |
|--------|----------|----------|------|-----------|
| 3 | port_of_loading | 装货港 | 货物装载港口 | answer |
| 4 | port_of_discharge | 卸货港 | 货物卸载港口 | answer |
| 5 | port_of_delivery | 交货港 | 交货地点 | answer |
| 6 | place_of_delivery | 交货地点 | 实际交货地点 | answer |
| 7 | place_of_receipt | 收货地点 | 货物接收地点 | answer |

### 运输信息类（5种）
| 标签ID | 类别名称 | 英文标识 | 描述 | FUNSD映射 |
|--------|----------|----------|------|-----------|
| 8 | vessel | 船名 | 承运船舶名称 | answer |
| 9 | voyage | 航次 | 船舶航次号 | answer |
| 10 | vessel_voyage | 船名航次 | 船名和航次组合 | answer |
| 11 | container_no | 集装箱号 | 集装箱编号 | answer |
| 12 | seal_no | 封号 | 集装箱封条编号 | answer |

### 货物信息类（5种）
| 标签ID | 类别名称 | 英文标识 | 描述 | FUNSD映射 |
|--------|----------|----------|------|-----------|
| 13 | description_of_goods | 货物描述 | 货物详细描述 | answer |
| 14 | marks_numbers | 唛头和编号 | 货物包装标记 | answer |
| 15 | package | 包装件数 | 货物包装及件数 | answer |
| 16 | weight | 重量 | 货物重量 | answer |
| 17 | volume | 体积 | 货物体积 | answer |

### 编号日期类（4种）
| 标签ID | 类别名称 | 英文标识 | 描述 | FUNSD映射 |
|--------|----------|----------|------|-----------|
| 18 | bl_no | 提单号 | 提单编号 | answer |
| 19 | freight | 运费 | 运输费用 | answer |
| 20 | date | 日期 | 各类日期信息 | answer |
| 21 | time | 时间 | 时间信息 | answer |

### 特殊标识类（3种）
| 标签ID | 类别名称 | 英文标识 | 描述 | FUNSD映射 |
|--------|----------|----------|------|-----------|
| 22 | header | 头部信息 | 单据头部信息 | header |
| 23 | footer | 底部信息 | 单据底部信息 | other |
| 24 | company_logo | 公司标志 | 公司标志或图标 | other |

### 费率类（2种）
| 标签ID | 类别名称 | 英文标识 | 描述 | FUNSD映射 |
|--------|----------|----------|------|-----------|
| 25 | rate | 费率 | 单位费率 | answer |
| 26 | total | 总计 | 总计金额或数量 | answer |

### 其他（2种）
| 标签ID | 类别名称 | 英文标识 | 描述 | FUNSD映射 |
|--------|----------|----------|------|-----------|
| 27 | other | 其他信息 | 其他重要信息 | other |
| 28 | abandon | 废弃内容 | 需要废弃的内容 | other |

## 🔧 环境要求

- **Python**: 3.7 或更高版本
- **API Key**: Gemini 2.0 Flash API Key（获取地址：https://aistudio.google.com/apikey）
- **内存**: 建议 8GB 以上
- **存储**: 至少 10GB 可用空间（用于存储中间文件和数据集）

## 📦 安装依赖

```bash
# 安装核心依赖
pip install -q -U google-genai

# 安装文档处理依赖
pip install pymupdf
pip install numpy
pip install tqdm
pip install rich

# 安装OCR依赖（必需）
pip install paddlepaddle paddleocr
```

## 📄 多格式文档支持

本工具支持处理多种文档格式，包括：

### 支持的文档格式

| 格式类型 | 文件扩展名 | 说明 | 是否需要额外依赖 |
|---------|-----------|------|-----------------|
| **PDF** | .pdf | PDF文档 | PyMuPDF |
| **Excel** | .xlsx, .xls | Excel工作簿 | openpyxl |
| **Word** | .docx | Word文档 | python-docx |
| **Word旧版** | .doc | Word文档（旧版） | docx2pdf |
| **图像** | .png, .jpg | 图像文件 | Pillow |

### 依赖安装说明

**方式一：自动安装（推荐）**
```bash
python install_dependencies.py
# 选择选项2：核心依赖 + 可选依赖 (支持多格式文档)
```

**方式二：手动安装**
```bash
# 核心依赖（必需）
pip install google-genai
pip install paddlepaddle paddleocr

# PDF支持
pip install pymupdf

# Excel支持
pip install openpyxl

# Word支持
pip install python-docx
pip install docx2pdf  # 用于支持.doc格式

# 图像处理
pip install pillow
pip install opencv-python
```

### 文档处理流程

所有文档格式都会经过以下统一流程：

```
1. 文档解析
   ├─ PDF → 图像（PyMuPDF）
   ├─ Excel → 图像（openpyxl渲染）
   └─ Word → 文本/图像（python-docx或docx2pdf）

2. 图像处理
   └─ 所有文档 → 统一图像格式

3. OCR识别
   └─ PaddleOCR → 文本+坐标

4. 语义分类
   └─ Gemini 2.0 Flash → 标签

5. FUNSD输出
   └─ JSON格式数据集
```

### 注意事项

1. **Excel文档**：会自动为每个工作表创建页面，支持多工作表处理
2. **Word文档**：
   - .docx格式：直接解析文本和表格
   - .doc格式：需要先转换为PDF（自动处理）
3. **PDF文档**：保持原始分页，支持多页处理
4. **图像质量**：所有文档转换的图像都使用300 DPI以确保OCR精度

## 🚀 快速开始

### 方式一：多格式文档一键处理（推荐）

1. **准备文档文件夹**
   ```bash
   # 支持PDF、Excel、Word文档
   mkdir -p bills_of_lading
   # 将海运单文档文件复制到此目录
   # 支持格式：.pdf, .xlsx, .xls, .docx, .doc
   ```

2. **安装依赖（支持多格式文档）**
   ```bash
   python install_dependencies.py
   # 选择选项2：核心依赖 + 可选依赖 (支持多格式文档)
   ```

3. **检查配置**
   ```bash
   python check_config.py
   ```
   - 确保API密钥已正确配置
   - 验证依赖包已安装
   - 检查输入输出路径

4. **一键生成FUNSD格式**
   ```bash
   python multi_format_to_funsd.py
   ```
   - 自动识别文档格式
   - 支持混合文档类型处理
   - 批量转换为FUNSD JSON格式

5. **查看结果**
   - FUNSD格式文件：`./bol_output/funsd_format/*.json`
   - 统计报告：`./bol_output/funsd_format/statistics.txt`

### 方式二：仅处理PDF文档

1. **准备海运单PDF文件夹**
   ```bash
   # 将海运单PDF文件放入 ./bills_of_lading 文件夹
   mkdir -p bills_of_lading
   # 复制您的海运单PDF文件到此目录
   ```

2. **检查配置**
   ```bash
   python check_config.py
   ```
   - 确保API密钥已正确配置
   - 验证依赖包已安装
   - 检查输入输出路径

3. **一键生成FUNSD格式**
   ```bash
   python run_all_bol.py
   ```
   - 选择选项1：从PDF直接生成FUNSD格式
   - 脚本会自动处理所有PDF并生成JSON文件

4. **查看结果**
   - FUNSD格式文件：`./bol_output/funsd_format/*.json`
   - 统计报告：`./bol_output/funsd_format/statistics.txt`

### 方式三：分步处理（高级用户）

```bash
# 步骤1: 提取文本框
python extract_paragraph_bol.py

# 步骤2: 第一次VLM标注（文本分组）
python vlm_anno_bol.py

# 步骤3: 校正格式
python correct_format_bol.py

# 步骤4: 校正边界框
python correct_box_bol.py

# 步骤5: 第二次VLM标注（关键字分类）
python vlm_anno2_bol.py

# 步骤6: 转换标签格式
python convert_label_bol.py

# 步骤7: 生成FUNSD格式
python pdf_to_funsd.py
```

## 🔄 工作流程

```
海运单PDF → 文本提取 → VLM语义分类 → FUNSD格式输出
                                           ↓
                                  结构化JSON数据集
```

详细流程：
```
PDF文档
  ↓ (extract_paragraph_bol.py)
文本块 + 坐标
  ↓ (vlm_anno_bol.py)
语义分组结果
  ↓ (correct_format_bol.py + correct_box_bol.py)
合并文本块
  ↓ (vlm_anno2_bol.py)
分类标签
  ↓ (convert_label_bol.py)
标签文件
  ↓ (pdf_to_funsd.py)
FUNSD JSON格式
```

## 📁 项目结构

```
海运单关键字识别数据集创建工具/
├── README.md                      # 项目说明文档（本文档）
├── config.py                      # 配置文件（标签类别、关键词映射等）
├── bill_of_lading_keywords.md     # 海运单关键字说明文档
├── FUNSD_FORMAT_GUIDE.md          # FUNSD格式详细说明
├── QUICKSTART.md                  # 快速开始指南
├── MIGRATION_GUIDE.md             # 迁移指南
├── check_config.py                # 配置检查脚本
│
├── 核心处理脚本/
│   ├── multi_format_to_funsd.py   # 多格式文档转FUNSD（推荐）
│   ├── pdf_to_funsd.py            # PDF转FUNSD格式
│   ├── generate_funsd_format.py   # 图像转FUNSD格式
│   ├── document_parser.py         # 多格式文档解析器
│   ├── extract_paragraph_bol.py   # PDF文本框提取
│   ├── vlm_anno_bol.py            # 第一次VLM标注（文本分组）
│   ├── vlm_anno2_bol.py           # 第二次VLM标注（关键字分类）
│   ├── convert_label_bol.py       # 标签格式转换
│   ├── correct_format_bol.py      # 格式校正
│   └── correct_box_bol.py         # 边界框校正
│
├── 辅助脚本/
│   ├── run_all_bol.py             # 一键运行脚本
│   └── install_dependencies.py    # 依赖安装脚本
│
├── 输入输出目录/
│   ├── bills_of_lading/           # 文档输入目录（支持PDF/Excel/Word）
│   └── bol_output/                # 处理结果输出目录
│       └── funsd_format/          # FUNSD格式输出
│           ├── *.json             # JSON标注文件
│           ├── statistics.txt     # 统计报告
│           └── README.md          # 使用说明
│
└── 示例数据/
    └── testing_data_example/      # FUNSD格式示例
```

## 📖 详细使用说明

### 配置文件说明

编辑 `config.py` 文件以自定义配置：

**⚠️ 首先配置API密钥：**
1. 访问 https://aistudio.google.com/apikey
2. 使用Google账号登录
3. 点击 "Create API key"
4. 复制生成的API密钥
5. 编辑 `config.py`，找到第349行：
   ```python
   "api_key": "YOUR_API_KEY",  # ⚠️  请替换为您的Gemini API密钥
   ```
6. 将 `YOUR_API_KEY` 替换为您的实际API密钥

**其他配置选项：**
```python
# API配置
DEFAULT_CONFIG = {
    "api_key": "YOUR_API_KEY",  # ⚠️  必须替换为您的API密钥
    "input_folder": "./bills_of_lading",  # 输入PDF目录
    "output_folder": "./bol_output",       # 输出目录
    "batch_size": 5,        # 并行处理数量
    "interval": 15,         # 批次间等待时间（秒）
    "model_name": "gemini-2.0-flash",
    "image_dpi": 300,       # 图像DPI
    "only_first_page": True # 是否只处理第一页
}
```

**验证配置：**
运行配置检查脚本：
```bash
python check_config.py
```

### 性能优化建议

1. **批处理大小**：根据API配额调整 `batch_size`（建议 3-10）
2. **等待间隔**：调整 `interval` 避免API限制（建议 10-20秒）
3. **图像DPI**：提高DPI可获得更精确的标注，但会增加处理时间
4. **多页处理**：将 `only_first_page` 设为 False 处理多页文档

### 常见错误处理

1. **API密钥错误**
   ```
   解决方案：检查 config.py 中的 GOOGLE_API_KEY 是否正确设置
   ```

2. **文件路径错误**
   ```
   解决方案：确保输入文件夹路径正确，且包含PDF文件
   ```

3. **内存不足**
   ```
   解决方案：减少 batch_size 或关闭其他程序释放内存
   ```

## 📊 FUNSD格式详细说明

### 标准格式

每个JSON文件包含以下字段：

```json
{
  "form": [
    {
      "box": [x1, y1, x2, y2],  // 边界框坐标（像素）
      "text": "文本内容",        // 识别的文本
      "label": "标签类型",       // answer/header/other/question
      "words": [                // 单词级别的详细信息
        {
          "text": "单词",        // 单词文本
          "box": [x1, y1, x2, y2]  // 单词边界框
        }
      ],
      "linking": [],            // 实体间的关系（可选）
      "id": 0                   // 实体唯一标识符
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `box` | list | 边界框坐标 [x1, y1, x2, y2] |
| `text` | str | 识别的文本内容 |
| `label` | str | 标签类型（question/answer/header/other） |
| `words` | list | 单词级别的详细信息 |
| `linking` | list | 实体间的关系（可选） |
| `id` | int | 实体唯一标识符 |

### 标签类型

- **answer**: 海运单的关键字段信息（托运人、收货人、港口等）
- **header**: 单据头部信息
- **other**: 其他信息（页脚、公司标志等）
- **question**: 问题标签（本项目中较少使用）

### 输出示例

```json
{
  "form": [
    {
      "box": [102, 345, 250, 380],
      "text": "ABC Trading Co.",
      "label": "answer",
      "words": [
        {
          "text": "ABC",
          "box": [102, 350, 140, 375]
        },
        {
          "text": "Trading",
          "box": [145, 345, 210, 380]
        },
        {
          "text": "Co.",
          "box": [215, 350, 250, 370]
        }
      ],
      "linking": [],
      "id": 0
    },
    {
      "box": [123, 567, 350, 620],
      "text": "Shanghai Port",
      "label": "answer",
      "words": [
        {
          "text": "Shanghai",
          "box": [123, 570, 250, 615]
        },
        {
          "text": "Port",
          "box": [255, 567, 350, 620]
        }
      ],
      "linking": [],
      "id": 1
    }
  ]
}
```

## 🎯 训练模型

### LayoutLMv3训练（推荐）

```python
from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Processor
from datasets import load_dataset

# 加载数据集
dataset = load_dataset('json', data_files='./bol_output/funsd_format/*.json')

# 初始化模型
model = LayoutLMv3ForTokenClassification.from_pretrained(
    "microsoft/layoutlmv3-base",
    num_labels=4  # answer, header, other, question
)

# 训练模型
model.train()
```

### BERT训练

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 提取文本进行分类
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=4
)
```

### 自定义Transformer

```python
import torch
from torch import nn
from transformers import AutoModel

class BillOfLadingExtractor(nn.Module):
    def __init__(self, num_labels=4):
        super().__init__()
        self.bert = AutoModel.from_pretrained("bert-base-uncased")
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_labels)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        logits = self.classifier(outputs.last_hidden_state)
        return logits
```

## 📚 海运单关键字详解

### 核心角色类

**托运人 (Shipper)**
- 定义：货物的发送方或发货人
- 位置：通常在提单右上角
- 内容：公司名称、地址、联系方式
- 关键词：Shipper, 发货人, 托运人

**收货人 (Consignee)**
- 定义：货物的接收方
- 位置：通常在提单右上角，托运人下方
- 内容：公司名称、地址、联系方式
- 关键词：Consignee, 收货人, Consigned to

**通知方 (Notify Party)**
- 定义：到货通知的接收方
- 位置：通常在提单中部
- 内容：公司名称、地址、联系方式
- 关键词：Notify Party, 通知方

### 地理信息类

**装货港 (Port of Loading)**
- 定义：货物装载的港口
- 位置：提单中部，运输信息区域
- 内容：港口名称、城市、国家
- 关键词：Port of Loading, POL, 装货港

**卸货港 (Port of Discharge)**
- 定义：货物卸载的港口
- 位置：提单中部，运输信息区域
- 内容：港口名称、城市、国家
- 关键词：Port of Discharge, POD, 卸货港

**交货港 (Port of Delivery)**
- 定义：最终交货的港口
- 位置：提单中部，运输信息区域
- 内容：港口名称、城市、国家
- 关键词：Port of Delivery, 交货港

### 运输信息类

**船名 (Vessel)**
- 定义：承运船舶的名称
- 位置：提单中部，运输信息区域
- 内容：船舶名称
- 关键词：Vessel, Ship, 船名, 船舶

**航次 (Voyage)**
- 定义：船舶的航次号
- 位置：提单中部，船名附近
- 内容：航次编号
- 关键词：Voyage, 航次, Voyage No

**集装箱号 (Container No.)**
- 定义：集装箱的编号
- 位置：提单下部，货物信息区域
- 内容：4字母+7数字格式（如：MSKU1234567）
- 关键词：Container No., 集装箱号, Container Number

### 货物信息类

**货物描述 (Description of Goods)**
- 定义：货物的详细描述
- 位置：提单中部，货物信息区域
- 内容：商品名称、规格、材质、用途等
- 关键词：Description of Goods, 货物描述, Goods Description

**重量 (Weight)**
- 定义：货物的重量
- 位置：提单下部，货物信息区域
- 内容：数值+单位（KGS, MT, LB等）
- 关键词：Weight, 重量, Gross Weight, Net Weight

**体积 (Volume)**
- 定义：货物的体积
- 位置：提单下部，货物信息区域
- 内容：数值+CBM
- 关键词：Volume, 体积, CBM, Measurement

### 编号日期类

**提单号 (B/L No.)**
- 定义：提单的编号
- 位置：提单顶部或底部
- 内容：字母+数字组合
- 关键词：B/L No., Bill of Lading, 提单号

**运费 (Freight)**
- 定义：运输费用
- 位置：提单下部或右侧
- 内容：金额+币种
- 关键词：Freight, 运费, Freight Charges

### 关键术语英中对照表

| 英文术语 | 中文术语 | 说明 |
|----------|----------|------|
| Shipper | 托运人 | 货物发送方 |
| Consignee | 收货人 | 货物接收方 |
| Notify Party | 通知方 | 到货通知接收方 |
| Port of Loading (POL) | 装货港 | 货物装载港口 |
| Port of Discharge (POD) | 卸货港 | 货物卸载港口 |
| Bill of Lading (B/L) | 提单 | 海运提单 |
| Freight | 运费 | 运输费用 |
| CBM | 立方米 | 体积单位 |
| TEU | 标准箱 | 集装箱单位 |
| Container No. | 集装箱号 | 集装箱编号 |
| Seal No. | 封号 | 集装箱封条编号 |

## 🔄 迁移指南

### 版本差异

| 功能 | v1.0 (原始) | v2.0 (海运单专用) |
|------|-------------|-------------------|
| 应用场景 | 通用学术论文 | 海运单（B/L）文档 |
| 标签类别 | 18种通用类别 | 29种海运单专门类别 |
| 提示词 | 段落分组和分类 | 海运单字段分组和识别 |
| 输出格式 | YOLO格式 | FUNSD格式 |
| 脚本命名 | `*.py` | `*_bol.py` |

### 迁移步骤

#### 1. 备份旧版本（可选）

如果您想保留原始版本：

```bash
# 创建备份目录
mkdir -p backup_v1.0

# 复制原始脚本
cp extract_paragraph.py vlm_anno.py vlm_anno2.py vlmdata2yolo.py backup_v1.0/
```

#### 2. 配置API密钥

编辑 `config.py` 文件：

```python
DEFAULT_CONFIG = {
    "api_key": "YOUR_API_KEY",  # 必须替换为您的Gemini 2.0 Flash API密钥
    "input_folder": "./bills_of_lading",  # 海运单PDF输入目录
    "output_folder": "./bol_output",       # 输出目录
    ...
}
```

#### 3. 准备数据

将海运单PDF文件放入指定目录：

```bash
mkdir -p bills_of_lading
# 复制您的海运单PDF文件到此目录
```

#### 4. 运行新流程

**方式一：一键运行（推荐）**

```bash
python run_all_bol.py
```

**方式二：分步运行**

```bash
# 步骤1: 提取文本框
python extract_paragraph_bol.py

# 步骤2: 第一次VLM标注（文本分组）
python vlm_anno_bol.py

# 步骤3: 校正格式
python correct_format_bol.py

# 步骤4: 校正边界框
python correct_box_bol.py

# 步骤5: 第二次VLM标注（关键字分类）
python vlm_anno2_bol.py

# 步骤6: 转换标签格式
python convert_label_bol.py

# 步骤7: 生成FUNSD格式
python pdf_to_funsd.py
```

### 新增功能

#### 1. 配置文件（config.py）

- **标签类别定义**: 29种海运单专门类别
- **关键词映射**: 常用英文港口名缩写等
- **默认配置**: 可自定义批处理大小、间隔等参数

#### 2. 快速启动脚本（run_all_bol.py）

- 一键运行整个流程
- 交互式配置选项
- 自动错误处理和恢复

#### 3. 安装脚本（install_dependencies.py）

- 自动安装所需依赖
- 验证安装结果
- 提供后续步骤指导

#### 4. 配置检查脚本（check_config.py）

- 自动检查API密钥配置
- 验证依赖包安装
- 检查输入输出路径

### 输出文件变化

#### v1.0 输出

```
arxiv_output/
├── images/
├── labels/
└── ...
```

#### v2.0 输出

```
bol_output/funsd_format/
├── *.json                    # FUNSD格式标注文件
├── statistics.txt            # 类别统计报告
├── README.md                 # 使用说明
└── label_mapping.txt         # 标签映射文件
```

### 常见问题

#### Q: 如何使用原始的v1.0功能？

A: 保留原始脚本在项目中：
```bash
# 使用原始脚本
python extract_paragraph.py
python vlm_anno.py
python vlm_anno2.py
python vlmdata2yolo.py
```

#### Q: v2.0支持处理学术论文吗？

A: 不支持。v2.0专门针对海运单文档优化，提示词和标签类别都是为海运单设计的。如需处理学术论文，请使用v1.0的原始脚本。

#### Q: 可以同时使用两个版本吗？

A: 可以。v1.0和v2.0使用不同的输出目录，互不影响。但请注意API配额限制。

### 性能优化建议

1. **批处理大小**: 根据API配额调整 `batch_size` (建议3-10)
2. **等待间隔**: 调整 `interval` 避免API限制 (建议10-20秒)
3. **图像DPI**: 提高DPI可获得更精确的标注，但会增加处理时间

## 📘 FUNSD格式生成指南

### 核心原理

本指南说明如何生成与testing_data_example格式一致的FUNSD JSON数据。FUNSD是一个用于文档表单理解的标准数据集格式，特别适用于LayoutLMv3等模型训练。

采用"**OCR提供坐标 + Gemini提供标签**"的混合模式：

```
PDF → 图像转换 → OCR提取文本和坐标 → Gemini语义分类 → FUNSD格式输出
```

#### 为什么使用这种模式？

1. **OCR提供精准坐标**：使用PaddleOCR提取文本的像素级边界框
2. **Gemini提供语义标签**：利用大模型的语义理解能力识别海运单字段类型
3. **组合输出标准格式**：生成符合FUNSD规范的JSON文件

### 脚本说明

#### 1. 从图像生成FUNSD格式

**脚本**: `generate_funsd_format.py`

```bash
python generate_funsd_format.py
```

**输入**: 图像文件（jpg, png, bmp等）
**输出**: FUNSD格式JSON文件

**特点**:
- 使用PaddleOCR进行文本识别
- 自动文本分词生成words字段
- 批量处理多张图像
- 高精度文本检测

#### 2. 从PDF生成FUNSD格式

**脚本**: `pdf_to_funsd.py`

```bash
python pdf_to_funsd.py
```

**输入**: PDF文件
**输出**: FUNSD格式JSON文件

**特点**:
- 将PDF转换为图像
- 使用PaddleOCR提取文本
- 适合处理大量PDF文档
- 支持多页处理

### 标签映射

海运单字段映射到FUNSD标签：

| 海运单字段 | FUNSD标签 | 说明 |
|-----------|-----------|------|
| shipper, consignee, notify_party | answer | 核心角色信息 |
| port_of_loading, port_of_discharge 等 | answer | 地理信息 |
| vessel, voyage, container_no 等 | answer | 运输信息 |
| description_of_goods, weight 等 | answer | 货物信息 |
| bl_no, date, freight 等 | answer | 编号日期信息 |
| header | header | 文档头部 |
| footer, company_logo | other | 其他信息 |

### 处理流程详解

#### 1. PDF处理（pdf_to_funsd.py）

```python
# 1. 解析PDF
il = parse_pdf(pdf_path)

# 2. 提取文本块
text_blocks = extract_text_blocks(pdf_path)

# 3. Gemini分类
classification = classify_with_gemini(text_blocks)

# 4. 生成FUNSD格式
funsd_data = generate_funsd_format(text_blocks, classification)

# 5. 保存JSON文件
with open(output_path, 'w') as f:
    json.dump(funsd_data, f)
```

#### 2. 图像处理（generate_funsd_format.py）

```python
# 1. OCR识别
ocr_results = ocr_with_paddle(image_path)

# 2. Gemini分类
classification = classify_with_gemini(ocr_results)

# 3. 生成FUNSD格式
funsd_data = generate_funsd_format(image_path, ocr_results, classification)

# 4. 保存JSON文件
with open(output_path, 'w') as f:
    json.dump(funsd_data, f)
```

### 高级配置

#### 调整批处理大小

编辑 `config.py`：

```python
DEFAULT_CONFIG = {
    "batch_size": 5,      # 并行处理数量
    "interval": 15,       # API调用间隔（秒）
    ...
}
```

#### 自定义标签映射

编辑脚本中的 `FUNSD_LABEL_MAPPING`：

```python
FUNSD_LABEL_MAPPING = {
    0: "answer",  # shipper
    1: "answer",  # consignee
    # ... 其他映射
}
```

#### 使用PaddleOCR

```python
# 使用PaddleOCR进行文本识别
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang="ch", enable_mkldnn=True)
ocr_results = ocr.ocr(image_path, cls=True)
```

### 性能优化

#### 1. 提高OCR精度

- 使用高分辨率图像（DPI ≥ 300）
- 确保图像清晰，无模糊或倾斜
- 对于扫描文档，先进行预处理（去噪、矫正）

#### 2. 优化Gemini分类

- 调整 `batch_size` 平衡速度和API限制
- 增加 `interval` 避免频繁调用
- 提供Few-Shot示例提高准确率

#### 3. 批量处理

```python
# 并行处理多个文件
for pdf_path in pdf_files:
    process_single_pdf(pdf_path, output_dir)
```

### 故障排除

#### 问题1：OCR识别失败

**原因**: PaddleOCR未安装或图像质量差

**解决**:
```bash
pip install paddlepaddle paddleocr
```

确保图像清晰，无模糊或倾斜。

#### 问题2：Gemini分类失败

**原因**: API密钥错误或网络问题

**解决**:
1. 检查 `config.py` 中的API密钥
2. 确认网络连接正常
3. 增加 `interval` 避免API限制

#### 问题3：输出格式不匹配

**原因**: 坐标系统不一致

**解决**:
- 检查输入图像/PDF的尺寸
- 确认坐标转换正确
- 参考 `testing_data_example` 的格式

### 参考资料

- [FUNSD数据集论文](https://arxiv.org/abs/1905.13538)
- [LayoutLMv3论文](https://arxiv.org/abs/2204.08387)
- [PaddleOCR文档](https://github.com/PaddlePaddle/PaddleOCR)

### 使用建议

1. **数据质量**：确保海运单图像清晰，文字可读
2. **样本多样性**：包含不同格式、不同语言的海运单
3. **人工校验**：生成后人工检查标注质量
4. **持续改进**：根据模型效果调整标注策略

## ❓ 常见问题

### Q: 如何获取Gemini 2.0 Flash API密钥？
A: 访问 [Google AI Studio](https://aistudio.google.com/apikey)，使用Google账号登录并创建API密钥。

### Q: 批处理时出现API限制错误怎么办？
A: 减小 `config.py` 中的 `batch_size` 或增加 `interval` 值。

### Q: 如何处理多页海运单？
A: 将 `config.py` 中的 `only_first_page` 设为 `False`。

### Q: 可以处理扫描版PDF吗？
A: 可以，使用PaddleOCR可以识别扫描版PDF，但效果可能不如原生PDF。建议使用清晰度高的扫描件。

### Q: FUNSD格式的优势是什么？
A: FUNSD格式保留完整的文本内容和语义信息，适合文档理解任务，比简单的边界框标注信息更丰富。

### Q: 训练需要多少数据？
A: 建议每类至少50-100个样本，总计至少2000-3000个样本。

### Q: 如何查看生成的JSON文件？
A: 使用任何文本编辑器或JSON查看器打开，或运行：
```bash
python -m json.tool your_file.json
```

### Q: 处理速度慢怎么办？
A: 编辑 `config.py`，调整参数：
```python
"batch_size": 10,    # 增加并行数
"interval": 5,       # 减少等待时间
```

### Q: OCR识别不准确？
A:
1. 确保PDF/图像清晰
2. 安装PaddleOCR：`pip install paddlepaddle paddleocr`
3. 提高图像DPI：`"image_dpi": 600`

### Q: 分类结果不准确？
A:
1. 提供更多样化的样本
2. 调整提示词
3. 人工校验并修正

### Q: 内存不足？
A:
1. 减少 `batch_size`
2. 只处理第一页：`"only_first_page": True`
3. 关闭其他程序释放内存

## 📊 输出说明

### 文件结构

```
bol_output/funsd_format/
├── 82092117.json          # FUNSD格式的标注文件
├── 82200067_0069.json
├── statistics.txt          # 类别统计报告
└── README.md              # 使用说明
```

### 统计报告（statistics.txt）

显示每个类别的实例数量和占比，帮助了解数据集分布。

### 使用说明（README.md）

详细说明FUNSD格式的使用方法和示例代码。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📜 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

## 📧 联系方式

- 项目主页：https://github.com/yourusername/bol-keyword-dataset-creator
- 问题反馈：https://github.com/yourusername/bol-keyword-dataset-creator/issues
- 邮箱：your.email@example.com

## 🙏 致谢

感谢以下开源项目：

- [Google Gemini](https://ai.google.dev/) - 提供强大的视觉语言模型
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF处理
- [LayoutLMv3](https://github.com/microsoft/unilm) - 微软文档理解模型
- [FUNSD Dataset](https://arxiv.org/abs/1905.13538) - 文档理解基准数据集
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - 百度OCR引擎

## 📝 更新日志

### v2.2.0 (2025-01-05)
- ✅ 新增多格式文档支持 (PDF, Excel, Word)
- ✅ 新增 `document_parser.py` - 统一文档解析器
- ✅ 新增 `multi_format_to_funsd.py` - 多格式文档转FUNSD
- ✅ 更新依赖安装脚本，支持多格式文档库
- ✅ 更新配置检查脚本，显示多格式支持状态
- ✅ 新增 `test_document_parser.py` - 解析器测试脚本
- ✅ 新增 `EXAMPLE_DOCUMENTS.md` - 多格式文档示例
- ✅ 更新README.md，添加多格式文档支持说明
- ✅ 优化项目结构，支持混合文档类型处理

### v2.1.0 (2025-01-05)
- ✅ 专注FUNSD格式支持，移除YOLO相关内容
- ✅ 优化一键运行脚本，简化操作流程
- ✅ 增强FUNSD格式文档和示例
- ✅ 改进错误处理和用户提示
- ✅ 添加完整的流程说明和脚本功能详解
- ✅ 整合所有文档到README.md

### v2.0.0 (2025-01-05)
- ✅ 重构为海运单关键字识别专用工具
- ✅ 新增29种海运单字段类别
- ✅ 优化VLM提示词，提高识别准确率
- ✅ 支持YOLO和FUNSD双格式输出
- ✅ 完善文档和使用说明

### v1.0.0 (原始版本)
- 📄 通用文档处理工具

---

**⭐ 如果这个项目对您有帮助，请给它一个星标！**
