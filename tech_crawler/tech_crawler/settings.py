BOT_NAME = 'tech_crawler'

SPIDER_MODULES = ['tech_crawler.spiders']
NEWSPIDER_MODULE = 'tech_crawler.spiders'

# Crawl responsibly by identifying yourself
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'tech_crawler.middlewares.RandomUserAgentMiddleware': 400,
    'tech_crawler.middlewares.TechCrawlerDownloaderMiddleware': 543,
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'tech_crawler.middlewares.TechCrawlerSpiderMiddleware': 543,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'tech_crawler.pipelines.MongoPipeline': 300,
}

# MongoDB settings
MONGO_URI = 'mongodb://localhost:27017'
MONGO_DATABASE = 'tech_data'

# Configure maximum depth that will be crawled
DEPTH_LIMIT = 2

# Configure retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Enable logging
LOG_ENABLED = True
LOG_LEVEL = 'INFO'