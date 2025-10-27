"""
Text2SQL工具模块
提供查询分析、表结构检索、SQL处理等工具函数
"""
import re
import json
import sqlparse
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session
from neo4j import GraphDatabase

from autogen_core.models import UserMessage
from app.core.config import settings
from app.core.llms import model_client
from app import crud

# 查询分析缓存，避免重复的LLM调用
query_analysis_cache = {}


async def analyze_query_with_llm(query: str) -> Dict[str, Any]:
    """
    使用LLM分析自然语言查询，提取关键实体和意图
    返回包含实体、关系和查询意图的结构化分析
    """
    # 检查缓存
    if query in query_analysis_cache:
        return query_analysis_cache[query]

    try:
        # 为LLM准备提示
        prompt = f"""
        你是一名数据库专家，帮助分析自然语言查询以找到相关的数据库表和列。
        请分析以下查询并提取关键信息：

        查询: "{query}"

        请以以下JSON格式提供分析：
        {{
            "entities": [查询中提到或暗示的实体名称列表],
            "relationships": [查询中暗示的实体间关系列表],
            "query_intent": "查询试图找到什么的简要描述",
            "likely_aggregations": [可能需要的聚合操作列表，如count、sum、avg],
            "time_related": 布尔值，表示查询是否涉及时间/日期过滤或分组,
            "comparison_related": 布尔值，表示查询是否涉及值比较
        }}
        """

        # 调用LLM
        response = await model_client.create([UserMessage(content=prompt, source="user")])
        response_text = response.content

        # 提取并解析JSON响应
        json_match = re.search(r'\{[\s\S]*}', response_text)
        if json_match:
            json_str = json_match.group(0)
            analysis = json.loads(json_str)

            # 验证必需字段
            if not all(k in analysis for k in ["entities", "relationships", "query_intent"]):
                analysis = _create_fallback_analysis(query)
        else:
            analysis = _create_fallback_analysis(query)

        # 缓存结果
        query_analysis_cache[query] = analysis
        return analysis
    except Exception as e:
        # 如果发生任何错误，回退到关键词提取
        analysis = _create_fallback_analysis(query)
        query_analysis_cache[query] = analysis
        return analysis


def _create_fallback_analysis(query: str) -> Dict[str, Any]:
    """创建回退分析结果"""
    return {
        "entities": extract_keywords(query),
        "relationships": [],
        "query_intent": query,
        "likely_aggregations": [],
        "time_related": False,
        "comparison_related": False
    }


def extract_keywords(query: str) -> List[str]:
    """
    使用正则表达式从查询中提取关键词（回退方法）
    """
    keywords = re.findall(r'\b\w+\b', query.lower())
    return [k for k in keywords if len(k) > 2 and k not in {
        'the', 'and', 'for', 'from', 'where', 'what', 'which', 'when', 'who',
        'how', 'many', 'much', 'with', 'that', 'this', 'these', 'those',
        '什么', '哪个', '哪些', '什么时候', '谁', '怎么', '多少', '和', '的', '是'
    }]


async def find_relevant_tables_semantic(query: str, query_analysis: Dict[str, Any],
                                       all_tables: List[Dict[str, Any]]) -> List[Tuple[int, float]]:
    """
    使用LLM进行语义匹配找到相关表
    返回(table_id, relevance_score)元组列表
    """
    try:
        # 为LLM准备表信息
        tables_info = "\n".join([
            f"表ID: {t['id']} - 名称: {t['name']} - 描述: {t['description'] or '无描述'}"
            for t in all_tables
        ])

        # 准备提示
        prompt = f"""
        你是一名数据库专家，帮助为自然语言查询找到相关表。

        查询: "{query}"

        查询分析: {json.dumps(query_analysis, ensure_ascii=False)}

        可用表:
        {tables_info}

        请按相关性对表进行排序，返回包含table_id和relevance_score(0-10)的JSON数组。
        table_id必须是每个表描述开头显示的整数ID（例如"表ID: 123"）。
        只包含实际相关的表（分数>3）。格式：
        [
            {{
                "table_id": 123, // 表的整数ID，不是名称
                "relevance_score": 8.5, // 0-10之间的浮点数
                "reasoning": "为什么这个表相关的简要解释"
            }},
            ...
        ]
        """

        # 调用LLM
        response = await model_client.create([UserMessage(content=prompt, source="user")])
        response_text = response.content

        # 提取并解析JSON响应
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            json_str = json_match.group(0)
            ranked_tables = json.loads(json_str)

            # 确保每个表都有所需字段且table_id是整数
            valid_tables = []
            for t in ranked_tables:
                if "table_id" in t and "relevance_score" in t:
                    if t["relevance_score"] > 3:
                        table_id = t["table_id"]
                        if not isinstance(table_id, int):
                            try:
                                table_id = int(table_id)
                            except (ValueError, TypeError):
                                continue
                        valid_tables.append((table_id, t["relevance_score"]))

            return valid_tables
        else:
            return basic_table_matching(query, all_tables)
    except Exception as e:
        return basic_table_matching(query, all_tables)


def basic_table_matching(query: str, all_tables: List[Dict[str, Any]]) -> List[Tuple[int, float]]:
    """
    基本关键词匹配回退方法
    """
    keywords = extract_keywords(query)
    relevant_tables = []

    for table in all_tables:
        score = 0
        table_name = table["name"].lower()
        table_desc = (table["description"] or "").lower()

        for keyword in keywords:
            if keyword in table_name:
                score += 5  # 名称匹配更高分
            elif keyword in table_desc:
                score += 3  # 描述匹配较低分

        if score > 0:
            relevant_tables.append((table["id"], min(score, 10)))  # 最高10分

    return sorted(relevant_tables, key=lambda x: x[1], reverse=True)


async def filter_expanded_tables_with_llm(query: str, query_analysis: Dict[str, Any],
                                        expanded_tables: List[Tuple[int, str, str]],
                                        relevance_scores: Dict[int, float]) -> Set[Tuple[int, str, str]]:
    """
    使用LLM根据实际相关性过滤扩展表
    """
    try:
        # 准备扩展表信息
        tables_info = "\n".join([
            f"表ID: {t[0]}, 名称: {t[1]}, 描述: {t[2] or '无描述'}, 分数: {relevance_scores.get(t[0], 0)}"
            for t in expanded_tables
        ])

        # 准备提示
        prompt = f"""
        你是一名数据库专家，帮助确定相关表是否真正与查询相关。

        查询: "{query}"

        查询分析: {json.dumps(query_analysis, ensure_ascii=False)}

        以下表是通过关系连接找到的，但我们需要确定它们是否真正相关：
        {tables_info}

        请返回实际与回答查询相关的表ID的JSON数组。
        只包含回答查询所需的表。格式：
        [
            {{
                "table_id": table_id,
                "include": true/false,
                "reasoning": "为什么应该包含或排除此表的简要解释"
            }},
            ...
        ]
        """

        # 调用LLM
        response = await model_client.create([UserMessage(content=prompt, source="user")])
        response_text = response.content

        # 提取并解析JSON响应
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            json_str = json_match.group(0)
            filtered_tables = json.loads(json_str)

            # 获取应包含的表的ID
            include_ids = [t["table_id"] for t in filtered_tables if t.get("include", False)]

            # 返回应包含的原始表元组
            return set(t for t in expanded_tables if t[0] in include_ids)
        else:
            # 如果解析失败，包含所有扩展表
            return set(expanded_tables)
    except Exception as e:
        # 如果发生任何错误，包含所有扩展表
        return set(expanded_tables)


def format_schema_for_prompt(schema_context: Dict[str, Any]) -> str:
    """
    将表结构上下文格式化为LLM提示的字符串
    """
    tables = schema_context["tables"]
    columns = schema_context["columns"]
    relationships = schema_context["relationships"]

    # 按表分组列
    columns_by_table = {}
    for column in columns:
        table_name = column["table_name"]
        if table_name not in columns_by_table:
            columns_by_table[table_name] = []
        columns_by_table[table_name].append(column)

    # 格式化表结构
    schema_str = ""

    for table in tables:
        table_name = table["name"]
        table_desc = f" ({table['description']})" if table["description"] else ""

        schema_str += f"-- 表: {table_name}{table_desc}\n"
        schema_str += "-- 列:\n"

        if table_name in columns_by_table:
            for column in columns_by_table[table_name]:
                col_name = column["name"]
                col_type = column["type"]
                col_desc = f" ({column['description']})" if column["description"] else ""
                pk_flag = " PK" if column["is_primary_key"] else ""
                fk_flag = " FK" if column["is_foreign_key"] else ""

                schema_str += f"--   {col_name} {col_type}{pk_flag}{fk_flag}{col_desc}\n"

        schema_str += "\n"

    if relationships:
        schema_str += "-- 关系:\n"
        for rel in relationships:
            rel_type = f" ({rel['relationship_type']})" if rel["relationship_type"] else ""
            schema_str += f"-- {rel['source_table']}.{rel['source_column']} -> {rel['target_table']}.{rel['target_column']}{rel_type}\n"

    return schema_str


def get_value_mappings(db: Session, schema_context: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    获取表结构上下文中列的值映射
    """
    mappings = {}

    for column in schema_context["columns"]:
        column_id = column["id"]
        column_mappings = crud.value_mapping.get_by_column(db=db, column_id=column_id)

        if column_mappings:
            table_col = f"{column['table_name']}.{column['name']}"
            mappings[table_col] = {m.nl_term: m.db_value for m in column_mappings}

    return mappings


def process_sql_with_value_mappings(sql: str, value_mappings: Dict[str, Dict[str, str]]) -> str:
    """
    处理SQL查询，将自然语言术语替换为数据库值
    """
    if not value_mappings:
        return sql

    # 这是一个简化的方法 - 更健壮的实现会使用适当的SQL解析器
    for column, mappings in value_mappings.items():
        table, col = column.split('.')

        # 查找类似"table.column = 'value'"或"column = 'value'"的模式
        for nl_term, db_value in mappings.items():
            # 尝试匹配带表名的模式
            pattern1 = rf"({table}\.{col}\s*=\s*['\"])({nl_term})(['\"])"
            sql = re.sub(pattern1, f"\\1{db_value}\\3", sql, flags=re.IGNORECASE)

            # 尝试匹配不带表名的模式
            pattern2 = rf"({col}\s*=\s*['\"])({nl_term})(['\"])"
            sql = re.sub(pattern2, f"\\1{db_value}\\3", sql, flags=re.IGNORECASE)

            # 也处理LIKE模式
            pattern3 = rf"({table}\.{col}\s+LIKE\s+['\"])%?({nl_term})%?(['\"])"
            sql = re.sub(pattern3, f"\\1%{db_value}%\\3", sql, flags=re.IGNORECASE)

            pattern4 = rf"({col}\s+LIKE\s+['\"])%?({nl_term})%?(['\"])"
            sql = re.sub(pattern4, f"\\1%{db_value}%\\3", sql, flags=re.IGNORECASE)

    return sql


def validate_sql(sql: str) -> bool:
    """
    验证SQL语法
    """
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return False

        # 检查是否是SELECT语句（为了安全）
        stmt = parsed[0]
        return stmt.get_type().upper() == 'SELECT'
    except Exception:
        return False


def extract_sql_from_llm_response(response: str) -> str:
    """
    从LLM响应中提取SQL查询
    """
    # 查找SQL代码块
    sql_match = re.search(r'```sql\n(.*?)\n```', response, re.DOTALL)
    if sql_match:
        return sql_match.group(1).strip()

    # 查找任何代码块
    code_match = re.search(r'```(.*?)```', response, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    # 如果没有代码块，尝试找到类似SQL的内容
    lines = response.split('\n')
    sql_lines = []
    in_sql = False

    for line in lines:
        if line.strip().upper().startswith('SELECT'):
            in_sql = True

        if in_sql:
            sql_lines.append(line)

            if ';' in line:
                break

    if sql_lines:
        return '\n'.join(sql_lines)

    # 如果都失败了，返回整个响应
    return response


async def retrieve_relevant_schema(db: Session, connection_id: int, query: str) -> Dict[str, Any]:
    """
    基于自然语言查询检索相关的表结构信息
    使用Neo4j图数据库和LLM找到相关表和列
    """
    try:
        # 1. 使用LLM分析查询并提取关键实体和意图
        query_analysis = await analyze_query_with_llm(query)

        # 连接到Neo4j
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

        # 使用字典按ID跟踪表以防止重复
        relevant_tables_dict = {}
        relevant_columns = set()
        table_relevance_scores = {}

        with driver.session() as session:
            # 2. 首先，获取此连接的所有表及其描述
            # 这将用于语义匹配
            all_tables = session.run(
                """
                MATCH (t:Table {connection_id: $connection_id})
                RETURN t.id AS id, t.name AS name, t.description AS description
                """,
                connection_id=connection_id
            ).data()

            # 3. 使用语义搜索基于查询分析找到相关表
            relevant_table_ids = await find_relevant_tables_semantic(query, query_analysis, all_tables)

            # 4. 按ID获取表并设置相关性分数
            for table_id, relevance_score in relevant_table_ids:
                # 确保table_id是整数类型
                if not isinstance(table_id, int):
                    try:
                        table_id = int(table_id)
                    except (ValueError, TypeError):
                        continue

                # 查找表信息
                table_info = next((t for t in all_tables if t["id"] == table_id), None)
                if table_info:
                    # 在字典中存储表，以ID为键
                    relevant_tables_dict[table_info["id"]] = (
                        table_info["id"], table_info["name"], table_info["description"]
                    )
                    table_relevance_scores[table_info["id"]] = relevance_score

            # 5. 找到与查询相关的列
            for entity in query_analysis["entities"]:
                # 搜索匹配实体名称或描述的列
                result = session.run(
                    """
                    MATCH (c:Column {connection_id: $connection_id})
                    WHERE toLower(c.name) CONTAINS $entity OR toLower(c.description) CONTAINS $entity
                    MATCH (t:Table)-[:HAS_COLUMN]->(c)
                    RETURN c.id AS id, c.name AS name, c.type AS type, c.description AS description,
                           c.is_pk AS is_pk, c.is_fk AS is_fk, t.id AS table_id, t.name AS table_name
                    """,
                    connection_id=connection_id,
                    entity=entity.lower()
                )

                for record in result:
                    relevant_columns.add((
                        record["id"], record["name"], record["type"], record["description"],
                        record["is_pk"], record["is_fk"], record["table_id"], record["table_name"]
                    ))
                    # 添加表或更新（如果已存在且有更好的描述）
                    if record["table_id"] not in relevant_tables_dict or not relevant_tables_dict[record["table_id"]][2]:
                        relevant_tables_dict[record["table_id"]] = (
                            record["table_id"], record["table_name"], ""
                        )
                    # 为有匹配列的表增加相关性分数
                    table_relevance_scores[record["table_id"]] = table_relevance_scores.get(record["table_id"], 0) + 0.5

            # 6. 如果找到了一些相关表/列，扩展以包含相关表
            if relevant_tables_dict or relevant_columns:
                table_ids = list(relevant_tables_dict.keys())

                # 通过外键找到连接的表（1跳）
                if table_ids:
                    result = session.run(
                        """
                        MATCH (t1:Table {connection_id: $connection_id})-[:HAS_COLUMN]->
                              (c1:Column)-[:REFERENCES]->
                              (c2:Column)<-[:HAS_COLUMN]-(t2:Table {connection_id: $connection_id})
                        WHERE t1.id IN $table_ids AND NOT t2.id IN $table_ids
                        RETURN t2.id AS id, t2.name AS name, t2.description AS description,
                               c1.id AS source_column_id, c1.name AS source_column_name,
                               c2.id AS target_column_id, c2.name AS target_column_name,
                               t1.id AS source_table_id
                        """,
                        connection_id=connection_id,
                        table_ids=table_ids
                    )

                    for record in result:
                        # 添加表或更新（如果已存在且有更好的描述）
                        if record["id"] not in relevant_tables_dict or (
                            not relevant_tables_dict[record["id"]][2] and record["description"]
                        ):
                            relevant_tables_dict[record["id"]] = (
                                record["id"], record["name"], record["description"]
                            )
                        # 相关表基于源表的分数获得相关性分数
                        source_score = table_relevance_scores.get(record["source_table_id"], 0)
                        table_relevance_scores[record["id"]] = source_score * 0.7  # 相关表分数降低

                # 7. 使用LLM评估扩展表是否真正与查询相关
                expanded_tables = [t for t in relevant_tables_dict.values() if t[0] not in table_ids]
                if expanded_tables:
                    filtered_expanded_tables = await filter_expanded_tables_with_llm(
                        query, query_analysis, expanded_tables, table_relevance_scores
                    )
                    # 移除LLM认为不相关的表
                    # 只保留相关表
                    filtered_table_ids = set(table_ids).union({t[0] for t in filtered_expanded_tables})
                    relevant_tables_dict = {
                        tid: t for tid, t in relevant_tables_dict.items() if tid in filtered_table_ids
                    }

        driver.close()

        # 8. 按相关性分数排序表
        sorted_tables = sorted(
            relevant_tables_dict.values(),
            key=lambda t: table_relevance_scores.get(t[0], 0),
            reverse=True
        )

        # 转换为字典列表
        tables_list = [{"id": t[0], "name": t[1], "description": t[2]} for t in sorted_tables]

        # 如果没有找到相关表，返回所有表
        if not tables_list:
            all_tables_from_db = crud.schema_table.get_by_connection(db=db, connection_id=connection_id)
            tables_list = [
                {
                    "id": table.id,
                    "name": table.table_name,
                    "description": table.description or ""
                }
                for table in all_tables_from_db
            ]

        columns_list = []

        # 获取表的所有列
        for table in tables_list:
            table_columns = crud.schema_column.get_by_table(db=db, table_id=table["id"])
            for column in table_columns:
                columns_list.append({
                    "id": column.id,
                    "name": column.column_name,
                    "type": column.data_type,
                    "description": column.description,
                    "is_primary_key": column.is_primary_key,
                    "is_foreign_key": column.is_foreign_key,
                    "table_id": table["id"],
                    "table_name": table["name"]
                })

        # 获取表之间的关系
        relationships_list = []
        table_ids = [t["id"] for t in tables_list]

        # 如果返回所有表，则获取所有关系
        all_tables_count = len(crud.schema_table.get_by_connection(db=db, connection_id=connection_id))
        if len(tables_list) == all_tables_count:
            all_relationships = crud.schema_relationship.get_by_connection(db=db, connection_id=connection_id)

            for rel in all_relationships:
                source_table = next((t for t in tables_list if t["id"] == rel.source_table_id), None)
                target_table = next((t for t in tables_list if t["id"] == rel.target_table_id), None)
                source_column = next((c for c in columns_list if c["id"] == rel.source_column_id), None)
                target_column = next((c for c in columns_list if c["id"] == rel.target_column_id), None)

                if source_table and target_table and source_column and target_column:
                    relationships_list.append({
                        "id": rel.id,
                        "source_table": source_table["name"],
                        "source_column": source_column["name"],
                        "target_table": target_table["name"],
                        "target_column": target_column["name"],
                        "relationship_type": rel.relationship_type
                    })
        else:
            # 如果只返回相关表，则获取这些表之间的关系
            for table in tables_list:
                source_rels = crud.schema_relationship.get_by_source_table(db=db, source_table_id=table["id"])
                target_rels = crud.schema_relationship.get_by_target_table(db=db, target_table_id=table["id"])

                for rel in source_rels + target_rels:
                    # 只包含相关表集中的表之间的关系
                    if rel.source_table_id in table_ids and rel.target_table_id in table_ids:
                        source_table = next((t for t in tables_list if t["id"] == rel.source_table_id), None)
                        target_table = next((t for t in tables_list if t["id"] == rel.target_table_id), None)
                        source_column = next((c for c in columns_list if c["id"] == rel.source_column_id), None)
                        target_column = next((c for c in columns_list if c["id"] == rel.target_column_id), None)

                        if source_table and target_table and source_column and target_column:
                            # 确保不重复添加关系
                            rel_dict = {
                                "id": rel.id,
                                "source_table": source_table["name"],
                                "source_column": source_column["name"],
                                "target_table": target_table["name"],
                                "target_column": target_column["name"],
                                "relationship_type": rel.relationship_type
                            }
                            if rel_dict not in relationships_list:
                                relationships_list.append(rel_dict)

        return {
            "tables": tables_list,
            "columns": columns_list,
            "relationships": relationships_list
        }
    except Exception as e:
        raise Exception(f"检索表结构上下文时出错: {str(e)}")
