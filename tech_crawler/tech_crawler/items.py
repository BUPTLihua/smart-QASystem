import scrapy

class TechCrawlerItem(scrapy.Item):
    title = scrapy.Field()       # 文章标题
    url = scrapy.Field()         # 文章链接
    content = scrapy.Field()     # 文章内容
    author = scrapy.Field()      # 作者
    date = scrapy.Field()        # 发布时间

