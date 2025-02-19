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
            api_key: DeepSeek API密钥
            mongo_uri: MongoDB连接URI
            index_prefix: 索引文件前缀
            model_name: 文本编码模型名称
        """
        # 初始化核心组件
        self.client = MongoClient(mongo_uri)
        self.collection = self.client["tech_data1"]["articles"]
        self.api_key = api_key

        # 加载预训练模型
        self.model = SentenceTransformer(model_name)

        # 加载索引文件
        self.content_index = faiss.read_index(f"{index_prefix}_content.index")

        # 加载元数据
        with open(f"{index_prefix}_metadata.json", "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        # 配置日志系统
        self.logger = logging.getLogger(__name__)
        self._configure_logging()

        # 打印调试信息，确认数据库连接
        self.logger.info(f"成功连接到MongoDB数据库 {mongo_uri}")

    def _configure_logging(self):
        """配置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()]
        )

    def _get_content_vector(self, index: int) -> np.ndarray:
        """获取指定文档的内容向量"""
        if index < 0 or index >= self.content_index.ntotal:
            raise ValueError(f"无效索引: {index}")
        return self.content_index.reconstruct(int(index))  # 显式类型转换

    def _strict_search(self, query: str) -> List[Dict]:
        """改进的检索逻辑：只与内容向量进行比较"""
        # 生成查询向量
        query_vector = self.model.encode([query])[0].astype(np.float32)
        faiss.normalize_L2(query_vector.reshape(1, -1))

        # 进行内容匹配
        content_scores, content_indices = self.content_index.search(query_vector.reshape(1, -1), 7)

        self.logger.info(f"\n=== 内容匹配结果 ===")
        for i in range(len(content_indices[0])):
            idx = content_indices[0][i]
            score = content_scores[0][i]
            if idx != -1:
                content = self.metadata[idx].get("content", "未知内容")
                self.logger.info(f"匹配 {i + 1}: 相似度={score:.4f} | 内容={content[:100]}")  # 输出内容的前100个字符

        # 获取候选结果
        candidate_results = []
        for i in range(len(content_indices[0])):
            idx = content_indices[0][i]
            if idx == -1:
                continue

            try:
                content_vector = self._get_content_vector(int(idx))
                faiss.normalize_L2(content_vector.reshape(1, -1))
                content_sim = float(np.dot(content_vector, query_vector))

                candidate_results.append({
                    "index": int(idx),
                    "content_sim": content_sim
                })

                self.logger.info(f"内容匹配检查：内容相似度={content_sim:.4f}")

            except Exception as e:
                self.logger.warning(f"处理索引 {idx} 时出错: {str(e)}")
                continue

        # 打印候选结果数量
        self.logger.info(f"候选结果数量: {len(candidate_results)}")

        if not candidate_results:
            self.logger.warning("未找到相关匹配")
            return []

        # 按内容相似度排序
        sorted_results = sorted(candidate_results,
                                key=lambda x: x["content_sim"],
                                reverse=True)

        self.logger.info(f"排序后的结果数量: {len(sorted_results)}")

        # 返回结果
        output = []
        for res in sorted_results[:3]:  # 只取前3个最相关的结果
            try:
                # 获取文档ID
                doc_id = ObjectId(self.metadata[res["index"]]["id"])

                # 打印调试信息：检查索引是否有效
                self.logger.info(f"正在处理索引 {res['index']}，对应的文档ID: {doc_id}")

                # 使用MongoDB查询该文档
                doc = self.collection.find_one({"_id": doc_id})

                # 如果文档存在，存储相关信息
                if doc:
                    output.append({
                        "score": float(res["content_sim"]),  # 存储相似度得分
                        "content": doc["content"][:2000]  # 限制内容长度为2000字符
                    })
                    self.logger.info(f"成功存储文档 {doc_id}，内容: {doc['content'][:100]}")  # 打印内容的前100个字符
                else:
                    self.logger.warning(f"未找到文档: {doc_id}")
            except Exception as e:
                # 如果获取文档失败，输出警告并继续处理其他文档
                self.logger.warning(f"获取文档失败: {str(e)}")

        # 如果没有结果，输出提示
        if not output:
            self.logger.warning("未找到任何有效的匹配文档")

        # 返回存储的结果
        return output

    def generate_answer(self, query: str) -> str:
        """生成严格限制的答案"""
        # 执行分层检索
        results = self._strict_search(query)

        if not results:
            self.logger.warning("未找到相关匹配")
            return "根据现有知识库，暂时无法回答该问题"

        # 构建更紧凑的上下文
        context = "\n".join([f"[文档 {i + 1}] {res['content'][:1000]}"  # 限制每个文档的长度
                             for i, res in enumerate(results)])

        # 构造严格限制的prompt
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
            "Authorization": "Bearer sk-TkFjGCG1NdXESZKa39D709663a7742Ba9e35359c63145039",
            "Content-Type": "application/json"
        }
        self.logger.info(f"发送API请求到: {url}")
        self.logger.info(f"请求头: {headers}")
        self.logger.info(f"请求数据: {json.dumps(data, ensure_ascii=False)[:200]}...")  # 只记录前200个字符
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            # 记录响应信息
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
    # 在这里直接配置API密钥（生产环境建议使用环境变量）
    API_KEY = "sk-TkFjGCG1NdXESZKa39D709663a7742Ba9e35359c63145039"

    qa = StrictQASystem(api_key=API_KEY)

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
