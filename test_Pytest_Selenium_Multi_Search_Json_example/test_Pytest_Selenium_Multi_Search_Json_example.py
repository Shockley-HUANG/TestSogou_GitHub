"""
Web自动化测试 - 异常截图功能（Pytest版本）
适配Pytest框架，保留所有核心功能，遵循Pytest最佳实践
"""
import os
# import time
from time import sleep
from datetime import datetime


import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

# 导入confiy.py配置
from config import SCREENSHOT_DIR, CHROME_DRIVER_PATH, BASE_URL, TESTRESULT_DIR

import json


# ==================== Pytest Fixture（替代unittest的setUp/tearDown） ====================
@pytest.fixture(scope="function")
def driver():
    """
    Pytest夹具：提供WebDriver实例，自动完成前置/后置操作
    scope="function"：每个测试函数独立创建/销毁driver实例
    """
    # 前置操作（替代setUp）
    service = Service(CHROME_DRIVER_PATH)
    chrome_driver = webdriver.Chrome(service=service)
    chrome_driver.implicitly_wait(10)
    chrome_driver.get(BASE_URL)
    chrome_driver.maximize_window()

    # 确保截图目录存在
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)

    # 将driver实例传递给测试函数
    yield chrome_driver

    # 后置操作（替代tearDown）
    sleep(2)
    chrome_driver.quit()


# ==================== 通用工具函数（抽离公共逻辑） ====================
def get_page_info(driver):
    """获取当前页面信息（独立函数，替代类方法）"""
    try:
        info = {
            "title": driver.title,
            "url": driver.current_url,
            "window_size": driver.get_window_size(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return info
    except Exception as e:
        print(f"获取页面信息失败: {e}")
        return {"error": str(e)}


def take_screenshot_on_success(driver, test_name="success"):
    """测试成功时截图（独立函数）"""
    try:
        page_info = get_page_info(driver)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}_{test_name}.png"
        screenshot_path = os.path.join(SCREENSHOT_DIR, filename)

        driver.save_screenshot(screenshot_path)
        print(f"✓ 测试成功截图已保存: {screenshot_path}")

        # 保存页面信息文件
        info_file = screenshot_path.replace('.png', '_info.txt')
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"测试名称: {test_name}\n")
            f.write(f"截图时间: {page_info['timestamp']}\n")
            f.write(f"页面标题: {page_info.get('title', 'N/A')}\n")
            f.write(f"页面URL: {page_info.get('url', 'N/A')}\n")
            f.write(f"窗口大小: {page_info.get('window_size', 'N/A')}\n")

        return screenshot_path
    except Exception as e:
        print(f"✗ 成功截图保存失败: {e}")
        return None


def save_screenshot_on_error(driver, filename):
    """异常时截图（独立函数）"""
    try:
        page_info = get_page_info(driver)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"{timestamp}_{filename}")

        driver.save_screenshot(screenshot_path)
        print(f"✗ 异常截图已保存: {screenshot_path}")

        # 保存错误信息文件
        error_info_file = screenshot_path.replace('.png', '_error.txt')
        with open(error_info_file, 'w', encoding='utf-8') as f:
            f.write(f"异常截图: {filename}\n")
            f.write(f"截图时间: {page_info.get('timestamp', 'N/A')}\n")
            f.write(f"错误页面标题: {page_info.get('title', 'N/A')}\n")
            f.write(f"错误页面URL: {page_info.get('url', 'N/A')}\n")
            f.write(f"异常类型: 断言失败或运行时异常\n")

        return screenshot_path
    except Exception as e:
        print(f"✗ 异常截图保存失败: {e}")
        return None


# ==================== 测试用例（Pytest风格） ====================

# 假设 JSON 文件与测试文件在同一个目录下
DATA_FILE = os.path.join(os.path.dirname(__file__), "search_data.json")

# 读取 JSON 文件
def load_test_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# 获取数据并生成参数列表
test_data = load_test_data()

@pytest.mark.parametrize(
    "item",
    test_data,
    ids=[item['description'] for item in test_data]
    # 使用 description 作为报告中的显示名
)
def test_multiple_searches(driver, item):
    """
    测试多次连续搜索（参数化读取外部json文件，替代原参数直接写在代码里面）
    使用@pytest.mark.parametrize实现参数化，更符合Pytest最佳实践
    """
    """
    item 是一个字典，包含 keyword, index, description 等键
    """
    try:

        keyword = item['keyword']
        index = item['index']
        print(f"\n正在搜索: {keyword}, 索引: {index}")
        # 记录搜索前信息
        before_info = get_page_info(driver)
        print(f"\n第 {index} 次搜索 - 搜索前: {before_info['title']}")

        # 执行搜索
        query_input = driver.find_element(By.ID, "query")
        query_input.clear()
        query_input.send_keys(keyword)

        search_button = driver.find_element(By.ID, "stb")
        search_button.click()

        # 等待结果加载
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "results"))
        )

        # 记录搜索后信息
        after_info = get_page_info(driver)
        print(f"第 {index} 次搜索 - 搜索后: {after_info['title']}")

        # 断言标题包含关键词
        assert keyword in after_info["title"], \
            f"页面标题应包含搜索关键词 '{keyword}'"

        # 成功截图
        take_screenshot_on_success(driver, f"search_{keyword}_{index}")

        # 返回到首页（最后一次搜索无需返回）
        if index < 3:
            driver.back()
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "query"))
            )
    except AssertionError as e:
        print(f"✗ 断言失败: {e}")
        print(f"第 {index} 次搜索失败 (关键词: {keyword}): {e}")
        save_screenshot_on_error(driver, "assertion_failed.png")
        raise  # 重新抛出异常，让pytest标记为失败
    except Exception as e:
        print(f"✗ 测试执行过程中发生异常: {e}")
        save_screenshot_on_error(driver, "unexpected_error.png")
        raise

