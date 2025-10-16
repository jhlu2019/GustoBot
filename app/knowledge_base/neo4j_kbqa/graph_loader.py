"""
Graph loading and caching helpers for Neo4j projections.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from neo4j.graph import Graph, Node, Relationship


def _convert_node(node: Node) -> Dict[str, Any]:
    data = dict(node.items())
    data["id"] = node.id
    data["labels"] = list(node.labels)
    return data


def _convert_relationship(rel: Relationship) -> Dict[str, Any]:
    payload = dict(rel.items())
    payload["source"] = rel.start_node.id
    payload["target"] = rel.end_node.id
    payload["type"] = rel.type
    return payload


def convert_graph(graph: Graph) -> Dict[str, Any]:
    return {
        "nodes": [_convert_node(node) for node in graph.nodes],
        "relationships": [_convert_relationship(rel) for rel in graph.relationships],
    }


class GraphCache:
    """Simple file based cache for the default graph snapshot."""

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any] | None:
        if not self.cache_path.is_file():
            return None
        with self.cache_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def save(self, graph: Dict[str, Any]) -> None:
        with self.cache_path.open("w", encoding="utf-8") as fp:
            json.dump(graph, fp, ensure_ascii=False)

