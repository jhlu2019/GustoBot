from typing import Any, Callable, Coroutine, Dict, Union
import logging
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_neo4j import Neo4jGraph
from app.agents.kg_sub_graph.agentic_rag_agents.components.cypher_tools.prompts import create_text2cypher_generation_prompt_template, create_text2cypher_validation_prompt_template, create_text2cypher_correction_prompt_template
from app.agents.kg_sub_graph.agentic_rag_agents.retrievers.cypher_examples.base import BaseCypherExampleRetriever
from typing_extensions import TypedDict
from typing import Annotated, Any, Dict, List, Optional, Callable, Coroutine
from operator import add
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from langchain_neo4j.chains.graph_qa.cypher_utils import CypherQueryCorrector, Schema
from neo4j.exceptions import CypherSyntaxError
from app.agents.kg_sub_graph.agentic_rag_agents.components.utils.utils import (
    retrieve_and_parse_schema_from_graph_for_prompts,
)

# 设置Neo4j驱动的日志级别为ERROR，禁止WARNING消息
logging.getLogger("neo4j").setLevel(logging.ERROR)
# 禁用langchain_neo4j相关日志
logging.getLogger("langchain_neo4j").setLevel(logging.ERROR)
# 禁用驱动相关日志
logging.getLogger("neo4j.io").setLevel(logging.ERROR)
logging.getLogger("neo4j.bolt").setLevel(logging.ERROR)


class CypherInputState(TypedDict):
    task: Annotated[list, add]

class CypherState(TypedDict):
    task: Annotated[list, add]
    statement: str
    parameters: Optional[Dict[str, Any]]
    errors: List[str]
    records: List[Dict[str, Any]]
    next_action_cypher: str
    attempts: int
    steps: Annotated[List[str], add]

class CypherOutputState(TypedDict):
    task: Annotated[list, add]
    statement: str
    parameters: Optional[Dict[str, Any]]
    errors: List[str]
    records: List[Dict[str, Any]]
    steps: List[str]

class Property(BaseModel):
    """
    Represents a filter condition based on a specific node property in a graph in a Cypher statement.
    """

    node_label: str = Field(
        description="The label of the node to which this property belongs."
    )
    property_key: str = Field(description="The key of the property being filtered.")
    property_value: str = Field(
        description="The value that the property is being matched against.",
        coerce_numbers_to_str=True,
    )

class ValidateCypherOutput(BaseModel):
    """
    Represents the validation result of a Cypher query's output,
    including any errors and applied filters.
    """

    errors: Optional[List[str]] = Field(
        description="A list of syntax or semantical errors in the Cypher statement. Always explain the discrepancy between schema and Cypher statement"
    )
    filters: Optional[List[Property]] = Field(
        description="A list of property-based filters applied in the Cypher statement."
    )

# 定义text2cypher generation prompt
generation_prompt = create_text2cypher_generation_prompt_template()

# 定义text2cypher validation prompt
validation_prompt_template = create_text2cypher_validation_prompt_template()

# 定义text2cypher correction prompt
correction_cypher_prompt = create_text2cypher_correction_prompt_template()


def validate_cypher_query_syntax(graph: Neo4jGraph, cypher_statement: str) -> List[str]:
    """
    Validate the Cypher statement syntax by running an EXPLAIN query.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    List[str]
        If the statement contains invalid syntax, return an error message in a list
    """
    errors = list()
    try:
        # 使用 EXPLAIN 查询来验证Cypher语句的语法，仅仅查看语法是否正确，而不实际执行查询
        graph.query(f"EXPLAIN {cypher_statement}")
    except CypherSyntaxError as e:
        errors.append(str(e.message))
    return errors


def correct_cypher_query_relationship_direction(
    graph: Neo4jGraph, cypher_statement: str
) -> str:
    """
    Correct Relationship directions in the Cypher statement with LangChain's `CypherQueryCorrector`.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    str
        The Cypher statement with corrected Relationship directions.
    """
    # 从数据库中提取关系的结构性信息
    corrector_schema = [
        Schema(el["start"], el["type"], el["end"])
        for el in graph.structured_schema.get("relationships", list())
    ]

    # 使用langchain_neo4j 的CypherQueryCorrector 来校验Cypher语句的语法
    # 比如 ：MATCH (a:Person)-[r:FRIENDS_WITH]->(b:Person) ，如果r:FRIENDS_WITH 是反向的，则会被纠正为：MATCH (a:Person)-[r:FRIENDS_WITH]->(b:Person)
    cypher_query_corrector = CypherQueryCorrector(corrector_schema)

    corrected_cypher: str = cypher_query_corrector(cypher_statement)

    return corrected_cypher


async def validate_cypher_query_with_llm(
    validate_cypher_chain: Runnable[Dict[str, Any], Any],
    question: str,
    graph: Neo4jGraph,
    cypher_statement: str,
) -> Dict[str, List[str]]:
    """
    Validate the Cypher statement with an LLM.
    Use declared LLM to find Node and Property pairs to validate.
    Validate Node and Property pairs against the Neo4j graph.

    Parameters
    ----------
    validate_cypher_chain : RunnableSerializable
        The LangChain LLM to perform processing.
    question : str
        The question associated with the Cypher statement.
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    Dict[str, List[str]]
        A Python dictionary with keys `errors` and `mapping_errors`, each with a list of found errors.
    """

    errors: List[str] = []
    mapping_errors: List[str] = []


    # 使用大模型验证Cypher语句的语法， 通过 Pydantic 结构化输出
    llm_output: ValidateCypherOutput = await validate_cypher_chain.ainvoke(
        {
            "question": question,
            "schema": retrieve_and_parse_schema_from_graph_for_prompts(graph),
            "cypher": cypher_statement,
        }
    )

    # 如果 Pydantic 结构化输出中包含 errors，则将 errors 添加到 errors 列表中
    if llm_output.errors:
        errors.extend(llm_output.errors)
    # 如果 Pydantic 结构化输出中包含 filters，则遍历每个过滤器。
    if llm_output.filters:
        for filter in llm_output.filters:
            # 仅对字符串类型的属性进行映射检查。通过检查 graph.structured_schema 中的节点属性，判断属性类型是否为字符串。
            if (
                not [
                    prop
                    for prop in graph.structured_schema["node_props"][filter.node_label]
                    if prop["property"] == filter.property_key
                ][0]["type"]
                == "STRING"
            ):
                continue

            # 对于每个过滤器，构建一个 Cypher 查询，检查数据库中是否存在具有指定属性值的节点。
            mapping = graph.query(
                f"MATCH (n:{filter.node_label}) WHERE toLower(n.`{filter.property_key}`) = toLower($value) RETURN 'yes' LIMIT 1",
                {"value": filter.property_value},
            )
            if not mapping:
                mapping_error = f"Missing value mapping for {filter.node_label} on property {filter.property_key} with value {filter.property_value}"
                mapping_errors.append(mapping_error)
    return {"errors": errors, "mapping_errors": mapping_errors}


def validate_cypher_query_with_schema(
    graph: Neo4jGraph, cypher_statement: str
) -> List[str]:
    """
    Validate the provided Cypher statement using the schema retrieved from the graph.
    This will ensure the existance of names nodes, relationships and properties.
    This will validate property values with enums and number ranges, if available.
    This method does not use an LLM.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher_statement : str
        The Cypher to be validated.

    Returns
    -------
    List[str]
        A list of any found errors.
    """
    from app.agents.kg_sub_graph.agentic_rag_agents.components.text2cypher.validation.models import (
    CypherValidationTask,
    Neo4jStructuredSchema,
    Neo4jStructuredSchemaPropertyNumber,
)
    from app.agents.kg_sub_graph.agentic_rag_agents.components.text2cypher.validation.validators import (
    extract_entities_for_validation,
    update_task_list_with_property_type,
    _validate_node_property_names_with_enum,
    _validate_node_property_values_with_enum,
    _validate_node_property_values_with_range,
    _validate_relationship_property_names_with_enum,
    _validate_relationship_property_values_with_enum,
    _validate_relationship_property_values_with_range,
    )

    schema: Neo4jStructuredSchema = Neo4jStructuredSchema.model_validate(
        graph.get_structured_schema
    )
    nodes_and_rels = extract_entities_for_validation(cypher_statement=cypher_statement)

    node_tasks = update_task_list_with_property_type(
        nodes_and_rels.get("nodes", list()), schema, "node"
    )
    rel_tasks = update_task_list_with_property_type(
        nodes_and_rels.get("relationships", list()), schema, "rel"
    )

    errors: List[str] = list()

    node_prop_name_enum_tasks = node_tasks
    node_prop_val_enum_tasks = [n for n in node_tasks if n.property_type == "STRING"]
    node_prop_val_range_tasks = [
        n
        for n in node_tasks
        if (n.property_type == "INTEGER" or n.property_type == "FLOAT")
    ]

    rel_prop_name_enum_tasks = rel_tasks
    rel_prop_val_enum_tasks = [n for n in rel_tasks if n.property_type == "STRING"]
    rel_prop_val_range_tasks = [
        n
        for n in rel_tasks
        if (n.property_type == "INTEGER" or n.property_type == "FLOAT")
    ]

    errors.extend(
        _validate_node_property_names_with_enum(schema, node_prop_name_enum_tasks)
    )
    errors.extend(
        _validate_node_property_values_with_enum(schema, node_prop_val_enum_tasks)
    )
    errors.extend(
        _validate_node_property_values_with_range(schema, node_prop_val_range_tasks)
    )

    errors.extend(
        _validate_relationship_property_names_with_enum(
            schema, rel_prop_name_enum_tasks
        )
    )
    errors.extend(
        _validate_relationship_property_values_with_enum(
            schema, rel_prop_val_enum_tasks
        )
    )
    errors.extend(
        _validate_relationship_property_values_with_range(
            schema, rel_prop_val_range_tasks
        )
    )

    return errors


def validate_no_writes_in_cypher_query(cypher_statement: str) -> List[str]:
    """
    Validate whether the provided Cypher contains any write clauses.

    Parameters
    ----------
    cypher_statement : str
        The Cypher statement to validate.

    Returns
    -------
    List[str]
        A list of any found errors.
    """
    errors: List[str] = list()

    # 限制不允许使用写操作
    WRITE_CLAUSES = {
    "CREATE",
    "DELETE",
    "DETACH DELETE",
    "SET",
    "REMOVE",
    "FOREACH",
    "MERGE",
    }

    for wc in WRITE_CLAUSES:
        if wc in cypher_statement.upper():
            errors.append(f"Cypher contains write clause: {wc}")

    return errors


def create_text2cypher_generation_node(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    cypher_example_retriever: BaseCypherExampleRetriever,
) -> Callable[[CypherInputState], Coroutine[Any, Any, Dict[str, Any]]]:
    
    text2cypher_chain = generation_prompt | llm | StrOutputParser()

    async def generate_cypher(state: CypherInputState) -> Dict[str, Any]:
        """
        Generates a cypher statement based on the provided schema and user input
        """
        task = state.get("task", "")
        # 获取针对当前任务的cypher示例, 选择 k 个
        examples: str = cypher_example_retriever.get_examples(
            **{"query": task[0] if isinstance(task, list) else task, "k": 3}
        )
        generated_cypher = await text2cypher_chain.ainvoke(
            {
                "question": state.get("task", ""),
                "fewshot_examples": examples,
                "schema": graph.schema,
            }
        )
        return {
            "statement": generated_cypher,
            "steps": ["generate_cypher"],
        }

    return generate_cypher

def create_text2cypher_validation_node(
    graph: Neo4jGraph,
    llm: Optional[BaseChatModel] = None,
    llm_validation: bool = True,
) -> Callable[[CypherState], Coroutine[Any, Any, dict[str, Any]]]:
    """
    Create a Text2Cypher query validation node for a LangGraph workflow.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    llm : Optional[BaseChatModel], optional
        The LLM to use for processing if LLM validation is desired. By default None
    llm_validation : bool, optional
        Whether to perform LLM validation with the provided LLM, by default True
    Returns
    -------
    Callable[[CypherState], CypherState]
        The LangGraph node.
    """
    # 如果传递了 LLM， 则会借助大模型进行Cypher 校验：针对语法格式的
    if llm is not None and llm_validation:
        validate_cypher_chain = validation_prompt_template | llm.with_structured_output(
            ValidateCypherOutput
        )

    async def validate_cypher(state: CypherState) -> Dict[str, Any]:
        """
        Validates the Cypher statements and maps any property values to the database.
        """

        errors: List[str] = []
        mapping_errors = []
        cypher_statement = state.get("statement", "")

        # 1. 语法校验：检查Cypher查询的语法是否正确，例如括号匹配、关键字使用等。
        syntax_error = validate_cypher_query_syntax(
            graph=graph, cypher_statement=cypher_statement
        )
        errors.extend(syntax_error)

        # 检查Cypher查询中是否包含写操作(如CREATE、DELETE、SET等)，防止大模型意外修改数据库,
        write_errors = validate_no_writes_in_cypher_query(cypher_statement=cypher_statement)
        errors.extend(write_errors)

        # Neo4j的关系是有方向性的。这一步会检查关系方向是否正确，如果不正确，会尝试自动修复。这对提高查询成功率很重要。
        corrected_cypher = correct_cypher_query_relationship_direction(
            graph=graph, cypher_statement=cypher_statement
        )

        # 如果启用了大模型验证，会使用语言模型检查Cypher查询的更高级错误，
        # 例如语义上是否符合用户问题、属性映射是否正确等。这是一种更智能的验证方式。
        if llm is not None and llm_validation:
            llm_errors = await validate_cypher_query_with_llm(
                validate_cypher_chain=validate_cypher_chain,
                question=state.get("task", [""])[0] if isinstance(state.get("task", [""]), list) else state.get("task", ""),
                graph=graph,
                cypher_statement=cypher_statement,
            )
            errors.extend(llm_errors.get("errors", []))
            mapping_errors.extend(llm_errors.get("mapping_errors", []))

        # 如果禁用大模型验证，会使用更严格的模式检查Cypher查询，确保所有节点和关系都存在，并且属性值符合类型限制。
        if not llm_validation:
            cypher_errors = validate_cypher_query_with_schema(
                graph=graph, cypher_statement=cypher_statement
            )
            errors.extend(cypher_errors)

        # 区分真正的语法错误和数据不存在的情况
        # Map：mapping_errors: ['Missing value mapping for Order on property orderId with value 12345', 'Missing value mapping for Product on property ProductName with value 小米音箱']
        # Map 会表明你的Cypher查询语法是正确的，但查询中使用的具体值在数据库中不存在。这是数据不存在的问题，而不是查询语法的问题。
        if errors:  # 真正的语法错误
            correct_cypher_chain = correction_cypher_prompt | llm | StrOutputParser()
            corrected_cypher_update = correct_cypher_chain.ainvoke(
                {
                    "question": state.get("task"),
                    "errors": errors, 
                    "cypher": cypher_statement,
                    "schema": graph.schema,
                }
            )
            corrected_cypher = corrected_cypher_update
            next_action = "execute_cypher" 

        elif mapping_errors:  # 数据映射错误
            # TODO：1. 可以直接结束查询，告诉用户数据库中不存在 2. 可以再次引导用户提问，确认信息， 3. 也可以针对历史对话重新生成Cypher，再次尝试
            next_action = "execute_cypher"  # 或 "__end__"
        else:  # 没有错误
            next_action = "execute_cypher"

        # # 如果有错误且未达到最大尝试次数，转到"correct_cypher"节点尝试修复错误
        # if (errors or mapping_errors) and GENERATION_ATTEMPT < max_attempts:
        #     next_action = "correct_cypher"
        # # 如果未达到最大尝试次数，转到"execute_cypher"节点执行Cypher查询
        # elif GENERATION_ATTEMPT < max_attempts:
        #     next_action = "execute_cypher"
        # elif (
        #     GENERATION_ATTEMPT == max_attempts
        #     and attempt_cypher_execution_on_final_attempt
        # ):
        #     next_action = "execute_cypher"
        # else:
        #     next_action = "__end__"

        return {
            "next_action_cypher": next_action,
            "statement": corrected_cypher,
            "errors": errors,
            "steps": ["validate_cypher"],
        }

    return validate_cypher

def create_text2cypher_execution_node(
    graph: Neo4jGraph,
    cypher: Union[str, Dict[str, Any]],
) -> Callable[
    [CypherState], Coroutine[Any, Any, Dict[str, List[CypherOutputState] | List[str]]]
]:
    """
    Create a Text2Cypher execution node for a LangGraph workflow.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    cypher : Union[str, Dict[str, Any]]
        Cypher statement string or validation payload containing statement/errors.

    Returns
    -------
    Callable[[CypherState], Dict[str, List[CypherOutputState] | List[str]]]
        The LangGraph node.
    """

    async def execute_cypher(
        state: CypherState,
    ) -> Dict[str, List[CypherOutputState] | List[str]]:
        """
        Executes the given Cypher statement.
        """
        cypher_payload = cypher
        validation_errors: List[str] = []
        statement_raw = ""

        if isinstance(cypher_payload, str):
            statement_raw = cypher_payload
        elif isinstance(cypher_payload, dict):
            statement_raw = str(cypher_payload.get("statement", ""))
            validation_errors = cypher_payload.get("errors", []) or []
        else:
            raise TypeError(
                f"Unsupported cypher payload type: {type(cypher_payload)!r}. "
                "Expected str or dict with 'statement'/'errors'."
            )

        if not statement_raw:
            statement_raw = state.get("statement", "")

        # 清理cypher语句中的换行符
        cypher_statement = statement_raw.replace("\n", " ").strip()
        records = graph.query(cypher_statement)
        steps = state.get("steps", list())
        steps.append("execute_cypher")

        NO_CYPHER_RESULTS = [{"error": "在数据库中找不到任何相关信息。"}]
        combined_errors = validation_errors or state.get("errors", list())

        return {
            "cyphers": [
                CypherOutputState(
                    **{
                        "task": state.get("task", []),
                        "statement": cypher_statement,
                        "parameters": None,
                        "errors": combined_errors,
                        "records": records if records != [] else NO_CYPHER_RESULTS,
                        "steps": steps,
                    }
                )
            ],
            "steps": ["text2cypher"],
        }

    return execute_cypher
