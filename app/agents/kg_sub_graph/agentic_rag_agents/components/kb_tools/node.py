"""
知识库Agent
负责查询向量数据库并基于检索结果生成回答。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from app.services import LLMClient


class KnowledgeAgentInput(BaseModel):
    """知识库Agent输入结构。"""

    message: str
    context: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeAgentOutput(BaseModel):
    """知识库Agent输出结果。"""

    answer: str
    type: str = "knowledge"
    sources: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeAgent(BaseAgent):
    """知识库Agent - 基于RAG回答菜谱相关问题。"""

    def __init__(self, knowledge_service=None, llm_client: Optional[LLMClient] = None):
        super().__init__(
            name="KnowledgeAgent",
            description="查询菜谱知识库，基于检索增强生成(RAG)回答用户问题"
        )
        self.knowledge_service = knowledge_service
        self.llm_client = llm_client or self._build_llm_client()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于知识库处理用户问题。
        """
        payload = KnowledgeAgentInput.model_validate(input_data)
        await self.log_action("Processing with knowledge base")

        retrieved_docs = await self._retrieve_documents(payload.message)
        if not retrieved_docs:
            await self.log_action("No relevant documents found")
            return KnowledgeAgentOutput(
                answer="抱歉，我在知识库中没有找到相关信息。您可以换个方式提问吗？",
                sources=[],
                confidence=0.0,
                metadata={"reason": "no_documents"},
            ).model_dump()

        answer_payload = await self._generate_answer(
            question=payload.message,
            documents=retrieved_docs,
            context=payload.context,
        )
        await self.log_action("Answer generated", {"confidence": answer_payload.confidence})
        return answer_payload.model_dump()

    async def _retrieve_documents(self, query: str) -> List[Dict[str, Any]]:
        """从知识库检索相关文档。"""
        if not self.knowledge_service:
            logger.warning("Knowledge service not configured")
            return []

        try:
            docs = await self.knowledge_service.search(query)
            await self.log_action(f"Retrieved {len(docs)} documents")
            return docs
        except Exception as exc:
            logger.error(f"Document retrieval failed: {exc}")
            return []

    async def _generate_answer(
        self,
        question: str,
        documents: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> KnowledgeAgentOutput:
        """基于检索文档生成回答。"""
        context_text = "\n\n".join(
            f"文档 {idx + 1}:\n{doc.get('content', '')}"
            for idx, doc in enumerate(documents[:5])
        )

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

        sources = [doc.get("source", "") for doc in documents]
        confidence = self._calculate_confidence(documents)

        if not self.llm_client:
            return KnowledgeAgentOutput(
                answer=documents[0].get("content", "找到相关内容，但无法生成回答"),
                sources=sources,
                confidence=confidence,
                metadata={"reason": "llm_missing"},
            )

        try:
            answer_text = await self._call_llm(
                system_prompt=system_prompt.format(context=context_text),
                user_message=question,
            )
            return KnowledgeAgentOutput(
                answer=answer_text,
                sources=sources,
                confidence=confidence,
            )
        except Exception as exc:
            logger.error(f"Answer generation failed: {exc}")
            return KnowledgeAgentOutput(
                answer="抱歉，生成回答时出现错误。",
                sources=[],
                confidence=0.0,
                metadata={"reason": "llm_failure", "error": str(exc)},
            )

    def _calculate_confidence(self, documents: List[Dict[str, Any]]) -> float:
        """根据文档相似度估算置信度。"""
        if not documents:
            return 0.0
        avg_score = sum(doc.get("score", 0) for doc in documents) / len(documents)
        return min(max(avg_score, 0.0), 1.0)

    async def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """调用LLM生成回答。"""
        if not self.llm_client:
            raise RuntimeError("LLM client is not configured.")

        return await self.llm_client.chat(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.3,
        )

    @staticmethod
    def _build_llm_client() -> Optional[LLMClient]:
        try:
            return LLMClient()
        except Exception as exc:
            logger.warning(
                "KnowledgeAgent LLM client unavailable, fallback to documents. reason={}",
                exc,
            )
            return None
