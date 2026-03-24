import requests
import time
from requests.exceptions import RequestException, Timeout, ConnectionError
from config import BASE_URL
import random



class RequestUtils:
    """基于requests的链接有效性测试工具类"""

    def __init__(self, timeout=5):
        """
        初始化请求工具
        :param timeout: 请求超时时间（秒），默认5秒
        """
        self.timeout = timeout
        # 自定义请求头，模拟浏览器（避免被搜狗反爬）
        USER_AGENTS = [
            # ==================== Chrome ====================
            # Windows Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",

            # macOS Chrome
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",

            # Linux Chrome
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

            # ==================== Firefox ====================
            # Windows Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",

            # macOS Firefox
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.4; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:121.0) Gecko/20100101 Firefox/121.0",

            # Linux Firefox
            "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",

            # ==================== Edge (Chromium) ====================
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",

            # macOS Edge
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",

            # ==================== Safari ====================
            # macOS Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",

            # iOS Safari (iPhone)
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",

            # iPad Safari
            "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",

            # ==================== Opera ====================
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",

            # ==================== 360安全浏览器 ====================
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 QIHU 360SE",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 QIHU 360SE",

            # ==================== 搜狗浏览器 ====================
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SE 2.X MetaSr 1.0",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SE 2.X MetaSr 1.0",

            # ==================== QQ浏览器 ====================
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 QBQrowser/11.5.0.0",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 QBQrowser/11.5.0.0",

            # ==================== 夸克浏览器 ====================
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Quark/1.0.0.0",

            # ==================== 百度浏览器 ====================
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 BaiduBoxLauncher/1.0.0.0",
        ]
        self.headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "Referer": "https://www.sogou.com/",  # 模拟从搜狗首页访问
        }

    def test_link_status(self, url):
        """
        测试单个链接的有效性
        :param url: 待测试的链接
        :return: 字典，包含测试结果（状态码、耗时、是否成功、错误信息）
        """
        result = {
            "url": url,
            "status_code": None,
            "response_time": None,
            "success": False,
            "error_msg": None
        }

        if not url or not url.startswith(("http://", "https://")):
            result["error_msg"] = "无效URL（非HTTP/HTTPS协议）"
            return result

        start_time = time.time()
        try:
            # 使用 HEAD 请求（轻量，仅获取响应头），如果失败则降级为 GET
            response = requests.head(
                url=url,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True  # 自动跟随重定向
            )
            # 降级逻辑：如果 HEAD 被拒绝，改用 GET
            if response.status_code == 405:
                response = requests.get(
                    url=url,
                    headers=self.headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )
            # 填充结果
            result["status_code"] = response.status_code
            result["response_time"] = round((time.time() - start_time) * 1000, 2)  # 毫秒
            # 2xx 状态码视为成功
            result["success"] = 200 <= response.status_code < 300

        except Timeout:
            result["error_msg"] = "请求超时"
        except ConnectionError:
            result["error_msg"] = "连接拒绝/网络错误"
        except RequestException as e:
            result["error_msg"] = f"请求异常：{str(e)}"
        except Exception as e:
            result["error_msg"] = f"未知异常：{str(e)}"

        return result

    def batch_test_links(self, links):
        """
        批量测试链接有效性
        :param links: 链接列表（去重后的）
        :return: 字典，包含汇总信息 + 每个链接的测试结果
        """
        # 去重（避免重复测试相同链接）
        unique_links = list(set(links))
        total = len(unique_links)
        success_count = 0
        failed_links = []
        test_results = []

        print(f"\n📡 开始批量测试链接（共 {total} 个唯一链接）")
        print("-" * 80)

        for idx, url in enumerate(unique_links, 1):
            result = self.test_link_status(url)
            test_results.append(result)

            # 统计成功数 + 失败链接
            if result["success"]:
                success_count += 1
            else:
                failed_links.append(result)

            # 打印单条结果（可视化）
            status_icon = "✅" if result["success"] else "❌"
            status_info = f"状态码: {result['status_code']}" if result[
                "status_code"] else f"错误: {result['error_msg']}"
            time_info = f"耗时: {result['response_time']}ms" if result["response_time"] else "耗时: --"
            print(f"{status_icon} [{idx}/{total}] {url} | {status_info} | {time_info}")

        # 汇总信息
        summary = {
            "total_links": total,
            "success_count": success_count,
            "failure_count": total - success_count,
            "success_rate": round((success_count / total) * 100, 2) if total > 0 else 0,
            "failed_links": failed_links
        }

        print("-" * 80)
        print(
            f"📊 批量测试汇总 | 总数: {total} | 成功: {success_count} | 失败: {total - success_count} | 成功率: {summary['success_rate']}%")

        return {
            "summary": summary,
            "details": test_results
        }

    def test_search_API(self,query_params):
        # 测试sogou API可用
        # 搜狗搜索API基础URL
        url = f"{BASE_URL}web"



        # 随机延迟 1-5 秒，模拟真人操作
        sleep_time = random.uniform(1, 5)
        time.sleep(sleep_time)
        # 查询参数（关键词、编码等）
        params = {
            "query": query_params,  # 搜索关键词
            "ie": "utf-8"  # 编码设置（可选，确保中文正常显示）
        }

        start_time = time.time()
        try:
            # 使用 GET 请求获取全部内容
            response = requests.get(
                url=url,
                headers=self.headers,
                params=query_params,
                timeout=self.timeout,
                allow_redirects=True  # 自动跟随重定向
            )

            result = {
                "url": url,
                "headers": self.headers,
                "query_params": query_params,
                "sleep_time": sleep_time,
                "status_code": None,
                "response_time": None,
                "success": False,
                "error_msg": None
            }
            # 填充结果
            result["status_code"] = response.status_code
            result["response_time"] = round((time.time() - start_time) * 1000, 2)  # 毫秒
            # 如果你是在编写爬虫或进行数据分析，通常会将 200-299 以及 301/302/304 视为“可处理的正常响应”，而将 4xx 和 5xx 视为异常（除非你专门处理软 404）
            result["success"] = (200 <= response.status_code < 300) or (response.status_code==301 or response.status_code==302 or response.status_code==304)

        except Timeout:
            result["error_msg"] = "请求超时"
        except ConnectionError:
            result["error_msg"] = "连接拒绝/网络错误"
        except RequestException as e:
            result["error_msg"] = f"请求异常：{str(e)}"
        except Exception as e:
            result["error_msg"] = f"未知异常：{str(e)}"

        return result