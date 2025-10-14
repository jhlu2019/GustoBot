"""
工具函数，用于安全地从Neo4j数据库提取和处理数据库结构信息
"""

import re
from typing import Optional, Dict, Any
from langchain_neo4j import Neo4jGraph

def safe_get_schema(graph: Optional[Neo4jGraph] = None) -> str:
    """
    安全地从Neo4j数据库获取结构信息，处理所有可能的错误和模板变量冲突
    
    Args:
        graph: Neo4jGraph对象，如果为None则返回空字符串
        
    Returns:
        str: 处理后的数据库结构描述
    """
    if graph is None:
        return ""
    
    try:
        # 获取原始schema字符串
        schema: str = graph.get_schema
        
        # 过滤不相关的内部节点信息
        if "CypherQuery" in schema:
            schema = re.sub(
                r"^(- \*\*CypherQuery\*\*[\s\S]+?)(^Relationship properties|- \*)", 
                r"\2", 
                schema, 
                flags=re.MULTILINE
            )
        
        # 转义所有花括号，避免与模板变量冲突
        # 例如: {name} -> {{name}}
        schema = schema.replace("{", "{{").replace("}", "}}")
        
        return schema
    except Exception as e:
        print(f"获取Neo4j数据库结构失败: {e}")
        return ""

def create_guardrails_context(
    graph: Optional[Neo4jGraph] = None, 
    scope_description: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建用于guardrails提示的上下文变量
    
    Args:
        graph: Neo4jGraph对象
        scope_description: 可选的范围描述
        
    Returns:
        Dict: 包含scope_context和graph_schema的字典
    """
    # 准备范围描述
    scope_context = ""
    if scope_description:
        scope_context = f"参考此范围描述来决策:\n{scope_description}\n\n"
    
    # 准备图结构描述
    graph_schema = ""
    if graph:
        schema = safe_get_schema(graph)
        if schema:
            graph_schema = f"参考图表结构来回答:\n{schema}\n\n"
    
    return {
        "scope_context": scope_context,
        "graph_schema": graph_schema
    } 