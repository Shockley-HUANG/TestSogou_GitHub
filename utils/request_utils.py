import requests
import time
from requests.exceptions import RequestException, Timeout, ConnectionError


class RequestUtils:
    """基于requests的链接有效性测试工具类"""

    def __init__(self, timeout=5):
        """
        初始化请求工具
        :param timeout: 请求超时时间（秒），默认5秒
        """
        self.timeout = timeout
        # 自定义请求头，模拟浏览器（避免被搜狗反爬）
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
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