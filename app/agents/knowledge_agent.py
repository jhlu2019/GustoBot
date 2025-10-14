"""
知识库Agent
负责查询向量数据库并基于检索结果生成回答
"""
from typing import Dict, Any, List
from loguru import logger
from .base_agent import BaseAgent


class KnowledgeAgent(BaseAgent):
    """知识库Agent - 基于RAG回答菜谱相关问题"""

    def __init__(self, knowledge_service=None, llm_client=None):
        super().__init__(
            name="KnowledgeAgent",
            description="查询菜谱知识库，基于检索增强生成(RAG)回答用户问题"
        )
        self.knowledge_service = knowledge_service
        self.llm_client = llm_client

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于知识库处理用户问题

        Args:
            input_data: {"message": "用户问题", "context": {...}}

        Returns:
            {"answer": "回答", "sources": [...], "confidence": 0.0-1.0}
        """
        await self.log_action("Processing with knowledge base")

        user_message = input_data.get("message", "")
        context = input_data.get("context", {})

        # 1. 检索相关文档
        retrieved_docs = await self._retrieve_documents(user_message)

        if not retrieved_docs:
            await self.log_action("No relevant documents found")
            return {
                "answer": "抱歉，我在知识库中没有找到相关信息。您可以换个方式提问吗？",
                "sources": [],
                "confidence": 0.0
            }

        # 2. 生成回答
        answer = await self._generate_answer(user_message, retrieved_docs, context)

        await self.log_action("Answer generated", {"confidence": answer.get("confidence")})

        return answer

    async def _retrieve_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        从知识库检索相关文档

        Args:
            query: 查询文本

        Returns:
            相关文档列表
        """
        if not self.knowledge_service:
            logger.warning("Knowledge service not configured")
            return []

        try:
            # 调用知识库服务进行检索
            docs = await self.knowledge_service.search(query)
            await self.log_action(f"Retrieved {len(docs)} documents")
            return docs
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []

    async def _generate_answer(
        self,
        question: str,
        documents: List[Dict[str, Any]],
        context: Dict
    ) -> Dict[str, Any]:
        """
        基于检索文档生成回答

        Args:
            question: 用户问题
            documents: 检索到的文档
            context: 对话上下文

        Returns:
            生成的回答
        """
        # 构建上下文文本
        context_text = "\n\n".join([
            f"文档 {i+1}:\n{doc.get('content', '')}"
            for i, doc in enumerate(documents[:5])  # 最多使用前5个文档
        ])

        # 构建提示词
        system_prompt = """你是一个专业的菜谱助手，基于提供的知识库内容回答用户问题。

要求：
1. 只基于提供的文档内容回答，不要编造信息
2. 如果文档中没有相关信息，明确告知用户
3. 回答要准确、详细、实用
4. 如果是烹饪步骤，要按顺序清晰列出
5. 回答要友好、自然

参考文档：
{context}

请基于以上文档回答用户问题。
"""

        if not self.llm_client:
            # 如果没有LLM，返回检索到的第一个文档的内容
            return {
                "answer": documents[0].get("content", "找到相关内容，但无法生成回答"),
                "sources": [doc.get("source", "") for doc in documents],
                "confidence": 0.6
            }

        try:
            # 调用LLM生成回答
            answer_text = await self._call_llm(
                system_prompt.format(context=context_text),
                question
            )

            return {
                "answer": answer_text,
                "sources": [doc.get("source", "") for doc in documents],
                "confidence": self._calculate_confidence(documents)
            }
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return {
                "answer": "抱歉，生成回答时出现错误。",
                "sources": [],
                "confidence": 0.0
            }

    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """
        计算回答的置信度

        Args:
            documents: 检索到的文档

        Returns:
            置信度分数 (0.0-1.0)
        """
        if not documents:
            return 0.0

        # 基于文档数量和相似度分数计算
        avg_score = sum(doc.get("score", 0) for doc in documents) / len(documents)
        return min(avg_score, 1.0)

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """
        调用LLM生成回答

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息

        Returns:
            LLM生成的回答
        """
        # TODO: 实现实际的LLM调用逻辑
        raise NotImplementedError("LLM integration pending")
