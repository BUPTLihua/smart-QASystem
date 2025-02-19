from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_database():
    """
    初始化MongoDB数据库，创建必要的集合和索引
    返回: bool 初始化是否成功
    """
    client = None
    try:
        # 连接到MongoDB
        client = MongoClient("mongodb://localhost:27017",
                             serverSelectionTimeoutMS=5000)  # 5秒超时

        # 验证连接
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")

        # 创建或连接到数据库
        db = client["tech_data"]

        # 创建或连接到集合
        collection = db["articles"]

        # 创建索引
        indices = [
            ("url", ASCENDING),  # URL唯一索引
            ("title", ASCENDING),  # 标题索引
            ("date", ASCENDING)  # 日期索引
        ]

        for field, direction in indices:
            if field == "url":
                collection.create_index(
                    [(field, direction)],
                    unique=True,  # URL必须唯一
                    background=True  # 后台创建索引
                )
            else:
                collection.create_index(
                    [(field, direction)],
                    background=True
                )

        logger.info("Created all necessary indexes")

        # 获取数据库统计信息
        stats = {
            "documents": collection.count_documents({}),
            "indexes": len(collection.list_indexes()),
            "database_size": db.command("dbStats")["dataSize"]
        }

        logger.info(f"Database statistics: {stats}")
        return True

    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return False
    except OperationFailure as e:
        logger.error(f"Database operation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False
    finally:
        if client:
            client.close()
            logger.info("Database connection closed")


def check_database_status():
    """检查数据库状态"""
    try:
        client = MongoClient("mongodb://localhost:27017",
                             serverSelectionTimeoutMS=5000)
        db = client["tech_data"]

        # 检查数据库状态
        status = {
            "collections": db.list_collection_names(),
            "document_count": db["articles"].count_documents({}),
            "indexes": list(db["articles"].list_indexes())
        }

        logger.info(f"Database status: {status}")
        return status

    except Exception as e:
        logger.error(f"Failed to check database status: {e}")
        return None
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    success = initialize_database()
    if success:
        logger.info("Database initialization completed successfully")
        # 检查数据库状态
        check_database_status()
    else:
        logger.error("Database initialization failed")
        sys.exit(1)