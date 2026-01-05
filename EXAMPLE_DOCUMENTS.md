# 多格式文档示例

本文档提供了多格式文档支持的示例说明。

## 支持的文档格式

### 1. PDF文档 (.pdf)

**示例海运单PDF**：
- 文件名：`bill_of_lading_sample.pdf`
- 包含内容：托运人、收货人、港口、船名等信息
- 页数：1-3页

**使用方式**：
```bash
# 将PDF文件放入输入目录
cp bill_of_lading_sample.pdf ./bills_of_lading/

# 运行处理
python multi_format_to_funsd.py
```

### 2. Excel工作簿 (.xlsx, .xls)

**示例Excel结构**：
```excel
工作表1: 海运单信息
| 字段名         | 值              |
|----------------|-----------------|
| 托运人         | ABC Company     |
| 收货人         | XYZ Trading     |
| 装货港         | Shanghai        |
| 卸货港         | Los Angeles     |
| 船名           | MV Ocean Star   |
| 提单号         | BOL20240001     |

工作表2: 货物信息
| 包装 | 货物描述         | 重量  | 体积  |
|------|------------------|-------|-------|
| 100  | Electronic Parts | 500KG | 2.5CBM|
```

**使用方式**：
```bash
# 将Excel文件放入输入目录
cp shipping_info.xlsx ./bills_of_lading/

# 运行处理（会自动处理所有工作表）
python multi_format_to_funsd.py
```

### 3. Word文档 (.docx, .doc)

**示例Word内容**：
```
海运单 (BILL OF LADING)

托运人 (Shipper):
ABC Import & Export Co., Ltd.

收货人 (Consignee):
XYZ Trading Company

装货港 (Port of Loading):
Shanghai, China

卸货港 (Port of Discharge):
Los Angeles, USA

船名 (Vessel):
MV Ocean Star

航次 (Voyage):
Voyage No. 2024-001

提单号 (B/L No.):
BOL20240001

货物描述 (Description of Goods):
Electronic Components

包装 (Package):
100 Cartons

重量 (Weight):
500 KG

体积 (Volume):
2.5 CBM
```

**使用方式**：
```bash
# 将Word文件放入输入目录
cp bill_of_lading_template.docx ./bills_of_lading/

# 运行处理
python multi_format_to_funsd.py
```

## 混合文档处理

您可以在同一个输入目录中放置多种格式的文档：

```
bills_of_lading/
├── bol_001.pdf        # PDF文档
├── bol_002.xlsx       # Excel文档
├── bol_003.docx       # Word文档
├── bol_004.doc        # Word文档（旧版）
└── bol_005.pdf        # 另一个PDF文档
```

运行 `python multi_format_to_funsd.py` 会自动：
1. 识别每个文件的格式
2. 使用对应的解析器处理
3. 统一转换为FUNSD JSON格式
4. 生成统计报告

## 输出示例

每个文档会生成对应的JSON文件：

```
bol_output/funsd_format/
├── bol_001_page_1.json      # PDF第1页
├── bol_001_page_2.json      # PDF第2页
├── bol_002_Sheet1.json      # Excel工作表1
├── bol_002_Sheet2.json      # Excel工作表2
├── bol_003_page_1.json      # Word文档
├── bol_004_page_1.json      # Word文档（.doc转换后）
├── bol_005_page_1.json      # PDF第1页
├── statistics.txt           # 统计报告
└── README.md                # 使用说明
```

## FUNSD格式示例

```json
{
  "image": "bol_001_page_1.png",
  "width": 1654,
  "height": 2339,
  "form": [
    {
      "text": "ABC Import & Export Co., Ltd.",
      "label": "shipper",
      "bbox": [100, 200, 500, 250],
      "linking": [],
      "id": 0
    },
    {
      "text": "XYZ Trading Company",
      "label": "consignee",
      "bbox": [100, 300, 500, 350],
      "linking": [],
      "id": 1
    },
    {
      "text": "Shanghai",
      "label": "port_of_loading",
      "bbox": [100, 400, 300, 450],
      "linking": [],
      "id": 2
    }
  ]
}
```

## 注意事项

1. **文档质量**：确保文档清晰，文字可读
2. **文件编码**：Excel和Word文件请使用UTF-8编码
3. **图片嵌入**：如果Word文档包含图片，会一并处理
4. **表格处理**：Excel和Word表格会自动识别为结构化文本
5. **页数限制**：建议单个文档不超过50页以确保处理效率

## 创建测试文档

您可以使用以下方式创建测试文档：

### 创建测试Excel文件
```python
import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "海运单信息"

data = [
    ["字段名", "值"],
    ["托运人", "ABC Company"],
    ["收货人", "XYZ Trading"],
    ["装货港", "Shanghai"],
    ["卸货港", "Los Angeles"],
]

for row in data:
    ws.append(row)

wb.save("test_bol.xlsx")
```

### 创建测试Word文件
```python
from docx import Document

doc = Document()
doc.add_heading('海运单', 0)

doc.add_paragraph('托运人 (Shipper):')
doc.add_paragraph('ABC Import & Export Co., Ltd.')

doc.add_paragraph('收货人 (Consignee):')
doc.add_paragraph('XYZ Trading Company')

doc.save("test_bol.docx")
```

## 故障排除

**问题1：Excel文件无法读取**
- 检查是否安装了 `openpyxl`
- 确保文件不是密码保护的
- 检查文件编码是否为UTF-8

**问题2：Word文档无法解析.doc格式**
- 需要安装 `docx2pdf`
- 或者将文件转换为.docx格式

**问题3：PDF文档转换失败**
- 检查PDF文件是否损坏
- 确保安装了 `PyMuPDF`
- 尝试使用其他PDF阅读器打开确认文件正常

**问题4：OCR识别率低**
- 确保文档分辨率足够（300 DPI）
- 检查文档是否为扫描版（可能需要预处理）
- 确认PaddleOCR模型已正确下载

## 更多信息

- 查看完整文档：README.md
- 运行测试：python test_document_parser.py
- 检查配置：python check_config.py
- 获取帮助：请提交 Issue
