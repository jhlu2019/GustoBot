# 混合检索服务 - 核心实现

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import json
import uuid
import re
import logging
from neo4j import GraphDatabase
from pymilvus import Collection, connections, FieldSchema, CollectionSchema, DataType, utility
from sentence_transformers import SentenceTransformer
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)

# ===== 数据模型 =====

@dataclass
class QAPairWithContext:
    """带上下文的问答对"""
    id: str
    question: str
    sql: str
    connection_id: int
    difficulty_level: int
    query_type: str
    success_rate: float
    verified: bool
    created_at: datetime

    # 上下文信息
    used_tables: List[str]
    used_columns: List[str]
    query_pattern: str
    mentioned_entities: List[str]

    # 向量表示
    embedding_vector: Optional[List[float]] = None

@dataclass
class RetrievalResult:
    """检索结果"""
    qa_pair: QAPairWithContext
    semantic_score: float = 0.0
    structural_score: float = 0.0
    pattern_score: float = 0.0
    quality_score: float = 0.0
    final_score: float = 0.0
    explanation: str = ""

# ===== 向量化服务 =====

class VectorService:
    """向量化服务"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = None
        self.dimension = None
        self._initialized = False

    async def initialize(self):
        """初始化模型"""
        if not self._initialized:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name, cache_folder=r"C:\Users\86134\.cache\huggingface\hub")
                self.dimension = self.model.get_sentence_embedding_dimension()
                self._initialized = True
                logger.info(f"Embedding model loaded, dimension: {self.dimension}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {str(e)}")
                raise

    async def embed_question(self, question: str) -> List[float]:
        """将问题转换为向量"""
        if not self._initialized:
            await self.initialize()

        processed_question = self._preprocess_question(question)
        embedding = self.model.encode(processed_question)
        return embedding.tolist()

    async def batch_embed(self, questions: List[str]) -> List[List[float]]:
        """批量向量化"""
        if not self._initialized:
            await self.initialize()

        processed_questions = [self._preprocess_question(q) for q in questions]
        embeddings = self.model.encode(processed_questions)
        return embeddings.tolist()

    def _preprocess_question(self, question: str) -> str:
        """预处理问题文本"""
        return question.strip().lower()

# ===== Milvus服务 =====

class MilvusService:
    """Milvus向量数据库服务"""

    def __init__(self, host: str = None, port: str = None):
        self.host = host or settings.MILVUS_HOST
        self.port = port or settings.MILVUS_PORT
        self.collection_name = "qa_pairs"
        self.collection = None
        self._initialized = False

    async def initialize(self, dimension: int):
        """初始化Milvus连接和集合"""
        try:
            # 连接到Milvus
            connections.connect("default", host=self.host, port=self.port)
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")

            # 定义集合schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
                FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=2000),
                FieldSchema(name="sql", dtype=DataType.VARCHAR, max_length=5000),
                FieldSchema(name="connection_id", dtype=DataType.INT64),
                FieldSchema(name="difficulty_level", dtype=DataType.INT64),
                FieldSchema(name="query_type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="success_rate", dtype=DataType.FLOAT),
                FieldSchema(name="verified", dtype=DataType.BOOL),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension)
            ]

            schema = CollectionSchema(fields, "QA pairs for Text2SQL optimization")

            # 创建或获取集合
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
            else:
                self.collection = Collection(self.collection_name, schema)
                logger.info(f"Created new collection: {self.collection_name}")

                # 创建索引
                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                self.collection.create_index("embedding", index_params)
                logger.info("Created index for embedding field")

            # 加载集合到内存
            self.collection.load()
            self._initialized = True
            logger.info("Milvus service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Milvus service: {str(e)}")
            raise

    async def insert_qa_pair(self, qa_pair: QAPairWithContext) -> str:
        """插入问答对"""
        if not self._initialized:
            raise RuntimeError("Milvus service not initialized")

        try:
            data = [
                [qa_pair.id],
                [qa_pair.question],
                [qa_pair.sql],
                [qa_pair.connection_id],
                [qa_pair.difficulty_level],
                [qa_pair.query_type],
                [qa_pair.success_rate],
                [qa_pair.verified],
                [qa_pair.embedding_vector]
            ]

            self.collection.insert(data)
            self.collection.flush()
            logger.info(f"Inserted QA pair: {qa_pair.id}")
            return qa_pair.id

        except Exception as e:
            logger.error(f"Failed to insert QA pair: {str(e)}")
            raise

    async def search_similar(self,
                           query_vector: List[float],
                           top_k: int = 5,
                           connection_id: Optional[int] = None) -> List[Dict]:
        """搜索相似的问答对"""
        if not self._initialized:
            raise RuntimeError("Milvus service not initialized")

        try:
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

            # 构建过滤表达式
            expr = None
            if connection_id:
                expr = f"connection_id == {connection_id}"

            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["id", "question", "sql", "connection_id",
                              "difficulty_level", "query_type", "success_rate", "verified"]
            )

            return self._format_search_results(results[0])

        except Exception as e:
            logger.error(f"Failed to search similar QA pairs: {str(e)}")
            return []

    def _format_search_results(self, results) -> List[Dict]:
        """格式化搜索结果"""
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.entity.get("id"),
                "question": result.entity.get("question"),
                "sql": result.entity.get("sql"),
                "connection_id": result.entity.get("connection_id"),
                "difficulty_level": result.entity.get("difficulty_level"),
                "query_type": result.entity.get("query_type"),
                "success_rate": result.entity.get("success_rate"),
                "verified": result.entity.get("verified"),
                "similarity_score": result.score
            })
        return formatted_results

# ===== 扩展的Neo4j服务 =====

class EnhancedNeo4jService:
    """扩展的Neo4j服务"""

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or settings.NEO4J_URI
        self.user = user or settings.NEO4J_USER
        self.password = password or settings.NEO4J_PASSWORD
        self.driver = None
        self._initialized = False

    async def initialize(self):
        """初始化Neo4j连接"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # 测试连接
            with self.driver.session() as session:
                session.run("RETURN 1")
            self._initialized = True
            logger.info("Neo4j service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j service: {str(e)}")
            raise

    async def store_qa_pair_with_context(self, qa_pair: QAPairWithContext,
                                       schema_context: Dict[str, Any]):
        """存储问答对及其完整上下文信息"""
        if not self._initialized:
            await self.initialize()

        with self.driver.session() as session:
            try:
                # 1. 创建QAPair节点
                session.run("""
                    CREATE (qa:QAPair {
                        id: $id,
                        question: $question,
                        sql: $sql,
                        connection_id: $connection_id,
                        difficulty_level: $difficulty_level,
                        query_type: $query_type,
                        success_rate: $success_rate,
                        verified: $verified,
                        created_at: datetime($created_at)
                    })
                """,
                    id=qa_pair.id,
                    question=qa_pair.question,
                    sql=qa_pair.sql,
                    connection_id=qa_pair.connection_id,
                    difficulty_level=qa_pair.difficulty_level,
                    query_type=qa_pair.query_type,
                    success_rate=qa_pair.success_rate,
                    verified=qa_pair.verified,
                    created_at=qa_pair.created_at.isoformat()
                )

                # 2. 建立与Table的USES_TABLES关系
                for table_name in qa_pair.used_tables:
                    session.run("""
                        MATCH (qa:QAPair {id: $qa_id})
                        MATCH (t:Table {name: $table_name, connection_id: $connection_id})
                        CREATE (qa)-[:USES_TABLES]->(t)
                    """, qa_id=qa_pair.id, table_name=table_name,
                        connection_id=qa_pair.connection_id)

                # 3. 创建或更新QueryPattern
                await self._create_or_update_pattern(session, qa_pair)

                # 4. 创建Entity节点和关系
                await self._create_entity_relationships(session, qa_pair)

                logger.info(f"Stored QA pair with context: {qa_pair.id}")

            except Exception as e:
                logger.error(f"Failed to store QA pair with context: {str(e)}")
                raise

    async def _create_or_update_pattern(self, session, qa_pair: QAPairWithContext):
        """创建或更新查询模式"""
        pattern_id = f"pattern_{qa_pair.query_type}_{qa_pair.difficulty_level}"

        # 检查模式是否存在
        result = session.run("""
            MATCH (p:QueryPattern {id: $pattern_id})
            RETURN p
        """, pattern_id=pattern_id)

        if result.single():
            # 更新使用计数
            session.run("""
                MATCH (p:QueryPattern {id: $pattern_id})
                SET p.usage_count = p.usage_count + 1
            """, pattern_id=pattern_id)
        else:
            # 创建新模式
            session.run("""
                CREATE (p:QueryPattern {
                    id: $pattern_id,
                    name: $query_type,
                    difficulty_level: $difficulty_level,
                    usage_count: 1,
                    created_at: datetime()
                })
            """,
                pattern_id=pattern_id,
                query_type=qa_pair.query_type,
                difficulty_level=qa_pair.difficulty_level
            )

        # 建立QAPair与Pattern的关系
        session.run("""
            MATCH (qa:QAPair {id: $qa_id})
            MATCH (p:QueryPattern {id: $pattern_id})
            CREATE (qa)-[:FOLLOWS_PATTERN]->(p)
        """, qa_id=qa_pair.id, pattern_id=pattern_id)

    async def _create_entity_relationships(self, session, qa_pair: QAPairWithContext):
        """创建实体关系"""
        for entity in qa_pair.mentioned_entities:
            entity_id = f"entity_{entity.lower().replace(' ', '_')}"

            # 创建或获取Entity节点
            session.run("""
                MERGE (e:Entity {id: $entity_id})
                ON CREATE SET e.name = $entity_name, e.created_at = datetime()
            """, entity_id=entity_id, entity_name=entity)

            # 建立关系
            session.run("""
                MATCH (qa:QAPair {id: $qa_id})
                MATCH (e:Entity {id: $entity_id})
                CREATE (qa)-[:MENTIONS_ENTITY]->(e)
            """, qa_id=qa_pair.id, entity_id=entity_id)

    async def structural_search(self, schema_context: Dict[str, Any],
                              connection_id: int, top_k: int = 20) -> List[RetrievalResult]:
        """基于schema结构的检索"""
        if not self._initialized:
            await self.initialize()

        table_names = [table.get('name') for table in schema_context.get('tables', [])]

        with self.driver.session() as session:
            result = session.run("""
                MATCH (qa:QAPair)-[:USES_TABLES]->(t:Table)
                WHERE t.name IN $table_names AND qa.connection_id = $connection_id
                WITH qa, count(t) as table_overlap, collect(t.name) as used_tables
                ORDER BY table_overlap DESC, qa.success_rate DESC
                LIMIT $top_k
                RETURN qa, table_overlap, used_tables
            """, table_names=table_names, connection_id=connection_id, top_k=top_k)

            results = []
            for record in result:
                qa_data = record['qa']
                table_overlap = record['table_overlap']
                used_tables = record['used_tables']

                # 计算结构相似性分数
                structural_score = table_overlap / max(len(table_names), 1)

                qa_pair = self._build_qa_pair_from_record(qa_data, used_tables)
                results.append(RetrievalResult(
                    qa_pair=qa_pair,
                    structural_score=structural_score,
                    explanation=f"使用了{table_overlap}个相同的表"
                ))

            return results

    async def pattern_search(self, query_type: str, difficulty_level: int,
                           connection_id: int, top_k: int = 20) -> List[RetrievalResult]:
        """基于查询模式的检索"""
        if not self._initialized:
            await self.initialize()

        with self.driver.session() as session:
            result = session.run("""
                MATCH (qa:QAPair)-[:FOLLOWS_PATTERN]->(p:QueryPattern)
                WHERE p.name = $query_type
                AND p.difficulty_level <= $difficulty_level + 1
                AND qa.connection_id = $connection_id
                RETURN qa, p.usage_count
                ORDER BY qa.success_rate DESC, p.usage_count DESC
                LIMIT $top_k
            """, query_type=query_type, difficulty_level=difficulty_level,
                connection_id=connection_id, top_k=top_k)

            results = []
            for record in result:
                qa_data = record['qa']
                usage_count = record['usage_count']

                # 计算模式匹配分数
                pattern_score = min(1.0, usage_count / 100.0)  # 归一化使用次数

                qa_pair = self._build_qa_pair_from_record(qa_data)
                results.append(RetrievalResult(
                    qa_pair=qa_pair,
                    pattern_score=pattern_score,
                    explanation=f"匹配查询模式，使用次数: {usage_count}"
                ))

            return results

    def _build_qa_pair_from_record(self, qa_data, used_tables=None) -> QAPairWithContext:
        """从Neo4j记录构建QAPair对象"""
        return QAPairWithContext(
            id=qa_data['id'],
            question=qa_data['question'],
            sql=qa_data['sql'],
            connection_id=qa_data['connection_id'],
            difficulty_level=qa_data['difficulty_level'],
            query_type=qa_data['query_type'],
            success_rate=qa_data['success_rate'],
            verified=qa_data['verified'],
            created_at=datetime.fromisoformat(qa_data['created_at']),
            used_tables=used_tables or [],
            used_columns=[],
            query_pattern=qa_data['query_type'],
            mentioned_entities=[]
        )

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()

# ===== 融合排序器 =====

class FusionRanker:
    """多维度融合排序器"""

    def __init__(self):
        self.weights = {
            'semantic': settings.SEMANTIC_WEIGHT,
            'structural': settings.STRUCTURAL_WEIGHT,
            'pattern': settings.PATTERN_WEIGHT,
            'quality': settings.QUALITY_WEIGHT
        }

    def fuse_and_rank(self, semantic_results: List[RetrievalResult],
                     structural_results: List[RetrievalResult],
                     pattern_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """融合多个检索结果并排序"""

        # 1. 收集所有唯一的QA对
        all_qa_pairs = {}

        # 处理语义检索结果
        for result in semantic_results:
            qa_id = result.qa_pair.id
            if qa_id not in all_qa_pairs:
                all_qa_pairs[qa_id] = result
            else:
                all_qa_pairs[qa_id].semantic_score = max(
                    all_qa_pairs[qa_id].semantic_score, result.semantic_score
                )

        # 处理结构检索结果
        for result in structural_results:
            qa_id = result.qa_pair.id
            if qa_id not in all_qa_pairs:
                all_qa_pairs[qa_id] = result
            else:
                all_qa_pairs[qa_id].structural_score = max(
                    all_qa_pairs[qa_id].structural_score, result.structural_score
                )

        # 处理模式检索结果
        for result in pattern_results:
            qa_id = result.qa_pair.id
            if qa_id not in all_qa_pairs:
                all_qa_pairs[qa_id] = result
            else:
                all_qa_pairs[qa_id].pattern_score = max(
                    all_qa_pairs[qa_id].pattern_score, result.pattern_score
                )

        # 2. 计算质量分数和最终分数
        final_results = []
        for qa_id, result in all_qa_pairs.items():
            # 计算质量分数
            quality_score = self._calculate_quality_score(result.qa_pair)
            result.quality_score = quality_score

            # 计算最终分数
            final_score = (
                result.semantic_score * self.weights['semantic'] +
                result.structural_score * self.weights['structural'] +
                result.pattern_score * self.weights['pattern'] +
                quality_score * self.weights['quality']
            )
            result.final_score = final_score

            # 生成解释
            result.explanation = self._generate_explanation(result)

            final_results.append(result)

        # 3. 按最终分数排序
        return sorted(final_results, key=lambda x: x.final_score, reverse=True)

    def _calculate_quality_score(self, qa_pair: QAPairWithContext) -> float:
        """计算问答对的质量分数"""
        quality_score = 0.0

        # 验证状态加分
        if qa_pair.verified:
            quality_score += 0.3

        # 成功率加分
        quality_score += qa_pair.success_rate * 0.5

        # 难度适中加分（难度2-3的问答对通常质量较高）
        if 2 <= qa_pair.difficulty_level <= 3:
            quality_score += 0.2

        return min(1.0, quality_score)

    def _generate_explanation(self, result: RetrievalResult) -> str:
        """生成推荐解释"""
        explanations = []

        if result.semantic_score > 0.7:
            explanations.append(f"语义高度相似({result.semantic_score:.2f})")
        elif result.semantic_score > 0.5:
            explanations.append(f"语义相似({result.semantic_score:.2f})")

        if result.structural_score > 0.7:
            explanations.append("使用相同的表结构")
        elif result.structural_score > 0.3:
            explanations.append("使用部分相同的表")

        if result.pattern_score > 0.5:
            explanations.append("匹配相似的查询模式")

        if result.qa_pair.verified:
            explanations.append("已验证的高质量示例")

        return "; ".join(explanations) if explanations else "相关示例"

# ===== 混合检索引擎 =====

class HybridRetrievalEngine:
    """混合检索引擎，结合向量检索和图检索"""

    def __init__(self):
        self.vector_service = VectorService()
        self.milvus_service = MilvusService()
        self.neo4j_service = EnhancedNeo4jService()
        self.fusion_ranker = FusionRanker()
        self._initialized = False

    async def initialize(self):
        """初始化所有服务"""
        if not self._initialized:
            try:
                # 初始化向量服务
                await self.vector_service.initialize()

                # 初始化Milvus服务
                await self.milvus_service.initialize(self.vector_service.dimension)

                # 初始化Neo4j服务
                await self.neo4j_service.initialize()

                self._initialized = True
                logger.info("Hybrid retrieval engine initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize hybrid retrieval engine: {str(e)}")
                raise

    async def hybrid_retrieve(self, query: str, schema_context: Dict[str, Any],
                            connection_id: int, top_k: int = 5) -> List[RetrievalResult]:
        """混合检索主函数"""
        if not self._initialized:
            await self.initialize()

        try:
            # 并行执行多种检索
            if settings.PARALLEL_RETRIEVAL:
                semantic_task = self._semantic_search(query, connection_id)
                structural_task = self._structural_search(schema_context, connection_id)
                pattern_task = self._pattern_search(query, connection_id)

                # 等待所有检索完成
                semantic_results, structural_results, pattern_results = await asyncio.gather(
                    semantic_task, structural_task, pattern_task, return_exceptions=True
                )

                # 处理异常结果
                semantic_results = semantic_results if not isinstance(semantic_results, Exception) else []
                structural_results = structural_results if not isinstance(structural_results, Exception) else []
                pattern_results = pattern_results if not isinstance(pattern_results, Exception) else []
            else:
                # 串行执行
                # 从向量数据库检索样本案例数据
                semantic_results = await self._semantic_search(query, connection_id)
                structural_results = await self._structural_search(schema_context, connection_id)
                pattern_results = await self._pattern_search(query, connection_id)

            # 融合排序
            final_results = self.fusion_ranker.fuse_and_rank(
                semantic_results, structural_results, pattern_results
            )

            return final_results[:top_k]

        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {str(e)}")
            return []

    async def _semantic_search(self, query: str, connection_id: int) -> List[RetrievalResult]:
        """语义检索"""
        try:
            # 向量化查询
            query_vector = await self.vector_service.embed_question(query)

            # Milvus检索
            milvus_results = await self.milvus_service.search_similar(
                query_vector, top_k=20, connection_id=connection_id
            )

            # 转换为RetrievalResult
            results = []
            for result in milvus_results:
                qa_pair = self._build_qa_pair_from_milvus_result(result)
                results.append(RetrievalResult(
                    qa_pair=qa_pair,
                    semantic_score=result['similarity_score'],
                    explanation=f"语义相似度: {result['similarity_score']:.3f}"
                ))

            return results

        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []

    def _build_qa_pair_from_milvus_result(self, result: Dict) -> QAPairWithContext:
        """从Milvus结果构建QAPair对象"""
        return QAPairWithContext(
            id=result["id"],
            question=result["question"],
            sql=result["sql"],
            connection_id=result["connection_id"],
            difficulty_level=result["difficulty_level"],
            query_type=result["query_type"],
            success_rate=result["success_rate"],
            verified=result["verified"],
            created_at=datetime.now(),  # 需要从存储中获取实际时间
            used_tables=[],
            used_columns=[],
            query_pattern=result["query_type"],
            mentioned_entities=[]
        )

    async def _structural_search(self, schema_context: Dict[str, Any],
                               connection_id: int) -> List[RetrievalResult]:
        """结构检索"""
        try:
            return await self.neo4j_service.structural_search(
                schema_context, connection_id, top_k=20
            )
        except Exception as e:
            logger.error(f"Error in structural search: {str(e)}")
            return []

    async def _pattern_search(self, query: str, connection_id: int) -> List[RetrievalResult]:
        """模式检索"""
        try:
            # 简单的查询类型识别
            query_type = self._classify_query_type(query)
            difficulty_level = self._estimate_difficulty(query)

            return await self.neo4j_service.pattern_search(
                query_type, difficulty_level, connection_id, top_k=20
            )
        except Exception as e:
            logger.error(f"Error in pattern search: {str(e)}")
            return []

    def _classify_query_type(self, query: str) -> str:
        """分类查询类型"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['count', 'sum', 'avg', 'max', 'min', '统计', '计算', '总数']):
            return "AGGREGATE"
        elif any(word in query_lower for word in ['join', '连接', '关联', '联合']):
            return "JOIN"
        elif any(word in query_lower for word in ['group', '分组', '按照', '分类']):
            return "GROUP_BY"
        elif any(word in query_lower for word in ['order', '排序', '排列']):
            return "ORDER_BY"
        else:
            return "SELECT"

    def _estimate_difficulty(self, query: str) -> int:
        """估算查询难度"""
        difficulty = 1
        query_lower = query.lower()

        if any(word in query_lower for word in ['join', '连接', '关联']):
            difficulty += 1
        if any(word in query_lower for word in ['group', '分组']):
            difficulty += 1
        if any(word in query_lower for word in ['having', '子查询', 'subquery']):
            difficulty += 1
        if any(word in query_lower for word in ['union', '联合']):
            difficulty += 1

        return min(5, difficulty)

    async def store_qa_pair(self, qa_pair: QAPairWithContext, schema_context: Dict[str, Any]):
        """存储问答对到Neo4j和Milvus"""
        if not self._initialized:
            await self.initialize()

        try:
            # 向量化问题
            if not qa_pair.embedding_vector:
                qa_pair.embedding_vector = await self.vector_service.embed_question(qa_pair.question)

            # 存储到Neo4j
            await self.neo4j_service.store_qa_pair_with_context(qa_pair, schema_context)

            # 存储到Milvus
            await self.milvus_service.insert_qa_pair(qa_pair)

            logger.info(f"Successfully stored QA pair: {qa_pair.id}")

        except Exception as e:
            logger.error(f"Failed to store QA pair: {str(e)}")
            raise

    def close(self):
        """关闭所有连接"""
        if self.neo4j_service:
            self.neo4j_service.close()

# ===== 工具函数 =====

def extract_tables_from_sql(sql: str) -> List[str]:
    """从SQL中提取表名"""
    # 简单的表名提取逻辑
    import re

    # 移除注释和多余空格
    sql_clean = re.sub(r'--.*?\n', '', sql)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    sql_clean = ' '.join(sql_clean.split())

    # 查找FROM和JOIN后的表名
    pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    matches = re.findall(pattern, sql_clean, re.IGNORECASE)

    return list(set(matches))

def extract_entities_from_question(question: str) -> List[str]:
    """从问题中提取实体"""
    # 简单的实体提取逻辑，可以后续用NER模型替换
    entities = []

    # 常见的业务实体关键词
    entity_keywords = {
        '用户': ['用户', '客户', '会员', 'user', 'customer'],
        '订单': ['订单', '交易', 'order', 'transaction'],
        '产品': ['产品', '商品', '物品', 'product', 'item'],
        '部门': ['部门', '科室', 'department'],
        '员工': ['员工', '职员', 'employee', 'staff']
    }

    question_lower = question.lower()
    for entity, keywords in entity_keywords.items():
        if any(keyword in question_lower for keyword in keywords):
            entities.append(entity)

    return entities

def clean_sql(sql: str) -> str:
    """清理SQL语句"""
    # 移除代码块标记
    sql = re.sub(r'```sql\n?', '', sql)
    sql = re.sub(r'```\n?', '', sql)

    # 移除多余的空格和换行
    sql = ' '.join(sql.split())

    # 确保以分号结尾
    if not sql.strip().endswith(';'):
        sql = sql.strip() + ';'

    return sql

def generate_qa_id() -> str:
    """生成问答对ID"""
    return f"qa_{uuid.uuid4().hex[:12]}"
