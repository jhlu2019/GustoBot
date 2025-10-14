"""基于词向量的查询匹配工具，用于将用户问题匹配到预定义的Cypher查询"""

import os
import numpy as np
import requests
from typing import Dict, List, Tuple, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import settings

class VectorQueryMatcher:
    """基于词向量的查询匹配器，用于将用户问题匹配到预定义的Cypher查询"""
    
    def __init__(
        self, 
        predefined_cypher_dict: Dict[str, str],
        query_descriptions: Dict[str, str],
        similarity_threshold: float = 0.5
    ):
        """
        初始化查询匹配器
        
        参数:
        predefined_cypher_dict: 预定义的Cypher查询字典
        query_descriptions: 每个查询的描述信息字典，用于增强匹配
        similarity_threshold: 相似度阈值，低于该阈值的匹配将被忽略
        """
        self.predefined_cypher_dict = predefined_cypher_dict
        self.query_descriptions = query_descriptions
        self.similarity_threshold = similarity_threshold
        
        # 使用环境变量获取Ollama的基础URL和模型名称
        self.ollama_base_url = settings.OLLAMA_BASE_URL.rstrip('/')
        self.ollama_embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        self.ollama_api_url = f"{self.ollama_base_url}/api/embed"
        
        print(f"使用Ollama模型: {self.ollama_embedding_model}, 地址: {self.ollama_base_url}")
        
        # 预计算查询向量
        self.query_vectors = self._compute_query_vectors()
    
    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """使用Ollama的embedding API将文本转换为向量"""
        payload = {
            "model": self.ollama_embedding_model,
            "input": texts
        }
        
        try:
            response = requests.post(self.ollama_api_url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["embeddings"]
        except Exception as e:
            print(f"生成embedding时出错: {str(e)}")
            # 如果调用失败，返回空向量作为后备
            return [[0.0] * 1024] * len(texts)  # 假设向量维度为1024
    
    def _compute_query_vectors(self) -> Dict[str, np.ndarray]:
        """预计算所有预定义查询的向量表示"""
        query_texts = []
        query_keys = []
        
        for query_name, cypher in self.predefined_cypher_dict.items():
            # 使用查询名称和描述创建更丰富的表示
            description = self.query_descriptions.get(query_name, "")
            query_text = f"{query_name} {description}"
            query_texts.append(query_text)
            query_keys.append(query_name)
        
        # 计算向量表示
        vectors = self._embed_texts(query_texts)
        
        # 创建查询名到向量的映射
        return {key: np.array(vector) for key, vector in zip(query_keys, vectors)}
    
    def match_query(self, user_question: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        将用户问题匹配到最相似的预定义查询
        
        参数:
        user_question: 用户问题
        top_k: 返回的最佳匹配数量
        
        返回:
        包含匹配查询名称和相似度分数的字典列表，按相似度降序排列
        """
        # 对用户问题进行向量化
        question_vector = np.array(self._embed_texts([user_question])[0])
        
        # 计算用户问题与所有预定义查询的相似度
        similarities = []
        for query_name, query_vector in self.query_vectors.items():
            similarity = cosine_similarity([question_vector], [query_vector])[0][0]
            similarities.append((query_name, similarity))
        
        # 按相似度降序排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 提取前top_k个结果，但过滤掉低于阈值的匹配
        results = []
        for query_name, similarity in similarities[:top_k]:
            if similarity >= self.similarity_threshold:
                results.append({
                    "query_name": query_name,
                    "similarity": float(similarity),
                    "cypher": self.predefined_cypher_dict[query_name]
                })
        
        return results
    
    def extract_parameters(self, user_question: str, query_name: str, llm=None) -> Dict[str, str]:
        """
        从用户问题中提取参数
        
        参数:
        user_question: 用户问题
        query_name: 匹配到的查询名称
        llm: 可选的语言模型，用于复杂参数提取
        
        返回:
        包含参数名和值的字典
        """
        # 检查查询是否存在
        if query_name not in self.predefined_cypher_dict:
            return {}
        
        # 获取查询模板
        cypher_template = self.predefined_cypher_dict[query_name]
        
        # 提取参数列表
        import re
        param_names = re.findall(r'\$(\w+)', cypher_template)
        
        # 使用LLM提取参数（如果提供）
        if llm is not None:
            return self._extract_parameters_with_llm(user_question, param_names, query_name, llm)
        
        # 使用简单规则进行参数提取
        return self._extract_parameters_with_rules(user_question, param_names)
    
    def _extract_parameters_with_rules(self, user_question: str, param_names: List[str]) -> Dict[str, str]:
        """使用规则从用户问题中提取参数"""
        params = {}
        
        for param_name in param_names:
            # 根据参数名称使用特定规则提取
            if param_name == "product_name":
                # 简单的产品名称提取规则
                import re
                product_match = re.search(r'[关于|查询|找|有关][\s]*([\w\s]+?)[\s]*[的|是|多少]', user_question)
                if product_match:
                    params[param_name] = product_match.group(1)
            
            elif param_name == "category_name":
                # 类别名称提取规则
                import re
                category_match = re.search(r'[类别|分类|种类|类型][\s]*([\w\s]+?)[\s]*[的|是|有]', user_question)
                if category_match:
                    params[param_name] = category_match.group(1)
            
            elif param_name == "order_id":
                # 订单ID提取规则
                import re
                order_match = re.search(r'订单[\s]*([0-9]+)', user_question)
                if order_match:
                    params[param_name] = order_match.group(1)
                    
            # 可以添加更多参数提取规则
        
        return params
    
    def _extract_parameters_with_llm(self, user_question: str, param_names: List[str], 
                                    query_name: str, llm: Any) -> Dict[str, str]:
        """使用LLM从用户问题中提取参数"""
        from langchain_core.prompts import ChatPromptTemplate
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是参数提取专家。你的任务是从用户问题中提取指定参数。
            只返回JSON格式的参数值，不要添加任何解释。
            如果无法提取某个参数，则该参数值为空字符串。"""),
            ("human", f"""
            用户问题: {user_question}
            查询类型: {query_name}
            需要提取的参数: {', '.join(param_names)}
            
            请提取这些参数并以JSON格式返回，格式如: {{"参数名": "参数值", ...}}
            """)
        ])
        
        # 调用LLM
        response = llm.invoke(prompt)
        
        # 解析响应
        import json
        import re
        
        # 尝试直接解析JSON
        try:
            # 查找JSON格式内容
            json_match = re.search(r'{.*}', response.content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                params = json.loads(json_str)
                return params
        except Exception as e:
            print(f"无法解析LLM响应为JSON: {str(e)}")
        
        # 如果解析失败，返回空字典
        return {}

# 创建实例化辅助函数
def create_vector_query_matcher(
    predefined_cypher_dict: Dict[str, str], 
    query_descriptions: Optional[Dict[str, str]] = None
) -> VectorQueryMatcher:
    """
    创建并返回VectorQueryMatcher实例
    
    参数:
    predefined_cypher_dict: 预定义的Cypher查询字典
    query_descriptions: 可选的查询描述字典
    
    返回:
    VectorQueryMatcher实例
    """
    # 如果没有提供描述，为每个查询生成默认描述
    if query_descriptions is None:
        query_descriptions = {}
        for query_name in predefined_cypher_dict.keys():
            # 将查询名称转换为更可读的描述
            description = query_name.replace('_', ' ')
            query_descriptions[query_name] = description
    
    return VectorQueryMatcher(predefined_cypher_dict, query_descriptions) 