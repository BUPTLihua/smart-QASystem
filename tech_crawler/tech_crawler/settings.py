# Scrapy 配置文件 - tech_crawler
# 本配置文件用于配置 Scrapy 爬虫的各种设置，如用户代理、并发请求数、下载延迟、MongoDB 设置等。
# 配置了中间件、管道、重试设置、HTTP缓存等功能，确保爬虫能够高效稳定地抓取数据并存储到 MongoDB 中。

BOT_NAME = 'tech_crawler'  # 设置爬虫的名称，用于标识爬虫

# Scrapy爬虫模块配置
SPIDER_MODULES = ['tech_crawler.spiders']  # 指定爬虫模块的位置，用于加载所有的爬虫
NEWSPIDER_MODULE = 'tech_crawler.spiders'  # 新爬虫的默认模块位置

# 用户代理配置
# 爬虫在请求时发送的用户代理（User-Agent）字段，模拟浏览器行为，避免被目标网站识别为爬虫。
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'  # 设置常见的浏览器标识

# 是否遵守 robots.txt 文件的规则
ROBOTSTXT_OBEY = True  # 默认遵守目标网站的 robots.txt 文件中的爬虫访问限制

# 配置并发请求设置
# 允许 Scrapy 同时发送的最大请求数。
CONCURRENT_REQUESTS = 16  # 设置最大并发请求数为16
CONCURRENT_REQUESTS_PER_DOMAIN = 8  # 同一域名上的最大并发请求数为8
CONCURRENT_REQUESTS_PER_IP = 8  # 同一 IP 上的最大并发请求数为8

# 配置请求间的延迟时间
# 为避免对目标网站造成过大负担，设置请求之间的延迟。
DOWNLOAD_DELAY = 3  # 设置请求的延迟时间为 3 秒
RANDOMIZE_DOWNLOAD_DELAY = True  # 随机化下载延迟时间，使请求的间隔不固定，增加爬虫的“人性化”

# 配置下载器中间件（Downloader Middlewares）
# 设置中间件的顺序，以控制请求的处理流程。
DOWNLOADER_MIDDLEWARES = {
    'tech_crawler.middlewares.RandomUserAgentMiddleware': 400,  # 随机用户代理中间件，顺序为400
    'tech_crawler.middlewares.TechCrawlerDownloaderMiddleware': 543,  # 自定义下载器中间件，顺序为543
}

# 配置爬虫中间件（Spider Middlewares）
# 设置中间件的顺序，以控制响应的处理流程。
SPIDER_MIDDLEWARES = {
    'tech_crawler.middlewares.TechCrawlerSpiderMiddleware': 543,  # 自定义爬虫中间件，顺序为543
}

# 配置项管道（Item Pipelines）
# 设置项管道的顺序，处理每个抓取到的 item。在这里我们使用 MongoPipeline 将数据存储到 MongoDB。
ITEM_PIPELINES = {
    'tech_crawler.pipelines.MongoPipeline': 300,  # MongoDB 存储管道，顺序为300
}

# MongoDB 配置
# 配置 MongoDB 连接 URI 和数据库名称，爬虫抓取的数据将存储到 MongoDB 中。
MONGO_URI = 'mongodb://localhost:27017'  # MongoDB 的连接 URI
MONGO_DATABASE = 'tech_data'  # 存储数据的 MongoDB 数据库名称

# 配置爬取的最大深度
# 限制爬虫的爬取深度，防止爬虫无限递归抓取链接，设置最大深度为 2。
DEPTH_LIMIT = 2  # 设置最大爬取深度为 2

# 配置重试设置
# 当遇到请求失败时，启用重试机制。可配置最大重试次数及重试的 HTTP 错误代码。
RETRY_ENABLED = True  # 启用重试机制
RETRY_TIMES = 3  # 设置最大重试次数为 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]  # 需要重试的 HTTP 错误代码

# 配置 HTTP 缓存
# 启用 HTTP 缓存机制，缓存请求的响应，减少对目标网站的请求压力。
HTTPCACHE_ENABLED = True  # 启用 HTTP 缓存
HTTPCACHE_EXPIRATION_SECS = 0  # 设置缓存过期时间为 0，表示不缓存响应（适用于每次请求都获取最新的内容）
HTTPCACHE_DIR = 'httpcache'  # 设置缓存存储的目录
HTTPCACHE_IGNORE_HTTP_CODES = []  # 设置忽略的 HTTP 错误代码
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'  # 使用文件系统存储缓存

# 启用日志记录
# 配置日志设置，用于记录爬虫的运行信息、警告和错误。
LOG_ENABLED = True  # 启用日志记录
LOG_LEVEL = 'INFO'  # 设置日志级别为 'INFO'，记录一般信息（可以更改为 'DEBUG'、'WARNING'、'ERROR' 等）
