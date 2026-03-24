# utils/json_utils.py
import json


def get_test_data_from_json(file_path="search_test_queries.json"):
    """
    从JSON文件读取测试数据，包含meta信息

    Args:
        file_path (str): JSON文件路径

    Returns:
        dict: 包含meta和test_cases的完整数据结构

    Raises:
        FileNotFoundError: 如果文件不存在
        ValueError: 如果JSON格式错误
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"请确保 {file_path} 文件存在于项目根目录")
    except json.JSONDecodeError:
        raise ValueError(f"{file_path} 文件格式不正确")