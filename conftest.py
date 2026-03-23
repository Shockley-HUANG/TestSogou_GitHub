import os
from datetime import datetime
from time import sleep
import pytest

# 导入config.py配置
from config import TESTRESULT_DIR, CHROME_DRIVER_PATH, SCREENSHOT_DIR, BASE_URL

# 把function fixture放到conftest，变成全局配置
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# 如果需要使用 webdriver-manager 自动管理驱动，请取消下面这行的注释并安装库: pip install webdriver-manager
# from webdriver_manager.chrome import ChromeDriverManager

def pytest_configure(config):
    """Pytest钩子：配置测试环境，生成带精确时间戳的HTML报告"""
    # 强制打印（优先级最高）
    import sys
    print("\n===== pytest_configure 开始执行 =====", file=sys.stderr)

    # 1. 创建报告目录（不存在就自动创建）
    if not os.path.exists(TESTRESULT_DIR):
        os.makedirs(TESTRESULT_DIR)

    # 2. 生成精确到毫秒的时间戳（保证文件名唯一）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    # 3. 拼接：目录 + 文件名
    report_filename = f"test_report_{timestamp}.html"
    report_path = os.path.join(TESTRESULT_DIR, report_filename)

    # 4. 配置 pytest-html 插件
    config.option.htmlpath = report_path  # 关键：把完整路径传给 pytest
    config.option.self_contained_html = True  # 独立报告，可直接打开

    # 新增：验证报告路径（执行时可在控制台看到）
    print(f"\n[Pytest配置] 测试报告将生成到：{report_path}")
    
    # ===========【新增代码】===========
    # 既然这里已经生成了唯一的时间戳和目录，
    # 我们顺势生成一个 .log 文件的路径，并存入 config 对象
    log_filename = f"test_report_{timestamp}.log"
    # 将路径挂载到 config 对象上，变量名随意，比如 log_path
    config.log_path = os.path.join(TESTRESULT_DIR, log_filename)
    
# ==================== Pytest Fixture（session，全部夹具） ====================
@pytest.fixture(scope="session", autouse=True)
def test_summary():
    """测试会话级夹具：输出测试汇总信息"""
    print("\n=== test_summary 已触发（会话开始）===")  # 新增：验证触发
    yield  # 所有测试执行完成后执行以下逻辑
    print("\n" + "=" * 50)
    print("测试执行完成")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 统计截图数量
    """
    原来的代码，没有考虑文件名排序
    if os.path.exists(SCREENSHOT_DIR):
        screenshot_files = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.png')]
        print(f"生成的截图数量: {len(screenshot_files)}")
        if screenshot_files:
            print("最近5个截图文件:")
            for file in screenshot_files[-5:]:
                print(f"  - {file}")
                
    """
    if os.path.exists(SCREENSHOT_DIR):
        # 1. 获取所有截图文件的完整路径
        screenshot_files = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith('.png')]
        
        # 2. 筛选出文件（排除子目录），并获取它们的完整路径和修改时间
        file_paths = [os.path.join(SCREENSHOT_DIR, f) for f in screenshot_files]
        # 过滤掉可能存在的目录，只保留文件
        file_paths = [f for f in file_paths if os.path.isfile(f)]
        
        # 3. 按照文件的修改时间（mtime）降序排序（最新的在前）
        # key=os.path.getmtime 表示按修改时间排序
        # reverse=True 表示从新到旧
        sorted_files = sorted(file_paths, key=os.path.getmtime, reverse=True)
        
        # 4. 取最新的5个（或者少于5个）
        latest_files = sorted_files[:5]
        
        print(f"生成的截图数量: {len(sorted_files)}")
        if latest_files:
            print("最近5个截图文件 (按时间倒序):")
            for file_path in latest_files:
                # 从完整路径中提取文件名显示
                filename = os.path.basename(file_path)
                # （可选）获取文件的具体修改时间，格式化显示
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"  - [{mtime.strftime('%H:%M:%S')}] {filename}")    

    # ====================== 【新增：打印测试报告信息】 ======================
    if os.path.exists(TESTRESULT_DIR):
        report_files = [f for f in os.listdir(TESTRESULT_DIR) if f.endswith('.html')]
        print(f"\n生成的测试报告数量: {len(report_files)}")

        if report_files:
            # 取最新生成的报告
            latest_report = sorted(report_files)[-1]
            print("最新测试报告:")
            print(f"  - 目录: {TESTRESULT_DIR}")
            print(f"  - 文件名: {latest_report}")
            print(f"  - 完整路径: {os.path.join(TESTRESULT_DIR, latest_report)}")

    print("=" * 50)


@pytest.fixture(scope="function")
def driver():
    """
    Pytest夹具：提供WebDriver实例，自动完成前置/后置操作
    scope="function"：每个测试函数独立创建/销毁driver实例
    """
    # --- 前置操作 (Setup) ---

    # 1. 配置 Chrome 选项 (可选，建议加上以防弹窗干扰)
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    # options.add_argument("--headless") # 如果需要无头模式，取消注释

    # 2. 初始化 Driver (使用本地路径)
    # 确保 CHROME_DRIVER_PATH 指向正确的 exe 文件
    service = Service(CHROME_DRIVER_PATH)
    chrome_driver = webdriver.Chrome(service=service, options=options)

    # 3. 基础设置
    chrome_driver.implicitly_wait(10)  # 隐式等待 10 秒
    chrome_driver.get(BASE_URL)  # 打开首页
    chrome_driver.maximize_window()  # 最大化窗口

    # 4. 确保截图目录存在
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)

    print(f"✅ 浏览器已启动: {BASE_URL}")

    # --- 传递实例给测试函数 ---
    yield chrome_driver

    # --- 后置操作 (Teardown) ---
    print("\n🧹 测试结束，正在关闭浏览器...")
    sleep(2)  # 稍微延迟一下，方便观察最后状态或截图
    chrome_driver.quit()
    print("✅ 浏览器已关闭")