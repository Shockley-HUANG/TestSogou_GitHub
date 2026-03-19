import pytest
from pages.sogou_home import SogouHomePage
from config import BASE_URL
import allure

# ========== 修改1：类级别注解（补充feature/story，title才会在报告显示） ==========
@allure.feature("搜狗首页测试模块")  # 大分类（报告里会显示）
@allure.story("首页元素完整性验证")  # 子分类
@allure.title("搜狗首页所有元素验证套件")  # 类标题（报告的“套件名称”）

class TestSogouHomepageElements:

    @pytest.fixture(autouse=True)
    def setup_homepage(self, driver):
        """每个测试前自动打开首页"""
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

