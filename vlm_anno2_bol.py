"""
海运单关键字识别 - VLM标注脚本（第二阶段：关键字分类）
Bill of Lading Keyword Recognition - VLM Annotation Script (Phase 2: Keyword Classification)

此脚本使用Gemini 2.0 Flash API对已合并的海运单文本框进行关键字分类，
识别每个文本框对应的海运单字段类型。
"""

from google import genai
from google.genai import types
import time
import PIL.Image
import os
from tqdm import tqdm
import concurrent.futures
from config import BILL_OF_LADING_LABELS, DEFAULT_CONFIG

# 海运单关键字分类提示词
BOL_KEYWORD_CLASSIFICATION_PROMPT = """## 任务：海运单关键字分类

你是一个专业的海运单（B/L）文档分析专家。请分析海运单图像中已合并的文本框，识别每个文本框对应的海运单字段类型。

### 海运单字段类型说明：

**核心角色类：**
0. shipper (托运人): 货物发送方/发货人
1. consignee (收货人): 货物接收方
2. notify_party (通知方): 到货通知接收方

**地理信息类：**
3. port_of_loading (装货港): 货物装载港口 (POL)
4. port_of_discharge (卸货港): 货物卸载港口 (POD)
5. port_of_delivery (交货港): 交货地点/最终目的地
6. place_of_delivery (交货地点): 实际交货地点
7. place_of_receipt (收货地点): 货物接收地点

**运输信息类：**
8. vessel (船名): 承运船舶名称
9. voyage (航次): 船舶航次号
10. vessel_voyage (船名航次): 船名和航次组合
11. container_no (集装箱号): 集装箱编号
12. seal_no (封号): 集装箱封条编号

**货物信息类：**
13. description_of_goods (货物描述): 货物详细描述
14. marks_numbers (唛头和编号): 货物包装标记和编号
15. package (包装件数): 货物包装及件数
16. weight (重量): 货物重量
17. volume (体积): 货物体积/立方米

**编号日期类：**
18. bl_no (提单号): 提单编号
19. freight (运费): 运输费用
20. date (日期): 各类日期信息
21. time (时间): 时间信息

**特殊标识类：**
22. header (头部信息): 单据头部信息
23. footer (底部信息): 单据底部信息
24. company_logo (公司标志): 公司标志或图标

**费率类：**
25. rate (费率): 单位费率
26. total (总计): 总计金额或数量

**其他：**
27. other (其他信息): 其他重要信息
28. abandon (废弃内容): 需要废弃的内容

### 识别规则：

1. **关键词匹配**：
   - 寻找明显的字段标签（如："Shipper:", "Port of Loading:"）
   - 识别数值模式（如：集装箱号格式、日期格式等）
   - 注意港口缩写（如：SHA/上海, NGN/宁波等）

2. **上下文分析**：
   - 结合位置信息（通常托运人在右上，收货人在右上等）
   - 考虑字段间的逻辑关系
   - 识别表格结构中的行列关系

3. **格式识别**：
   - 提单号：通常有"B/L No.", "Bill of Lading"等前缀
   - 港口名：可能包含城市名、国家名
   - 重量：数值+单位（KGS, MT, LB等）
   - 体积：数值+CBM
   - 集装箱号：4字母+7数字（如：MSKU1234567）
   - 日期：多种格式（DD/MM/YYYY, MM/DD/YYYY等）

### 输出格式：
返回Python字典格式：{"0": 类别ID, "1": 类别ID, ...}
- 键：文本框ID（字符串格式）
- 值：对应的类别ID（整数）

### 示例：

示例1：
文本框0: "ABC Trading Co."
文本框1: "Shanghai Port"
文本框2: "MSKU1234567"
文本框3: "B/L No.: BL123456"
输出: {"0": 0, "1": 3, "2": 11, "3": 18}

示例2：
文本框0: "Shipper"
文本框1: "Description of Goods"
文本框2: "1000 KGS"
输出: {"0": 22, "1": 22, "2": 16}

请基于以上规则和说明，对提供的文本框进行准确分类。"""

GOOGLE_API_KEY = DEFAULT_CONFIG["api_key"]

def test():
    """测试函数"""
    image = PIL.Image.open('./test_bol_merged.png')

    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=DEFAULT_CONFIG["model_name"],
        contents=[image, BOL_KEYWORD_CLASSIFICATION_PROMPT],
    )

    print(response.text)

def process_single_request(client, image_path):
    """处理单个图像标注请求"""
    try:
        image = PIL.Image.open(image_path)
        response = client.models.generate_content(
            model=DEFAULT_CONFIG["model_name"],
            contents=[image, BOL_KEYWORD_CLASSIFICATION_PROMPT],
        )
        return response.text
    except Exception as e:
        print(f'处理图像 {image_path} 时出错: {str(e)}')
        return None

def main(batch_size=None, interval=None):
    """
    主函数：批量处理海运单图像的关键字分类

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
            if file.lower().endswith("_merged.png"):
                img_path = os.path.join(root, file)
                txt_path = img_path.replace(".png", "_classified.txt")
                if os.path.exists(txt_path):
                    print(f'😊{txt_path} 已分类，跳过...')
                    continue
                img_paths.append((img_path, txt_path))

    print(f"找到 {len(img_paths)} 个待分类的海运单图像")

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

    print('😊海运单关键字分类完成！')

if __name__ == '__main__':
    # 可以通过命令行参数调整批处理大小和间隔
    import sys
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else None
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else None

    main(batch_size=batch_size, interval=interval)
    # test()
