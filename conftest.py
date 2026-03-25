import os
import glob
import json
import uuid

from datetime import datetime
from time import sleep

import allure
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

    # 创建一个临时的session file用于存放具体的报告子目录信息，传递给并发进程
    SESSION_FILE = os.path.join(TESTRESULT_DIR, ".current_session_path.txt") # s.path.join()只是拼接路径字符串，不创建任何文件或目录。

    # 只在 Controller (主进程) 中创建log子目录并初始化各种全局参数
    if not hasattr(config, 'workerinput'):
        # 2. 生成精确到毫秒的时间戳（保证文件名唯一）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        session_dir = os.path.join(TESTRESULT_DIR, timestamp)
        os.makedirs(session_dir) # 根据时间戳生成一个子目录

        # 3. 拼接：目录 + 文件名创建pytest的测试报告
        report_filename = f"test_report_{timestamp}.html"
        report_path = os.path.join(session_dir, report_filename)

        # 4. 配置 pytest-html 插件
        config.option.htmlpath = report_path  # 关键：把完整路径传给 pytest
        config.option.self_contained_html = True  # 独立报告，可直接打开

        # 新增：验证报告路径（执行时可在控制台看到）
        print(f"\n[Pytest配置] 测试报告将生成到：{report_path}")

        # 【关键】将session_dir路径写入文件，供 Worker 读取
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            f.write(session_dir)
        # 主进程自己也可以存一份
        config.session_dir = session_dir
    else:
        # Worker 进程：从文件中读取session_dir路径
        # 需要稍微等一下，或者加个循环确保文件已生成（通常主进程比Worker先跑，直接读即可）
        # 时序问题- Worker 启动太快，添加重试机制
        max_retries = 10
        for i in range(max_retries):
            if os.path.exists(SESSION_FILE):
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    config.session_log_dir = f.read().strip()
                break
            else:
                time.sleep(0.1)  # 等待100ms
        else:
            # 极端情况：Worker 启动太快，文件还没生成，给个默认路径兜底
            config.session_log_dir = ROOT_LOG_DIR
    # ===========【新增代码】===========



    """pytest-xdist 配置钩子用于每个worker ID单独写log"""
    if hasattr(config, 'workerinput'):
        # 多 worker 模式, 从 config 中获取当前 worker 的唯一标识 ID (例如 'gw0', 'gw1', 'gw2'...)
        worker_id = config.workerinput['workerid']
        print(f"\n🚀 Worker {worker_id} 已启动")
        # 设置 worker 级别的配置
        config.worker_stats = {'worker_id': worker_id}
        # pytest-xdist模式，为每个worker_ID生成一个 .log 文件的路径，并存入 config 对象
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        log_filename = f"test_report_pytest_xdist_{worker_id}_{timestamp}.log"
        # 将路径挂载到 config 对象上，变量名随意，比如 log_path
        config.log_path = os.path.join(config.session_log_dir, log_filename)
        # 引入log文件
        # 👇【新增】在这里写入文件头，每个 Worker 启动时只执行一次
        # 【A. 写入文件头】每个进程启动时只写这一次
        log_path = config.log_path
        if not log_path:
            raise ValueError("未在 conftest 中找到 log_path 配置")
        print(f"📝 ===================日志将写入: {log_path}=======================")
        with open(log_path, "w", encoding="utf-8") as f:  # 建议用 "w" 模式，每次运行清空旧日志；如果想追加用 "a"
            # ========== 文件头 ==========
            f.write("=" * 80 + "\n")
            f.write(f"test_{worker_id} Started.....................\n")
            f.write("=" * 80 + "\n\n")
            # 最后两个空行
            f.write("\n\n")
    else:
        # 不是Worker，可能是Controller或单进程
        # 检查是否使用了 -n 参数（并发模式）
        num_processes = getattr(config.option, 'numprocesses', 0)
        is_parallel = num_processes and num_processes > 0

        if is_parallel:
            # Controller进程（并发模式）：不需要自己的日志文件
            print(f"[Controller] 管理 {num_processes} 个Worker，不创建日志文件")
            config.log_path = None  # 或 config.log_path = ""
        else:
            # 真正的单进程模式：需要日志文件
            # 单进程模式（没有用 -n 参数）
            print("\n🚀 运行在单进程模式")
            worker_id = 'Main'
            # 单进程模式，生成一个 .log 文件的路径，并存入 config 对象
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            log_filename = f"test_report_single_process_{timestamp}.log"
            # 将路径挂载到 config 对象上，变量名随意，比如 log_path
            config.log_path = os.path.join(session_dir, log_filename)
            # 引入log文件
            # 👇【新增】在这里写入文件头，每个 Worker 启动时只执行一次
            # 【A. 写入文件头】每个进程启动时只写这一次
            log_path = config.log_path
            if not log_path:
                raise ValueError("未在 conftest 中找到 log_path 配置")
            print(f"📝 ===================日志将写入: {log_path}=======================")
            with open(log_path, "w", encoding="utf-8") as f:  # 建议用 "w" 模式，每次运行清空旧日志；如果想追加用 "a"
                # ========== 文件头 ==========
                f.write("=" * 80 + "\n")
                f.write(f"test_{worker_id} Started.....................\n")
                f.write("=" * 80 + "\n\n")
                # 最后两个空行
                f.write("\n\n")



# 清理函数（可选）：测试结束后删除那个临时通信文件
"""
def pytest_unconfigure(config):
    if not hasattr(config, 'workerinput') and os.path.exists(SESSION_FILE):
      os.remove(SESSION_FILE)
"""

# 每个测试执行前：自动写入函数名（动态获取）
# 我们可以在 conftest.py 中使用 pytest_runtest_setup 钩子。这个钩子会在每个测试函数执行前自动运行，它能获取到当前的函数名，并且不需要你在测试代码里写任何 f.write
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """
    在每个测试函数开始执行前自动触发
    :param item: 包含当前测试的所有信息（函数名、参数等）
    """
    log_path = item.config.log_path

    # 获取动态函数名称
    # item.name 包含参数，例如: test_search[test_case0]
    # item.originalname 是原始函数名，例如: test_search
    func_name = item.name

    # 【B. 写入动态内容】
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"⏳ Start Running: {func_name}\n")

# (可选) 每个测试执行后：写入结果
def pytest_runtest_makereport(item, call):
    if call.when == "call":  # 只在测试执行阶段（非setup/teardown）记录
        log_path = item.config.log_path
        outcome = call.excinfo is None  # 如果没有异常，说明通过

        status = "✅ PASSED" if outcome else "❌ FAILED"

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{status}: {item.name}\n\n")
    
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

"""
@pytest.fixture(scope="session") 尝试dependency解决并发收尾，无效，无法保证收尾测试放在最后执行
def log_dir(request):

    获取日志目录。
    由于作用域是 session，无论多少个测试/进程调用，
    都会返回同一个 pytest_configure 中设置的路径。

    # 这里直接从 config 读取我们在 pytest_configure 中保存的属性
    return request.config.session_log_dir
"""

# 真正的收尾，整个session结束后执行
def pytest_sessionfinish(session, exitstatus):
    """
    整个pytest会话结束时调用
    注意：在使用xdist时，每个Worker都会调用一次
    """
    # 只在主进程（Controller）中执行一次
    if not hasattr(session.config, 'workerinput'):
        print("\n" + "=" * 60)
        print("所有测试执行完毕，开始附加日志到Allure报告")
        print("=" * 60)

        log_dir = session.config.session_dir
        if log_dir and os.path.exists(log_dir):
            print(f"\n[收尾测试] 正在附加日志: {log_dir}")
        else:
            print(f"\n[收尾测试] 日志目录不存在: {log_dir}")
            return

        # 获取 Allure 结果目录
        # 优先从命令行参数获取，默认为 'allure-results'
        allure_results_dir = session.config.getoption('--alluredir', 'allure_result')
        if not os.path.exists(allure_results_dir):
            os.makedirs(allure_results_dir)

        # 扫描目录下所有的 .log 文件
        # sorted 用于排序，保证报告里的文件顺序一致 (例如 gw0 在前，gw1 在后)
        log_files = sorted(glob.glob(os.path.join(log_dir, "*.log")))

        if not log_files:
            print(f"\n[收尾测试] 目录 {log_dir} 下没有找到任何日志文件")
            return

        print(f"\n[收尾测试] 发现 {len(log_files)} 个日志文件，准备附加到 Allure...")

        # 准备附件数据
        # 为了美观，我们将所有日志合并到一个文本中，或者逐个添加
        # 这里演示：创建一个虚拟测试用例，包含所有日志作为附件

        # 生成一个唯一的 UUID 作为这个虚拟测试的 ID
        case_uuid = str(uuid.uuid4())
        result_file = os.path.join(allure_results_dir, f"{case_uuid}-result.json")

        # 构建测试结果 JSON 结构
        result_data = {
            "uuid": case_uuid,
            "historyId": "global-log-collector",
            "name": "00_并发测试日志汇总 (All Logs)",
            "status": "passed" if exitstatus == 0 else "failed",
            "stage": "finished",
            "start": int(datetime.now().timestamp() * 1000),
            "stop": int(datetime.now().timestamp() * 1000),
            "attachments": []
        }

        # 6. 将日志文件复制到 Allure 目录并添加附件记录
        for log_path in log_files:
            file_name = os.path.basename(log_path)

            # Allure 要求附件文件名必须是 UUID 格式（无后缀），但在 JSON 里指定后缀
            attachment_uuid = str(uuid.uuid4())
            attachment_source = os.path.join(allure_results_dir, f"{attachment_uuid}.json")
            # 此时 attachment_source 还是一个字符串，比如：
            # "/allure-results/550e8400-e29b-41d4-a716-446655440000"


            try:
                # 直到这里才创建文件（复制）
                # 复制日志文件到 "/allure-results/550e8400-e29b-41d4-a716-446655440000"
                import shutil
                shutil.copy(log_path, attachment_source)

                # 在结果中添加附件信息
                result_data["attachments"].append({
                    "name": f"日志: {file_name}",
                    "source": attachment_uuid,
                    "type": "json"
                })
            except Exception as e:
                print(f"Error copying log {log_path}: {e}")

        # 7. 写入 JSON 结果文件
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=4)

        print(f"\n[Allure 收尾] 已将并发日志汇总写入报告，共 {len(log_files)} 个文件。")

"""
        # 原方法使用allure attach，但这个时候测试进程已经跑完，收尾的时候无法执行
        # 循环附加每一个文件
        for log_file_path in log_files:
            try:
                if os.path.exists(log_file_path):
                    log_file_name = os.path.basename(log_file_path) # os.path模块中的一个函数，专门用来返回路径中的最后一部分（即基本名称）。
                    # 附加到 Allure，name 是报告里显示的标题
                    allure.attach.file(
                        source=log_file_path,
                        name=f"测试详情 - {log_file_name}",  # 例如：测试详情 - result_gw0.log
                        attachment_type=allure.attachment_type.TEXT
                    )
                    print(f"     ✓ 已附加日志文件:: {log_file_name}")
                else:
                    print(f"    ⚠ 日志文件不存在: {log_file_path}")
            except Exception as e:
                print(f"    ✗ 附加日志失败 {log_file_path}: {e}")

        print("日志附加完成！")
        print("=" * 60)
"""