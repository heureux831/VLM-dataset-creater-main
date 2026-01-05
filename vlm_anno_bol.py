"""
海运单关键字识别 - VLM标注脚本（第一阶段：文本分组）
Bill of Lading Keyword Recognition - VLM Annotation Script (Phase 1: Text Grouping)

此脚本使用Gemini 2.0 Flash API对海运单中的文本框进行语义分组，
将属于同一海运单字段的文本框合并为一个逻辑单元。
"""

from google import genai
from google.genai import types
import time
import PIL.Image
import os
from tqdm import tqdm
import concurrent.futures
from config import DEFAULT_CONFIG

# 海运单关键字识别提示词
BOL_TEXT_GROUPING_PROMPT = """## 任务：海运单文本框语义分组

你是一个专业的海运单（B/L）文档分析专家。请分析海运单图片中的文本框坐标和文本内容，将属于同一海运单字段的文本框进行语义分组。

### 分析步骤：

1. **理解海运单结构**：
   海运单是国际贸易中的核心单据，包含托运人、收货人、船名航次、港口、货物信息等关键字段。

2. **语义分组原则**：
   - 同一字段的文本应合并（如："Shanghai" + "China" → 上海港信息）
   - 考虑逻辑连贯性（如：公司名称、地址信息应合并）
   - 识别表格中的关联字段（如：包装件数和重量通常在同一行）
   - 数字和单位应合并（如："1000" + "KGS" → 重量信息）

3. **特殊处理规则**：
   - **托运人/收货人**：公司名、地址、联系方式应合并
   - **港口信息**：港口名、城市名、国家应合并
   - **货物描述**：商品名称、规格、材质应合并
   - **重量/体积**：数值和单位应合并
   - **日期时间**：日期和具体时间应合并
   - **编号信息**：前缀和编号应合并
   - **表格数据**：同一行的相关字段应合并

4. **不应合并的情况**：
   - 完全独立的字段（如：托运人和收货人）
   - 标题和正文（如："Shipper"标签和实际公司名）
   - 页眉页脚与正文内容
   - 表格中的不同行数据

### 输出格式：
返回Python列表格式：[[0, 1], [2, 3, 4], [5], ...]
- 每个子列表包含需要合并的文本框ID
- 每个ID只出现一次
- 不合并的文本框单独成组

### 示例：

示例1：托运人信息
文本框0: "ABC Trading Co."
文本框1: "123 Main Street"
文本框2: "New York, NY 10001"
文本框3: "USA"
输出: [[0, 1, 2, 3]] (合并为完整的托运人信息)

示例2：港口信息
文本框0: "Port of Loading:"
文本框1: "Shanghai"
文本框2: "China"
文本框3: "Port of Discharge:"
文本框4: "Los Angeles"
输出: [[0, 1, 2], [3, 4]] (分别合并装载港和卸货港信息)

示例3：混合信息
文本框0: "Shipper"
文本框1: "ABC Corp"
文本框2: "123 Test St"
文本框3: "Consignee"
文本框4: "XYZ Ltd"
输出: [[0], [1, 2], [3], [4]] (标签和实际内容分离，独立字段分离)

请基于以上规则，对提供的文本框进行语义分组。"""

GOOGLE_API_KEY = DEFAULT_CONFIG["api_key"]

def test():
    """测试函数"""
    image = PIL.Image.open('./test_bol.png')

    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=DEFAULT_CONFIG["model_name"],
        contents=[image, BOL_TEXT_GROUPING_PROMPT],
    )

    print(response.text)

def process_single_request(client, image_path):
    """处理单个图像标注请求"""
    try:
        image = PIL.Image.open(image_path)
        response = client.models.generate_content(
            model=DEFAULT_CONFIG["model_name"],
            contents=[image, BOL_TEXT_GROUPING_PROMPT],
        )
        return response.text
    except Exception as e:
        print(f'处理图像 {image_path} 时出错: {str(e)}')
        return None

def main(batch_size=None, interval=None):
    """
    主函数：批量处理海运单图像的文本分组

    Args:
        batch_size: 并行处理的图像数量，默认从配置文件读取
        interval: 批次间等待时间（秒），默认从配置文件读取
    """
    # 使用配置或默认值
    batch_size = batch_size or DEFAULT_CONFIG["batch_size"]
    interval = interval or DEFAULT_CONFIG["interval"]

    folder_path = DEFAULT_CONFIG["input_folder"]

    # 创建多个client实例
    clients = [genai.Client(api_key=GOOGLE_API_KEY) for _ in range(batch_size)]

    # 收集所有需要处理的图像路径
    img_paths = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith("_annotated.png"):
                img_path = os.path.join(root, file)
                txt_path = img_path.replace(".png", ".txt")
                if os.path.exists(txt_path):
                    with open(txt_path, 'r') as f:
                        lines = f.readlines()
                        if len(lines) == 1:
                            print(f'😊{txt_path} 已标注，跳过...')
                            continue
                img_paths.append((img_path, txt_path))

    print(f"找到 {len(img_paths)} 个待处理的海运单图像")

    # 使用线程池并行处理请求
    with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
        # 按批次处理请求
        for i in range(0, len(img_paths), batch_size):
            batch_futures = []
            print(f'处理批次 {i//batch_size + 1}/{(len(img_paths) + batch_size - 1)//batch_size}')

            # 提交这一批的请求
            for j in range(batch_size):
                if i + j >= len(img_paths):
                    break
                img_path, txt_path = img_paths[i+j]
                future = executor.submit(process_single_request, clients[j], img_path)
                batch_futures.append((future, txt_path))

            # 等待这一批完成并保存结果
            for j, (future, txt_path) in enumerate(batch_futures):
                try:
                    result = future.result()
                    if result:
                        with open(txt_path, 'w') as f:
                            f.write(result)
                        print(f'已保存: {txt_path}')
                except Exception as e:
                    print(f'处理 {txt_path} 时出错: {str(e)}')

            # 在处理下一批之前等待
            if i + batch_size < len(img_paths):
                print(f"等待{interval}秒后处理下一批...")
                time.sleep(interval)

    print('😊海运单文本分组标注完成！')

if __name__ == '__main__':
    # 可以通过命令行参数调整批处理大小和间隔
    import sys
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else None
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else None

    main(batch_size=batch_size, interval=interval)
    # test()
