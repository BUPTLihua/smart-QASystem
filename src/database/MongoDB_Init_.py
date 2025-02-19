# MongoDB 初始化与状态检查脚本
# 该脚本用于初始化 MongoDB 数据库并创建必要的集合和索引，同时提供数据库状态检查功能。
# 初始化过程包括连接到 MongoDB 实例、创建集合、创建索引以及记录数据库统计信息。
# 通过日志记录提供连接、操作和状态检查的详细信息，以便开发者能够及时跟踪和排查问题。
# 此脚本也可以用来验证 MongoDB 的连接是否正常，并检查数据库的当前状态（集合、文档数量和索引）。

from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO，记录一般的信息
    format='%(asctime)s - %(levelname)s - %(message)s'  # 设置日志输出格式
)
logger = logging.getLogger(__name__)  # 获取当前模块的日志记录器


def initialize_database():
    """
    初始化MongoDB数据库，创建必要的集合和索引。

    该方法会连接到MongoDB实例，创建名为"tech_data"的数据库，并在"articles"集合中创建必要的索引。
    索引包括：url（唯一索引），title（标题索引），date（日期索引）。

    返回:
        bool: 返回数据库初始化是否成功的状态。成功返回True，失败返回False。
    """
    client = None  # 用于存储数据库连接的客户端对象
    try:
        # 连接到MongoDB（指定连接超时时间为5秒）
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)

        # 尝试执行ping命令以验证MongoDB是否正常连接
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")  # 连接成功，记录日志

        # 获取数据库，若数据库不存在，则会自动创建
        db = client["tech_data"]

        # 获取集合（若集合不存在，也会自动创建）
        collection = db["articles"]

        # 索引配置：URL、标题、日期索引
        indices = [
            ("url", ASCENDING),  # URL字段索引，升序排列，保证唯一性
            ("title", ASCENDING),  # 标题字段索引，升序排列
            ("date", ASCENDING)  # 日期字段索引，升序排列
        ]

        # 创建索引
        for field, direction in indices:
            if field == "url":
                # 对url字段创建唯一索引，确保URL唯一
                collection.create_index(
                    [(field, direction)],
                    unique=True,  # 强制要求URL字段唯一
                    background=True  # 后台创建索引，不阻塞其他操作
                )
            else:
                # 对title和date字段创建普通索引
                collection.create_index(
                    [(field, direction)],
                    background=True  # 后台创建索引
                )

        logger.info("Created all necessary indexes")  # 索引创建成功，记录日志

        # 获取数据库的统计信息：文档数量、索引数量、数据库大小
        stats = {
            "documents": collection.count_documents({}),  # 获取集合中所有文档的数量
            "indexes": len(collection.list_indexes()),  # 获取集合中索引的数量
            "database_size": db.command("dbStats")["dataSize"]  # 获取数据库的存储大小
        }

        logger.info(f"Database statistics: {stats}")  # 记录数据库统计信息
        return True  # 数据库初始化成功

    except ConnectionFailure as e:
        # 连接失败的异常处理
        logger.error(f"Failed to connect to MongoDB: {e}")
        return False
    except OperationFailure as e:
        # 操作失败的异常处理
        logger.error(f"Database operation failed: {e}")
        return False
    except Exception as e:
        # 其他未知错误的异常处理
        logger.error(f"An unexpected error occurred: {e}")
        return False
    finally:
        if client:
            # 关闭数据库连接
            client.close()
            logger.info("Database connection closed")


def check_database_status():
    """
    检查数据库状态，包括集合、文档数量、索引等。

    该方法连接到MongoDB数据库并输出数据库的当前状态，包括集合名称、文档数量和索引。

    返回:
        dict or None: 返回包含数据库状态的字典，若失败则返回None。
    """
    try:
        # 连接到MongoDB
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        db = client["tech_data"]

        # 获取数据库状态：集合名称、文档数量、索引信息
        status = {
            "collections": db.list_collection_names(),  # 获取数据库中所有集合的名称
            "document_count": db["articles"].count_documents({}),  # 获取"articles"集合中的文档数量
            "indexes": list(db["articles"].list_indexes())  # 获取"articles"集合中的所有索引信息
        }

        logger.info(f"Database status: {status}")  # 记录数据库状态
        return status  # 返回数据库状态

    except Exception as e:
        # 异常处理：输出错误信息
        logger.error(f"Failed to check database status: {e}")
        return None
    finally:
        if 'client' in locals():
            # 关闭数据库连接
            client.close()


if __name__ == "__main__":
    # 初始化数据库
    success = initialize_database()
    if success:
        # 初始化成功，记录日志
        logger.info("Database initialization completed successfully")
        # 检查数据库状态
        check_database_status()
    else:
        # 初始化失败，记录日志并退出程序
        logger.error("Database initialization failed")
        sys.exit(1)
