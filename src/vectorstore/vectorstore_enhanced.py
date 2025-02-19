from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pymongo import MongoClient
import logging
import json
from tqdm import tqdm


class EnhancedVectorStore:
    def __init__(self, model_name: str = "shibing624/text2vec-base-chinese"):
        self.model = SentenceTransformer(model_name)
        self.content_index = None  # 只保留内容的索引
        self.metadata = []
        self.logger = logging.getLogger(__name__)

    def create_indices(self):
        """创建空索引结构"""
        dim = self.model.get_sentence_embedding_dimension()
        self.content_index = faiss.IndexFlatIP(dim)  # 只创建内容的索引

    def process_data(self, mongo_uri: str = "mongodb://localhost:27017"):
        """处理MongoDB数据并构建索引"""
        client = MongoClient(mongo_uri)
        collection = client["tech_data1"]["articles"]

        # 获取并处理数据
        cursor = collection.find({})
        documents = list(cursor)

        contents = []
        self.metadata = []

        for doc in tqdm(documents, desc="Processing documents"):
            contents.append(doc["content"])  # 只提取内容
            self.metadata.append({
                "id": str(doc["_id"]),
            })

        # 生成内容的向量
        content_vectors = self.model.encode(contents, show_progress_bar=True)

        # 归一化向量
        faiss.normalize_L2(content_vectors)

        # 添加到内容索引
        self.content_index.add(content_vectors.astype(np.float32))

    def save_indices(self, prefix: str = "enhanced"):
        """保存索引和元数据"""
        faiss.write_index(self.content_index, f"{prefix}_content.index")
        with open(f"{prefix}_metadata.json", "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False)


if __name__ == "__main__":
    store = EnhancedVectorStore()
    store.create_indices()
    store.process_data()
    store.save_indices()
