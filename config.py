# -*- coding: utf-8 -*-
"""
海运单关键字识别 - 配置文件
Bill of Lading Keyword Recognition - Configuration
"""

import os
from pathlib import Path

def load_api_key():
    """
    从环境变量或 .env 文件加载 API 密钥

    优先级：
    1. 环境变量 GEMINI_API_KEY
    2. .env 文件中的 GEMINI_API_KEY

    Returns:
        str: API 密钥，如果未找到则返回 None
    """
    # 首先尝试从环境变量获取
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        return api_key

    # 如果环境变量中没有，尝试从 .env 文件获取
    try:
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过注释和空行
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() == 'GEMINI_API_KEY':
                                return value.strip()
    except Exception as e:
        print(f"警告：读取 .env 文件时出错: {e}")

    return None

# ==============================================================================
# 🔐  安全配置 API 密钥！
# ==============================================================================
# 为了避免 API 密钥泄露，请使用以下任一方式配置：
#
# 方式1：环境变量（推荐）
#   export GEMINI_API_KEY="your-actual-api-key-here"
#   或者在 ~/.bashrc 或 ~/.zshrc 中添加：
#   export GEMINI_API_KEY="your-actual-api-key-here"
#
# 方式2：.env 文件（项目根目录）
#   创建 .env 文件，内容为：
#   GEMINI_API_KEY=your-actual-api-key-here
#   ⚠️  .env 文件已添加到 .gitignore，不会被提交到版本控制
#
# 获取 API 密钥步骤：
#   1. 访问 https://aistudio.google.com/apikey
#   2. 使用 Google 账号登录
#   3. 点击 "Create API key"
#   4. 复制生成的 API 密钥
#
# 验证配置：
#   python -c "from config import load_api_key; print('API Key loaded:', 'Yes' if load_api_key() else 'No')"
# ==============================================================================

# 标签类别定义
BILL_OF_LADING_LABELS = {
    # 核心角色类
    0: {
        "name": "shipper",
        "name_cn": "托运人",
        "name_en": "Shipper",
        "description": "货物发送方",
        "category": "role"
    },
    1: {
        "name": "consignee",
        "name_cn": "收货人",
        "name_en": "Consignee",
        "description": "货物接收方",
        "category": "role"
    },
    2: {
        "name": "notify_party",
        "name_cn": "通知方",
        "name_en": "Notify Party",
        "description": "到货通知接收方",
        "category": "role"
    },

    # 地理信息类
    3: {
        "name": "port_of_loading",
        "name_cn": "装货港",
        "name_en": "Port of Loading",
        "description": "货物装载港口",
        "category": "geography"
    },
    4: {
        "name": "port_of_discharge",
        "name_cn": "卸货港",
        "name_en": "Port of Discharge",
        "description": "货物卸载港口",
        "category": "geography"
    },
    5: {
        "name": "port_of_delivery",
        "name_cn": "交货港",
        "name_en": "Port of Delivery",
        "description": "交货地点/最终目的地",
        "category": "geography"
    },
    6: {
        "name": "place_of_delivery",
        "name_cn": "交货地点",
        "name_en": "Place of Delivery",
        "description": "实际交货地点",
        "category": "geography"
    },
    7: {
        "name": "place_of_receipt",
        "name_cn": "收货地点",
        "name_en": "Place of Receipt",
        "description": "货物接收地点",
        "category": "geography"
    },

    # 运输信息类
    8: {
        "name": "vessel",
        "name_cn": "船名",
        "name_en": "Vessel",
        "description": "承运船舶名称",
        "category": "transport"
    },
    9: {
        "name": "voyage",
        "name_cn": "航次",
        "name_en": "Voyage",
        "description": "船舶航次号",
        "category": "transport"
    },
    10: {
        "name": "vessel_voyage",
        "name_cn": "船名航次",
        "name_en": "Vessel/Voyage",
        "description": "船名和航次组合",
        "category": "transport"
    },
    11: {
        "name": "container_no",
        "name_cn": "集装箱号",
        "name_en": "Container No.",
        "description": "集装箱编号",
        "category": "transport"
    },
    12: {
        "name": "seal_no",
        "name_cn": "封号",
        "name_en": "Seal No.",
        "description": "集装箱封条编号",
        "category": "transport"
    },

    # 货物信息类
    13: {
        "name": "description_of_goods",
        "name_cn": "货物描述",
        "name_en": "Description of Goods",
        "description": "货物详细描述",
        "category": "cargo"
    },
    14: {
        "name": "marks_numbers",
        "name_cn": "唛头和编号",
        "name_en": "Marks & Numbers",
        "description": "货物包装标记和编号",
        "category": "cargo"
    },
    15: {
        "name": "package",
        "name_cn": "包装件数",
        "name_en": "Package",
        "description": "货物包装及件数",
        "category": "cargo"
    },
    16: {
        "name": "weight",
        "name_cn": "重量",
        "name_en": "Weight",
        "description": "货物重量",
        "category": "cargo"
    },
    17: {
        "name": "volume",
        "name_cn": "体积",
        "name_en": "Volume",
        "description": "货物体积/立方米",
        "category": "cargo"
    },

    # 编号日期类
    18: {
        "name": "bl_no",
        "name_cn": "提单号",
        "name_en": "B/L No.",
        "description": "提单编号",
        "category": "number"
    },
    19: {
        "name": "freight",
        "name_cn": "运费",
        "name_en": "Freight",
        "description": "运输费用",
        "category": "number"
    },
    20: {
        "name": "date",
        "name_cn": "日期",
        "name_en": "Date",
        "description": "各类日期信息",
        "category": "number"
    },
    21: {
        "name": "time",
        "name_cn": "时间",
        "name_en": "Time",
        "description": "时间信息",
        "category": "number"
    },

    # 特殊标识类
    22: {
        "name": "header",
        "name_cn": "头部信息",
        "name_en": "Header",
        "description": "单据头部信息",
        "category": "layout"
    },
    23: {
        "name": "footer",
        "name_cn": "底部信息",
        "name_en": "Footer",
        "description": "单据底部信息",
        "category": "layout"
    },
    24: {
        "name": "company_logo",
        "name_cn": "公司标志",
        "name_en": "Logo",
        "description": "公司标志或图标",
        "category": "layout"
    },

    # 费率类
    25: {
        "name": "rate",
        "name_cn": "费率",
        "name_en": "Rate",
        "description": "单位费率",
        "category": "rate"
    },
    26: {
        "name": "total",
        "name_cn": "总计",
        "name_en": "Total",
        "description": "总计金额或数量",
        "category": "rate"
    },

    # 其他
    27: {
        "name": "other",
        "name_cn": "其他信息",
        "name_en": "Other",
        "description": "其他重要信息",
        "category": "other"
    },
    28: {
        "name": "abandon",
        "name_cn": "废弃内容",
        "name_en": "Abandon",
        "description": "需要废弃的内容",
        "category": "other"
    }
}

# 按类别分组的标签
LABELS_BY_CATEGORY = {
    "role": [0, 1, 2],
    "geography": [3, 4, 5, 6, 7],
    "transport": [8, 9, 10, 11, 12],
    "cargo": [13, 14, 15, 16, 17],
    "number": [18, 19, 20, 21],
    "layout": [22, 23, 24],
    "rate": [25, 26],
    "other": [27, 28]
}

# 常用关键词映射
KEYWORD_MAPPING = {
    # 角色类关键词
    "shipper": ["shipper", "发货人", "托运人", "sender"],
    "consignee": ["consignee", "收货人", "consigned to"],
    "notify_party": ["notify party", "通知方", "notify party:"],

    # 地理类关键词
    "port_of_loading": ["port of loading", "装货港", "pol", "loading port", "port of lading"],
    "port_of_discharge": ["port of discharge", "卸货港", "pod", "discharge port", "destination port"],
    "port_of_delivery": ["port of delivery", "交货港", "place of delivery"],
    "place_of_delivery": ["place of delivery", "交货地点", "final destination"],
    "place_of_receipt": ["place of receipt", "收货地点"],

    # 运输类关键词
    "vessel": ["vessel", "ship", "船名", "船舶"],
    "voyage": ["voyage", "航次", "voyage no"],
    "container_no": ["container no", "集装箱号", "container number", "ctnr no"],
    "seal_no": ["seal no", "封号", "seal number"],

    # 货物类关键词
    "description_of_goods": ["description of goods", "货物描述", "goods description", "commodity"],
    "marks_numbers": ["marks & numbers", "唛头", "marks and nos"],
    "package": ["package", "包装", "packages", "ctns"],
    "weight": ["weight", "重量", "gross weight", "net weight"],
    "volume": ["volume", "体积", "cbm", "measurement"],

    # 编号日期类关键词
    "bl_no": ["b/l no", "提单号", "bill of lading no", "b/l number"],
    "freight": ["freight", "运费", "freight charges"],
    "date": ["date", "日期", "shipped on", "issued on"],
}

# 常用英文港口名缩写
PORT_ABBREVIATIONS = {
    "SHA": "上海/Shanghai",
    "NGN": "宁波/Ningbo",
    "SZX": "深圳/Shenzhen",
    "HKG": "香港/Hong Kong",
    "Yantian": "盐田/Yantian",
    "Chiwan": "赤湾/Chiwan",
    "Shekou": "蛇口/Shekou",
    "Qingdao": "青岛/Qingdao",
    "Tianjin": "天津/Tianjin",
    "Dalian": "大连/Dalian",
    "Xiamen": "厦门/Xiamen",
    "Fuzhou": "福州/Fuzhou",
    "Nansha": "南沙/Nansha",
    "Huangpu": "黄埔/Huangpu",
    "Lagos": "拉各斯/Lagos",
    "Dubai": "迪拜/Dubai",
    "Rotterdam": "鹿特丹/Rotterdam",
    "Hamburg": "汉堡/Hamburg",
    "Antwerp": "安特卫普/Antwerp",
    "Singapore": "新加坡/Singapore",
    "Jebel Ali": "杰贝阿里/Jebel Ali",
    "Port Klang": "巴生港/Port Klang",
    "Laem Chabang": "林查班/Laem Chabang",
    "Ho Chi Minh": "胡志明市/Ho Chi Minh",
    "Bangkok": "曼谷/Bangkok",
    "Manila": "马尼拉/Manila",
    "Jakarta": "雅加达/Jakarta",
    "Surabaya": "泗水/Surabaya",
    "Long Beach": "长滩/Long Beach",
    "Los Angeles": "洛杉矶/Los Angeles",
    "New York": "纽约/New York",
    "Savannah": "萨凡纳/Savannah",
    "Norfolk": "诺福克/Norfolk",
    "Charleston": "查尔斯顿/Charleston",
    "Miami": "迈阿密/Miami",
    "Oakland": "奥克兰/Oakland",
    "Seattle": "西雅图/Seattle",
    "Vancouver": "温哥华/Vancouver",
    "Toronto": "多伦多/Toronto",
    "Montreal": "蒙特利尔/Montreal"
}

# ==============================================================================
# ⚙️  默认配置
# ==============================================================================
# API 密钥现在通过 load_api_key() 函数自动加载
# 如果未配置 API 密钥，程序将在启动时提示错误

# 默认配置
DEFAULT_CONFIG = {
    "api_key": load_api_key(),  # 🔐 自动从环境变量或 .env 文件加载
    "input_folder": "./bills_of_lading",
    "output_folder": "./bol_output",
    "batch_size": 5,
    "interval": 15,
    "model_name": "gemini-1.5-flash",
    "confidence_threshold": 0.5,
    "nms_threshold": 0.4,
    "image_dpi": 300,
    "only_first_page": True
}
