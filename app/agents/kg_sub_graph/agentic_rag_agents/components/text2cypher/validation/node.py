"""
This code is based on content found in the LangGraph documentation: https://python.langchain.com/docs/tutorials/graph/#advanced-implementation-with-langgraph
"""

from typing import Any, Callable, Coroutine, Dict, Optional

from langchain_core.language_models import BaseChatModel
from langchain_neo4j import Neo4jGraph



from ....components.text2cypher.validation.models import ValidateCypherOutput
from ....components.text2cypher.validation.prompts import (
    create_text2cypher_validation_prompt_template,
)
from ..state import CypherState
from .validators import (
    correct_cypher_query_relationship_direction,
    validate_cypher_query_syntax,
    validate_cypher_query_with_llm,
    validate_cypher_query_with_schema,
    validate_no_writes_in_cypher_query,
)

validation_prompt_template = create_text2cypher_validation_prompt_template()


def create_text2cypher_validation_node(
    graph: Neo4jGraph,
    llm: Optional[BaseChatModel] = None,
    llm_validation: bool = True,
    max_attempts: int = 3,
    attempt_cypher_execution_on_final_attempt: bool = False,
) -> Callable[[CypherState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a Text2Cypher query validation node for a LangGraph workflow.
    This is the last node in the workflow before Cypher execution may be attempted.
    If errors are detected and max attempts have not been reached, then the Cypher Statement must be corrected by the Correction node.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    llm : Optional[BaseChatModel], optional
        The LLM to use for processing if LLM validation is desired. By default None
    llm_validation : bool, optional
        Whether to perform LLM validation with the provided LLM, by default True
    max_attempts: int, optional
        The max number of allowed attempts to generate valid Cypher, by default 3
    attempt_cypher_execution_on_final_attempt, bool, optional
        THIS MAY BE DANGEROUS.
        Whether to attempt Cypher execution on the last attempt, regardless of if the Cypher contains errors, by default False

    Returns
    -------
    Callable[[CypherState], CypherState]
        The LangGraph node.
    """

    if llm is not None and llm_validation:
        validate_cypher_chain = validation_prompt_template | llm.with_structured_output(
            ValidateCypherOutput
        )

    async def validate_cypher(state: CypherState) -> Dict[str, Any]:
        """
        Validates the Cypher statements and maps any property values to the database.
        """

        # 记录当前是第几次尝试生成/验证Cypher查询
        GENERATION_ATTEMPT: int = state.get("attempts", 0) + 1
        errors = []
        mapping_errors = []

        # 检查Cypher查询的语法是否正确，例如括号匹配、关键字使用等。
        syntax_error = validate_cypher_query_syntax(
            graph=graph, cypher_statement=state.get("statement", "")
        )

        errors.extend(syntax_error)

        # 检查Cypher查询中是否包含写操作(如CREATE、DELETE、SET等)，防止大模型意外修改数据库
        write_errors = validate_no_writes_in_cypher_query(state.get("statement", ""))
        errors.extend(write_errors)

        # Neo4j的关系是有方向性的。这一步会检查关系方向是否正确，如果不正确，会尝试自动修复。这对提高查询成功率很重要。
        corrected_cypher = correct_cypher_query_relationship_direction(
            graph=graph, cypher_statement=state.get("statement", "")
        )

        # 如果启用了大模型验证，会使用语言模型检查Cypher查询的更高级错误，
        # 例如语义上是否符合用户问题、属性映射是否正确等。这是一种更智能的验证方式。
        if llm is not None and llm_validation:
            llm_errors = await validate_cypher_query_with_llm(
                validate_cypher_chain=validate_cypher_chain,
                question=state.get("task", ""),
                graph=graph,
                cypher_statement=state.get("statement", ""),
            )
            errors.extend(llm_errors.get("errors", []))
            mapping_errors.extend(llm_errors.get("mapping_errors", []))

        # 如果禁用大模型验证，会使用更严格的模式检查Cypher查询，确保所有节点和关系都存在，并且属性值符合类型限制。
        if not llm_validation:
            cypher_errors = validate_cypher_query_with_schema(
                graph=graph, cypher_statement=state.get("statement", "")
            )
            errors.extend(cypher_errors)

        # 如果有错误且未达到最大尝试次数，转到"correct_cypher"节点尝试修复错误
        if (errors or mapping_errors) and GENERATION_ATTEMPT < max_attempts:
            next_action = "correct_cypher"
        # 如果未达到最大尝试次数，转到"execute_cypher"节点执行Cypher查询
        elif GENERATION_ATTEMPT < max_attempts:
            next_action = "execute_cypher"
        elif (
            GENERATION_ATTEMPT == max_attempts
            and attempt_cypher_execution_on_final_attempt
        ):
            next_action = "execute_cypher"
        else:
            next_action = "__end__"

        return {
            "next_action_cypher": next_action,
            "statement": corrected_cypher,
            "errors": errors,
            "attempts": GENERATION_ATTEMPT,
            "steps": ["validate_cypher"],
        }

    return validate_cypher
