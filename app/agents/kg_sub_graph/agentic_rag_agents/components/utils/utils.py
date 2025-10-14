import regex as re
from langchain_neo4j import Neo4jGraph

from .regex_patterns import get_cypher_query_node_graph_schema


def retrieve_and_parse_schema_from_graph_for_prompts(graph: Neo4jGraph) -> str:
    
    """
    关键点：
    schema 指的是 Neo4j 数据库的结构描述，包括：
    - 节点类型：如 Product, Category, Supplier 等
    - 节点属性：如 ProductName, UnitPrice, CategoryName 等
    - 关系类型：如 BELONGS_TO, SUPPLIED_BY, CONTAINS 等
    - 关系属性：关系上可能的属性（如有）

    提取出来的Schema 大致如下：
    Node properties:
        - **Product**: ProductID, ProductName, UnitPrice, UnitsInStock...
        - **Category**: CategoryID, CategoryName, Description...

    Relationship properties:
        - **BELONGS_TO**: 
        - **SUPPLIED_BY**: 
    
    必要性：
    1. 动态适应数据库变化：如果数据库结构变化（新增节点类型、关系或属性），系统无需修改代码即可适应
    2. 提高查询准确性：通过向大语言模型提供准确的数据库结构，大大降低生成错误查询的可能性
    3. 促进零样本学习：即使没有特定领域的示例，模型也能根据提供的结构信息生成符合语法的查询
    """
    
    schema: str = graph.get_schema

    # 过滤掉对用户查询不相关的内部结构信息
    if "CypherQuery" in schema:
        schema = re.sub(  
            get_cypher_query_node_graph_schema(), r"\2", schema, flags=re.MULTILINE
        )
    
    # 在这里添加一行：将所有花括号替换为方括号，避免模板变量冲突
    # 因为 Schema 中包含 { } ，会与 ChatPromptTemplate 模版中的 input_variables 
    schema = schema.replace("{", "[").replace("}", "]")
    
    return schema
