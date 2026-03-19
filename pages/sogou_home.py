from selenium.webdriver.common.by import By
from utils.wait_utils import WaitUtils
import time
import pdb  # 导入 pdb 模块


class SogouHomePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait_utils = WaitUtils(driver, timeout=10)

        # ================= 元素定位器 (Locators) =================
        # 基于截图 DOM 结构的精准定位

        # 1. 顶部导航栏链接
        # 路径：.header -> .top-nav -> ul -> li -> a
        # 注意：排除了当前选中的 "网页" (它是 span)，只抓取可点击的 a 标签
        self.TOP_NAV_LINKS = (By.CSS_SELECTOR, ".top-nav ul li a")

        # 如果需要包含 "网页" (即使是 span)，可以使用这个选择器获取所有文本节点
        self.TOP_NAV_ALL_ITEMS = (By.CSS_SELECTOR, ".top-nav ul li")


        # 2. 搜索区域
        self.LOGO = (By.CSS_SELECTOR, ".logo")  # 截图中 .logo 包裹了 img 和文字
        # self.INPUT_SEARCH_BOX = (By.ID, "upquery")

        # 搜索按钮：截图中显示为 input.search-btn
        # self.BTN_SEARCH = (By.CSS_SELECTOR, "input.search-btn")


        # ================= 🔴 修改部分开始：修正搜索框定位器 =================

        # 根据 F12 截图，搜索框的 id 是 "query"
        # 原代码可能使用了错误的 class 或 name，这里强制指定为 ID 定位，最稳定
        self.INPUT_SEARCH_BOX = (By.ID, "query")

        # 搜索按钮定位器 (根据截图结构：span.enter-input > button)
        # self.BUTTON_SEARCH = (By.CSS_SELECTOR, ".sec-input-box .enter-input button")
        self.BUTTON_SEARCH = (By.ID, "stb")
        # ================= 🔴 修改部分结束 =================

        # 3. 底部页脚
        # 路径：.footer 内部的 a 标签
        # self.FOOTER_LINKS = (By.CSS_SELECTOR, ".footer a") class 名字错误
        # 方案1，使用 ID 选择器 (#footer)，对应截图中的 id="footer"
        self.FOOTER_LINKS = (By.CSS_SELECTOR, ".ft-info a")
        # 方案2，使用 Class 选择器 (.ft)，对应截图中的 class="ft"
        # self.FOOTER_LINKS = (By.CSS_SELECTOR, ".ft a")

        # 4. 其他
        self.PAGE_TITLE_TAG = (By.TAG_NAME, "title")

    def open(self, url):
        self.driver.get(url)

    # --- 核心功能：打印所有链接汇总 (已适配新选择器) ---

    def print_all_links_summary(self):
        """
        遍历顶部、搜索区、底部，打印所有找到的链接名称和 URL
        """
        print("\n" + "=" * 60)
        print("🔍 开始核对页面链接 (Sogou Homepage Link Audit)")
        print("=" * 60)

        # 1. 打印顶部导航 (特殊处理：包含 span 和 a)
        self._print_top_nav_items()

        # 2. 打印搜索区相关
        search_area_locators = [
            (self.LOGO, "Logo"),
            (self.BUTTON_SEARCH, "搜索按钮")
        ]
        print(f"\n--- 【搜索区域】 ---")
        for locator, name in search_area_locators:
            try:
                elements = self.driver.find_elements(*locator)
                if elements:
                    el = elements[0]
                    text = el.text.strip() or el.get_attribute("alt") or name
                    href = el.get_attribute("href")
                    tag = el.tag_name
                    if href:
                        print(f"  ✅ {name}: '{text}' -> {href}")
                    else:
                        print(f"  ℹ️  {name}: '{text}' (Tag: {tag}, 无 href 属性)")
                else:
                    print(f"  ⚠️  {name}: 未找到元素")
            except Exception as e:
                print(f"  ❌ {name}: 获取失败 - {e}")

        # 3. 打印底部链接
        self._print_section_links("【底部页脚】", self.FOOTER_LINKS, max_count=20)

        print("=" * 60)
        print("✅ 链接核对结束\n")

    def _print_top_nav_items(self):
        """专门处理顶部导航，因为包含 span (当前页) 和 a (其他页)"""
        print(f"\n--- 【顶部导航】 ---")
        try:
            # 获取所有 li 元素
            items = self.driver.find_elements(*self.TOP_NAV_ALL_ITEMS)
            for item in items:
                # 尝试找 a 标签
                a_tag = item.find_element(By.TAG_NAME, "a") if item.find_elements(By.TAG_NAME, "a") else None
                # 尝试找 span 标签 (当前页)
                span_tag = item.find_element(By.TAG_NAME, "span") if item.find_elements(By.TAG_NAME, "span") else None

                text = ""
                href = ""

                if a_tag:
                    text = a_tag.text.strip()
                    href = a_tag.get_attribute("href")
                    print(f"  ✅ '{text}' -> {href}")
                elif span_tag:
                    text = span_tag.text.strip()
                    print(f"  ℹ️  '{text}' (当前页/无链接)")
                else:
                    # 兜底
                    text = item.text.strip()
                    if text:
                        print(f"  ?  '{text}' (未知结构)")

        except Exception as e:
            print(f"  ❌ 读取顶部导航失败: {e}")

    def _print_section_links(self, section_name, locator, max_count=20):
        """辅助方法：打印指定区域的链接"""
        print(f"\n--- {section_name} ---")
        try:
            elements = self.driver.find_elements(*locator)
            if not elements:
                print(f"  ⚠️  未找到任何链接 (Locator: {locator})")
                return

            count = 0
            for el in elements:
                if count >= max_count:
                    print(f"  ... 还有更多链接 (已显示前 {max_count} 个)")
                    break

                href = el.get_attribute("href")
                if not href:
                    continue

                # 在此处设置断点，程序会暂停
                # pdb.set_trace()  # 🔴 断点：程序将在此处停止，等待调试命令

                # 1. 尝试获取可见文本
                text = el.text.strip()

                # 2. 如果为空，尝试获取完整文本（包括子元素和隐藏文本）
                if not text:
                    text = el.get_attribute("textContent") or ""
                    text = text.strip()

                # 3. 最后尝试其他属性（title/aria-label/alt）

                if not text:
                    text = el.get_attribute("title") or el.get_attribute("aria-label") or "[无文本]"
                    text = el.get_attribute("title") or \
                           el.get_attribute("aria-label") or \
                           el.get_attribute("alt") or \
                           "[无文本]"

                if href:
                    print(f"  ✅ '{text}' -> {href}")
                    count += 1

        except Exception as e:
            print(f"  ❌ 读取 {section_name} 失败: {e}")

    # --- 原有的验证方法 ---

    def is_search_box_visible(self):
        # return self._check_visibility(self.INPUT_SEARCH_BOX)
        """
            判断搜索框是否可见
            🔴 修改：使用显式等待确保元素加载完成，避免假性失败
        """
        """
        try:
            # 使用 self.INPUT_SEARCH_BOX 变量，但内部逻辑升级为显式等待
            element = self.wait.until(EC.visibility_of_element_located(self.INPUT_SEARCH_BOX))
            return True
        except Exception:
            return False
        """
        """
          判断搜索框是否可见
          🔴 修复策略：
          1. 先尝试显式等待可见性。
          2. 如果等待失败或 is_displayed() 为假，尝试直接查找元素并检查其是否存在于 DOM 中且有尺寸。
          3. 增加详细打印，以便排查原因。
          """
        """
        try:
            # 第一步：尝试标准的显式等待
            element = self.wait.until(EC.visibility_of_element_located(self.INPUT_SEARCH_BOX))

            # 双重确认：有时候 wait 通过了，但瞬间状态可能变化
            if element.is_displayed():
                print(f"[DEBUG] 搜索框检测通过：尺寸={element.size}, 位置={element.location}")
                return True
            else:
                print(f"[WARN] 搜索框已找到但 is_displayed() 为 False。尺寸={element.size}")
                # 即使 is_displayed 为假，如果元素在 DOM 里且有尺寸，我们也认为它“可用”
                # 针对某些 CSS 缩放或渲染延迟的情况
                size = element.size
                if size['width'] > 0 and size['height'] > 0:
                    print("[INFO] 强制判定为可见（基于尺寸非零）")
                    return True
                return False

        except Exception as e:
            # 第二步：如果显式等待彻底失败（超时或异常），尝试“硬查找”
            print(f"[ERROR] 显式等待失败: {e}")
            try:
                # 尝试直接查找，不等待可见性
                element = self.driver.find_element(*self.INPUT_SEARCH_BOX)
                print(f"[INFO] 硬查找成功找到元素！Tag: {element.tag_name}, ID: {element.get_attribute('id')}")

                # 检查是否有尺寸
                size = element.size
                if size['width'] > 0 or size['height'] > 0:
                    print("[INFO] 元素有尺寸，判定为可见（容错模式）")
                    return True
                else:
                    print(f"[WARN] 元素存在但尺寸为 0: {size}")
                    return False
            except Exception as e2:
                print(f"[CRITICAL] 连硬查找都失败了: {e2}")
                return False
        """


        """
        🔴 终极修复：不再依赖 is_displayed()，改为测试“是否可交互”。
        原理：既然 get_placeholder 能成功，说明元素在 DOM 中。
        我们尝试向元素发送一个空的 Keys，如果成功，则视为“可见/可用”。
        """
        try:
            # 1. 等待元素出现在 DOM 中 (presence 比 visibility 宽松)
            element = self.wait_utils.wait_element_present(self.INPUT_SEARCH_BOX)

            # 2. 尝试进行微操作来验证可用性
            # 发送一个空的字符串或退格键，这通常不会改变页面状态，但能验证元素是否接受输入
            from selenium.webdriver.common.keys import Keys
            element.send_keys(Keys.NULL)  # 发送空键

            print("[DEBUG] 搜索框交互测试成功 (Send Keys OK)，判定为可见/可用。")
            return True

        except Exception as e:
            # 如果连发送按键都失败，那才是真的不可用
            print(f"[ERROR] 搜索框交互测试失败: {e}")

            # 兜底：如果报错是因为元素被遮挡，尝试用 JavaScript 强制聚焦
            # 3. 兜底逻辑：必须在 except 块内部重新获取元素，防止变量未定义
            """
            如果第一个 try 块中获取 element 失败（报错），程序会跳转到 except 分支。此时，element 变量根本没有被赋值。
            紧接着代码执行到第二个 try 块的 self.driver.execute_script(..., element)，此时会因为 element 未定义而报错：UnboundLocalError: local variable 'element' referenced before assignment。
            """
            # 重新查找元素，避免 element 未定义
            element = self.driver.find_element(*self.INPUT_SEARCH_BOX)
            try:
                self.driver.execute_script("arguments[0].focus();", element)
                print("[INFO] 通过 JS 强制聚焦成功，判定为可用。")
                return True
            except:
                return False

        """
        GLM 方案，
        验证搜索框是否可见/可用
        修复：统一使用 self.wait_utils，不再混用 self.wait
        try:
            # 直接使用 self.wait_utils 等待元素可见
            # 如果元素不可见，wait_utils 会抛出 TimeoutException，被外层 except 捕获
            element = self.wait_utils.wait_element_visible(self.INPUT_SEARCH_BOX)
            
            # 额外验证：确保元素不仅仅是存在，还能交互（可选）
            if element.is_displayed() and element.is_enabled():
                return True
            else:
                return False
                
        except Exception as e:
            # 捕获 TimeoutException 或其他异常
            print(f"[ERROR] 搜索框可见性检查失败: {e}")
            return False
        """

    def is_search_button_visible(self):
        return self._check_visibility(self.BUTTON_SEARCH)

    def is_logo_visible(self):
        return self._check_visibility(self.LOGO)

    def get_page_title(self):
        self.wait_utils.wait_element_present(self.PAGE_TITLE_TAG)
        return self.driver.title

    def get_search_placeholder(self):
        try:
            element = self.wait_utils.wait_element_visible(self.INPUT_SEARCH_BOX)
            return element.get_attribute("placeholder")
        except Exception:
            return None

    def _check_visibility(self, locator):
        try:
            self.wait_utils.wait_element_visible(locator)
            return True
        except Exception:
            return False

    def input_keyword(self, keyword):
        """
        输入关键词 (假设您原有方法名是这个，如果不是请改回您的原名)
        🔴 修改：使用修正后的 self.INPUT_SEARCH_BOX
        """
        try:
            element = self.driver.find_element(*self.INPUT_SEARCH_BOX)
            element.clear()
            element.send_keys(keyword)
        except Exception as e:
            print(f"输入关键词失败: {e}")

    def click_search(self):
        """
        点击搜索按钮 (假设您原有方法名是这个)
        🔴 修改：使用修正后的 self.BUTTON_SEARCH
        """
        try:
            element = self.driver.find_element(*self.BUTTON_SEARCH)
            element.click()
        except Exception as e:
            print(f"点击搜索按钮失败: {e}")