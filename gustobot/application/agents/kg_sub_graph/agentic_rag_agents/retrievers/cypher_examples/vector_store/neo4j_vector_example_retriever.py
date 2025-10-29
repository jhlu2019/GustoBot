"""
LangChain Embedder Base: https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/embeddings/embeddings.py
Neo4j GraphRAG Embedder Base: https://github.com/neo4j/neo4j-graphrag-python/blob/main/src/neo4j_graphrag/embeddings/base.py
"""

from typing import Any, Dict, List

from neo4j import Driver, Record
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.types import RetrieverResultItem
from pydantic import Field

from ....embeddings import EmbedderProtocol
from ....exceptions import CypherExampleRetrieverError
from ..base import BaseCypherExampleRetriever


class Neo4jVectorSearchCypherExampleRetriever(BaseCypherExampleRetriever):
    neo4j_driver: Driver = Field(
        description="The Neo4j Python Driver to perform database operations with.",
    )
    neo4j_database: str = Field(
        default="neo4j", description="The Neo4j database name to connect to."
    )
    vector_index_name: str = Field(description="The name of the vector index to use.")
    embedder: EmbedderProtocol = Field(
        description="The embedder to generate an embedding from an input query."
    )

    def get_examples(self, query: str, k: int = 5, *args: Any, **kwargs: Any) -> str:
        """
        Perform vector similarity search between the provided query and queries that exist in the Neo4j database.
        Returns Cypher queries associated with the top K most similar query results.

        Parameters
        ----------
        query : str
            The query to match against.
        k: int, optional
            The number of Cypher statements to return.
        Returns
        -------
        str
            A list of examples as a string.
        """

        examples = self._retrieve_examples(query, k)
        if len(examples) > 0:
            return self._format_examples_list(examples)
        else:
            return ""

    def _retrieve_examples(self, query: str, k: int) -> List[Dict[str, Any]]:
        try:
            embedding = self._embed_query(query)

            retriever = VectorRetriever(
                driver=self.neo4j_driver,
                index_name=self.vector_index_name,
                neo4j_database=self.neo4j_database,
                result_formatter=self._result_formatter,
                return_properties=["question", "cypherStatement"],
            )

            result = retriever.search(query_vector=embedding, top_k=k)

            return [x.content for x in result.items]
        except Exception as e:
            raise CypherExampleRetrieverError(
                f"Error occurred while retrieving Cypher examples: {e}"
            )

    def _embed_query(self, query: str) -> List[float]:
        return self.embedder.embed_query(query)

    def _result_formatter(self, record: Record) -> RetrieverResultItem:
        """Format the returned result from the vector search."""

        return RetrieverResultItem(
            content=record.data().get("node", dict()), metadata=record.get("metadata")
        )

    def _format_examples_list(self, unformatted_examples: List[Dict[str, str]]) -> str:
        if len(unformatted_examples) > 0:
            return ("\n" * 2).join(
                [
                    f"Question: {el['question']}\nCypher:\n{el['cypherStatement']}"
                    for el in unformatted_examples
                ]
            )
        else:
            return ""
