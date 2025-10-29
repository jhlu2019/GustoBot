from typing import Literal
from langchain_core.language_models import BaseChatModel
from langchain_neo4j import Neo4jGraph
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph

from ...components.state import (
    OverallState,
)
from ...components.text2cypher import (
    create_text2cypher_correction_node,
    create_text2cypher_execution_node,
    create_text2cypher_generation_node,
    create_text2cypher_validation_node,
)
from ...components.text2cypher.state import CypherInputState, CypherState
from ...retrievers.cypher_examples.base import BaseCypherExampleRetriever


def create_text2cypher_agent(
    llm: BaseChatModel,
    graph: Neo4jGraph,
    cypher_example_retriever: BaseCypherExampleRetriever,
    llm_cypher_validation: bool = True,
    max_attempts: int = 3,
    attempt_cypher_execution_on_final_attempt: bool = False,
) -> CompiledStateGraph:
    """
    Create a Text2Cypher agent using LangGraph.
    This agent contains only Text2cypher components with no guardrails, query parser or summarizer.
    This agent may be used as an independent workflow or a node in a larger LangGraph workflow.

    Parameters
    ----------
    graph : Neo4jGraph
        The Neo4j graph wrapper.
    llm : BaseChatModel
        The LLM to use for processing.
    cypher_example_retriever: BaseCypherExampleRetriever
        The retriever used to collect Cypher examples for few shot prompting.
    llm_cypher_validation : bool, optional
        Whether to perform LLM validation with the provided LLM, by default True
    max_attempts: int, optional
        The max number of allowed attempts to generate valid Cypher, by default 3
    attempt_cypher_execution_on_final_attempt, bool, optional
        THIS MAY BE DANGEROUS.
        Whether to attempt Cypher execution on the last attempt, regardless of if the Cypher contains errors, by default False

    Returns
    -------
    CompiledStateGraph
        The workflow.
    """

    # 1. 根据自定义的 Cypher 示例，引导大模型生成 当前输入 问题的 Cypher 查询语句
    generate_cypher = create_text2cypher_generation_node(
        llm=llm, graph=graph, cypher_example_retriever=cypher_example_retriever
    )
    # 2. 验证生成的 Cypher 查询语句是否正确
    validate_cypher = create_text2cypher_validation_node(
        llm=llm,
        graph=graph,
        llm_validation=llm_cypher_validation,
        max_attempts=max_attempts,
        attempt_cypher_execution_on_final_attempt=attempt_cypher_execution_on_final_attempt,
    )
    correct_cypher = create_text2cypher_correction_node(llm=llm, graph=graph)
    execute_cypher = create_text2cypher_execution_node(graph=graph)



    text2cypher_graph_builder = StateGraph(
        CypherState, input=CypherInputState, output=OverallState
    )

    text2cypher_graph_builder.add_node(generate_cypher)
    text2cypher_graph_builder.add_node(validate_cypher)
    text2cypher_graph_builder.add_node(correct_cypher)
    text2cypher_graph_builder.add_node(execute_cypher)

    text2cypher_graph_builder.add_edge(START, "generate_cypher")
    # text2cypher_graph_builder.add_edge("generate_cypher", "validate_cypher")
    # text2cypher_graph_builder.add_conditional_edges(
    #     "validate_cypher",
    #     validate_cypher_conditional_edge,
    # )
    # text2cypher_graph_builder.add_edge("correct_cypher", "validate_cypher")
    text2cypher_graph_builder.add_edge("generate_cypher", "execute_cypher")
    text2cypher_graph_builder.add_edge("execute_cypher", END)

    return text2cypher_graph_builder.compile()


def validate_cypher_conditional_edge(
    state: CypherState,
) -> Literal["correct_cypher", "execute_cypher", "__end__"]:
    match state.get("next_action_cypher"):
        case "correct_cypher":
            return "correct_cypher"
        case "execute_cypher":
            return "execute_cypher"
        case "__end__":
            return "__end__"
        case _:
            return "__end__"
