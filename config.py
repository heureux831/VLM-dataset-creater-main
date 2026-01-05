# -*- coding: utf-8 -*-
"""
海运单关键字识别 - 配置文件
Bill of Lading Keyword Recognition - Configuration
"""

# ==============================================================================
# ⚠️  首先配置您的API密钥！
# ==============================================================================
# 1. 访问 https://aistudio.google.com/apikey 获取Gemini 2.0 Flash API密钥
# 2. 将下面的 "YOUR_API_KEY" 替换为您的实际API密钥
# 3. 保存文件后即可使用
#
# 获取API密钥步骤：
#   - 使用Google账号登录 https://aistudio.google.com/apikey
#   - 点击 "Create API key"
#   - 复制生成的API密钥
#   - 替换下面的 "YOUR_API_KEY"
#
# 示例：
#   "api_key": "AIzaSyC-Your-Actual-API-Key-Here",
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
# ⚠️ 重要：请在下面配置您的API密钥
# ==============================================================================
# 找到这一行： "api_key": "YOUR_API_KEY",
# 将 "YOUR_API_KEY" 替换为您的实际API密钥
#
# 例如：
#   "api_key": "AIzaSyC-Your-Actual-API-Key-Here",
#
# 警告：如果不配置API密钥，程序将无法运行！
# ==============================================================================

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "YOUR_API_KEY",  # ⚠️  请替换为您的Gemini API密钥
    "input_folder": "./bills_of_lading",
    "output_folder": "./bol_output",
    "batch_size": 5,
    "interval": 15,
    "model_name": "gemini-2.0-flash",
    "confidence_threshold": 0.5,
    "nms_threshold": 0.4,
    "image_dpi": 300,
    "only_first_page": True
}
