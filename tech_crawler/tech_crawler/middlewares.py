# Scrapy 中间件介绍:
# 1. RandomUserAgentMiddleware:
#    - 该中间件用于在每次请求时随机选择一个用户代理（User-Agent），
#      目的是模拟不同浏览器的请求，避免被目标网站的反爬虫机制识别为爬虫。
#    - 它通过重写 Scrapy 的 UserAgentMiddleware 类的 process_request 方法来实现此功能。
#
# 2. TechCrawlerSpiderMiddleware:
#    - 该中间件主要负责爬虫层面的请求、响应处理，以及异常处理。
#    - 它实现了 Scrapy 的 SpiderMiddleware 接口，提供了多种钩子方法，能够处理爬虫输入和输出，
#      处理爬虫启动时的日志记录等。
#    - 主要包含 `process_spider_input`、`process_spider_output`、`process_start_requests` 等方法。
#
# 3. TechCrawlerDownloaderMiddleware:
#    - 该中间件负责下载器层面的请求和响应处理。
#    - 它实现了 Scrapy 的 DownloaderMiddleware 接口，能够在请求发送到目标网站之前进行修改，或在响应返回时进行处理。
#    - 包括 `process_request`、`process_response`、`process_exception` 等方法，主要用于在下载器层面做一些额外的处理和日志记录。
#
# 总体来说，这些中间件增强了爬虫的请求响应处理能力，包括随机化用户代理、日志记录以及异常处理等功能，
# 使得爬虫能够更好地应对各种网络请求和目标网站的反爬虫策略。

# 导入必要的模块
from scrapy import signals  # 导入Scrapy的信号模块，用于与爬虫信号交互
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware  # 导入用户代理中间件的基类
import random  # 导入随机模块，用于从用户代理列表中随机选择一个用户代理

# 随机用户代理中间件
class RandomUserAgentMiddleware(UserAgentMiddleware):
    # 定义一个常见的用户代理列表，用于模拟不同浏览器的请求
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  # Chrome浏览器
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  # Mac上的Chrome浏览器
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',  # Firefox浏览器
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',  # Safari浏览器
    ]

    # 重写父类的 process_request 方法，在每个请求中添加一个随机的用户代理
    def process_request(self, request, spider):
        # 从 user_agents 列表中随机选择一个用户代理，并将其设置到请求头中
        request.headers['User-Agent'] = random.choice(self.user_agents)

# 定义爬虫中间件
class TechCrawlerSpiderMiddleware:
    # 该方法会在爬虫启动时被调用
    @classmethod
    def from_crawler(cls, crawler):
        # 实例化中间件对象，并连接爬虫打开信号
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)  # 连接爬虫打开时的信号
        return s

    # 处理每个Spider返回的响应输入
    def process_spider_input(self, response, spider):
        # 默认返回None，表示不做处理
        return None

    # 处理Spider返回的结果输出
    def process_spider_output(self, response, result, spider):
        # 遍历Spider输出的结果，将它们逐一返回
        for i in result:
            yield i

    # 处理爬虫抛出的异常
    def process_spider_exception(self, response, exception, spider):
        # 默认不做处理
        pass

    # 处理开始请求时的处理
    def process_start_requests(self, start_requests, spider):
        # 遍历开始请求，逐一返回
        for r in start_requests:
            yield r

    # 爬虫打开时记录日志
    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

# 定义下载器中间件
class TechCrawlerDownloaderMiddleware:
    # 该方法会在爬虫启动时被调用
    @classmethod
    def from_crawler(cls, crawler):
        # 实例化中间件对象，并连接爬虫打开信号
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)  # 连接爬虫打开时的信号
        return s

    # 处理下载器的请求
    def process_request(self, request, spider):
        # 默认不做处理，返回None表示请求继续传递
        return None

    # 处理下载器的响应
    def process_response(self, request, response, spider):
        # 返回响应，不做任何修改
        return response

    # 处理下载器的异常
    def process_exception(self, request, exception, spider):
        # 默认不做处理
        pass

    # 爬虫打开时记录日志
    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
