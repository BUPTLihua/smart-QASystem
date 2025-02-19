
# 该脚本实现了一个严格问答系统，支持从MongoDB数据库中提取文档并进行内容检索，
# 基于问答的上下文生成专业的答案。系统的主要流程包括：
# 1. 从MongoDB数据库中获取文档并将其向量化。
# 2. 使用Faiss向量检索库进行相似度匹配，从候选文档中找到最相关的内容。
# 3. 通过DeepSeek API结合选定文档内容生成精准回答，确保回答严格参考原文。
# 4. 支持命令行交互，用户输入技术问题后返回基于数据库内容的专业答案。

import faiss
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import requests
import logging
import json
from typing import List, Dict, Any
from bson import ObjectId
from openai import OpenAI

class StrictQASystem:
    def __init__(self,
                 api_key: str,
                 mongo_uri: str = "mongodb://localhost:27017",
                 index_prefix: str = "enhanced",
                 model_name: str = "shibing624/text2vec-base-chinese"):
        """
        初始化严格问答系统

        Args:
            api_key: DeepSeek API密钥，用于通过API获取生成的回答
            mongo_uri: MongoDB连接URI，用于连接MongoDB数据库
            index_prefix: 索引文件的前缀，用于加载预构建的Faiss向量索引和元数据
            model_name: 用于将文本内容转换为向量的SentenceTransformer模型名称，默认为中文模型 "shibing624/text2vec-base-chinese"
        """
        # 初始化MongoDB连接，获取相关集合
        self.client = MongoClient(mongo_uri)
        self.collection = self.client["tech_data1"]["articles"]  # 获取数据库中的文档集合
        self.api_key = api_key  # DeepSeek API密钥

        # 加载预训练的SentenceTransformer模型，用于文本向量化
        self.model = SentenceTransformer(model_name)

        # 从磁盘加载Faiss内容向量索引
        self.content_index = faiss.read_index(f"{index_prefix}_content.index")

        # 加载文档的元数据
        with open(f"{index_prefix}_metadata.json", "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        # 配置日志记录器
        self.logger = logging.getLogger(__name__)
        self._configure_logging()

        # 输出调试信息，确认数据库连接是否成功
        self.logger.info(f"成功连接到MongoDB数据库 {mongo_uri}")

    def _configure_logging(self):
        """配置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()]
        )

    def _get_content_vector(self, index: int) -> np.ndarray:
        """根据索引获取对应文档的内容向量"""
        if index < 0 or index >= self.content_index.ntotal:
            raise ValueError(f"无效索引: {index}")  # 检查索引是否有效
        return self.content_index.reconstruct(int(index))  # 获取Faiss索引中存储的内容向量

    def _strict_search(self, query: str) -> List[Dict]:
        """基于严格匹配的检索逻辑：仅与内容向量进行比较"""
        # 将查询转换为向量
        query_vector = self.model.encode([query])[0].astype(np.float32)
        faiss.normalize_L2(query_vector.reshape(1, -1))  # 归一化查询向量

        # 使用Faiss进行内容匹配，返回相似度和索引
        content_scores, content_indices = self.content_index.search(query_vector.reshape(1, -1), 7)

        self.logger.info(f"\n=== 内容匹配结果 ===")
        for i in range(len(content_indices[0])):
            idx = content_indices[0][i]
            score = content_scores[0][i]
            if idx != -1:
                content = self.metadata[idx].get("content", "未知内容")
                self.logger.info(f"匹配 {i + 1}: 相似度={score:.4f} | 内容={content[:100]}")  # 输出前100个字符

        # 获取候选匹配结果
        candidate_results = []
        for i in range(len(content_indices[0])):
            idx = content_indices[0][i]
            if idx == -1:
                continue

            try:
                # 获取当前文档的内容向量
                content_vector = self._get_content_vector(int(idx))
                faiss.normalize_L2(content_vector.reshape(1, -1))  # 归一化
                content_sim = float(np.dot(content_vector, query_vector))  # 计算相似度

                candidate_results.append({
                    "index": int(idx),
                    "content_sim": content_sim
                })

                self.logger.info(f"内容匹配检查：内容相似度={content_sim:.4f}")

            except Exception as e:
                self.logger.warning(f"处理索引 {idx} 时出错: {str(e)}")
                continue

        # 输出候选结果的数量
        self.logger.info(f"候选结果数量: {len(candidate_results)}")

        if not candidate_results:
            self.logger.warning("未找到相关匹配")
            return []

        # 按内容相似度进行排序
        sorted_results = sorted(candidate_results,
                                key=lambda x: x["content_sim"],
                                reverse=True)

        self.logger.info(f"排序后的结果数量: {len(sorted_results)}")

        # 返回结果
        output = []
        for res in sorted_results[:3]:  # 只返回前三个最相关的结果
            try:
                # 获取文档ID
                doc_id = ObjectId(self.metadata[res["index"]]["id"])

                # 打印调试信息，确认索引是否有效
                self.logger.info(f"正在处理索引 {res['index']}，对应的文档ID: {doc_id}")

                # 从MongoDB查询文档
                doc = self.collection.find_one({"_id": doc_id})

                if doc:
                    output.append({
                        "score": float(res["content_sim"]),  # 存储相似度得分
                        "content": doc["content"][:2000]  # 限制内容长度为2000字符
                    })
                    self.logger.info(f"成功存储文档 {doc_id}，内容: {doc['content'][:100]}")  # 输出文档前100个字符
                else:
                    self.logger.warning(f"未找到文档: {doc_id}")
            except Exception as e:
                self.logger.warning(f"获取文档失败: {str(e)}")

        if not output:
            self.logger.warning("未找到任何有效的匹配文档")

        return output

    def generate_answer(self, query: str) -> str:
        """生成严格限制的答案"""
        # 执行严格的搜索逻辑，找到相关文档
        results = self._strict_search(query)

        if not results:
            self.logger.warning("未找到相关匹配")
            return "根据现有知识库，暂时无法回答该问题"

        # 构建简明的上下文信息
        context = "\n".join([f"[文档 {i + 1}] {res['content'][:1000]}"  # 限制每个文档内容为1000字符
                             for i, res in enumerate(results)])

        # 构建用于生成答案的prompt
        prompt = f"""你现在是一个智能问答助手，请参考以下文档内容，简明扼要地回答用户问题。请严格参考原文的内容回答，如果文档内容与问题无关，请回答"暂无相关信息"。

相关文档：
{context}

当前问题：{query}
请基于上下文用中文给出专业回答："""
        print(prompt)

        url = "http://maas-api.cn-huabei-1.xf-yun.com/v1/chat/completions"
        data = {
            "model": "xdeepseekr1",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        headers = {
            "Authorization": "Bearer " + self.api_key,  # 使用DeepSeek API密钥进行身份验证
            "Content-Type": "application/json"
        }
        self.logger.info(f"发送API请求到: {url}")
        self.logger.info(f"请求头: {headers}")
        self.logger.info(f"请求数据: {json.dumps(data, ensure_ascii=False)[:200]}...")  # 只记录前200个字符

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            # 记录API响应
            self.logger.info(f"API响应状态码: {response.status_code}")
            self.logger.info(f"API响应内容: {response.text[:200]}...")  # 只记录前200个字符

            if response.status_code == 200:
                response_data = response.json()
                return response_data['choices'][0]['message']['content']
            else:
                error_message = f"API请求失败，状态码：{response.status_code}，响应：{response.text}"
                self.logger.error(error_message)
                return f"抱歉，服务暂时不可用。错误信息：{error_message}"
        except requests.exceptions.RequestException as e:
            return f"请求失败: {str(e)}"

# 使用示例
if __name__ == "__main__":
    # 设置DeepSeek API密钥
    API_KEY = ""#输入你的API秘钥

    # 创建问答系统实例
    qa = StrictQASystem(api_key=API_KEY)

    # 命令行交互，用户输入问题后系统返回答案
    while True:
        try:
            question = input("\n请输入技术问题（输入q退出）: ")
            if question.lower() in ["q", "exit"]:
                break

            if not question.strip():
                continue

            answer = qa.generate_answer(question)
            print(f"\n专业回答：\n{answer}")
            print("-" * 60)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"发生错误: {str(e)}")
