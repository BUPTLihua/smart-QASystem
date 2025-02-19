
import scrapy

class TechCrawlerItem(scrapy.Item):
    content = scrapy.Field()     # 文章内容
    author = scrapy.Field()      # 作者
    date = scrapy.Field()        # 发布时间