from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import re


class UrlUtils:
    """URL标准化工具类：消除格式差异，统一链接格式"""

    @staticmethod
    def standardize_url(url):
        """
        标准化URL核心方法：
        1. 去除末尾多余的/
        2. 合并重复的//（除了协议后的//）
        3. 统一参数拼接格式（?前无多余/）
        4. 去除空参数（可选）
        """
        if not url or not url.startswith(("http://", "https://")):
            return None

        # 1. 合并重复斜杠（协议:// 后的重复//替换为/）
        url = re.sub(r'(?<!:)//+', '/', url)

        # 2. 解析URL为6大组件（scheme/netloc/path/params/query/fragment）
        parsed = urlparse(url)
        # 去除path末尾的/（如/pic/ → /pic，/ → 空）
        path = parsed.path.rstrip('/') if parsed.path != '/' else ''
        # 3. 重新拼接query参数（确保格式统一，无空参数）
        query = parse_qs(parsed.query, keep_blank_values=True)
        query = urlencode(query, doseq=True)

        # 4. 重新组装URL（fragment锚点直接丢弃，无实际意义）
        standardized = urlunparse((
            parsed.scheme.lower(),  # 协议小写（如HTTPS→https）
            parsed.netloc.lower(),  # 域名小写（如Pic.Sogou.com→pic.sogou.com）
            path,
            parsed.params,
            query,
            ''  # 丢弃fragment（如#top）
        ))
        # 最终处理：如果path为空，补一个/（如pic.sogou.com → pic.sogou.com/），统一最终格式
        if not standardized.endswith(('/?', '?')) and '?' not in standardized and not standardized.endswith('/'):
            standardized += '/'
        return standardized

    @staticmethod
    def standardize_url_list(url_list):
        """批量标准化URL列表，过滤无效URL"""
        standardized_list = []
        for url in url_list:
            std_url = UrlUtils.standardize_url(url)
            if std_url and std_url not in standardized_list:
                standardized_list.append(std_url)
        return standardized_list