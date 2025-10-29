from typing import Dict, List, Optional, Set

import neo4j

from ...embeddings import EmbedderProtocol
from ...exceptions import CypherQueryNodesReadError
from .models import CypherIngestRecord, EmbedderResult
from .utils import batch_data


def embed_cypher_query_nodes(
    embedder: EmbedderProtocol,
    nodes_to_embed: List[Dict[str, str]],
    embedding_model_name: Optional[str] = None,
) -> EmbedderResult:
    result = list()
    errored = list()

    if embedding_model_name is None:
        try:
            model = embedder.model  # type: ignore[attr-defined]
        except Exception as _:
            model = None
    else:
        model = embedding_model_name

    for batch in batch_data(nodes_to_embed, 10):
        for task in batch:
            q = task.get("question")
            cql = task.get("cql")
            if q is not None and cql is not None:
                vector = embedder.embed_query(q)
                result.append(
                    CypherIngestRecord(
                        cypher_statement=cql,
                        question=q,
                        question_embedding=vector,
                        embedding_model=model,
                    )
                )
            else:
                errored.append(task)

    return {"nodes": result, "failed": errored}


def load_cypher_query_nodes(
    driver: neo4j.Driver, nodes: List[CypherIngestRecord], database: str = "neo4j"
) -> None:
    query = """
UNWIND $tasks as task
MERGE (n:CypherQuery {question: task.question})
SET
    n.cypherStatement = task.cypher_statement,
    n.embeddingModel = task.embedding_model
WITH task, n
CALL db.create.setNodeVectorProperty(n, 'questionEmbedding', task.question_embedding)
"""

    with driver.session(database=database) as session:
        for idx, batch in enumerate(batch_data(nodes, 10)):
            # print("batch: ", batch)
            session.run(
                query=query, parameters={"tasks": [node.model_dump() for node in batch]}
            )


def get_existing_questions(
    driver: neo4j.Driver,
    node_label: str = "CypherQuery",
    embedding_property_name: str = "cypherStatement",
    database: str = "neo4j",
) -> Set[str]:
    try:
        query = f"""
    MATCH (n:{node_label})
    WHERE n.{embedding_property_name} IS NOT NULL
    RETURN n.question AS question
    """
        with driver.session(database=database) as session:
            result = session.run(query=query)

            questions = {
                str(r.get("question"))
                for r in result.data()
                if r.get("question") is not None
            }

        return questions
    except Exception as e:
        raise CypherQueryNodesReadError(e)
