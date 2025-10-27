"""
Text2SQL服务 - 重构后的版本
提供向后兼容的接口，内部使用新的工具模块
"""
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.db_connection import DBConnection
from app.schemas.query import QueryResponse
from app.services.db_service import execute_query
from app.services.text2sql_utils import (
    retrieve_relevant_schema, get_value_mappings, format_schema_for_prompt,
    process_sql_with_value_mappings, validate_sql, extract_sql_from_llm_response
)
from app.core.llms import model_client


def construct_prompt(schema_context: Dict[str, Any], query: str, value_mappings: Dict[str, Dict[str, str]]) -> str:
    """
    为LLM构建增强上下文和指令的提示
    """
    # 格式化表结构信息
    schema_str = format_schema_for_prompt(schema_context)

    # 如果有值映射，添加到提示中
    mappings_str = ""
    if value_mappings:
        mappings_str = "-- 值映射:\n"
        for column, mappings in value_mappings.items():
            mappings_str += f"-- 对于 {column}:\n"
            for nl_term, db_value in mappings.items():
                mappings_str += f"--   自然语言中的'{nl_term}'指数据库中的'{db_value}'\n"
        mappings_str += "\n"

    prompt = f"""
你是一名专业的SQL开发专家，专门将自然语言问题转换为精确的SQL查询。

### 数据库结构:
```sql
{schema_str}
{mappings_str}
```

### 自然语言问题:
"{query}"

### 指令:
1. 分析问题并识别相关的表和列。
2. 考虑表之间的关系以确定必要的连接。
3. 如果问题提到的术语可能与实际数据库值不同（例如，"中石化" vs "中国石化"），使用提供的值映射或考虑使用LIKE操作符。
4. 生成回答问题的有效SQL查询。
5. 只使用结构中提供的表和列。
6. 如果需要，使用适当的聚合函数（COUNT、SUM、AVG等）。
7. 根据需要包含适当的GROUP BY、ORDER BY和LIMIT子句。
8. 如果查询与时间相关，适当处理日期/时间比较。
9. 简要解释你的推理。

### SQL查询:
"""

    return prompt


def call_llm_api(prompt: str) -> str:
    """
    调用LLM API使用model_client生成SQL
    """
    try:
        system_message = """
        你是一名专业的SQL开发专家，专门将自然语言问题转换为精确的SQL查询。
        你的专长包括:
        1. 理解复杂的数据库结构和关系
        2. 将自然语言意图转换为正确的SQL语法
        3. 处理连接、聚合和复杂的过滤条件
        4. 确保查询优化并遵循最佳实践

        始终生成遵循标准SQL语法的有效SQL。专注于准确性和精确性。
        """

        # 直接使用model_client以保持一致性
        response = model_client.complete(
            prompt=prompt,
            system_prompt=system_message,
            temperature=0.1  # 较低的温度以获得更确定的输出
        )

        # 确保返回字符串
        return response if isinstance(response, str) else response.content
    except Exception as e:
        raise Exception(f"调用LLM API时出错: {str(e)}")


def process_text2sql_query(db: Session, connection: DBConnection, natural_language_query: str) -> QueryResponse:
    """
    处理自然语言查询并转换为SQL
    """
    try:
        # 1. 检索相关表结构
        schema_context = retrieve_relevant_schema(db, connection.id, natural_language_query)

        # 如果没有找到相关表结构，返回错误
        if not schema_context["tables"]:
            return QueryResponse(
                sql="",
                results=None,
                error="无法为此查询识别相关表。",
                context={"schema_context": schema_context}
            )

        # 2. 获取值映射
        value_mappings = get_value_mappings(db, schema_context)

        # 3. 构建提示
        prompt = construct_prompt(schema_context, natural_language_query, value_mappings)

        # 4. 调用LLM API
        llm_response = call_llm_api(prompt)

        # 5. 从响应中提取SQL
        sql = extract_sql_from_llm_response(llm_response)

        # 6. 使用值映射处理SQL
        processed_sql = process_sql_with_value_mappings(sql, value_mappings)

        # 7. 验证SQL
        if not validate_sql(processed_sql):
            return QueryResponse(
                sql=processed_sql,
                results=None,
                error="生成的SQL验证失败。它可能不是有效的SELECT语句。",
                context={
                    "schema_context": schema_context,
                    "prompt": prompt,
                    "llm_response": llm_response
                }
            )

        # 8. 执行SQL
        try:
            results = execute_query(connection, processed_sql)

            return QueryResponse(
                sql=processed_sql,
                results=results,
                error=None,
                context={
                    "schema_context": schema_context,
                    "prompt": prompt,
                    "llm_response": llm_response
                }
            )
        except Exception as e:
            return QueryResponse(
                sql=processed_sql,
                results=None,
                error=f"SQL执行失败: {str(e)}",
                context={
                    "schema_context": schema_context,
                    "prompt": prompt,
                    "llm_response": llm_response
                }
            )
    except Exception as e:
        return QueryResponse(
            sql="",
            results=None,
            error=f"处理查询时出错: {str(e)}",
            context=None
        )
