from itemadapter import ItemAdapter
from pymongo import MongoClient
import logging


class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'tech_data')
        )

    def open_spider(self, spider):
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        logging.info("MongoDB connection established")

    def close_spider(self, spider):
        self.client.close()
        logging.info("MongoDB connection closed")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        collection = self.db['articles']

        # 确保所有必需字段都存在
        required_fields = ['title', 'url', 'content']
        for field in required_fields:
            if not adapter.get(field):
                logging.warning(f"Missing required field: {field}")
                return item

        try:
            # 检查是否存在相同URL的文档
            existing = collection.find_one({'url': adapter['url']})
            if existing:
                collection.update_one(
                    {'url': adapter['url']},
                    {'$set': dict(adapter)}
                )
                logging.info(f"Updated article: {adapter['title']}")
            else:
                collection.insert_one(dict(adapter))
                logging.info(f"Inserted new article: {adapter['title']}")
        except Exception as e:
            logging.error(f"MongoDB operation failed: {str(e)}")

        return item