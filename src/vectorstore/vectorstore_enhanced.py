
# 该脚本用于从MongoDB数据库中提取文档内容，使用预训练的SentenceTransformer模型将文本内容转换为向量表示，
# 然后使用Faiss库构建高效的向量索引以便进行快速的相似度查询。脚本的主要功能包括：
# 1. 从MongoDB中提取文档内容。
# 2. 使用SentenceTransformer将文本转化为向量表示。
# 3. 使用Faiss构建和保存内容的向量索引，支持快速相似度检索。
# 4. 存储向量索引和相关元数据，以便后续查询和检索。

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pymongo import MongoClient
import logging
import json
from tqdm import tqdm


class EnhancedVectorStore:
    def __init__(self, model_name: str = "shibing624/text2vec-base-chinese"):
        """
        初始化EnhancedVectorStore类实例，配置SentenceTransformer模型。

        :param model_name: 用于文本向量化的SentenceTransformer模型的名称，默认为中文模型 "shibing624/text2vec-base-chinese"
        """
        self.model = SentenceTransformer(model_name)  # 初始化模型
        self.content_index = None  # 内容向量的Faiss索引
        self.metadata = []  # 用于存储文档的元数据（例如，文档ID）
        self.logger = logging.getLogger(__name__)  # 配置日志记录器

    def create_indices(self):
        """
        创建空的Faiss向量索引结构，用于存储文本内容的向量表示。

        初始化Faiss索引时，需要知道向量的维度，通过SentenceTransformer模型获取。
        """
        dim = self.model.get_sentence_embedding_dimension()  # 获取向量的维度
        self.content_index = faiss.IndexFlatIP(dim)  # 创建一个基于内积的向量索引（适用于相似度查询）

    def process_data(self, mongo_uri: str = "mongodb://localhost:27017"):
        """
        从MongoDB数据库中提取文档内容，并使用SentenceTransformer模型将内容转换为向量表示，
        生成并添加到Faiss索引中。

        :param mongo_uri: MongoDB的连接URI，默认为 "mongodb://localhost:27017"
        """
        client = MongoClient(mongo_uri)  # 连接MongoDB
        collection = client["tech_data1"]["articles"]  # 连接到指定的数据库和集合

        # 获取集合中的所有文档
        cursor = collection.find({})
        documents = list(cursor)  # 将文档转换为列表

        contents = []  # 存储文档内容
        self.metadata = []  # 存储文档的元数据（例如，文档ID）

        # 遍历每一个文档，提取内容并收集元数据
        for doc in tqdm(documents, desc="Processing documents"):
            contents.append(doc["content"])  # 提取内容字段
            self.metadata.append({
                "id": str(doc["_id"]),  # 提取文档的ID，并将其转换为字符串格式
            })

        # 使用SentenceTransformer将内容转换为向量
        content_vectors = self.model.encode(contents, show_progress_bar=True)

        # 对向量进行归一化处理，确保所有向量长度相同，方便进行高效的相似度计算
        faiss.normalize_L2(content_vectors)


