import pytest
from pages.sogou_home import SogouHomePage
from config import BASE_URL
import allure

from utils.request_utils import RequestUtils


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


    # 新增导入
    from utils.request_utils import RequestUtils



    # 在 TestSogouHomepageElements 类中新增测试方法
    @allure.title("批量测试首页链接有效性（requests）")
    def test_batch_check_links_with_requests(self):
        """
        批量测试搜狗首页所有链接的有效性（基于requests库）
        核心验证：链接是否可访问、状态码是否2xx、响应耗时是否合理
        """
        # 1. 提取页面所有链接
        all_links = self.home_page.extract_all_links()
        assert len(all_links) > 0, "未提取到任何有效链接，无法进行测试"
        print(f"\n🔍 从页面提取到 {len(all_links)} 个唯一有效链接")

        # 2. 初始化 requests 测试工具
        request_utils = RequestUtils(timeout=8)

        # 3. 批量测试链接
        test_result = request_utils.batch_test_links(all_links)

        # 4. 断言：成功率不低于80%（可根据需求调整）
        success_rate = test_result["summary"]["success_rate"]
        assert success_rate >= 80, f"链接成功率过低：{success_rate}%（预期≥80%）"

        # 5. （可选）将失败链接写入 Allure 报告
        print(f"测试结果-summary: {test_result['summary']}")
        if test_result["summary"]["failure_count"] > 0:
            failed_links_str = "\n".join([f"{item['url']} - {item['error_msg']}" for item in test_result["summary"]["failed_links"]])
            print(f"failed links: {failed_links_str}")
            allure.attach(
                body=failed_links_str,
                name="失败链接列表",
                attachment_type=allure.attachment_type.TEXT
            )

        # 6. 【新增】将 details 写入 Allure 报告（完整原始数据）
        print(f"测试结果—details: {test_result['details']}")
        details_str = ""
        for idx, detail in enumerate(test_result["details"], 1):
            status = "成功" if detail["success"] else "失败"
            details_str += f"{idx}. URL: {detail['url']} | 状态: {status} | 状态码: {detail['status_code']} | 耗时: {detail['response_time']}ms | 错误: {detail['error_msg']}\n"

        allure.attach(
            body=details_str,
            name="所有链接测试详情",
            attachment_type=allure.attachment_type.TEXT
        )

        print(f"\n✅ 链接测试完成，成功率：{success_rate}%")