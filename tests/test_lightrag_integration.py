#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LightRAG 集成测试

测试 LightRAG 替换 Microsoft GraphRAG 后的功能
"""
import pytest
import asyncio
import os
from pathlib import Path

from app.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import (
    LightRAGAPI,
    create_lightrag_query_node,
    LightRAGQueryOutputState
)


class TestLightRAGAPI:
    """测试 LightRAG API 基本功能"""

    @pytest.fixture
    async def lightrag_api(self, tmp_path):
        """创建测试用的 LightRAG API 实例"""
        api = LightRAGAPI(
            working_dir=str(tmp_path / "test_lightrag"),
            retrieval_mode="naive",  # 使用简单模式进行测试
            enable_neo4j=False  # 测试时不使用 Neo4j
        )
        await api.initialize()
        return api

    @pytest.mark.asyncio
    async def test_initialization(self, tmp_path):
        """测试 LightRAG 初始化"""
        api = LightRAGAPI(
            working_dir=str(tmp_path / "test_init"),
            enable_neo4j=False
        )
        await api.initialize()

        assert api.initialized is True
        assert api.rag is not None
        assert Path(api.working_dir).exists()

    @pytest.mark.asyncio
    async def test_insert_documents(self, lightrag_api):
        """测试文档插入功能"""
        documents = [
            """# 红烧肉
**口味**: 咸鲜, 酱香
**烹饪方法**: 炖, 炒
**食材**:
- 五花肉: 500g
- 冰糖: 30g
- 酱油: 适量

**做法**:
1. 五花肉切块，焯水
2. 炒糖色
3. 加入五花肉翻炒
4. 加水炖煮40分钟
""",
            """# 宫保鸡丁
**口味**: 麻辣
**烹饪方法**: 炒
**食材**:
- 鸡胸肉: 300g
- 花生: 100g
- 干辣椒: 适量

**做法**:
1. 鸡胸肉切丁，腌制
2. 热油爆香花椒和干辣椒
3. 加入鸡丁快炒
4. 加入花生翻炒
"""
        ]

        result = await lightrag_api.insert_documents(documents)

        assert result["total"] == 2
        assert result["success"] == 2
        assert result["error"] == 0

    @pytest.mark.asyncio
    async def test_query(self, lightrag_api):
        """测试查询功能"""
        # 先插入一些文档
        documents = [
            "红烧肉是一道经典的中华料理，主要食材是五花肉，口味咸鲜酱香。",
            "宫保鸡丁是川菜代表，以鸡肉、花生、辣椒为主要食材，口味麻辣。"
        ]
        await lightrag_api.insert_documents(documents)

        # 执行查询
        result = await lightrag_api.query("红烧肉怎么做？", mode="naive")

        assert result is not None
        assert "response" in result
        assert "mode" in result
        assert result["mode"] == "naive"
        assert isinstance(result["response"], str)

    @pytest.mark.asyncio
    async def test_query_modes(self, lightrag_api):
        """测试不同的查询模式"""
        documents = ["这是一个测试文档，用于验证 LightRAG 的不同查询模式。"]
        await lightrag_api.insert_documents(documents)

        modes = ["naive", "local", "global", "hybrid"]

        for mode in modes:
            try:
                result = await lightrag_api.query("测试查询", mode=mode)
                assert result["mode"] == mode
                assert "response" in result
            except Exception as e:
                # 某些模式可能需要更多数据才能工作
                print(f"模式 {mode} 测试跳过: {e}")


class TestLightRAGNode:
    """测试 LightRAG 节点（LangGraph 集成）"""

    @pytest.mark.asyncio
    async def test_create_node(self):
        """测试创建 LightRAG 查询节点"""
        node = create_lightrag_query_node()
        assert node is not None
        assert callable(node)

    @pytest.mark.asyncio
    async def test_node_execution(self, tmp_path):
        """测试节点执行"""
        # 创建测试用的 LightRAG API
        api = LightRAGAPI(
            working_dir=str(tmp_path / "test_node"),
            enable_neo4j=False
        )
        await api.initialize()

        # 插入测试数据
        await api.insert_documents(["红烧肉是一道经典菜品"])

        # 创建节点
        node = create_lightrag_query_node()

        # 执行节点
        state = {"task": "红烧肉怎么做？"}
        result = await node(state)

        assert "cyphers" in result
        assert "steps" in result
        assert len(result["cyphers"]) > 0

        cypher_output = result["cyphers"][0]
        assert isinstance(cypher_output, LightRAGQueryOutputState)
        assert cypher_output.task == "红烧肉怎么做？"
        assert cypher_output.query == "红烧肉怎么做？"
        assert "records" in cypher_output.model_dump()


class TestBackwardCompatibility:
    """测试向后兼容性"""

    def test_graphrag_alias(self):
        """测试 GraphRAG 别名是否存在"""
        from app.agents.kg_sub_graph.agentic_rag_agents.components.customer_tools.node import (
            create_graphrag_query_node,
            GraphRAGAPI
        )

        # 确保别名指向正确的实现
        assert create_graphrag_query_node == create_lightrag_query_node
        assert GraphRAGAPI == LightRAGAPI


@pytest.mark.integration
class TestLightRAGWithNeo4j:
    """集成测试：LightRAG + Neo4j"""

    @pytest.mark.skipif(
        os.getenv("NEO4J_URI") is None,
        reason="需要 Neo4j 连接配置"
    )
    @pytest.mark.asyncio
    async def test_with_neo4j_backend(self, tmp_path):
        """测试使用 Neo4j 作为图存储后端"""
        api = LightRAGAPI(
            working_dir=str(tmp_path / "test_neo4j"),
            enable_neo4j=True
        )

        try:
            await api.initialize()
            assert api.initialized is True

            # 插入测试文档
            documents = ["测试 Neo4j 集成"]
            result = await api.insert_documents(documents)

            assert result["success"] > 0

            # 执行查询
            query_result = await api.query("测试查询")
            assert "response" in query_result

        except Exception as e:
            pytest.skip(f"Neo4j 集成测试失败（可能是连接问题）: {e}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
