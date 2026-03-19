from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class WaitUtils:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def wait_element_visible(self, locator):
        """等待元素可见"""
        try:
            return self.wait.until(EC.visibility_of_element_located(locator))
        except TimeoutException:
            raise TimeoutException(f"元素 {locator} 在 {self.timeout} 秒内未可见")

    def wait_element_clickable(self, locator):
        """等待元素可点击"""
        try:
            return self.wait.until(EC.element_to_be_clickable(locator))
        except TimeoutException:
            raise TimeoutException(f"元素 {locator} 在 {self.timeout} 秒内不可点击")

    def wait_element_present(self, locator):
        """等待元素存在于DOM中（不一定可见）"""
        try:
            return self.wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            raise TimeoutException(f"元素 {locator} 在 {self.timeout} 秒内不存在于DOM")

    def wait_title_contains(self, text):
        """等待标题包含特定文本"""
        try:
            return self.wait.until(EC.title_contains(text))
        except TimeoutException:
            raise TimeoutException(f"标题在 {self.timeout} 秒内未包含 '{text}'")

    # 可能的扩展方法
    def wait_element_disappear(self, locator):
        """等待元素消失"""
        try:
            return self.wait.until(EC.invisibility_of_element_located(locator))
        except TimeoutException:
            raise TimeoutException(f"元素 {locator} 在 {self.timeout} 秒内未消失")