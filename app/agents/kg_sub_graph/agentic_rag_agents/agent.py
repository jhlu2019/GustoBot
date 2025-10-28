"""This file is for LangGraph Studio testing."""

import os

from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from neo4j import GraphDatabase

from app.config import settings

from app.agents.kg_sub_graph.agentic_rag_agents.retrievers.cypher_examples import (
    recipe_retriever,
)

# from ps_genai_agents.workflows.single_agent import create_text2cypher_agent
from ps_genai_agents.workflows.multi_agent import (
    create_text2cypher_with_visualization_workflow,
)

neo4j_graph = Neo4jGraph(enhanced_schema=True)
llm = ChatOpenAI(
    openai_api_key=settings.OPENAI_API_KEY,
    openai_api_base=settings.OPENAI_API_BASE,
    model_name=settings.OPENAI_MODEL,
)
embedder = OpenAIEmbeddings(
    model=settings.EMBEDDING_MODEL,
    openai_api_key=settings.EMBEDDING_API_KEY or settings.OPENAI_API_KEY,
    openai_api_base=settings.EMBEDDING_BASE_URL or settings.OPENAI_API_BASE,
)

neo4j_uri = os.getenv("NEO4J_URI", "")
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")
auth = None
if neo4j_username and neo4j_password:
    auth = (neo4j_username, neo4j_password)

neo4j_driver = GraphDatabase.driver(uri=neo4j_uri, auth=auth)
vector_index_name = "cypher_query_vector_index"

cypher_example_retriever = Neo4jVectorSearchCypherExampleRetriever(
    neo4j_driver=neo4j_driver, vector_index_name=vector_index_name, embedder=embedder
)

# Create the graph to be found by LangGraph Studio
graph = create_text2cypher_with_visualization_workflow(
    llm=llm,
    cypher_example_retriever=cypher_example_retriever,
    llm_cypher_validation=False,
    graph=neo4j_graph,
)
