import os

import pytest
from pages.sogou_home import SogouHomePage
from config import BASE_URL
import allure

from utils.request_utils import RequestUtils

# 新增导入URL工具类
from utils.url_utils import UrlUtils

import json  # 尝试allure attach json

# ========== 修改1：类级别注解（补充feature/story，title才会在报告显示） ==========
@allure.feature("搜狗首页测试模块")  # 大分类（报告里会显示）
@allure.story("首页元素完整性验证")  # 子分类
@allure.title("搜狗首页所有元素验证套件")  # 类标题（报告的“套件名称”）

class TestSogouHomepageElements:

    @pytest.fixture(autouse=True)
    def setup_homepage(self, driver):
        """每个测试前自动打开首页"""
        print("setup homepage running in fixture")
        self.driver = driver
        self.home_page = SogouHomePage(driver)
        self.home_page.open(BASE_URL)

    # 方法级标题（Allure 中作为“测试用例”标题，必加）
    @allure.title("打印所有链接供人工核对")
    def test_print_all_links_for_manual_review(self):
        """
        【专用测试】打印所有区域的链接供人工核对
        运行此测试时，请在控制台查看输出结果
        命令：pytest test_homepage_elements.py::TestSogouHomepageElements::test_print_all_links_for_manual_review -s
        """
        # 稍微等待一下，确保动态加载的底部链接也出来了
        self.driver.implicitly_wait(2)
        self.home_page.print_all_links_summary()

        # 断言：至少应该找到一些链接，否则页面可能完全加载失败
        # 这里只是一个 sanity check，主要目的是看上面的 print 输出
        assert self.home_page.is_search_box_visible(), "搜索框未加载，无法进行后续核对"

    @allure.title("验证首页核心元素存在性")
    def test_homepage_elements_presence(self):
        """验证核心元素存在性"""
        assert self.home_page.is_search_box_visible(), "搜索框未显示"
        assert self.home_page.is_search_button_visible(), "搜索按钮未显示"
        assert self.home_page.is_logo_visible(), "Logo 未显示"

    @allure.title("验证热搜提示词非空")
    def test_hot_search_placeholder(self):
        """验证热搜提示词"""
        placeholder = self.home_page.get_search_placeholder()
        assert placeholder is not None, "未获取到搜索框提示词"
        print(f"\n🔥 当前热搜提示词：{placeholder}")
        assert len(placeholder) > 0, "搜索框提示词为空"

        # ===== 新增：对比 Selenium 和 Requests 提取/验证链接的测试 =====

    @allure.title("对比 Selenium 和 Requests 提取链接结果")
    def test_compare_selenium_and_requests_links(self):
        """
        核心对比点：
        1. 对两种方法提取的链接做标准化
        2. 分析链接列表差异（Selenium vs Requests 提取的链接）
        """
        # 1. 分别获取两种方式提取的链接
        selenium_links_original = self.home_page.extract_all_links_by_selenium()  # 原有Selenium方法
        requests_links_original = self.home_page.extract_all_links_by_requests()  # 新增Requests方法

        # ========== 新增：URL标准化（核心修复步骤）==========
        selenium_links = UrlUtils.standardize_url_list(selenium_links_original)
        requests_links = UrlUtils.standardize_url_list(requests_links_original)
        # ====================================================
        # 打印基础统计
        print("\n===== 链接标准化后提取结果对比 =====")
        print(f"Selenium 标准化后提取链接数：{len(selenium_links)}")
        print(f"Requests 标准化后提取链接数：{len(requests_links)}")

        # 2. 计算链接列表的交集/差集（找差异）
        selenium_set = set(selenium_links)
        requests_set = set(requests_links)
        # 两者都有的链接（交集）
        common_links = selenium_set & requests_set
        # Selenium有、Requests没有的链接
        selenium_only_links = selenium_set - requests_set
        # Requests有、Selenium没有的链接
        requests_only_links = requests_set - selenium_set

        # 输出差异结果
        print(f"\n✅ 两者共有的链接数：{len(common_links)}")
        if common_links:
            print(f"\n ========两者共有的链接==========")
            for link in common_links:
                print(f"\n - {link}")
        if selenium_only_links:
            print(f"\n⚠️  Selenium有、Requests没有的链接：")
            for link in selenium_only_links:
                print(f"  - {link}")
        if requests_only_links:
            print(f"\n⚠️  Requests有、Selenium没有的链接：")
            for link in requests_only_links:
                print(f"  - {link}")

        # 构造一个字典结构
        result_data = {
            "common_links": list(common_links),
            "selenium_only": list(selenium_only_links),
            "requests_only": list(requests_only_links)
        }
        print(json.dumps(result_data, indent=2, ensure_ascii=False))

        allure.attach(
            body=json.dumps(result_data, indent=2, ensure_ascii=False), # 转成JSON字符串, 缩进2格，支持中文
            name="selenium和requests提取到的链接",
            attachment_type=allure.attachment_type.JSON
        )


    # 在 TestSogouHomepageElements 类中新增测试方法
    @allure.title("批量测试首页链接（通过selenium提取）有效性（requests）")
    def test_batch_check_links_extract_by_selenium_with_requests(self, request):
        """
        批量测试搜狗首页所有链接的有效性（链接提取基于selenium, 测试基于requests库）
        核心验证：链接是否可访问、状态码是否2xx、响应耗时是否合理
        """
        # 1. 提取页面所有链接
        all_links = self.home_page.extract_all_links_by_selenium()
        assert len(all_links) > 0, "未提取到任何有效链接，无法进行测试"
        print(f"\n🔍 使用selenium从页面提取到 {len(all_links)} 个唯一有效链接")

        # 2. 初始化 requests 测试工具
        request_utils = RequestUtils(timeout=8)

        # 3. 批量测试链接
        test_result = request_utils.batch_test_links(all_links)

        # 4. 断言：成功率不低于80%（可根据需求调整）
        success_rate = test_result["summary"]["success_rate"]
        assert success_rate >= 80, f"链接成功率过低：{success_rate}%（预期≥80%）"

        # 5. （可选）将失败链接写入 Allure 报告
        print(f"📝测试结果-summary: {json.dumps(test_result['summary'], indent=2, ensure_ascii=False)}")
        if test_result["summary"]["failure_count"] > 0:
            failed_links_str = "\n".join([f"{item['url']} - {item['error_msg']}" for item in test_result["summary"]["failed_links"]])
            print(f"failed links: {failed_links_str}")
            allure.attach(
                body=failed_links_str,
                name="失败链接列表",
                attachment_type=allure.attachment_type.TEXT
            )

        # 6. 【新增】将 details 写入 Allure 报告（完整原始数据）
        print(f"💯测试结果-details: {json.dumps(test_result['details'], indent=2, ensure_ascii=False)}")
        details_str = ""
        for idx, detail in enumerate(test_result["details"], 1):
            status = "成功" if detail["success"] else "失败"
            details_str += f"{idx}. URL: {detail['url']} | 状态: {status} | 状态码: {detail['status_code']} | 耗时: {detail['response_time']}ms | 错误: {detail['error_msg']}\n"

        print(f"💯测试结果-details_str: {json.dumps(details_str, indent=2, ensure_ascii=False)}")
        allure.attach(
            body=details_str,
            name="所有链接测试详情",
            attachment_type=allure.attachment_type.TEXT
        )

        print(f"\n✅ 链接测试完成，成功率：{success_rate}%")

    @allure.title("批量测试首页链接（通过REQUESTS提取）有效性（requests）")
    def test_batch_check_links_extract_by_requests_with_requests(self, request): # <--- 加上 request
        """
        批量测试搜狗首页所有链接的有效性（链接提取基于REQUESTS, 测试基于requests库）
        核心验证：链接是否可访问、状态码是否2xx、响应耗时是否合理
        """


        # 1. 从 request.config 中读取 conftest 存入的路径
        # 注意：这里变量名要和 conftest 中定义的一致 (log_path)
        # 出现request.config没有定义或者报错，通常是因为没有把request作为参数传给测试函数。
        # 在Pytest中，request是一个内置的Fixture，必须像传参数一样放在函数括号里才能使用。
        log_path = request.config.log_path
        # 如果担心未定义，可以加个容错判断
        if not log_path:
            raise ValueError("未在 conftest 中找到 log_path 配置")
        print(f"📝 本次test_batch_check_links_extract_by_requests_with_requests日志将写入: {log_path}")
        with open(log_path, "a", encoding="utf-8") as f:
            # ========== 文件头 ==========
            f.write("=" * 80 + "\n")
            f.write("test_batch_check_links_extract_by_requests_with_requests\n")
            f.write("=" * 80 + "\n\n")
            # 最后两个空行
            f.write("\n\n")

        # 1. 提取页面所有链接
        all_links = self.home_page.extract_all_links_by_requests()
        assert len(all_links) > 0, "未提取到任何有效链接，无法进行测试"
        print(f"\n🔍 使用REQUESTS从页面提取到 {len(all_links)} 个唯一有效链接")

        # 2. 初始化 requests 测试工具
        request_utils = RequestUtils(timeout=8)

        # 3. 批量测试链接
        test_result = request_utils.batch_test_links(all_links)

        # 4. 断言：成功率不低于80%（可根据需求调整）
        success_rate = test_result["summary"]["success_rate"]
        assert success_rate >= 80, f"链接成功率过低：{success_rate}%（预期≥80%）"

        # 5. （可选）将失败链接写入 Allure 报告
        print(f"📝测试结果-summary: {json.dumps(test_result['summary'], indent=2, ensure_ascii=False)}")
        if test_result["summary"]["failure_count"] > 0:
            failed_links_str = "\n".join(
                [f"{item['url']} - {item['error_msg']}" for item in test_result["summary"]["failed_links"]])
            print(f"failed links: {failed_links_str}")

        with open(log_path, "a", encoding="utf-8") as f:
            # ========== 文件头 ==========
            f.write("=" * 80 + "\n")
            f.write("测试结果-summary\n")
            f.write("=" * 80 + "\n\n")
            # ========== 主体内容 ==========
            f.write(json.dumps(test_result['summary'], indent=2, ensure_ascii=False))
            f.write("\n")  # 内容结束后换行
            # 最后两个空行
            f.write("\n\n")

        # 6. 【新增】将 details 写入 Allure 报告（完整原始数据）
        print(f"💯测试结果-details: {json.dumps(test_result['details'], indent=2, ensure_ascii=False)}")

        details_str = ""
        # details_str = details_str.encode('utf-8').decode('utf-8')  # 确保是UTF-8
        for idx, detail in enumerate(test_result["details"], 1):
            status = "成功" if detail["success"] else "失败"
            details_str += f"{idx}. URL: {detail['url']} | 状态: {status} | 状态码: {detail['status_code']} | 耗时: {detail['response_time']}ms | 错误: {detail['error_msg']}{os.linesep}"
            # 使用 os.linesep (最通用写法)
            # 这是 Python 推荐的跨平台换行写法，它会自动适应当前系统的换行符。

        print(f"💯测试结果-details_str: {details_str}")

        # 写入log文件
        with open(log_path, "a", encoding="utf-8") as f:
            # ========== 文件头 ==========
            f.write("=" * 80 + "\n")
            f.write("测试结果-details\n")
            f.write("=" * 80 + "\n\n")
            # ========== 主体内容 ==========
            f.write(details_str)
            f.write("\n")  # 内容结束后换行
            # 最后两个空行
            f.write("\n\n")

        # 3. 附加到 Allure
        allure.attach.file(
            source=log_path,
            name="所有链接测试详情",
            attachment_type=allure.attachment_type.TEXT
        )
        """
        allure.attach(
            body=details_str,
            name="所有链接测试详情",
            attachment_type=allure.attachment_type.TEXT,
            extension = "txt"
        )
        """

        print(f"\n✅ 链接测试完成，成功率：{success_rate}%")