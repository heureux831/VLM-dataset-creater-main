# -*- coding: utf-8 -*-
"""
VLM 数据集创建工具 - 配置文件
VLM Dataset Creator - Configuration
"""

import os
from pathlib import Path

# ==============================================================================
# 环境变量加载
# ==============================================================================

def _load_env_value(key_name):
    """从环境变量或 .env 文件加载配置值"""
    value = os.getenv(key_name)
    if value:
        return value

    try:
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, val = line.split('=', 1)
                        if key.strip() == key_name:
                            val = val.strip()
                            if (val.startswith('"') and val.endswith('"')) or \
                               (val.startswith("'") and val.endswith("'")):
                                val = val[1:-1]
                            return val
    except Exception as e:
        print(f"警告：读取 .env 文件时出错: {e}")
    return None


# ==============================================================================
# API 配置
# ==============================================================================

def load_api_key():
    """加载 API 密钥 (OPENAI_API_KEY)"""
    return _load_env_value('OPENAI_API_KEY')


def load_base_url():
    """加载 API Base URL (OPENAI_BASE_URL)"""
    base_url = _load_env_value('OPENAI_BASE_URL')
    return base_url if base_url else "https://api.openai.com/v1"


def load_model_name():
    """加载模型名称 (MODEL_NAME)"""
    model_name = _load_env_value('MODEL_NAME')
    return model_name if model_name else "gpt-4o"


# ==============================================================================
# 项目路径配置
# ==============================================================================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 输入输出目录配置
PATHS = {
    # 原始文档目录
    "input_documents": PROJECT_ROOT / "data" / "01_raw_documents",

    # 流水线中间结果目录
    "step1_images": PROJECT_ROOT / "data" / "02_images",           # 文档转换后的图片
    "step2_ocr": PROJECT_ROOT / "data" / "03_ocr_results",         # OCR结果
    "step3_grouping": PROJECT_ROOT / "data" / "04_vlm_grouping",   # VLM第一阶段-分组结果
    "step4_classification": PROJECT_ROOT / "data" / "05_vlm_classification",  # VLM第二阶段-分类结果
    "step5_funsd": PROJECT_ROOT / "data" / "06_funsd_output",      # 最终FUNSD格式

    # 可视化目录
    "visualizations": PROJECT_ROOT / "data" / "visualizations",    # 可视化结果

    # 临时文件目录
    "temp": PROJECT_ROOT / "temp",
}


# ==============================================================================
# 默认配置
# ==============================================================================

DEFAULT_CONFIG = {
    # API 配置
    "api_key": load_api_key(),
    "base_url": load_base_url(),
    "model_name": load_model_name(),

    # 批处理配置
    "batch_size": 5,
    "interval": 15,  # 批次间隔（秒）

    # 图像处理配置
    "image_dpi": 300,
    "only_first_page": True,

    # OCR配置
    "ocr_lang": "ch",  # PaddleOCR语言: ch, en, japan, korean等

    # 置信度配置
    "confidence_threshold": 0.5,
}


# ==============================================================================
# 海运单标签定义
# ==============================================================================

BILL_OF_LADING_LABELS = {
    # 核心角色类
    0: {"name": "shipper", "name_cn": "托运人", "category": "role"},
    1: {"name": "consignee", "name_cn": "收货人", "category": "role"},
    2: {"name": "notify_party", "name_cn": "通知方", "category": "role"},

    # 地理信息类
    3: {"name": "port_of_loading", "name_cn": "装货港", "category": "geography"},
    4: {"name": "port_of_discharge", "name_cn": "卸货港", "category": "geography"},
    5: {"name": "port_of_delivery", "name_cn": "交货港", "category": "geography"},
    6: {"name": "place_of_delivery", "name_cn": "交货地点", "category": "geography"},
    7: {"name": "place_of_receipt", "name_cn": "收货地点", "category": "geography"},

    # 运输信息类
    8: {"name": "vessel", "name_cn": "船名", "category": "transport"},
    9: {"name": "voyage", "name_cn": "航次", "category": "transport"},
    10: {"name": "vessel_voyage", "name_cn": "船名航次", "category": "transport"},
    11: {"name": "container_no", "name_cn": "集装箱号", "category": "transport"},
    12: {"name": "seal_no", "name_cn": "封号", "category": "transport"},

    # 货物信息类
    13: {"name": "description_of_goods", "name_cn": "货物描述", "category": "cargo"},
    14: {"name": "marks_numbers", "name_cn": "唛头和编号", "category": "cargo"},
    15: {"name": "package", "name_cn": "包装件数", "category": "cargo"},
    16: {"name": "weight", "name_cn": "重量", "category": "cargo"},
    17: {"name": "volume", "name_cn": "体积", "category": "cargo"},

    # 编号日期类
    18: {"name": "bl_no", "name_cn": "提单号", "category": "number"},
    19: {"name": "freight", "name_cn": "运费", "category": "number"},
    20: {"name": "date", "name_cn": "日期", "category": "number"},
    21: {"name": "time", "name_cn": "时间", "category": "number"},

    # 特殊标识类
    22: {"name": "header", "name_cn": "头部信息", "category": "layout"},
    23: {"name": "footer", "name_cn": "底部信息", "category": "layout"},
    24: {"name": "company_logo", "name_cn": "公司标志", "category": "layout"},

    # 费率类
    25: {"name": "rate", "name_cn": "费率", "category": "rate"},
    26: {"name": "total", "name_cn": "总计", "category": "rate"},

    # 其他
    27: {"name": "other", "name_cn": "其他信息", "category": "other"},
    28: {"name": "abandon", "name_cn": "废弃内容", "category": "other"},
}

# 标签ID到名称的快速映射
LABEL_ID_TO_NAME = {k: v["name"] for k, v in BILL_OF_LADING_LABELS.items()}
LABEL_NAME_TO_ID = {v["name"]: k for k, v in BILL_OF_LADING_LABELS.items()}


# ==============================================================================
# 工具函数
# ==============================================================================

def ensure_directories():
    """确保所有必要的目录存在"""
    for path in PATHS.values():
        path.mkdir(parents=True, exist_ok=True)


def get_path(name: str) -> Path:
    """获取指定名称的路径"""
    return PATHS.get(name, PROJECT_ROOT / name)


# ==============================================================================
# 配置验证说明
# ==============================================================================
#
# 在 .env 文件中配置:
#   OPENAI_API_KEY=your-api-key
#   OPENAI_BASE_URL=https://your-api-base-url/v1  (可选)
#   MODEL_NAME=gpt-4o  (可选)
#
# 验证配置:
#   python -c "from config import DEFAULT_CONFIG; print(DEFAULT_CONFIG)"
#
