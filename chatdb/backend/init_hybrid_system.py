# 混合检索系统初始化脚本

import asyncio
import logging
from datetime import datetime
from typing import List

from app.core.config import settings
from app.services.hybrid_retrieval_service import (
    HybridRetrievalEngine, QAPairWithContext, VectorService, MilvusService, EnhancedNeo4jService,
    generate_qa_id, extract_tables_from_sql, extract_entities_from_question, clean_sql
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_hybrid_system():
    """初始化混合检索系统"""
    
    logger.info("开始初始化混合检索系统...")
    
    try:
        # 1. 初始化混合检索引擎
        logger.info("初始化混合检索引擎...")
        hybrid_engine = HybridRetrievalEngine()
        await hybrid_engine.initialize()
        
        # 2. 创建必要的Neo4j索引和约束
        logger.info("创建Neo4j索引和约束...")
        await create_neo4j_indexes(hybrid_engine.neo4j_service)
        
        # 3. 预加载示例数据
        if settings.AUTO_LEARNING_ENABLED:
            logger.info("预加载示例数据...")
            await preload_sample_data(hybrid_engine)
        
        logger.info("混合检索系统初始化完成！")
        
        # 4. 运行健康检查
        await health_check(hybrid_engine)
        
    except Exception as e:
        logger.error(f"初始化混合检索系统失败: {str(e)}")
        raise
    finally:
        # 清理资源
        if 'hybrid_engine' in locals():
            hybrid_engine.close()

async def create_neo4j_indexes(neo4j_service: EnhancedNeo4jService):
    """创建Neo4j索引和约束"""
    with neo4j_service.driver.session() as session:
        try:
            # 创建唯一约束
            constraints = [
                "CREATE CONSTRAINT qa_pair_id IF NOT EXISTS FOR (qa:QAPair) REQUIRE qa.id IS UNIQUE",
                "CREATE CONSTRAINT pattern_id IF NOT EXISTS FOR (p:QueryPattern) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"创建约束成功: {constraint}")
                except Exception as e:
                    logger.warning(f"约束可能已存在: {str(e)}")
            
            # 创建索引
            indexes = [
                "CREATE INDEX qa_connection_id IF NOT EXISTS FOR (qa:QAPair) ON (qa.connection_id)",
                "CREATE INDEX qa_query_type IF NOT EXISTS FOR (qa:QAPair) ON (qa.query_type)",
                "CREATE INDEX qa_success_rate IF NOT EXISTS FOR (qa:QAPair) ON (qa.success_rate)",
                "CREATE INDEX qa_verified IF NOT EXISTS FOR (qa:QAPair) ON (qa.verified)",
                "CREATE INDEX pattern_name IF NOT EXISTS FOR (p:QueryPattern) ON (p.name)",
                "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"创建索引成功: {index}")
                except Exception as e:
                    logger.warning(f"索引可能已存在: {str(e)}")
                    
        except Exception as e:
            logger.error(f"创建索引和约束时出错: {str(e)}")
            raise

async def preload_sample_data(hybrid_engine: HybridRetrievalEngine):
    """预加载示例数据"""
    
    # 通用SQL示例数据
    sample_qa_pairs = [
        {
            "question": "查询所有用户信息",
            "sql": "SELECT * FROM users;",
            "query_type": "SELECT",
            "difficulty": 1,
            "connection_id": 0,
            "verified": True
        },
        {
            "question": "统计用户总数",
            "sql": "SELECT COUNT(*) as total_users FROM users;",
            "query_type": "AGGREGATE",
            "difficulty": 1,
            "connection_id": 0,
            "verified": True
        },
        {
            "question": "查询用户的姓名和邮箱",
            "sql": "SELECT name, email FROM users;",
            "query_type": "SELECT",
            "difficulty": 1,
            "connection_id": 0,
            "verified": True
        },
        {
            "question": "按部门统计员工数量",
            "sql": "SELECT department, COUNT(*) as employee_count FROM employees GROUP BY department;",
            "query_type": "GROUP_BY",
            "difficulty": 2,
            "connection_id": 0,
            "verified": True
        },
        {
            "question": "查询订单和客户信息",
            "sql": "SELECT o.order_id, o.order_date, c.customer_name FROM orders o JOIN customers c ON o.customer_id = c.customer_id;",
            "query_type": "JOIN",
            "difficulty": 3,
            "connection_id": 0,
            "verified": True
        },
        {
            "question": "查询销售额最高的产品",
            "sql": "SELECT product_name, SUM(quantity * price) as total_sales FROM order_items oi JOIN products p ON oi.product_id = p.product_id GROUP BY product_name ORDER BY total_sales DESC LIMIT 1;",
            "query_type": "AGGREGATE",
            "difficulty": 4,
            "connection_id": 0,
            "verified": True
        },
        {
            "question": "查询最近30天的订单",
            "sql": "SELECT * FROM orders WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY);",
            "query_type": "SELECT",
            "difficulty": 2,
            "connection_id": 0,
            "verified": True
        },
        {
            "question": "查询每个客户的订单数量",
            "sql": "SELECT c.customer_name, COUNT(o.order_id) as order_count FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.customer_name;",
            "query_type": "GROUP_BY",
            "difficulty": 3,
            "connection_id": 0,
            "verified": True
        }
    ]
    
    created_count = 0
    
    for sample in sample_qa_pairs:
        try:
            # 提取表名和实体
            used_tables = extract_tables_from_sql(sample["sql"])
            mentioned_entities = extract_entities_from_question(sample["question"])
            
            # 创建问答对对象
            qa_pair = QAPairWithContext(
                id=generate_qa_id(),
                question=sample["question"],
                sql=clean_sql(sample["sql"]),
                connection_id=sample["connection_id"],
                difficulty_level=sample["difficulty"],
                query_type=sample["query_type"],
                success_rate=0.9,  # 示例数据设置较高的成功率
                verified=sample["verified"],
                created_at=datetime.now(),
                used_tables=used_tables,
                used_columns=[],
                query_pattern=sample["query_type"],
                mentioned_entities=mentioned_entities
            )
            
            # 构建schema上下文
            schema_context = {
                "tables": [{"name": table} for table in used_tables]
            }
            
            # 存储问答对
            await hybrid_engine.store_qa_pair(qa_pair, schema_context)
            created_count += 1
            logger.info(f"创建示例问答对: {qa_pair.question}")
            
        except Exception as e:
            logger.error(f"创建示例问答对失败: {str(e)}")
    
    logger.info(f"成功预加载 {created_count} 个示例问答对")

async def health_check(hybrid_engine: HybridRetrievalEngine):
    """健康检查"""
    logger.info("开始健康检查...")
    
    try:
        # 测试向量服务
        test_vector = await hybrid_engine.vector_service.embed_question("测试查询")
        logger.info(f"✅ 向量服务正常，维度: {len(test_vector)}")
        
        # 测试Milvus连接
        test_results = await hybrid_engine.milvus_service.search_similar(test_vector, top_k=1)
        logger.info(f"✅ Milvus服务正常，返回结果数: {len(test_results)}")
        
        # 测试Neo4j连接
        with hybrid_engine.neo4j_service.driver.session() as session:
            result = session.run("MATCH (qa:QAPair) RETURN count(qa) as count")
            count = result.single()["count"]
            logger.info(f"✅ Neo4j服务正常，问答对数量: {count}")
        
        # 测试混合检索
        test_results = await hybrid_engine.hybrid_retrieve(
            query="测试查询",
            schema_context={"tables": []},
            connection_id=0,
            top_k=3
        )
        logger.info(f"✅ 混合检索正常，返回结果数: {len(test_results)}")
        
        logger.info("🎉 所有健康检查通过！")
        
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {str(e)}")
        raise

async def cleanup_system():
    """清理系统数据（谨慎使用）"""
    logger.warning("开始清理系统数据...")
    
    try:
        # 初始化服务
        neo4j_service = EnhancedNeo4jService()
        await neo4j_service.initialize()
        
        milvus_service = MilvusService()
        vector_service = VectorService()
        await vector_service.initialize()
        await milvus_service.initialize(vector_service.dimension)
        
        # 清理Neo4j数据
        with neo4j_service.driver.session() as session:
            session.run("MATCH (qa:QAPair) DETACH DELETE qa")
            session.run("MATCH (p:QueryPattern) DETACH DELETE p")
            session.run("MATCH (e:Entity) DETACH DELETE e")
            logger.info("✅ Neo4j数据清理完成")
        
        # 清理Milvus数据
        if milvus_service.collection:
            milvus_service.collection.drop()
            logger.info("✅ Milvus数据清理完成")
        
        logger.info("🧹 系统数据清理完成")
        
    except Exception as e:
        logger.error(f"❌ 清理系统数据失败: {str(e)}")
        raise
    finally:
        if 'neo4j_service' in locals():
            neo4j_service.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        # 清理模式
        print("⚠️  警告：这将删除所有混合检索系统的数据！")
        confirm = input("请输入 'YES' 确认清理: ")
        if confirm == "YES":
            asyncio.run(cleanup_system())
        else:
            print("清理操作已取消")
    else:
        # 正常初始化模式
        asyncio.run(init_hybrid_system())
