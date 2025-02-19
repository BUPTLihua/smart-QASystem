# MongoPipeline 介绍:
# 该中间件用于将 Scrapy 爬虫抓取的 `item` 存储到 MongoDB 数据库中。
# 主要功能：
# 1. 在爬虫开始时打开与 MongoDB 的连接，爬虫结束时关闭连接。
# 2. 处理每个 `item`，确保必需的字段（如标题、URL和内容）存在，并将其插入到 MongoDB 的 `articles` 集合中。
# 3. 如果 MongoDB 中已存在相同的 URL，则更新该条目；否则，插入新条目。
# 4. 在操作过程中，记录相应的日志，帮助追踪数据库的操作和潜在问题。

from itemadapter import ItemAdapter  # 导入 ItemAdapter，用于将 Scrapy 的 item 转换为字典
from pymongo import MongoClient  # 导入 MongoClient，用于连接和操作 MongoDB
import logging  # 导入 logging，用于记录日志


class MongoPipeline:
    """
    MongoDB 数据存储中间件，将 Scrapy 爬虫抓取的 `item` 存储到 MongoDB 数据库中。
    """

    def __init__(self, mongo_uri, mongo_db):
        """
        初始化 MongoPipeline 实例，传入 MongoDB 的 URI 和数据库名。

        :param mongo_uri: MongoDB 连接 URI
        :param mongo_db: 要存储数据的 MongoDB 数据库名称
        """
        self.mongo_uri = mongo_uri  # MongoDB URI
        self.mongo_db = mongo_db  # MongoDB 数据库名称

    @classmethod
    def from_crawler(cls, crawler):
        """
        从 Scrapy 爬虫中获取 MongoDB 连接配置。
        该方法是 Scrapy 中间件的标准方法，用于从爬虫的设置中获取参数。

        :param crawler: Scrapy 爬虫对象
        :return: MongoPipeline 实例
        """
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),  # 获取 MongoDB 连接 URI
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'tech_data')  # 获取数据库名，默认 'tech_data'
        )

    def open_spider(self, spider):
        """
        当爬虫开始时，打开 MongoDB 连接，并初始化数据库对象。

        :param spider: Scrapy 爬虫对象
        """
        self.client = MongoClient(self.mongo_uri)  # 创建 MongoClient 实例并连接到 MongoDB
        self.db = self.client[self.mongo_db]  # 获取指定的数据库
        logging.info("MongoDB connection established")  # 记录连接成功的日志

    def close_spider(self, spider):
        """
        当爬虫结束时，关闭 MongoDB 连接。

        :param spider: Scrapy 爬虫对象
        """
        self.client.close()  # 关闭 MongoDB 连接
        logging.info("MongoDB connection closed")  # 记录连接关闭的日志

    def process_item(self, item, spider):
        """
        处理每个 `item`，将其存储到 MongoDB 数据库的 `articles` 集合中。

        1. 确保 `item` 包含必需的字段（title, url, content）。
        2. 如果数据库中已经存在相同的 URL，更新该文档；否则，插入新文档。

        :param item: Scrapy 抓取的 item
        :param spider: Scrapy 爬虫对象
        :return: 处理后的 item
        """
        adapter = ItemAdapter(item)  # 将 item 转换为字典格式
        collection = self.db['articles']  # 选择要操作的 MongoDB 集合：articles

        # 确保所有必需字段都存在
        required_fields = ['title', 'url', 'content']  # 定义必需字段列表
        for field in required_fields:
            if not adapter.get(field):  # 如果字段为空，则发出警告
                logging.warning(f"Missing required field: {field}")
                return item  # 如果缺少字段，直接返回 item

        try:
            # 检查 MongoDB 中是否已存在相同 URL 的文档
            existing = collection.find_one({'url': adapter['url']})
            if existing:  # 如果已存在，则更新该文档
                collection.update_one(
                    {'url': adapter['url']},  # 查找 URL 匹配的文档
                    {'$set': dict(adapter)}  # 更新文档中的所有字段
                )
                logging.info(f"Updated article: {adapter['title']}")  # 记录更新操作日志
            else:  # 如果不存在，则插入新文档
                collection.insert_one(dict(adapter))
                logging.info(f"Inserted new article: {adapter['title']}")  # 记录插入操作日志
        except Exception as e:  # 捕获 MongoDB 操作中的异常
            logging.error(f"MongoDB operation failed: {str(e)}")  # 记录错误日志

        return item  # 返回处理后的 item
