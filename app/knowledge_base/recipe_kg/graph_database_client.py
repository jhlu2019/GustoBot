"""
Neo4j数据库客户端封装
Simplified wrapper around the official neo4j driver to provide a small API
surface for the KBQA pipeline.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional

from neo4j import GraphDatabase, Result
from neo4j.graph import Graph


class Neo4jDatabase:
    """Thin wrapper around the neo4j driver."""

    def __init__(
        self,
        uri: str,
        user: Optional[str],
        password: Optional[str],
        **driver_kwargs: Any,
    ) -> None:
        auth = None
        if user and password not in (None, ""):
            auth = (user, password)

        self._driver = GraphDatabase.driver(uri, auth=auth, **driver_kwargs)

    def close(self) -> None:
        """Close the underlying driver."""
        if self._driver:
            self._driver.close()

    @contextmanager
    def _session(self):
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def execute(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """Execute a write query without returning records."""
        with self._session() as session:
            session.run(query, parameters or {})

    def fetch(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a read query and return records as dictionaries."""
        with self._session() as session:
            result: Result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def fetch_graph(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Graph:
        """Execute a read query and return the graph projection."""
        with self._session() as session:
            return session.read_transaction(lambda tx: tx.run(query, parameters or {}).graph())

    def fetch_records(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """Execute query and return raw records (for custom processing)."""
        with self._session() as session:
            result: Result = session.run(query, parameters or {})
            return list(result)
